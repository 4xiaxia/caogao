# -*- coding: utf-8 -*-
"""统一依赖注入模块

提供统一的依赖注入容器，避免每个 router 重复写 get_xxx() 函数。

使用示例:
    @router.get("/chats")
    async def list_chats(
        mgr: ChatManager = Depends(get_deps().get_chat_manager),
    ):
        ...
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from fastapi import Depends, HTTPException

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..runner.manager import ChatManager
    from ..crons.manager import CronManager
    from ..runner.runner import AgentRunner
    from ..channels.manager import ChannelManager


class Dependencies:
    """依赖注入容器
    
    集中管理所有依赖，提供统一的获取接口。
    在 app/_app.py 的 lifespan 中初始化。
    """
    
    _instance: Optional[Dependencies] = None
    
    def __init__(self):
        self._chat_manager: Optional[ChatManager] = None
        self._cron_manager: Optional[CronManager] = None
        self._runner: Optional[AgentRunner] = None
        self._channel_manager: Optional[ChannelManager] = None
    
    @classmethod
    def initialize(cls) -> "Dependencies":
        """初始化依赖容器"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "Dependencies":
        """获取依赖容器实例"""
        if cls._instance is None:
            raise RuntimeError(
                "Dependencies not initialized. "
                "Please call Dependencies.initialize() in app lifespan."
            )
        return cls._instance
    
    # ----- Setters (在 lifespan 中调用) -----
    
    def set_chat_manager(self, mgr: ChatManager) -> None:
        """设置 ChatManager"""
        self._chat_manager = mgr
        logger.debug("ChatManager set in dependencies")
    
    def set_cron_manager(self, mgr: CronManager) -> None:
        """设置 CronManager"""
        self._cron_manager = mgr
        logger.debug("CronManager set in dependencies")
    
    def set_runner(self, runner: AgentRunner) -> None:
        """设置 AgentRunner"""
        self._runner = runner
        logger.debug("AgentRunner set in dependencies")
    
    def set_channel_manager(self, mgr: ChannelManager) -> None:
        """设置 ChannelManager"""
        self._channel_manager = mgr
        logger.debug("ChannelManager set in dependencies")
    
    # ----- Getters (在 router 中通过 Depends 调用) -----
    
    def get_chat_manager(self) -> ChatManager:
        """获取 ChatManager"""
        if self._chat_manager is None:
            raise HTTPException(
                status_code=503,
                detail="Chat manager not initialized",
            )
        return self._chat_manager
    
    def get_cron_manager(self) -> CronManager:
        """获取 CronManager"""
        if self._cron_manager is None:
            raise HTTPException(
                status_code=503,
                detail="Cron manager not initialized",
            )
        return self._cron_manager
    
    def get_runner(self) -> AgentRunner:
        """获取 AgentRunner"""
        if self._runner is None:
            raise HTTPException(
                status_code=503,
                detail="Runner not initialized",
            )
        return self._runner
    
    def get_channel_manager(self) -> ChannelManager:
        """获取 ChannelManager"""
        if self._channel_manager is None:
            raise HTTPException(
                status_code=503,
                detail="Channel manager not initialized",
            )
        return self._channel_manager


# ----- 便捷函数 (供 router 使用) -----

def get_deps() -> Dependencies:
    """获取依赖容器实例"""
    return Dependencies.get_instance()


def get_chat_manager() -> ChatManager:
    """获取 ChatManager (用于 Depends)"""
    return get_deps().get_chat_manager()


def get_cron_manager() -> CronManager:
    """获取 CronManager (用于 Depends)"""
    return get_deps().get_cron_manager()


def get_runner() -> AgentRunner:
    """获取 AgentRunner (用于 Depends)"""
    return get_deps().get_runner()


def get_channel_manager() -> ChannelManager:
    """获取 ChannelManager (用于 Depends)"""
    return get_deps().get_channel_manager()


__all__ = [
    "Dependencies",
    "get_deps",
    "get_chat_manager",
    "get_cron_manager",
    "get_runner",
    "get_channel_manager",
]
