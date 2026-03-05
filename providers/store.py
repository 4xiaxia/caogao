# -*- coding: utf-8 -*-
"""Provider store — persistence, CRUD, key rotation, and health tracking.

Design:
  - providers.json lives in WORKING_DIR (~/.copaw/), NOT inside the package
  - Users can add/edit/delete providers freely (no hardcoded constraints)
  - Multi-key pool with round-robin / random / failover rotation
  - Per-key health tracking with automatic backoff on failures
  - Full backward compat with v1 format (auto-migration)
"""

from __future__ import annotations

import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from constant import WORKING_DIR
from .models import (
    KeyEntry,
    KeyHealth,
    ModelSlotConfig,
    ProviderConfig,
    ProvidersData,
    ResolvedModelConfig,
    RotationStrategy,
)

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────
# Path management
# ───────────────────────────────────────────────────────────────────────────

_PROVIDERS_JSON = WORKING_DIR / "providers.json"

# Legacy path (inside package) — used only for migration
_LEGACY_PROVIDERS_JSON = Path(__file__).resolve().parent / "providers.json"

# Auto-backoff: disable key for N seconds after consecutive failures
_BACKOFF_SECONDS = [0, 0, 30, 60, 120, 300]  # indexed by consec. failures


def get_providers_json_path() -> Path:
    """Return the providers.json path (in WORKING_DIR)."""
    return _PROVIDERS_JSON


# ───────────────────────────────────────────────────────────────────────────
# Internal helpers
# ───────────────────────────────────────────────────────────────────────────


def _normalize_base_url(base_url: str) -> str:
    """Normalize OpenAI-compatible base URLs.

    Strips trailing slash and ``/chat/completions`` suffix so we always
    store the root (e.g. ``https://api.openai.com/v1``).
    """
    raw = (base_url or "").strip().rstrip("/")
    if raw.endswith("/chat/completions"):
        raw = raw[: -len("/chat/completions")]
    return raw


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ───────────────────────────────────────────────────────────────────────────
# V1 → V2 Migration
# ───────────────────────────────────────────────────────────────────────────


def _migrate_v1_to_v2(raw: dict) -> ProvidersData:
    """Convert v1 providers.json format to v2 ProvidersData.

    V1 had:
      { "providers": { "id": { "base_url", "api_key", "api_keys", ... } },
        "active_llm": { "provider_id", "model" } }
    """
    providers: Dict[str, ProviderConfig] = {}

    for pid, settings in raw.get("providers", {}).items():
        if not isinstance(settings, dict):
            continue

        base_url = _normalize_base_url(settings.get("base_url", ""))
        api_key = (settings.get("api_key", "") or "").strip()
        api_keys = settings.get("api_keys", [])

        # Build key pool from v1 data
        keys: List[KeyEntry] = []
        seen: set = set()
        for k in api_keys:
            k = k.strip()
            if k and k not in seen:
                keys.append(KeyEntry(key=k))
                seen.add(k)
        if api_key and api_key not in seen:
            keys.insert(0, KeyEntry(key=api_key))

        # Map old provider IDs to sensible names
        name_map = {
            "cli-openai": "OpenAI Compatible",
            "uji-fixed": "UJI",
            "custom": "Custom",
        }
        name = name_map.get(pid, pid)

        rotation = (
            RotationStrategy.RANDOM
            if settings.get("multi_key_enabled")
            else RotationStrategy.ROUND_ROBIN
        )

        providers[pid] = ProviderConfig(
            id=pid,
            name=name,
            base_url=base_url,
            keys=keys,
            rotation=rotation,
            models=[],
            enabled=True,
        )

    # Active LLM
    llm_raw = raw.get("active_llm", {})
    active_llm = ModelSlotConfig(
        provider_id=llm_raw.get("provider_id", ""),
        model=llm_raw.get("model", ""),
    )

    return ProvidersData(
        version=2,
        providers=providers,
        active_llm=active_llm,
    )


def _migrate_legacy_flat(raw: dict) -> ProvidersData:
    """Convert very old flat-format providers.json."""
    providers: Dict[str, ProviderConfig] = {}
    old_active = raw.get("active_provider", "")
    old_model = ""

    for key, value in raw.items():
        if key in ("active_provider", "active_llm"):
            continue
        if not isinstance(value, dict):
            continue
        model_val = value.pop("model", "")
        base_url = _normalize_base_url(value.get("base_url", ""))
        api_key = (value.get("api_key", "") or "").strip()
        keys = [KeyEntry(key=api_key)] if api_key else []
        providers[key] = ProviderConfig(
            id=key,
            name=key,
            base_url=base_url,
            keys=keys,
        )
        if key == old_active and model_val:
            old_model = model_val

    active_llm = (
        ModelSlotConfig(provider_id=old_active, model=old_model)
        if old_active
        else ModelSlotConfig()
    )

    return ProvidersData(version=2, providers=providers, active_llm=active_llm)


# ───────────────────────────────────────────────────────────────────────────
# Load / Save
# ───────────────────────────────────────────────────────────────────────────


def load_providers_json(
    path: Optional[Path] = None,
) -> ProvidersData:
    """Load providers.json from WORKING_DIR.

    - Auto-migrates from legacy in-package location on first run
    - Auto-migrates v1 format to v2
    - Creates empty v2 if nothing exists
    """
    if path is None:
        path = get_providers_json_path()

    raw: Optional[dict] = None

    # Try WORKING_DIR first
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Corrupt providers.json at %s: %s", path, e)

    # Fallback: migrate from legacy in-package location
    if raw is None and _LEGACY_PROVIDERS_JSON.is_file() and path == _PROVIDERS_JSON:
        try:
            with open(_LEGACY_PROVIDERS_JSON, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            logger.info(
                "Migrating providers.json from %s to %s",
                _LEGACY_PROVIDERS_JSON,
                path,
            )
        except (json.JSONDecodeError, ValueError):
            pass

    if raw is None:
        data = ProvidersData(version=2)
        save_providers_json(data, path)
        return data

    # Parse based on version
    version = raw.get("version", 1)

    if version >= 2:
        # V2 native format
        providers = {}
        for pid, praw in raw.get("providers", {}).items():
            if isinstance(praw, dict):
                # Ensure 'id' is set
                praw.setdefault("id", pid)
                providers[pid] = ProviderConfig.model_validate(praw)
        data = ProvidersData(
            version=2,
            providers=providers,
            active_llm=ModelSlotConfig.model_validate(
                raw.get("active_llm", {}),
            ),
            rotation_state=raw.get("rotation_state", {}),
            key_health={
                pid: {
                    k: KeyHealth.model_validate(v)
                    for k, v in kh.items()
                }
                for pid, kh in raw.get("key_health", {}).items()
                if isinstance(kh, dict)
            },
        )
    elif "providers" in raw and isinstance(raw["providers"], dict):
        # V1 new format
        data = _migrate_v1_to_v2(raw)
    else:
        # V1 legacy flat format
        data = _migrate_legacy_flat(raw)

    save_providers_json(data, path)
    return data


def save_providers_json(
    data: ProvidersData,
    path: Optional[Path] = None,
) -> None:
    """Write providers.json to WORKING_DIR with atomic tmp-write."""
    if path is None:
        path = get_providers_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    out: dict = {
        "version": 2,
        "providers": {
            pid: cfg.model_dump(mode="json")
            for pid, cfg in data.providers.items()
        },
        "active_llm": data.active_llm.model_dump(mode="json"),
        "rotation_state": data.rotation_state,
        "key_health": {
            pid: {k: v.model_dump(mode="json") for k, v in kh.items()}
            for pid, kh in data.key_health.items()
        },
    }

    # Atomic write: tmp file then rename
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


# ───────────────────────────────────────────────────────────────────────────
# Provider CRUD
# ───────────────────────────────────────────────────────────────────────────


def create_provider(
    *,
    provider_id: str,
    name: str,
    base_url: str = "",
    models: Optional[List[str]] = None,
    rotation: str = "round-robin",
) -> ProvidersData:
    """Create a new provider. Returns updated state.

    Raises ValueError if provider_id already exists.
    """
    data = load_providers_json()
    if provider_id in data.providers:
        raise ValueError(f"Provider '{provider_id}' already exists")

    try:
        rot = RotationStrategy(rotation)
    except ValueError:
        rot = RotationStrategy.ROUND_ROBIN

    data.providers[provider_id] = ProviderConfig(
        id=provider_id,
        name=name,
        base_url=_normalize_base_url(base_url),
        models=models or [],
        rotation=rot,
    )
    save_providers_json(data)
    return data


def update_provider(
    provider_id: str,
    *,
    name: Optional[str] = None,
    base_url: Optional[str] = None,
    models: Optional[List[str]] = None,
    rotation: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> ProvidersData:
    """Update provider fields. Returns updated state.

    Raises KeyError if provider not found.
    """
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise KeyError(f"Provider '{provider_id}' not found")

    if name is not None:
        cfg.name = name
    if base_url is not None:
        cfg.base_url = _normalize_base_url(base_url)
    if models is not None:
        cfg.models = models
    if rotation is not None:
        try:
            cfg.rotation = RotationStrategy(rotation)
        except ValueError:
            pass
    if enabled is not None:
        cfg.enabled = enabled

    save_providers_json(data)
    return data


def delete_provider(provider_id: str) -> ProvidersData:
    """Delete a provider. Returns updated state.

    If this was the active LLM, clears the active slot.
    Raises KeyError if provider not found.
    """
    data = load_providers_json()
    if provider_id not in data.providers:
        raise KeyError(f"Provider '{provider_id}' not found")

    del data.providers[provider_id]
    data.rotation_state.pop(provider_id, None)
    data.key_health.pop(provider_id, None)

    if data.active_llm.provider_id == provider_id:
        data.active_llm = ModelSlotConfig()

    save_providers_json(data)
    return data


# ───────────────────────────────────────────────────────────────────────────
# Key Pool CRUD
# ───────────────────────────────────────────────────────────────────────────


def add_key(
    provider_id: str,
    key: str,
    label: str = "",
) -> ProvidersData:
    """Add an API key to a provider's pool. Returns updated state."""
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise KeyError(f"Provider '{provider_id}' not found")

    # Deduplicate
    existing = {ke.key for ke in cfg.keys}
    key = key.strip()
    if key and key not in existing:
        cfg.keys.append(KeyEntry(key=key, label=label))

    save_providers_json(data)
    return data


def remove_key(
    provider_id: str,
    key_index: int,
) -> ProvidersData:
    """Remove an API key by index. Returns updated state."""
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise KeyError(f"Provider '{provider_id}' not found")

    if 0 <= key_index < len(cfg.keys):
        removed = cfg.keys.pop(key_index)
        # Clean up health for this key
        kh = data.key_health.get(provider_id, {})
        kh.pop(removed.key, None)
    else:
        raise IndexError(f"Key index {key_index} out of range")

    # If no keys left and this was active, clear active slot
    if not cfg.keys and data.active_llm.provider_id == provider_id:
        data.active_llm = ModelSlotConfig()

    save_providers_json(data)
    return data


def toggle_key(
    provider_id: str,
    key_index: int,
    enabled: bool,
) -> ProvidersData:
    """Enable/disable a key by index. Returns updated state."""
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise KeyError(f"Provider '{provider_id}' not found")

    if 0 <= key_index < len(cfg.keys):
        cfg.keys[key_index].enabled = enabled
    else:
        raise IndexError(f"Key index {key_index} out of range")

    save_providers_json(data)
    return data


def batch_add_keys(
    provider_id: str,
    keys_csv: str,
    label: str = "",
) -> ProvidersData:
    """Add multiple keys from a comma-separated string."""
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise KeyError(f"Provider '{provider_id}' not found")

    existing = {ke.key for ke in cfg.keys}
    for k in keys_csv.split(","):
        k = k.strip()
        if k and k not in existing:
            cfg.keys.append(KeyEntry(key=k, label=label))
            existing.add(k)

    save_providers_json(data)
    return data


# ───────────────────────────────────────────────────────────────────────────
# Active LLM Slot
# ───────────────────────────────────────────────────────────────────────────


def set_active_llm(provider_id: str, model: str) -> ProvidersData:
    """Set the active LLM slot. Returns updated state."""
    data = load_providers_json()
    data.active_llm = ModelSlotConfig(provider_id=provider_id, model=model)
    save_providers_json(data)
    return data


# ───────────────────────────────────────────────────────────────────────────
# Key Rotation — smart selection
# ───────────────────────────────────────────────────────────────────────────


def _get_enabled_keys(
    cfg: ProviderConfig,
    health: Dict[str, KeyHealth],
) -> List[KeyEntry]:
    """Return keys that are enabled and not in backoff period."""
    now = datetime.now(timezone.utc)
    result = []
    for ke in cfg.keys:
        if not ke.enabled:
            continue
        kh = health.get(ke.key)
        if kh and kh.disabled_until:
            try:
                until = datetime.fromisoformat(kh.disabled_until)
                if now < until:
                    continue  # Still in backoff
            except ValueError:
                pass
        result.append(ke)
    return result


def _select_key(
    cfg: ProviderConfig,
    data: ProvidersData,
) -> Optional[str]:
    """Select an API key using the configured rotation strategy.

    Returns the key string, or None if no keys available.
    """
    health = data.key_health.get(cfg.id, {})
    available = _get_enabled_keys(cfg, health)

    if not available:
        # Fallback: try ALL enabled keys ignoring backoff
        available = [ke for ke in cfg.keys if ke.enabled]
    if not available:
        # Last resort: try all keys
        available = cfg.keys
    if not available:
        return None

    strategy = cfg.rotation

    if strategy == RotationStrategy.RANDOM:
        return random.choice(available).key

    elif strategy == RotationStrategy.FAILOVER:
        # Always use first available
        return available[0].key

    else:
        # Round-robin (default)
        idx = data.rotation_state.get(cfg.id, 0)
        idx = idx % len(available)
        selected = available[idx].key
        # Advance index
        data.rotation_state[cfg.id] = (idx + 1) % len(available)
        save_providers_json(data)
        return selected


# ───────────────────────────────────────────────────────────────────────────
# Key Health Tracking
# ───────────────────────────────────────────────────────────────────────────


def report_key_success(provider_id: str, api_key: str) -> None:
    """Report a successful API call — resets failure counter."""
    data = load_providers_json()
    kh = data.key_health.setdefault(provider_id, {})
    health = kh.get(api_key, KeyHealth())
    health.consecutive_failures = 0
    health.last_success_at = _now_iso()
    health.total_requests += 1
    health.disabled_until = None
    kh[api_key] = health
    save_providers_json(data)


def report_key_failure(provider_id: str, api_key: str) -> None:
    """Report a failed API call — may trigger backoff disable."""
    data = load_providers_json()
    kh = data.key_health.setdefault(provider_id, {})
    health = kh.get(api_key, KeyHealth())
    health.consecutive_failures += 1
    health.last_failure_at = _now_iso()
    health.total_requests += 1
    health.total_failures += 1

    # Auto-backoff
    cf = min(health.consecutive_failures, len(_BACKOFF_SECONDS) - 1)
    backoff = _BACKOFF_SECONDS[cf]
    if backoff > 0:
        until = datetime.now(timezone.utc).timestamp() + backoff
        health.disabled_until = datetime.fromtimestamp(
            until,
            tz=timezone.utc,
        ).isoformat()
        logger.warning(
            "Key %s...%s disabled for %ds after %d consecutive failures",
            api_key[:8],
            api_key[-4:] if len(api_key) > 4 else "",
            backoff,
            health.consecutive_failures,
        )

    kh[api_key] = health
    save_providers_json(data)


# ───────────────────────────────────────────────────────────────────────────
# Query — resolved config for agent use
# ───────────────────────────────────────────────────────────────────────────


def get_active_llm_config() -> Optional[ResolvedModelConfig]:
    """Resolve the active LLM slot to (model, base_url, api_key).

    Returns None if no active LLM is configured or no keys available.
    """
    data = load_providers_json()
    slot = data.active_llm

    if not slot.provider_id or not slot.model:
        return None

    cfg = data.providers.get(slot.provider_id)
    if cfg is None or not cfg.enabled:
        return None

    selected_key = _select_key(cfg, data)

    return ResolvedModelConfig(
        model=slot.model,
        base_url=_normalize_base_url(cfg.base_url),
        api_key=selected_key or "",
    )


# ───────────────────────────────────────────────────────────────────────────
# Legacy compat helpers
# ───────────────────────────────────────────────────────────────────────────


def update_provider_settings(
    provider_id: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    multi_key_enabled: Optional[bool] = None,
) -> ProvidersData:
    """Legacy compat — update provider via old-style parameters.

    Translates to new ProviderConfig format internally.
    """
    data = load_providers_json()
    cfg = data.providers.get(provider_id)

    if cfg is None:
        # Auto-create provider for legacy callers
        cfg = ProviderConfig(
            id=provider_id,
            name=provider_id,
        )
        data.providers[provider_id] = cfg

    if base_url is not None:
        cfg.base_url = _normalize_base_url(base_url)

    if api_key is not None:
        # Parse comma-separated keys into pool
        new_keys = [k.strip() for k in api_key.split(",") if k.strip()]
        if not new_keys and api_key.strip():
            new_keys = [api_key.strip()]
        cfg.keys = [KeyEntry(key=k) for k in new_keys]

    if multi_key_enabled is not None:
        cfg.rotation = (
            RotationStrategy.RANDOM
            if multi_key_enabled
            else RotationStrategy.ROUND_ROBIN
        )

    # Clear active LLM if keys were emptied
    if api_key == "" and data.active_llm.provider_id == provider_id:
        data.active_llm = ModelSlotConfig()

    save_providers_json(data)
    return data


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """Mask an API key for safe display.

    Example: ``"sk-abcdefghijk"`` → ``"sk-****hijk"``
    """
    if not api_key:
        return ""
    if len(api_key) <= visible_chars:
        return "*" * len(api_key)
    prefix = api_key[:3] if len(api_key) > 3 else ""
    suffix = api_key[-visible_chars:]
    hidden_len = len(api_key) - len(prefix) - visible_chars
    return f"{prefix}{'*' * max(hidden_len, 4)}{suffix}"
