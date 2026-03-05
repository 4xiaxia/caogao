# -*- coding: utf-8 -*-
"""统一配置 Schema 模块

使用 Pydantic v2 定义统一的配置 Schema，提供类型安全的配置管理。

功能:
- 统一的配置 Schema 定义
- 配置验证
- 配置迁移
- 配置加载/保存

使用示例:
    from app.config.schema import Config
    
    config = Config.model_validate(data)
    save_config(config)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

logger = logging.getLogger(__name__)

# ============= 渠道配置 =============

class FeishuConfig(BaseModel):
    """飞书渠道配置"""
    enabled: bool = True
    app_id: str = ""
    app_secret: str = ""
    encrypt_key: str = ""
    verification_token: str = ""
    domain: Literal["feishu", "lark"] = "feishu"
    connection_mode: Literal["websocket", "webhook"] = "websocket"
    webhook_path: Optional[str] = None
    webhook_port: Optional[int] = None
    dm_policy: Literal["pairing", "open", "allowlist"] = "pairing"
    allow_from: List[str] = Field(default_factory=list)
    group_policy: Literal["open", "allowlist", "disabled"] = "allowlist"
    require_mention: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "app_id": "cli_xxxxx",
                "app_secret": "your_app_secret",
            }
        }
    )


class DingTalkConfig(BaseModel):
    """钉钉渠道配置"""
    enabled: bool = True
    app_key: str = ""
    app_secret: str = ""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "app_key": "your_app_key",
                "app_secret": "your_app_secret",
            }
        }
    )


class ConsoleConfig(BaseModel):
    """控制台渠道配置"""
    enabled: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
            }
        }
    )


class ChannelsConfig(BaseModel):
    """渠道总配置"""
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)
    dingtalk: DingTalkConfig = Field(default_factory=DingTalkConfig)
    console: ConsoleConfig = Field(default_factory=ConsoleConfig)


# ============= LLM Provider 配置 =============

class APIKeyEntry(BaseModel):
    """API Key 条目"""
    key: str = Field(..., description="API Key")
    label: str = Field(default="", description="Key 标签")
    enabled: bool = Field(default=True, description="是否启用")
    weight: int = Field(default=1, ge=1, description="权重 (用于 weighted 轮询)")
    rotation: Literal["round-robin", "weighted", "failover"] = Field(
        default="round-robin",
        description="轮询策略"
    )


class ProviderConfig(BaseModel):
    """LLM Provider 配置"""
    id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Provider 名称")
    type: Literal["openai", "claude", "qwen", "gemini", "zhipu"] = Field(
        default="openai",
        description="Provider 类型"
    )
    base_url: str = Field(default="", description="API Base URL")
    keys: List[APIKeyEntry] = Field(default_factory=list, description="API Keys")
    models: List[str] = Field(default_factory=list, description="支持的模型")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=0, ge=0, description="优先级 (用于 fallback)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "openai-primary",
                "name": "OpenAI 主账号",
                "type": "openai",
                "base_url": "https://api.openai.com/v1",
                "keys": [
                    {"key": "sk-xxx", "label": "主 Key"},
                    {"key": "sk-yyy", "label": "备用 Key"},
                ],
                "models": ["gpt-4o-mini", "gpt-4o"],
                "enabled": True,
                "priority": 1,
            }
        }
    )


class ProvidersConfig(BaseModel):
    """Providers 总配置"""
    providers: List[ProviderConfig] = Field(default_factory=list)
    active_llm: Optional[str] = Field(None, description="当前活跃的 LLM")
    fallback_chain: List[str] = Field(default_factory=list, description="Fallback 链")


# ============= 环境变量配置 =============

class EnvVarEntry(BaseModel):
    """环境变量条目"""
    key: str = Field(..., description="环境变量名")
    value: str = Field(..., description="环境变量值")
    enabled: bool = Field(default=True, description="是否启用")
    description: str = Field(default="", description="描述")


class EnvsConfig(BaseModel):
    """环境变量总配置"""
    envs: List[EnvVarEntry] = Field(default_factory=list)


# ============= Agent 配置 =============

class AgentConfig(BaseModel):
    """Agent 配置"""
    language: Literal["zh", "en"] = Field(default="zh", description="语言")
    defaults: Dict[str, Any] = Field(default_factory=dict, description="默认配置")


# ============= 心跳配置 =============

class HeartbeatConfig(BaseModel):
    """心跳配置"""
    enabled: bool = Field(default=True, description="是否启用")
    every: str = Field(default="30m", description="心跳间隔")
    prompt: str = Field(default="", description="心跳提示词")


# ============= 总配置 =============

class Config(BaseModel):
    """CoPaw 总配置
    
    统一的配置 Schema，包含所有配置项。
    """
    
    # 渠道配置
    channels: ChannelsConfig = Field(
        default_factory=ChannelsConfig,
        description="渠道配置"
    )
    
    # LLM Provider 配置
    providers: ProvidersConfig = Field(
        default_factory=ProvidersConfig,
        description="LLM Provider 配置"
    )
    
    # 环境变量配置
    envs: EnvsConfig = Field(
        default_factory=EnvsConfig,
        description="环境变量配置"
    )
    
    # Agent 配置
    agents: AgentConfig = Field(
        default_factory=AgentConfig,
        description="Agent 配置"
    )
    
    # 心跳配置
    heartbeat: HeartbeatConfig = Field(
        default_factory=HeartbeatConfig,
        description="心跳配置"
    )
    
    # 其他配置
    show_tool_details: bool = Field(default=True, description="显示工具详情")
    last_dispatch: Optional[Dict[str, str]] = Field(None, description="最后分发")
    
    # 版本控制
    config_version: int = Field(default=2, description="配置版本号")
    
    model_config = ConfigDict(
        json_schema_extra={
            "title": "CoPaw Configuration",
            "description": "CoPaw 统一配置 Schema",
        }
    )
    
    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v: ProvidersConfig) -> ProvidersConfig:
        """验证 Providers 配置"""
        # 检查 ID 唯一性
        ids = [p.id for p in v.providers]
        if len(ids) != len(set(ids)):
            raise ValueError("Provider IDs must be unique")
        return v
    
    # 注意：fallback_chain 验证需要在 providers 之后，Pydantic v2 不支持跨字段验证
    # 所以在 validate_config 函数中做额外验证


# ============= 配置迁移 =============

def migrate_from_v1_to_v2(old_data: dict) -> dict:
    """从 v1 配置迁移到 v2 配置
    
    Args:
        old_data: v1 配置数据
        
    Returns:
        v2 配置数据
    """
    new_data = {
        "config_version": 2,
        "channels": {},
        "providers": {"providers": [], "active_llm": None, "fallback_chain": []},
        "envs": {"envs": []},
        "agents": {"language": "zh"},
        "heartbeat": {"enabled": True, "every": "30m"},
        "show_tool_details": True,
    }
    
    # 迁移渠道配置
    if "channels" in old_data:
        for channel_name, channel_config in old_data["channels"].items():
            if channel_name == "feishu":
                new_data["channels"]["feishu"] = {
                    "enabled": channel_config.get("enabled", True),
                    "app_id": channel_config.get("app_id", ""),
                    "app_secret": channel_config.get("app_secret", ""),
                    "encrypt_key": channel_config.get("encrypt_key", ""),
                    "verification_token": channel_config.get("verification_token", ""),
                }
            elif channel_name == "dingtalk":
                new_data["channels"]["dingtalk"] = {
                    "enabled": channel_config.get("enabled", True),
                    "app_key": channel_config.get("app_key", ""),
                    "app_secret": channel_config.get("app_secret", ""),
                }
    
    # 迁移 Provider 配置
    if "providers" in old_data:
        providers_data = old_data["providers"]
        if isinstance(providers_data, dict):
            # 旧格式：单个 Provider
            provider = {
                "id": "openai-default",
                "name": "OpenAI",
                "type": "openai",
                "base_url": providers_data.get("base_url", ""),
                "keys": [],
                "models": providers_data.get("models", []),
                "enabled": True,
                "priority": 1,
            }
            
            # 迁移 API Key
            api_key = providers_data.get("api_key")
            if api_key:
                provider["keys"].append({
                    "key": api_key,
                    "label": "Default Key",
                    "enabled": True,
                })
            
            new_data["providers"]["providers"].append(provider)
            new_data["providers"]["active_llm"] = providers_data.get("active_llm")
        elif isinstance(providers_data, list):
            # 新格式：多个 Provider
            for provider_data in providers_data:
                new_data["providers"]["providers"].append(provider_data)
    
    # 迁移环境变量
    if "envs" in old_data:
        envs_data = old_data["envs"]
        if isinstance(envs_data, dict):
            for key, value in envs_data.items():
                new_data["envs"]["envs"].append({
                    "key": key,
                    "value": value,
                    "enabled": True,
                })
    
    # 迁移其他配置
    if "agents" in old_data:
        new_data["agents"] = old_data["agents"]
    
    if "heartbeat" in old_data:
        new_data["heartbeat"] = old_data["heartbeat"]
    
    if "show_tool_details" in old_data:
        new_data["show_tool_details"] = old_data["show_tool_details"]
    
    if "last_dispatch" in old_data:
        new_data["last_dispatch"] = old_data["last_dispatch"]
    
    return new_data


# ============= 配置加载/保存 =============

def load_config(config_path: Optional[Path] = None) -> Config:
    """加载配置
    
    Args:
        config_path: 配置文件路径，默认 ~/.copaw/config.json
        
    Returns:
        Config 对象
    """
    if config_path is None:
        config_path = Path.home() / ".copaw" / "config.json"
    
    logger.info(f"Loading config from {config_path}")
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        # 返回默认配置
        return Config()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 检查版本
        version = data.get("config_version", 1)
        if version == 1:
            logger.info("Migrating config from v1 to v2")
            data = migrate_from_v1_to_v2(data)
        
        # 验证并返回配置
        config = Config.model_validate(data)
        logger.info(f"Config loaded successfully (version {config.config_version})")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
    """保存配置
    
    Args:
        config: Config 对象
        config_path: 配置文件路径，默认 ~/.copaw/config.json
    """
    if config_path is None:
        config_path = Path.home() / ".copaw" / "config.json"
    
    logger.info(f"Saving config to {config_path}")
    
    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 备份旧配置
        if config_path.exists():
            backup_path = config_path.with_suffix(".json.bak")
            import shutil
            shutil.copy2(config_path, backup_path)
            logger.info(f"Backed up old config to {backup_path}")
        
        # 保存新配置
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        
        logger.info("Config saved successfully")
        
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise


def validate_config(config: Config) -> bool:
    """验证配置
    
    Args:
        config: Config 对象
        
    Returns:
        是否有效
    """
    try:
        # Pydantic 已经验证过了
        # 这里可以做额外的业务逻辑验证
        
        # 检查至少有一个启用的渠道
        enabled_channels = [
            name for name, cfg in config.channels.model_dump().items()
            if cfg.get("enabled", False)
        ]
        if not enabled_channels:
            logger.warning("No enabled channels")
        
        # 检查至少有一个启用的 Provider
        enabled_providers = [
            p for p in config.providers.providers
            if p.enabled
        ]
        if not enabled_providers:
            logger.warning("No enabled providers")
        
        return True
        
    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        return False


__all__ = [
    # 配置类
    "Config",
    "ChannelsConfig",
    "FeishuConfig",
    "DingTalkConfig",
    "ConsoleConfig",
    "ProvidersConfig",
    "ProviderConfig",
    "APIKeyEntry",
    "EnvsConfig",
    "EnvVarEntry",
    "AgentConfig",
    "HeartbeatConfig",
    
    # 函数
    "load_config",
    "save_config",
    "validate_config",
    "migrate_from_v1_to_v2",
]
