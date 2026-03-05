# -*- coding: utf-8 -*-
"""Pydantic data models for the provider system.

Design principles:
  - Zero vendor lock-in: any OpenAI-compatible endpoint works
  - Multi-key pool with smart rotation (round-robin / random / failover)
  - User-definable providers via web UI — no hardcoded constraints
  - Backward compatible with v1 providers.json format
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ───────────────────────────────────────────────────────────────────────────
# Enums
# ───────────────────────────────────────────────────────────────────────────


class RotationStrategy(str, Enum):
    """Key rotation strategy for multi-key pools."""

    ROUND_ROBIN = "round-robin"  # Deterministic, even distribution
    RANDOM = "random"  # Random pick each request
    FAILOVER = "failover"  # First key primary, switch on failure


# ───────────────────────────────────────────────────────────────────────────
# Key Pool
# ───────────────────────────────────────────────────────────────────────────


class KeyEntry(BaseModel):
    """A single API key in the pool."""

    key: str = Field(..., description="API key value")
    label: str = Field(
        default="",
        description="User-friendly label (e.g. 'personal', 'team-A')",
    )
    enabled: bool = Field(default=True, description="Whether this key is active")


class KeyHealth(BaseModel):
    """Per-key health tracking (persisted in providers.json)."""

    consecutive_failures: int = 0
    last_failure_at: Optional[str] = None  # ISO datetime
    last_success_at: Optional[str] = None  # ISO datetime
    total_requests: int = 0
    total_failures: int = 0
    disabled_until: Optional[str] = None  # ISO datetime — auto-backoff


# ───────────────────────────────────────────────────────────────────────────
# Provider Config (unified: replaces ProviderDefinition + ProviderSettings)
# ───────────────────────────────────────────────────────────────────────────


class ProviderConfig(BaseModel):
    """A single LLM provider — fully user-configurable.

    This is the core storage unit in providers.json.
    Every field is editable via the web UI.
    """

    id: str = Field(..., description="Unique provider identifier (slug)")
    name: str = Field(..., description="Display name")
    base_url: str = Field(
        default="",
        description="OpenAI-compatible base URL (e.g. https://api.openai.com/v1)",
    )
    keys: List[KeyEntry] = Field(
        default_factory=list,
        description="API key pool",
    )
    rotation: RotationStrategy = Field(
        default=RotationStrategy.ROUND_ROBIN,
        description="Key rotation strategy",
    )
    models: List[str] = Field(
        default_factory=list,
        description="Known model IDs (user-added or discovered)",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this provider is available for selection",
    )


# ───────────────────────────────────────────────────────────────────────────
# Active LLM Slot
# ───────────────────────────────────────────────────────────────────────────


class ModelSlotConfig(BaseModel):
    """Identifies the currently active provider + model."""

    provider_id: str = Field(default="", description="Selected provider ID")
    model: str = Field(default="", description="Selected model identifier")


# ───────────────────────────────────────────────────────────────────────────
# Top-level persistence (providers.json v2, stored in ~/.copaw/)
# ───────────────────────────────────────────────────────────────────────────


class ProvidersData(BaseModel):
    """Top-level structure of providers.json (v2)."""

    version: int = Field(default=2)
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    active_llm: ModelSlotConfig = Field(default_factory=ModelSlotConfig)
    # Round-robin index per provider (persisted for determinism)
    rotation_state: Dict[str, int] = Field(default_factory=dict)
    # Per-provider per-key health tracking
    key_health: Dict[str, Dict[str, KeyHealth]] = Field(default_factory=dict)


# ───────────────────────────────────────────────────────────────────────────
# API Response Models
# ───────────────────────────────────────────────────────────────────────────


class KeyInfoMasked(BaseModel):
    """API key info with the key value masked for safe display."""

    label: str = ""
    masked_key: str = ""
    enabled: bool = True
    health: Optional[KeyHealth] = None


class ProviderInfo(BaseModel):
    """Provider info returned by the API — keys masked, ready for UI."""

    id: str
    name: str
    base_url: str = ""
    keys: List[KeyInfoMasked] = Field(default_factory=list)
    key_count: int = 0
    rotation: str = "round-robin"
    models: List[str] = Field(default_factory=list)
    enabled: bool = True
    is_configured: bool = Field(
        default=False,
        description="True when base_url is set AND at least 1 key exists",
    )

    # Legacy compat fields (for existing frontend)
    has_api_key: bool = False
    current_api_key: str = ""
    current_base_url: str = ""
    api_key_prefix: str = ""
    allow_custom_base_url: bool = True
    multi_key_enabled: bool = False
    api_key_count: int = 0


class ActiveModelsInfo(BaseModel):
    """Response model for active LLM configuration."""

    active_llm: ModelSlotConfig


class ResolvedModelConfig(BaseModel):
    """Resolved config for agent use — model + URL + key."""

    model: str = Field(default="", description="Model identifier")
    base_url: str = Field(default="", description="API base URL")
    api_key: str = Field(default="", description="Selected API key")


class ProviderHealthResult(BaseModel):
    """Result of a provider health/connectivity check."""

    provider_id: str
    reachable: bool = False
    latency_ms: Optional[float] = None
    models_discovered: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    streaming_ok: Optional[bool] = None


# ───────────────────────────────────────────────────────────────────────────
# Legacy models (kept for backward compat — import guards)
# ───────────────────────────────────────────────────────────────────────────


class ModelInfo(BaseModel):
    """A single model offered by a provider (legacy)."""

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable name")


class ProviderDefinition(BaseModel):
    """Static provider definition (legacy — use ProviderConfig instead)."""

    id: str = ""
    name: str = ""
    default_base_url: str = ""
    api_key_prefix: str = ""
    models: List[ModelInfo] = Field(default_factory=list)
    allow_custom_base_url: bool = False


class ProviderSettings(BaseModel):
    """Per-provider settings (legacy — use ProviderConfig instead)."""

    base_url: str = ""
    api_key: str = ""
    api_keys: List[str] = Field(default_factory=list)
    multi_key_enabled: bool = False
