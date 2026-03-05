# -*- coding: utf-8 -*-
"""API routes for LLM providers, key pools, and model management.

Design principles:
  - Zero vendor lock-in: any OpenAI-compatible endpoint works
  - Full CRUD for providers (create/read/update/delete)
  - Key pool management with rotation strategies
  - Connectivity health check + model discovery
  - Streaming verification endpoint
  - Backward compatible with existing frontend (GET /models, PUT /active)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from pydantic import BaseModel, Field

from providers import (
    PROVIDER_PRESETS,
    ActiveModelsInfo,
    KeyInfoMasked,
    ModelSlotConfig,
    ProviderConfig,
    ProviderHealthResult,
    ProviderInfo,
    ProvidersData,
    add_key,
    batch_add_keys,
    create_provider,
    delete_provider,
    get_active_llm_config,
    get_preset,
    list_presets,
    load_providers_json,
    mask_api_key,
    remove_key,
    set_active_llm,
    toggle_key,
    update_provider,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


# ───────────────────────────────────────────────────────────────────────────
# Request schemas
# ───────────────────────────────────────────────────────────────────────────


class CreateProviderRequest(BaseModel):
    """Create a new provider."""

    id: str = Field(..., description="Unique slug (e.g. 'my-openai')")
    name: str = Field(..., description="Display name")
    base_url: str = Field(
        default="",
        description="OpenAI-compatible API base URL",
    )
    models: List[str] = Field(
        default_factory=list,
        description="Known model IDs",
    )
    rotation: str = Field(
        default="round-robin",
        description="Key rotation: round-robin | random | failover",
    )


class UpdateProviderRequest(BaseModel):
    """Update provider fields (partial)."""

    name: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[List[str]] = None
    rotation: Optional[str] = None
    enabled: Optional[bool] = None


class AddKeyRequest(BaseModel):
    """Add one or more API keys."""

    keys: str = Field(
        ...,
        description="API key(s) — single key or comma-separated for batch",
    )
    label: str = Field(default="", description="Optional label for the key(s)")


class ToggleKeyRequest(BaseModel):
    """Enable/disable a key by index."""

    enabled: bool


class ModelSlotRequest(BaseModel):
    """Set the active LLM slot."""

    provider_id: str = Field(..., description="Provider to use")
    model: str = Field(..., description="Model identifier")


class InstallPresetRequest(BaseModel):
    """Install a provider preset."""

    preset_id: str = Field(..., description="Preset ID to install")


# Legacy compat
class ProviderConfigRequest(BaseModel):
    """Legacy: configure api_key/base_url (for existing frontend)."""

    api_key: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)
    multi_key_enabled: Optional[bool] = Field(default=None)


# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────


def _build_provider_info(cfg: ProviderConfig, data: ProvidersData) -> ProviderInfo:
    """Build a ProviderInfo response from a ProviderConfig."""
    health_map = data.key_health.get(cfg.id, {})

    keys_masked = []
    for ke in cfg.keys:
        kh = health_map.get(ke.key)
        keys_masked.append(
            KeyInfoMasked(
                label=ke.label,
                masked_key=mask_api_key(ke.key),
                enabled=ke.enabled,
                health=kh,
            ),
        )

    first_key = cfg.keys[0].key if cfg.keys else ""
    is_configured = bool(cfg.base_url and cfg.keys)

    return ProviderInfo(
        id=cfg.id,
        name=cfg.name,
        base_url=cfg.base_url,
        keys=keys_masked,
        key_count=len(cfg.keys),
        rotation=cfg.rotation.value if hasattr(cfg.rotation, "value") else str(cfg.rotation),
        models=cfg.models,
        enabled=cfg.enabled,
        is_configured=is_configured,
        # Legacy compat fields
        has_api_key=bool(cfg.keys),
        current_api_key=mask_api_key(first_key),
        current_base_url=cfg.base_url,
        api_key_prefix="",
        allow_custom_base_url=True,
        multi_key_enabled=len(cfg.keys) > 1,
        api_key_count=len(cfg.keys),
    )


# ───────────────────────────────────────────────────────────────────────────
# Provider List & Create (root "")
# ───────────────────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=List[ProviderInfo],
    summary="List all providers",
)
async def list_all_providers() -> List[ProviderInfo]:
    """Return all configured providers with masked keys."""
    data = load_providers_json()
    return [_build_provider_info(cfg, data) for cfg in data.providers.values()]


@router.post(
    "",
    response_model=ProviderInfo,
    summary="Create a new provider",
    status_code=201,
)
async def create_new_provider(
    body: CreateProviderRequest = Body(...),
) -> ProviderInfo:
    """Create a provider with custom base_url. No vendor restrictions."""
    try:
        data = create_provider(
            provider_id=body.id,
            name=body.name,
            base_url=body.base_url,
            models=body.models,
            rotation=body.rotation,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return _build_provider_info(data.providers[body.id], data)


# ───────────────────────────────────────────────────────────────────────────
# Active LLM Slot  (MUST be before /{provider_id} to avoid path clash)
# ───────────────────────────────────────────────────────────────────────────


@router.get(
    "/active",
    response_model=ActiveModelsInfo,
    summary="Get active LLM slot",
)
async def get_active_models() -> ActiveModelsInfo:
    """Return the currently active provider + model selection."""
    data = load_providers_json()
    return ActiveModelsInfo(active_llm=data.active_llm)


@router.put(
    "/active",
    response_model=ActiveModelsInfo,
    summary="Set active LLM slot",
)
async def set_active_model(
    body: ModelSlotRequest = Body(...),
) -> ActiveModelsInfo:
    """Choose a provider + model as the active LLM."""
    data = load_providers_json()
    cfg = data.providers.get(body.provider_id)
    if cfg is None:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{body.provider_id}' not found",
        )

    if not cfg.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{cfg.name}' is disabled",
        )

    if not cfg.base_url:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{cfg.name}' has no base_url configured",
        )

    if not cfg.keys:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{cfg.name}' has no API keys. Add at least one key first.",
        )

    if not body.model:
        raise HTTPException(status_code=400, detail="Model is required")

    data = set_active_llm(body.provider_id, body.model)
    return ActiveModelsInfo(active_llm=data.active_llm)


# ───────────────────────────────────────────────────────────────────────────
# Presets  (MUST be before /{provider_id} to avoid path clash)
# ───────────────────────────────────────────────────────────────────────────


class PresetInfo(BaseModel):
    """Preset info for API response."""

    id: str
    name: str
    base_url: str
    models: List[str]
    installed: bool = False


@router.get(
    "/presets",
    response_model=List[PresetInfo],
    summary="List available provider presets",
)
async def list_available_presets() -> List[PresetInfo]:
    """Return all provider presets with installation status."""
    data = load_providers_json()
    result = []
    for preset in list_presets():
        result.append(
            PresetInfo(
                id=preset.id,
                name=preset.name,
                base_url=preset.base_url,
                models=preset.models,
                installed=preset.id in data.providers,
            ),
        )
    return result


@router.post(
    "/presets/install",
    response_model=ProviderInfo,
    summary="Install a provider preset",
    status_code=201,
)
async def install_preset(
    body: InstallPresetRequest = Body(...),
) -> ProviderInfo:
    """Install a preset as a new provider. User still needs to add API key(s)."""
    preset = get_preset(body.preset_id)
    if preset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{body.preset_id}' not found",
        )

    data = load_providers_json()
    if preset.id in data.providers:
        # Already installed — return as-is
        return _build_provider_info(data.providers[preset.id], data)

    try:
        data = create_provider(
            provider_id=preset.id,
            name=preset.name,
            base_url=preset.base_url,
            models=preset.models,
            rotation=preset.rotation.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return _build_provider_info(data.providers[preset.id], data)


# ───────────────────────────────────────────────────────────────────────────
# Provider CRUD  (parameterised /{provider_id} — after all literal routes)
# ───────────────────────────────────────────────────────────────────────────


@router.get(
    "/{provider_id}",
    response_model=ProviderInfo,
    summary="Get a single provider",
)
async def get_single_provider(
    provider_id: str = Path(...),
) -> ProviderInfo:
    """Return a single provider's info."""
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    return _build_provider_info(cfg, data)


@router.put(
    "/{provider_id}",
    response_model=ProviderInfo,
    summary="Update a provider",
)
async def update_existing_provider(
    provider_id: str = Path(...),
    body: UpdateProviderRequest = Body(...),
) -> ProviderInfo:
    """Update provider fields (name, base_url, models, rotation, enabled)."""
    try:
        data = update_provider(
            provider_id,
            name=body.name,
            base_url=body.base_url,
            models=body.models,
            rotation=body.rotation,
            enabled=body.enabled,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _build_provider_info(data.providers[provider_id], data)


@router.delete(
    "/{provider_id}",
    summary="Delete a provider",
)
async def delete_existing_provider(
    provider_id: str = Path(...),
) -> Dict[str, str]:
    """Delete a provider and all its keys."""
    try:
        delete_provider(provider_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "deleted", "provider_id": provider_id}


# Legacy compat endpoint
@router.put(
    "/{provider_id}/config",
    response_model=ProviderInfo,
    summary="Configure a provider (legacy)",
)
async def configure_provider_legacy(
    provider_id: str = Path(...),
    body: ProviderConfigRequest = Body(...),
) -> ProviderInfo:
    """Legacy endpoint: set api_key/base_url/multi_key_enabled."""
    from providers import update_provider_settings

    data = update_provider_settings(
        provider_id,
        api_key=body.api_key,
        base_url=body.base_url,
        multi_key_enabled=body.multi_key_enabled,
    )

    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    return _build_provider_info(cfg, data)


# ───────────────────────────────────────────────────────────────────────────
# Key Pool Management
# ───────────────────────────────────────────────────────────────────────────


@router.post(
    "/{provider_id}/keys",
    response_model=ProviderInfo,
    summary="Add API key(s) to pool",
)
async def add_provider_keys(
    provider_id: str = Path(...),
    body: AddKeyRequest = Body(...),
) -> ProviderInfo:
    """Add one or more API keys (comma-separated for batch)."""
    try:
        data = batch_add_keys(provider_id, body.keys, body.label)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _build_provider_info(data.providers[provider_id], data)


@router.delete(
    "/{provider_id}/keys/{key_index}",
    response_model=ProviderInfo,
    summary="Remove an API key by index",
)
async def remove_provider_key(
    provider_id: str = Path(...),
    key_index: int = Path(..., ge=0),
) -> ProviderInfo:
    """Remove an API key from the pool by its index."""
    try:
        data = remove_key(provider_id, key_index)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _build_provider_info(data.providers[provider_id], data)


@router.put(
    "/{provider_id}/keys/{key_index}/toggle",
    response_model=ProviderInfo,
    summary="Enable/disable a key",
)
async def toggle_provider_key(
    provider_id: str = Path(...),
    key_index: int = Path(..., ge=0),
    body: ToggleKeyRequest = Body(...),
) -> ProviderInfo:
    """Enable or disable a specific key in the pool."""
    try:
        data = toggle_key(provider_id, key_index, body.enabled)
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=404 if isinstance(e, KeyError) else 400,
            detail=str(e),
        )
    return _build_provider_info(data.providers[provider_id], data)


# ───────────────────────────────────────────────────────────────────────────
# Health Check & Model Discovery
# ───────────────────────────────────────────────────────────────────────────


@router.post(
    "/{provider_id}/test",
    response_model=ProviderHealthResult,
    summary="Test provider connectivity",
)
async def test_provider(
    provider_id: str = Path(...),
) -> ProviderHealthResult:
    """Test connectivity to the provider by calling GET /models.

    This probes the OpenAI-compatible ``/v1/models`` endpoint to verify
    the base_url and API key work, measures latency, and returns
    discovered models.
    """
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    if not cfg.base_url:
        return ProviderHealthResult(
            provider_id=provider_id,
            reachable=False,
            error="No base_url configured",
        )

    # Pick a key for the test
    test_key = ""
    for ke in cfg.keys:
        if ke.enabled:
            test_key = ke.key
            break
    if not test_key and cfg.keys:
        test_key = cfg.keys[0].key

    import httpx

    base = cfg.base_url.rstrip("/")
    models_url = f"{base}/models"
    headers = {}
    if test_key:
        headers["Authorization"] = f"Bearer {test_key}"

    try:
        t0 = time.monotonic()
        transport = httpx.AsyncHTTPTransport(http1=True, http2=False)
        async with httpx.AsyncClient(timeout=15.0, transport=transport) as client:
            resp = await client.get(models_url, headers=headers)
        latency = (time.monotonic() - t0) * 1000

        if resp.status_code == 200:
            body = resp.json()
            models: List[str] = []
            if isinstance(body, dict) and "data" in body:
                for m in body["data"]:
                    if isinstance(m, dict) and "id" in m:
                        models.append(m["id"])
            return ProviderHealthResult(
                provider_id=provider_id,
                reachable=True,
                latency_ms=round(latency, 1),
                models_discovered=sorted(models),
            )
        else:
            return ProviderHealthResult(
                provider_id=provider_id,
                reachable=False,
                latency_ms=round(latency, 1),
                error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            )

    except Exception as e:
        return ProviderHealthResult(
            provider_id=provider_id,
            reachable=False,
            error=str(e)[:300],
        )


@router.post(
    "/{provider_id}/discover-models",
    response_model=ProviderInfo,
    summary="Discover and update model list from provider",
)
async def discover_models(
    provider_id: str = Path(...),
) -> ProviderInfo:
    """Call /v1/models and update the provider's model list."""
    result = await test_provider(provider_id)
    if not result.reachable:
        raise HTTPException(
            status_code=502,
            detail=result.error or "Provider unreachable",
        )

    if result.models_discovered:
        data = update_provider(provider_id, models=result.models_discovered)
        return _build_provider_info(data.providers[provider_id], data)

    # No models discovered — return current state
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return _build_provider_info(cfg, data)


@router.post(
    "/{provider_id}/test-streaming",
    response_model=ProviderHealthResult,
    summary="Test streaming support",
)
async def test_streaming(
    provider_id: str = Path(...),
) -> ProviderHealthResult:
    """Send a minimal streaming request to verify SSE works.

    Sends: ``POST /chat/completions`` with ``stream=true`` and a tiny prompt.
    Validates that the response is chunked SSE (``text/event-stream``).
    """
    data = load_providers_json()
    cfg = data.providers.get(provider_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    if not cfg.base_url:
        return ProviderHealthResult(
            provider_id=provider_id,
            reachable=False,
            error="No base_url configured",
        )

    test_key = ""
    for ke in cfg.keys:
        if ke.enabled:
            test_key = ke.key
            break

    # Use first known model or "gpt-4o-mini" as test model
    test_model = cfg.models[0] if cfg.models else "gpt-4o-mini"

    import httpx

    base = cfg.base_url.rstrip("/")
    url = f"{base}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if test_key:
        headers["Authorization"] = f"Bearer {test_key}"

    payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "Say hi"}],
        "stream": True,
        "max_tokens": 5,
    }

    try:
        t0 = time.monotonic()
        transport = httpx.AsyncHTTPTransport(http1=True, http2=False)
        async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                latency = (time.monotonic() - t0) * 1000

                if resp.status_code != 200:
                    body = await resp.aread()
                    return ProviderHealthResult(
                        provider_id=provider_id,
                        reachable=True,
                        latency_ms=round(latency, 1),
                        streaming_ok=False,
                        error=f"HTTP {resp.status_code}: {body.decode()[:200]}",
                    )

                # Read first chunk to verify streaming
                content_type = resp.headers.get("content-type", "")
                is_sse = "text/event-stream" in content_type
                got_chunk = False
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        got_chunk = True
                        break

                return ProviderHealthResult(
                    provider_id=provider_id,
                    reachable=True,
                    latency_ms=round(latency, 1),
                    streaming_ok=is_sse and got_chunk,
                    error=None if (is_sse and got_chunk) else f"Content-Type: {content_type}, chunk received: {got_chunk}",
                )

    except Exception as e:
        return ProviderHealthResult(
            provider_id=provider_id,
            reachable=False,
            streaming_ok=False,
            error=str(e)[:300],
        )
