# -*- coding: utf-8 -*-
"""Channel Plugin 接口定义 - 骨架版本

定义 Channel Plugin 的标准接口，支持插件化渠道。

这是骨架版本，只定义核心接口，详细功能后续完善。
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Protocol, List
from dataclasses import dataclass, field


@dataclass
class ChannelMeta:
    """渠道元数据"""
    id: str
    label: str
    selection_label: str = ""
    docs_path: str = ""
    blurb: str = ""
    aliases: List[str] = field(default_factory=list)
    order: int = 0


@dataclass
class ChannelCapabilities:
    """渠道能力"""
    chat_types: List[str] = field(default_factory=lambda: ["direct", "channel"])
    polls: bool = False
    threads: bool = False
    media: bool = False
    reactions: bool = False
    edit: bool = False
    reply: bool = False


class MessagingHelpers(Protocol):
    """消息辅助接口"""
    
    def normalize_target(self, target: str) -> str:
        """标准化目标地址"""
        ...
    
    def looks_like_id(self, id: str) -> bool:
        """检查是否像 ID"""
        ...
    
    def hint(self) -> str:
        """返回提示"""
        ...


class GatewayHelpers(Protocol):
    """网关辅助接口"""
    
    async def start_account(self, ctx: Any) -> None:
        """启动账号"""
        ...


class ChannelPlugin(Protocol):
    """Channel Plugin 接口
    
    渠道插件的标准接口，所有渠道都应实现此接口。
    """
    
    @property
    def id(self) -> str:
        """渠道 ID"""
        ...
    
    @property
    def meta(self) -> ChannelMeta:
        """渠道元数据"""
        ...
    
    @property
    def capabilities(self) -> ChannelCapabilities:
        """渠道能力"""
        ...
    
    @property
    def messaging(self) -> MessagingHelpers:
        """消息辅助"""
        ...
    
    @property
    def gateway(self) -> GatewayHelpers:
        """网关辅助"""
        ...


# 便捷函数

def create_channel_meta(
    id: str,
    label: str,
    selection_label: str = "",
    docs_path: str = "",
    blurb: str = "",
    aliases: List[str] = None,
    order: int = 0
) -> ChannelMeta:
    """创建渠道元数据
    
    Args:
        id: 渠道 ID
        label: 渠道标签
        selection_label: 选择标签
        docs_path: 文档路径
        blurb: 描述
        aliases: 别名
        order: 排序
        
    Returns:
        ChannelMeta 对象
    """
    return ChannelMeta(
        id=id,
        label=label,
        selection_label=selection_label,
        docs_path=docs_path,
        blurb=blurb,
        aliases=aliases or [],
        order=order,
    )


def create_channel_capabilities(
    chat_types: List[str] = None,
    polls: bool = False,
    threads: bool = False,
    media: bool = False,
    reactions: bool = False,
    edit: bool = False,
    reply: bool = False
) -> ChannelCapabilities:
    """创建渠道能力
    
    Args:
        chat_types: 聊天类型
        polls: 是否支持投票
        threads: 是否支持主题
        media: 是否支持媒体
        reactions: 是否支持表情回应
        edit: 是否支持编辑
        reply: 是否支持回复
        
    Returns:
        ChannelCapabilities 对象
    """
    return ChannelCapabilities(
        chat_types=chat_types or ["direct", "channel"],
        polls=polls,
        threads=threads,
        media=media,
        reactions=reactions,
        edit=edit,
        reply=reply,
    )


__all__ = [
    # 数据类
    "ChannelMeta",
    "ChannelCapabilities",
    
    # 接口
    "MessagingHelpers",
    "GatewayHelpers",
    "ChannelPlugin",
    
    # 便捷函数
    "create_channel_meta",
    "create_channel_capabilities",
]
