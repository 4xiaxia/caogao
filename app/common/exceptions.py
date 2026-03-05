# -*- coding: utf-8 -*-
"""统一错误处理模块

参考 clawdbot-feishu 的错误处理模式：
- 统一的异常基类
- 分层的异常类型
- 友好的错误消息
- 完整的错误上下文
- 日志记录规范
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


# ============= 错误代码枚举 =============

class ErrorCode(str, Enum):
    """错误代码枚举
    
    格式：CATEGORY_CODE
    - CATEGORY: 错误类别 (SYS, API, CHANNEL, SOUL, CONFIG, etc.)
    - CODE: 具体错误编号
    """
    
    # 系统级错误 (SYS)
    SYS_UNKNOWN_ERROR = "SYS_001"
    SYS_SERVICE_UNAVAILABLE = "SYS_002"
    SYS_INITIALIZATION_FAILED = "SYS_003"
    
    # API 相关错误 (API)
    API_REQUEST_FAILED = "API_001"
    API_TIMEOUT = "API_002"
    API_RATE_LIMIT = "API_003"
    API_AUTH_FAILED = "API_004"
    API_NOT_FOUND = "API_005"
    API_INVALID_RESPONSE = "API_006"
    
    # 渠道相关错误 (CHANNEL)
    CHANNEL_NOT_FOUND = "CHANNEL_001"
    CHANNEL_SEND_FAILED = "CHANNEL_002"
    CHANNEL_RECEIVE_FAILED = "CHANNEL_003"
    CHANNEL_CONNECTION_LOST = "CHANNEL_004"
    
    # Soul 文件相关错误 (SOUL)
    SOUL_FILE_NOT_FOUND = "SOUL_001"
    SOUL_FILE_PROTECTED = "SOUL_002"
    SOUL_FILE_CORRUPTED = "SOUL_003"
    SOUL_INTEGRITY_CHECK_FAILED = "SOUL_004"
    
    # 配置相关错误 (CONFIG)
    CONFIG_NOT_FOUND = "CONFIG_001"
    CONFIG_INVALID = "CONFIG_002"
    CONFIG_MISSING_FIELD = "CONFIG_003"
    
    # 会话相关错误 (SESSION)
    SESSION_NOT_FOUND = "SESSION_001"
    SESSION_EXPIRED = "SESSION_002"
    SESSION_INVALID = "SESSION_003"
    
    # 聊天相关错误 (CHAT)
    CHAT_NOT_FOUND = "CHAT_001"
    CHAT_MESSAGE_NOT_FOUND = "CHAT_002"
    
    # 定时任务相关错误 (CRON)
    CRON_NOT_FOUND = "CRON_001"
    CRON_EXECUTION_FAILED = "CRON_002"
    CRON_INVALID_EXPRESSION = "CRON_003"
    
    # 技能相关错误 (SKILL)
    SKILL_NOT_FOUND = "SKILL_001"
    SKILL_EXECUTION_FAILED = "SKILL_002"
    
    # 模型相关错误 (MODEL)
    MODEL_NOT_FOUND = "MODEL_001"
    MODEL_CONFIG_INVALID = "MODEL_002"
    MODEL_API_KEY_INVALID = "MODEL_003"


# ============= 错误响应 =============

@dataclass
class ErrorDetail:
    """错误详细信息"""
    
    # 错误代码
    code: ErrorCode
    
    # 错误消息
    message: str
    
    # 详细上下文
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 建议的解决方案
    suggestion: Optional[str] = None
    
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # 请求 ID (用于追踪)
    request_id: Optional[str] = None
    
    # 堆栈追踪 (仅开发环境)
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code.value if isinstance(self.code, ErrorCode) else self.code,
            "message": self.message,
            "context": self.context,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
        }


# ============= 异常基类 =============

class CoPawException(Exception):
    """CoPaw 异常基类
    
    所有 CoPaw 自定义异常都应继承此类
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.SYS_UNKNOWN_ERROR,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        
        self.message = message
        self.code = code
        self.context = context or {}
        self.suggestion = suggestion
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()
    
    def to_error_detail(self, request_id: Optional[str] = None) -> ErrorDetail:
        """转换为 ErrorDetail"""
        return ErrorDetail(
            code=self.code,
            message=self.message,
            context=self.context,
            suggestion=self.suggestion,
            request_id=request_id,
        )
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


# ============= 具体异常类型 =============

class APIException(CoPawException):
    """API 相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.API_REQUEST_FAILED, **kwargs)


class APITimeoutException(APIException):
    """API 超时异常"""
    
    def __init__(self, message: str = "API 请求超时", **kwargs):
        super().__init__(message, code=ErrorCode.API_TIMEOUT, **kwargs)


class APIRateLimitException(APIException):
    """API 速率限制异常"""
    
    def __init__(self, message: str = "API 请求过于频繁", **kwargs):
        super().__init__(message, code=ErrorCode.API_RATE_LIMIT, **kwargs)


class APIAuthException(APIException):
    """API 认证失败异常"""
    
    def __init__(self, message: str = "API 认证失败", **kwargs):
        super().__init__(message, code=ErrorCode.API_AUTH_FAILED, **kwargs)


class ChannelException(CoPawException):
    """渠道相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.CHANNEL_SEND_FAILED, **kwargs)


class ChannelNotFoundException(ChannelException):
    """渠道未找到异常"""
    
    def __init__(self, channel_name: str):
        super().__init__(
            message=f"渠道未找到：{channel_name}",
            code=ErrorCode.CHANNEL_NOT_FOUND,
            context={"channel_name": channel_name},
            suggestion=f"请检查渠道配置是否正确，支持的渠道包括：feishu, dingtalk, wechat 等",
        )


class SoulFileException(CoPawException):
    """Soul 文件相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.SOUL_FILE_NOT_FOUND, **kwargs)


class SoulFileProtectedException(SoulFileException):
    """Soul 文件保护异常"""
    
    def __init__(self, file_path: str):
        super().__init__(
            message=f"Soul 文件受保护，不能删除：{file_path}",
            code=ErrorCode.SOUL_FILE_PROTECTED,
            context={"file_path": file_path},
            suggestion="Soul 文件是 zo 的记忆和生命，删除后可能导致记忆丢失。如果确实需要修改，请先备份。",
        )


class ConfigException(CoPawException):
    """配置相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.CONFIG_INVALID, **kwargs)


class ConfigNotFoundException(ConfigException):
    """配置未找到异常"""
    
    def __init__(self, config_key: str):
        super().__init__(
            message=f"配置未找到：{config_key}",
            code=ErrorCode.CONFIG_NOT_FOUND,
            context={"config_key": config_key},
            suggestion="请检查配置文件是否正确设置",
        )


class SessionException(CoPawException):
    """会话相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.SESSION_NOT_FOUND, **kwargs)


class ChatException(CoPawException):
    """聊天相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.CHAT_NOT_FOUND, **kwargs)


class ChatNotFoundException(ChatException):
    """聊天未找到异常"""
    
    def __init__(self, chat_id: str):
        super().__init__(
            message=f"聊天未找到：{chat_id}",
            code=ErrorCode.CHAT_NOT_FOUND,
            context={"chat_id": chat_id},
        )


class CronException(CoPawException):
    """定时任务相关异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code=ErrorCode.CRON_EXECUTION_FAILED, **kwargs)


class CronNotFoundException(CronException):
    """定时任务未找到异常"""
    
    def __init__(self, job_id: str):
        super().__init__(
            message=f"定时任务未找到：{job_id}",
            code=ErrorCode.CRON_NOT_FOUND,
            context={"job_id": job_id},
        )


# ============= 错误处理工具函数 =============

def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
) -> None:
    """记录错误日志
    
    Args:
        error: 异常对象
        context: 额外上下文
        level: 日志级别 (debug, info, warning, error, critical)
    """
    log_func = getattr(logger, level, logger.error)
    
    # 构建日志消息
    msg_parts = []
    
    if isinstance(error, CoPawException):
        msg_parts.append(f"[{error.code.value}]")
        msg_parts.append(error.message)
        
        if error.context:
            for k, v in error.context.items():
                msg_parts.append(f"{k}={v}")
        
        if error.suggestion:
            msg_parts.append(f"Suggestion: {error.suggestion}")
    else:
        msg_parts.append(str(error))
    
    if context:
        for k, v in context.items():
            msg_parts.append(f"{k}={v}")
    
    msg = " ".join(msg_parts)
    
    # 记录日志
    if level == "exception":
        log_func(msg, exc_info=True)
    else:
        log_func(msg)


def handle_exception(
    error: Exception,
    default_message: str = "操作失败",
    raise_new: bool = False,
    new_exception_type: Optional[type] = None,
) -> Optional[Exception]:
    """统一异常处理
    
    Args:
        error: 原始异常
        default_message: 默认错误消息
        raise_new: 是否抛出新的异常
        new_exception_type: 新异常类型
    
    Returns:
        处理后的异常，如果 raise_new=True 则抛出
    
    Example:
        ```python
        try:
            some_operation()
        except Exception as e:
            handle_exception(e, default_message="操作失败")
        
        # 或者抛出新的异常
        try:
            some_operation()
        except Exception as e:
            handle_exception(e, raise_new=True, new_exception_type=APIException)
        ```
    """
    # 记录原始异常
    log_error(error, level="exception")
    
    if raise_new:
        if new_exception_type:
            new_error = new_exception_type(default_message, original_exception=error)
        else:
            new_error = CoPawException(default_message, original_exception=error)
        
        raise new_error from error
    
    return None


# ============= 全局异常处理器 (FastAPI) =============

async def fastapi_exception_handler(request, exc: Exception) -> Dict[str, Any]:
    """FastAPI 全局异常处理器
    
    在 app/_app.py 中注册:
    ```python
    from app.common.exceptions import fastapi_exception_handler
    
    app.add_exception_handler(Exception, fastapi_exception_handler)
    ```
    """
    import uuid
    
    request_id = str(uuid.uuid4())
    
    # 记录异常
    log_error(exc, context={"request_id": request_id, "path": request.url.path})
    
    # 构建错误响应
    if isinstance(exc, CoPawException):
        error_detail = exc.to_error_detail(request_id)
        status_code = _get_status_code(exc.code)
    else:
        error_detail = ErrorDetail(
            code=ErrorCode.SYS_UNKNOWN_ERROR,
            message=str(exc),
            request_id=request_id,
        )
        status_code = 500
    
    return {
        "success": False,
        "error": error_detail.to_dict(),
    }


def _get_status_code(code: ErrorCode) -> int:
    """根据错误代码获取 HTTP 状态码"""
    if code.value.startswith("SYS"):
        return 500
    elif code.value.startswith("API"):
        if code == ErrorCode.API_NOT_FOUND:
            return 404
        elif code == ErrorCode.API_AUTH_FAILED:
            return 401
        elif code == ErrorCode.API_RATE_LIMIT:
            return 429
        else:
            return 500
    elif code.value.startswith("CHANNEL"):
        return 500
    elif code.value.startswith("SOUL"):
        if code == ErrorCode.SOUL_FILE_PROTECTED:
            return 403
        else:
            return 404
    elif code.value.startswith("CONFIG"):
        return 400
    elif code.value.startswith("SESSION"):
        return 401
    elif code.value.startswith("CHAT"):
        return 404
    elif code.value.startswith("CRON"):
        return 404
    else:
        return 500


__all__ = [
    # 错误代码
    "ErrorCode",
    
    # 错误详情
    "ErrorDetail",
    
    # 异常基类
    "CoPawException",
    
    # 具体异常
    "APIException",
    "APITimeoutException",
    "APIRateLimitException",
    "APIAuthException",
    "ChannelException",
    "ChannelNotFoundException",
    "SoulFileException",
    "SoulFileProtectedException",
    "ConfigException",
    "ConfigNotFoundException",
    "SessionException",
    "ChatException",
    "ChatNotFoundException",
    "CronException",
    "CronNotFoundException",
    
    # 工具函数
    "log_error",
    "handle_exception",
    "fastapi_exception_handler",
]
