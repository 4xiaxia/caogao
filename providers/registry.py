# -*- coding: utf-8 -*-
"""Provider presets — quick-start templates for popular LLM services.

Presets are NOT constraints. Users can:
  - Install a preset → creates a ProviderConfig with sensible defaults
  - Add any custom provider with arbitrary base_url
  - Edit/delete any provider freely

No vendor lock-in: every preset uses the OpenAI-compatible API standard.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import (
    KeyEntry,
    ModelInfo,
    ProviderConfig,
    ProviderDefinition,
    RotationStrategy,
)

# ───────────────────────────────────────────────────────────────────────────
# Provider Presets — curated defaults for one-click setup
# ───────────────────────────────────────────────────────────────────────────

PROVIDER_PRESETS: Dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        id="openai",
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        models=[
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "o3",
            "o3-mini",
            "o4-mini",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "deepseek": ProviderConfig(
        id="deepseek",
        name="DeepSeek",
        base_url="https://api.deepseek.com",
        models=[
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "anthropic-openai": ProviderConfig(
        id="anthropic-openai",
        name="Anthropic (OpenAI-compat)",
        base_url="https://api.anthropic.com/v1",
        models=[
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-haiku-20241022",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "dashscope": ProviderConfig(
        id="dashscope",
        name="DashScope (Aliyun)",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        models=[
            "qwen3-max",
            "qwen3-plus",
            "qwen3-coder-plus",
            "qwen-turbo-latest",
            "qwen-max-latest",
            "qwq-plus",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "siliconflow": ProviderConfig(
        id="siliconflow",
        name="SiliconFlow",
        base_url="https://api.siliconflow.cn/v1",
        models=[
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen3-8B",
            "Qwen/Qwen3-32B",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "openrouter": ProviderConfig(
        id="openrouter",
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        models=[
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4",
            "google/gemini-2.5-pro",
            "deepseek/deepseek-r1",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "groq": ProviderConfig(
        id="groq",
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        models=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "together": ProviderConfig(
        id="together",
        name="Together AI",
        base_url="https://api.together.xyz/v1",
        models=[
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen3-235B-A22B",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "mistral": ProviderConfig(
        id="mistral",
        name="Mistral AI",
        base_url="https://api.mistral.ai/v1",
        models=[
            "mistral-large-latest",
            "mistral-small-latest",
            "codestral-latest",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "zhipu": ProviderConfig(
        id="zhipu",
        name="Zhipu AI (GLM)",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        models=[
            "glm-4-plus",
            "glm-4-flash",
            "glm-4-long",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "moonshot": ProviderConfig(
        id="moonshot",
        name="Moonshot (Kimi)",
        base_url="https://api.moonshot.cn/v1",
        models=[
            "moonshot-v1-auto",
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "volcengine": ProviderConfig(
        id="volcengine",
        name="Volcengine (Doubao)",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        models=[
            "doubao-1.5-pro-32k",
            "doubao-1.5-lite-32k",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
    "github-copilot": ProviderConfig(
        id="github-copilot",
        name="GitHub Copilot (Local Proxy)",
        base_url="http://localhost:4141/v1",
        models=[
            "gpt-5.2",
            "gpt-5.1",
            "gpt-5-mini",
            "gpt-4.1",
            "gpt-4o",
            "gpt-4o-mini",
            "gemini-3.1-pro-preview",
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "grok-code-fast-1",
            "claude-sonnet-4",
            "claude-opus-4-6",
        ],
        rotation=RotationStrategy.ROUND_ROBIN,
    ),
}


def get_preset(preset_id: str) -> Optional[ProviderConfig]:
    """Return a preset by ID, or None."""
    return PROVIDER_PRESETS.get(preset_id)


def list_presets() -> List[ProviderConfig]:
    """Return all available presets."""
    return list(PROVIDER_PRESETS.values())


# ───────────────────────────────────────────────────────────────────────────
# Legacy compat — PROVIDERS dict used by old store.py imports
# ───────────────────────────────────────────────────────────────────────────

# Build ProviderDefinition from presets for backward compatibility.
# This is used ONLY during v1 → v2 migration; new code should use
# ProviderConfig / PROVIDER_PRESETS directly.

PROVIDERS: Dict[str, ProviderDefinition] = {}

# Also keep the old 3 providers for migration
_LEGACY_MAP = {
    "cli-openai": "openai",
    "uji-fixed": None,  # no preset equivalent
    "custom": None,
}


def get_provider(provider_id: str) -> Optional[ProviderDefinition]:
    """Return a legacy provider definition (for backward compat)."""
    return PROVIDERS.get(provider_id)


def list_providers() -> List[ProviderDefinition]:
    """Return all legacy provider definitions (for backward compat)."""
    return list(PROVIDERS.values())
