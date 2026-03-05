# -*- coding: utf-8 -*-
"""Streaming Interface - 骨架版本

提供流式响应的标准接口，支持 SSE 和 WebSocket。

这是骨架版本，只定义核心接口，详细功能后续完善。
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Optional, Any

logger = logging.getLogger(__name__)


class StreamingSession:
    """流式会话 - 骨架版本"""
    
    def __init__(self):
        self._is_active = False
        self._message_id: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """是否正在流式传输"""
        return self._is_active
    
    async def start(self, **kwargs) -> None:
        """开始流式会话"""
        self._is_active = True
        logger.debug("Streaming session started")
    
    async def update(self, content: str) -> None:
        """更新流式内容"""
        if not self._is_active:
            return
        logger.debug(f"Streaming update: {content[:50]}...")
    
    async def close(self, final_content: str = "") -> None:
        """关闭流式会话"""
        self._is_active = False
        logger.debug("Streaming session closed")


class SSEStreamingSession(StreamingSession):
    """SSE 流式会话 - 骨架版本"""
    
    async def start(self, **kwargs) -> None:
        await super().start()
        logger.debug("SSE streaming started")
    
    async def update(self, content: str) -> None:
        await super().update(content)
    
    async def close(self, final_content: str = "") -> None:
        await super().close(final_content)


def create_sse_session() -> SSEStreamingSession:
    """创建 SSE 会话"""
    return SSEStreamingSession()


__all__ = [
    # 类
    "StreamingSession",
    "SSEStreamingSession",
    
    # 便捷函数
    "create_sse_session",
]
