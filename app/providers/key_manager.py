# -*- coding: utf-8 -*-
"""API Key 管理器 - 骨架版本

提供 API Key 的统一管理，支持多 Key 轮询、权重、健康检查。

这是骨架版本，只实现核心接口，详细功能后续完善。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class APIKeyManager:
    """API Key 管理器 - 骨架版本
    
    核心功能:
    - Key 加载
    - Key 轮询 (round-robin)
    - Key 健康检查
    """
    
    def __init__(self, provider_id: str, keys_config: List[Dict]):
        """初始化 Key 管理器
        
        Args:
            provider_id: Provider ID
            keys_config: Key 配置列表
        """
        self.provider_id = provider_id
        self._keys: List[Dict] = []
        self._current_index = 0
        self._key_health: Dict[str, Dict] = {}
        
        # 加载 Keys
        self._load_keys(keys_config)
        logger.info(f"APIKeyManager initialized for {provider_id} with {len(self._keys)} keys")
    
    def _load_keys(self, keys_config: List[Dict]) -> None:
        """加载 Keys
        
        Args:
            keys_config: Key 配置列表
        """
        for key_config in keys_config:
            key = key_config.get("key")
            if key:
                self._keys.append({
                    "key": key,
                    "label": key_config.get("label", ""),
                    "enabled": key_config.get("enabled", True),
                    "weight": key_config.get("weight", 1),
                })
    
    def get_next_key(self) -> Optional[str]:
        """获取下一个 Key (轮询)
        
        Returns:
            API Key，没有可用 Key 返回 None
        """
        if not self._keys:
            return None
        
        # 过滤启用的 Key
        enabled_keys = [k for k in self._keys if k["enabled"]]
        if not enabled_keys:
            return None
        
        # 轮询
        key = enabled_keys[self._current_index % len(enabled_keys)]
        self._current_index += 1
        
        logger.debug(f"Got next key for {self.provider_id}: {key['label']}")
        return key["key"]
    
    def mark_key_unhealthy(self, key: str, error: str) -> None:
        """标记 Key 不健康
        
        Args:
            key: API Key
            error: 错误信息
        """
        self._key_health[key] = {
            "healthy": False,
            "error": error,
        }
        logger.warning(f"Key marked unhealthy: {key[:10]}... - {error}")
    
    def mark_key_healthy(self, key: str) -> None:
        """标记 Key 健康
        
        Args:
            key: API Key
        """
        self._key_health[key] = {
            "healthy": True,
        }
        logger.debug(f"Key marked healthy: {key[:10]}...")
    
    def is_key_healthy(self, key: str) -> bool:
        """检查 Key 是否健康
        
        Args:
            key: API Key
            
        Returns:
            是否健康
        """
        return self._key_health.get(key, {}).get("healthy", True)


# 便捷函数

def create_key_manager(provider_id: str, keys_config: List[Dict]) -> APIKeyManager:
    """创建 Key 管理器
    
    Args:
        provider_id: Provider ID
        keys_config: Key 配置列表
        
    Returns:
        Key 管理器实例
    """
    return APIKeyManager(provider_id, keys_config)


__all__ = [
    "APIKeyManager",
    "create_key_manager",
]
