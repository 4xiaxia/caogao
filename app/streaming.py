# -*- coding: utf-8 -*-
"""流式响应抽象模块

参考 clawdbot-feishu 的流式响应设计，提供统一的流式响应抽象层。

功能:
- 统一的流式响应接口
- 支持 SSE (Server-Sent Events)
- 支持 WebSocket
- 支持 Markdown 卡片更新
- 自动错误处理

使用示例:
    async def stream_chat(chat_id: str):
        streaming = StreamingSession()
        await streaming.start(chat_id)
        
        async for chunk in generate_response():
            await streaming.update(chunk)
        
        await streaming.close()
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, Callable, Any, Dict

from fastapi import Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


class StreamingSession(ABC):
    """流式响应抽象基类
    
    提供统一的流式响应接口，子类实现具体的发送逻辑。
    """
    
    def __init__(self):
        self._is_active = False
        self._message_id: Optional[str] = None
        self._error: Optional[Exception] = None
    
    @property
    def is_active(self) -> bool:
        """是否正在流式传输"""
        return self._is_active
    
    @property
    def message_id(self) -> Optional[str]:
        """消息 ID"""
        return self._message_id
    
    @abstractmethod
    async def start(self, **kwargs) -> None:
        """开始流式会话
        
        Args:
            **kwargs: 子类特定的参数
        """
        self._is_active = True
        logger.debug("Streaming session started")
    
    @abstractmethod
    async def update(self, content: str) -> None:
        """更新流式内容
        
        Args:
            content: 内容片段
        """
        if not self._is_active:
            logger.warning("Cannot update inactive streaming session")
    
    @abstractmethod
    async def close(self, final_content: str = "") -> None:
        """关闭流式会话
        
        Args:
            final_content: 最终内容
        """
        self._is_active = False
        logger.debug("Streaming session closed")
    
    async def __aenter__(self) -> "StreamingSession":
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        if exc_val:
            self._error = exc_val
            await self.close(final_content=f"Error: {exc_val}")
        else:
            await self.close()


class SSEStreamingSession(StreamingSession):
    """SSE (Server-Sent Events) 流式会话
    
    用于 HTTP SSE 流式响应。
    """
    
    def __init__(self):
        super().__init__()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, **kwargs) -> None:
        """开始 SSE 流"""
        await super().start()
        logger.debug("SSE streaming session started")
    
    async def update(self, content: str) -> None:
        """推送内容片段到 SSE 队列"""
        if not self._is_active:
            return
        
        # 放入队列
        await self._queue.put({
            "type": "content",
            "content": content,
        })
    
    async def close(self, final_content: str = "") -> None:
        """关闭 SSE 流"""
        await super().close(final_content)
        
        # 发送结束信号
        await self._queue.put({
            "type": "done",
            "content": final_content,
        })
        
        # 等待队列处理完成
        await asyncio.sleep(0.1)
    
    async def event_generator(self) -> AsyncGenerator[str, None]:
        """生成 SSE 事件
        
        Yields:
            SSE 格式的事件字符串
        """
        try:
            while True:
                event = await self._queue.get()
                
                if event["type"] == "content":
                    # SSE 格式
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                elif event["type"] == "done":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    break
        except asyncio.CancelledError:
            logger.debug("SSE streaming cancelled")
        except Exception as e:
            logger.error(f"SSE streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    def create_response(self) -> StreamingResponse:
        """创建 FastAPI StreamingResponse"""
        return StreamingResponse(
            self.event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            },
        )


class WebSocketStreamingSession(StreamingSession):
    """WebSocket 流式会话
    
    用于 WebSocket 实时通信。
    """
    
    def __init__(self, websocket: Any):
        """
        Args:
            websocket: WebSocket 连接对象
        """
        super().__init__()
        self._websocket = websocket
    
    async def start(self, **kwargs) -> None:
        """接受 WebSocket 连接"""
        await self._websocket.accept()
        await super().start()
        logger.debug("WebSocket streaming session started")
    
    async def update(self, content: str) -> None:
        """通过 WebSocket 发送内容"""
        if not self._is_active:
            return
        
        try:
            await self._websocket.send_json({
                "type": "content",
                "content": content,
            })
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            self._error = e
    
    async def close(self, final_content: str = "") -> None:
        """关闭 WebSocket 连接"""
        await super().close(final_content)
        
        try:
            # 发送最终内容
            if final_content:
                await self._websocket.send_json({
                    "type": "done",
                    "content": final_content,
                })
            
            # 关闭连接
            await self._websocket.close()
        except Exception as e:
            logger.error(f"WebSocket close error: {e}")


class StreamingManager:
    """流式响应管理器
    
    管理流式会话的创建和生命周期。
    """
    
    _instance: Optional["StreamingManager"] = None
    
    def __init__(self):
        self._sessions: Dict[str, StreamingSession] = {}
    
    @classmethod
    def get_instance(cls) -> "StreamingManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def create_sse_session(self) -> SSEStreamingSession:
        """创建 SSE 流式会话"""
        session = SSEStreamingSession()
        session_id = id(session)
        self._sessions[session_id] = session
        return session
    
    def create_websocket_session(self, websocket: Any) -> WebSocketStreamingSession:
        """创建 WebSocket 流式会话"""
        session = WebSocketStreamingSession(websocket)
        session_id = id(session)
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """获取流式会话"""
        return self._sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> None:
        """移除流式会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]


# 便捷函数

def create_sse_streaming() -> SSEStreamingSession:
    """创建 SSE 流式会话"""
    return StreamingManager.get_instance().create_sse_session()


def create_websocket_streaming(websocket: Any) -> WebSocketStreamingSession:
    """创建 WebSocket 流式会话"""
    return StreamingManager.get_instance().create_websocket_session(websocket)


__all__ = [
    # 基类
    "StreamingSession",
    
    # SSE
    "SSEStreamingSession",
    
    # WebSocket
    "WebSocketStreamingSession",
    
    # 管理器
    "StreamingManager",
    
    # 便捷函数
    "create_sse_streaming",
    "create_websocket_streaming",
]
