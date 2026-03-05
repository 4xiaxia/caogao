# -*- coding: utf-8 -*-
"""API Provider 管理器 - 骨架版本

提供 API Provider 的统一管理，支持多 Provider 注册、获取、Fallback。

这是骨架版本，只实现核心接口，详细功能后续完善。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def singleton(cls):
    """简单的单例装饰器"""
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class APIProviderManager:
    """API Provider 管理器 (单例) - 骨架版本
    
    核心功能:
    - Provider 注册
    - Provider 获取
    - Provider 列表
    - Fallback 链管理
    """
    
    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self._fallback_chain: List[str] = []
        self._initialized = False
    
    def initialize(self, providers_config: List[Dict], fallback_chain: List[str]) -> None:
        """初始化 Provider 管理器
        
        Args:
            providers_config: Provider 配置列表
            fallback_chain: Fallback 链
        """
        if self._initialized:
            logger.warning("APIProviderManager already initialized")
            return
        
        # 注册 Provider
        for provider_config in providers_config:
            provider_id = provider_config.get("id")
            if provider_id:
                self._providers[provider_id] = provider_config
                logger.info(f"Registered provider: {provider_id}")
        
        # 设置 Fallback 链
        self._fallback_chain = fallback_chain
        logger.info(f"Fallback chain set: {fallback_chain}")
        
        self._initialized = True
        logger.info("APIProviderManager initialized")
    
    def get_provider(self, provider_id: str) -> Optional[Dict]:
        """获取 Provider 配置
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider 配置，不存在返回 None
        """
        return self._providers.get(provider_id)
    
    def list_providers(self) -> List[str]:
        """获取所有 Provider ID 列表
        
        Returns:
            Provider ID 列表
        """
        return list(self._providers.keys())
    
    def get_fallback_chain(self) -> List[str]:
        """获取 Fallback 链
        
        Returns:
            Fallback 链
        """
        return self._fallback_chain
    
    def execute_with_fallback(self, func, *args, **kwargs):
        """执行 API 调用，支持 Fallback - 骨架版本
        
        Args:
            func: 执行函数，签名应为 func(provider_id, *args, **kwargs)
            *args: 参数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
            
        Raises:
            Exception: 所有 Provider 都失败
        """
        last_error = None
        
        # 使用 Fallback 链
        for provider_id in self._fallback_chain:
            try:
                logger.debug(f"Trying provider: {provider_id}")
                result = func(provider_id, *args, **kwargs)
                logger.info(f"Provider {provider_id} succeeded")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_id} failed: {e}, trying next...")
                continue
        
        # 所有 Provider 都失败
        error_msg = f"All providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)


# 便捷函数

def get_provider_manager() -> APIProviderManager:
    """获取 Provider 管理器实例"""
    return APIProviderManager()


__all__ = [
    "APIProviderManager",
    "get_provider_manager",
]
