# -*- coding: utf-8 -*-
"""API Fallback 管理器 - 骨架版本

提供 API Fallback 的统一管理，支持 Fallback 链、重试机制。

这是骨架版本，只实现核心接口，详细功能后续完善。
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class APIFallbackManager:
    """API Fallback 管理器 - 骨架版本
    
    核心功能:
    - Fallback 链管理
    - 错误重试
    - 指数退避
    """
    
    def __init__(self, fallback_chain: List[str], max_retries: int = 3):
        """初始化 Fallback 管理器
        
        Args:
            fallback_chain: Fallback 链
            max_retries: 最大重试次数
        """
        self.fallback_chain = fallback_chain
        self.max_retries = max_retries
        logger.info(f"APIFallbackManager initialized with chain: {fallback_chain}")
    
    def execute_with_retry(
        self,
        func: Callable,
        provider_id: str,
        *args,
        should_retry: Optional[Callable[[Exception], bool]] = None,
        **kwargs
    ) -> Any:
        """执行 API 调用，支持重试
        
        Args:
            func: 执行函数
            provider_id: Provider ID
            *args: 参数
            should_retry: 判断是否应该重试的函数
            **kwargs: 关键字参数
            
        Returns:
            执行结果
            
        Raises:
            Exception: 重试后仍然失败
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Executing with provider {provider_id}, attempt {attempt + 1}")
                result = func(provider_id, *args, **kwargs)
                logger.info(f"Provider {provider_id} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_id} failed on attempt {attempt + 1}: {e}")
                
                # 判断是否应该重试
                if should_retry and not should_retry(e):
                    logger.warning(f"Not retrying for provider {provider_id}: {e}")
                    raise
                
                # 指数退避
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
        
        # 重试后仍然失败
        error_msg = f"Provider {provider_id} failed after {self.max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def should_retry(self, error: Exception) -> bool:
        """判断是否应该重试
        
        Args:
            error: 异常对象
            
        Returns:
            是否应该重试
        """
        error_str = str(error).lower()
        
        # 可重试的错误
        retry_errors = [
            "timeout",
            "connection",
            "rate limit",
            "429",
            "503",
            "502",
        ]
        
        for retry_error in retry_errors:
            if retry_error in error_str:
                return True
        
        return False


# 便捷函数

def create_fallback_manager(fallback_chain: List[str], max_retries: int = 3) -> APIFallbackManager:
    """创建 Fallback 管理器
    
    Args:
        fallback_chain: Fallback 链
        max_retries: 最大重试次数
        
    Returns:
        Fallback 管理器实例
    """
    return APIFallbackManager(fallback_chain, max_retries)


__all__ = [
    "APIFallbackManager",
    "create_fallback_manager",
]
