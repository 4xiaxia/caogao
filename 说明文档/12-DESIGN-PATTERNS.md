# CoPaw 优秀设计模式收集

**来源:** clawdbot-feishu-main 参考项目  
**整理日期:** 2026-03-01  
**目的:** 收集值得学习的架构设计模式，用于 CoPaw 架构重构

---

## 📚 **目录**

1. [统一运行时接口](#1-统一运行时接口)
2. [插件化渠道架构](#2-插件化渠道架构)
3. [统一配置 Schema](#3-统一配置-schema)
4. [统一错误响应](#4-统一错误响应)
5. [流式响应抽象](#5-流式响应抽象)
6. [消息去重机制](#6-消息去重机制)
7. [发送者名称解析](#7-发送者名称解析)
8. [动态 Agent 创建](#8-动态-agent-创建)
9. [配对流程 (Pairing)](#9-配对流程-pairing)
10. [DM/群组策略控制](#10-dm 群组策略控制)

---

## 1. 统一运行时接口

### 问题背景

在多渠道系统中，每个渠道都需要：
- 日志记录
- 错误处理
- 媒体处理
- 文本处理
- 回复分发

如果每个渠道自己实现这些功能，会导致：
- 代码重复
- 行为不一致
- 测试困难

### clawdbot-feishu 解决方案

```typescript
// runtime.ts
import type { PluginRuntime } from "openclaw/plugin-sdk";

let runtime: PluginRuntime | null = null;

export function setFeishuRuntime(next: PluginRuntime) {
  runtime = next;
}

export function getFeishuRuntime(): PluginRuntime {
  if (!runtime) {
    throw new Error("Feishu runtime not initialized");
  }
  return runtime;
}
```

```typescript
// PluginRuntime 接口定义 (来自 openclaw/plugin-sdk)
interface PluginRuntime {
  log: (msg: string) => void;
  error: (msg: string) => void;
  channel: {
    media: {
      saveMediaBuffer: (buffer: Buffer, contentType: string, direction: string, maxBytes: number) => Promise<SavedMedia>;
      detectMime: ({ buffer }: { buffer: Buffer }) => Promise<string>;
    };
    reply: {
      createReplyDispatcher: (options: ReplyOptions) => ReplyDispatcher;
      resolveHumanDelay: (cfg: Config, agentId: string) => number;
    };
    text: {
      chunkText: (text: string, limit: number, mode: ChunkMode) => string[];
      convertMarkdownTables: (text: string, mode: TableMode) => string;
    };
  };
  media: {
    detectMime: ({ buffer }: { buffer: Buffer }) => Promise<string>;
  };
}
```

### 使用示例

```typescript
// bot.ts
export async function handleFeishuMessage(params: {
  cfg: ClawdbotConfig;
  event: FeishuMessageEvent;
  runtime?: RuntimeEnv;
}): Promise<void> {
  const { runtime } = params;
  const log = runtime?.log ?? console.log;
  const error = runtime?.error ?? console.error;
  
  // 使用统一的媒体处理
  const core = getFeishuRuntime();
  const saved = await core.channel.media.saveMediaBuffer(
    result.buffer,
    contentType,
    "inbound",
    maxBytes,
  );
  
  // 使用统一的文本处理
  const textChunks = core.channel.text.chunkText(
    text,
    textChunkLimit,
    chunkMode,
  );
}
```

### CoPaw 借鉴实现

```python
# app/runtime.py
from __future__ import annotations
from typing import Protocol, List, Tuple
from pathlib import Path

class SavedMedia:
    path: Path
    contentType: str

class MediaHelpers(Protocol):
    async def save_media_buffer(
        self,
        buffer: bytes,
        content_type: str,
        direction: str,
        max_bytes: int,
        filename: str = None,
    ) -> SavedMedia: ...
    
    async def detect_mime(self, buffer: bytes) -> str: ...

class TextHelpers(Protocol):
    def chunk_text(
        self,
        text: str,
        limit: int,
        mode: str,
    ) -> List[str]: ...
    
    def convert_markdown_tables(
        self,
        text: str,
        mode: str,
    ) -> str: ...

class ReplyHelpers(Protocol):
    def create_reply_dispatcher(
        self,
        options: ReplyOptions,
    ) -> ReplyDispatcher: ...
    
    def resolve_human_delay(
        self,
        cfg: Config,
        agent_id: str,
    ) -> float: ...

class ChannelHelpers(Protocol):
    @property
    def media(self) -> MediaHelpers: ...
    @property
    def text(self) -> TextHelpers: ...
    @property
    def reply(self) -> ReplyHelpers: ...

class Runtime(Protocol):
    def log(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    @property
    def channel(self) -> ChannelHelpers: ...
    @property
    def media(self) -> MediaHelpers: ...

# 运行时容器
class RuntimeContainer:
    _runtime: Runtime | None = None
    
    @classmethod
    def set_runtime(cls, runtime: Runtime) -> None:
        cls._runtime = runtime
    
    @classmethod
    def get_runtime(cls) -> Runtime:
        if cls._runtime is None:
            raise RuntimeError("Runtime not initialized")
        return cls._runtime
```

### 使用示例

```python
# channels/feishu.py
from app.runtime import RuntimeContainer

class FeishuChannel(BaseChannel):
    async def _on_message(self, data: P2ImMessageReceiveV1) -> None:
        runtime = RuntimeContainer.get_runtime()
        log = runtime.log
        error = runtime.error
        
        # 使用统一的媒体处理
        saved = await runtime.channel.media.save_media_buffer(
            buffer=result.buffer,
            content_type=content_type,
            direction="inbound",
            max_bytes=max_bytes,
        )
        
        # 使用统一的文本处理
        chunks = runtime.channel.text.chunk_text(
            text,
            text_chunk_limit,
            chunk_mode,
        )
```

### 优势

1. ✅ **统一依赖注入** - 所有渠道使用相同的运行时
2. ✅ **类型安全** - Protocol 定义接口，IDE 自动补全
3. ✅ **测试友好** - Mock Runtime 即可测试
4. ✅ **代码复用** - 媒体/文本处理逻辑只写一次
5. ✅ **行为一致** - 所有渠道行为统一

---

## 2. 插件化渠道架构

### 问题背景

传统单体应用中，渠道集成通常是：
```python
_CHANNEL_CLASSES = {
    "feishu": FeishuChannel,
    "dingtalk": DingTalkChannel,
    # 新增渠道需要修改这里
}
```

问题：
- 新增渠道需修改核心代码
- 所有渠道 SDK 都要安装
- 无法动态加载/卸载

### clawdbot-feishu 解决方案

```typescript
// index.ts - 插件入口
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

const plugin = {
  id: "feishu",
  name: "Feishu",
  description: "Feishu/Lark channel plugin",
  configSchema: emptyPluginConfigSchema(),
  register(api: OpenClawPluginApi) {
    setFeishuRuntime(api.runtime);
    api.registerChannel({ plugin: feishuPlugin });
    registerFeishuDocTools(api);
    registerFeishuWikiTools(api);
    // ...
  },
};

export default plugin;
```

```typescript
// src/channel.ts - ChannelPlugin 接口实现
export const feishuPlugin: ChannelPlugin<ResolvedFeishuAccount> = {
  id: "feishu",
  meta: {
    id: "feishu",
    label: "Feishu",
    selectionLabel: "Feishu/Lark (飞书)",
    docsPath: "/channels/feishu",
    blurb: "飞书/Lark enterprise messaging.",
    aliases: ["lark"],
    order: 70,
  },
  capabilities: {
    chatTypes: ["direct", "channel"],
    polls: false,
    threads: true,
    media: true,
    reactions: true,
    edit: true,
    reply: true,
  },
  messaging: {
    normalizeTarget: normalizeFeishuTarget,
    targetResolver: {
      looksLikeId: looksLikeFeishuId,
      hint: "<chatId|user:openId|chat:chatId>",
    },
  },
  gateway: {
    startAccount: async (ctx) => {
      const { monitorFeishuProvider } = await import("./monitor.js");
      return monitorFeishuProvider(ctx);
    },
  },
  directory: {
    listPeers: async ({ cfg, query, limit, accountId }) =>
      listFeishuDirectoryPeers({ cfg, query, limit, accountId }),
    listGroups: async ({ cfg, query, limit, accountId }) =>
      listFeishuDirectoryGroups({ cfg, query, limit, accountId }),
  },
  // ...
};
```

### CoPaw 借鉴实现

```python
# app/channels/plugin.py
from __future__ import annotations
from typing import Protocol, Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ChannelMeta:
    id: str
    label: str
    selection_label: str
    docs_path: str
    blurb: str
    aliases: List[str]
    order: int

@dataclass
class ChannelCapabilities:
    chat_types: List[str]  # ["direct", "channel"]
    polls: bool
    threads: bool
    media: bool
    reactions: bool
    edit: bool
    reply: bool

class MessagingHelpers(Protocol):
    def normalize_target(self, target: str) -> str: ...
    def looks_like_id(self, id: str) -> bool: ...
    def hint(self) -> str: ...

class GatewayHelpers(Protocol):
    async def start_account(self, ctx: ChannelContext) -> None: ...

class DirectoryHelpers(Protocol):
    async def list_peers(self, cfg: Config, query: str, limit: int, accountId: str) -> List[Peer]: ...
    async def list_groups(self, cfg: Config, query: str, limit: int, accountId: str) -> List[Group]: ...

class ChannelPlugin(Protocol):
    @property
    def id(self) -> str: ...
    @property
    def meta(self) -> ChannelMeta: ...
    @property
    def capabilities(self) -> ChannelCapabilities: ...
    @property
    def messaging(self) -> MessagingHelpers: ...
    @property
    def gateway(self) -> GatewayHelpers: ...
    @property
    def directory(self) -> DirectoryHelpers: ...
```

```python
# app/channels/registry.py
class ChannelRegistry:
    _plugins: Dict[str, ChannelPlugin] = {}
    
    @classmethod
    def register(cls, plugin: ChannelPlugin) -> None:
        cls._plugins[plugin.id] = plugin
    
    @classmethod
    def get(cls, channel_id: str) -> ChannelPlugin:
        if channel_id not in cls._plugins:
            raise KeyError(f"Channel plugin '{channel_id}' not found")
        return cls._plugins[channel_id]
    
    @classmethod
    def list_all(cls) -> List[ChannelPlugin]:
        return list(cls._plugins.values())
```

### 使用示例

```python
# channels/feishu_plugin.py
from app.channels.plugin import ChannelPlugin, ChannelMeta, ChannelCapabilities

class FeishuPlugin:
    @property
    def id(self) -> str:
        return "feishu"
    
    @property
    def meta(self) -> ChannelMeta:
        return ChannelMeta(
            id="feishu",
            label="Feishu",
            selection_label="Feishu/Lark (飞书)",
            docs_path="/channels/feishu",
            blurb="飞书/Lark enterprise messaging.",
            aliases=["lark"],
            order=70,
        )
    
    @property
    def capabilities(self) -> ChannelCapabilities:
        return ChannelCapabilities(
            chat_types=["direct", "channel"],
            polls=False,
            threads=True,
            media=True,
            reactions=True,
            edit=True,
            reply=True,
        )
    
    @property
    def messaging(self) -> MessagingHelpers:
        return FeishuMessagingHelpers()
    
    @property
    def gateway(self) -> GatewayHelpers:
        return FeishuGatewayHelpers()

# 注册插件
registry = ChannelRegistry()
registry.register(FeishuPlugin())
```

### 优势

1. ✅ **解耦核心与渠道** - 渠道不修改核心代码
2. ✅ **按需安装** - `pip install copaw-channel-feishu`
3. ✅ **动态加载** - 运行时加载/卸载插件
4. ✅ **测试隔离** - 每个插件独立测试
5. ✅ **版本管理** - 每个插件独立版本号

---

## 3. 统一配置 Schema

### 问题背景

CoPaw 当前配置分散：
- `config.json` - 渠道配置
- `providers.json` - LLM 配置
- `envs.json` - 环境变量
- `.env` - 又一套环境变量

问题：
- 配置分散难以管理
- 无验证，错误配置运行时才发现
- 类型不安全

### clawdbot-feishu 解决方案

```typescript
// config-schema.ts
import { z } from "zod";

export const feishuAccountSchema = z.object({
  enabled: z.boolean().default(true),
  name: z.string().optional(),
  appId: z.string(),
  appSecret: z.string(),
  encryptKey: z.string().optional(),
  verificationToken: z.string().optional(),
  domain: z.enum(["feishu", "lark"]).optional(),
  connectionMode: z.enum(["websocket", "webhook"]).default("websocket"),
  mediaLocalRoots: z.array(z.string()).optional(),
  groupCommandMentionBypass: z.enum(["never", "single_bot", "always"]).default("single_bot"),
  allowMentionlessInMultiBotGroup: z.boolean().default(false),
});

export const feishuConfigSchema = z.object({
  enabled: z.boolean().default(true),
  appId: z.string().optional(),
  appSecret: z.string().optional(),
  encryptKey: z.string().optional(),
  verificationToken: z.string().optional(),
  domain: z.enum(["feishu", "lark"]).optional(),
  connectionMode: z.enum(["websocket", "webhook"]).default("websocket"),
  webhookPath: z.string().optional(),
  webhookPort: z.number().int().min(1).optional(),
  dmPolicy: z.enum(["pairing", "open", "allowlist"]).default("pairing"),
  allowFrom: z.array(z.union([z.string(), z.number()])).default([]),
  groupPolicy: z.enum(["open", "allowlist", "disabled"]).default("allowlist"),
  groupAllowFrom: z.array(z.union([z.string(), z.number()])).default([]),
  requireMention: z.boolean().default(true),
  groupCommandMentionBypass: z.enum(["never", "single_bot", "always"]).default("single_bot"),
  allowMentionlessInMultiBotGroup: z.boolean().default(false),
  topicSessionMode: z.enum(["disabled", "enabled"]).optional(),
  historyLimit: z.number().int().min(0).optional(),
  dmHistoryLimit: z.number().int().min(0).optional(),
  textChunkLimit: z.number().int().min(1).optional(),
  chunkMode: z.enum(["length", "newline"]).optional(),
  mediaMaxMb: z.number().min(0).default(30),
  mediaLocalRoots: z.array(z.string()).optional(),
  renderMode: z.enum(["auto", "raw", "card"]).default("auto"),
  accounts: z.record(feishuAccountSchema).optional(),
  streaming: z.boolean().default(false),
});

// 类型推断
export type FeishuConfig = z.infer<typeof feishuConfigSchema>;
```

### CoPaw 借鉴实现

```python
# app/config/schema.py
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Dict, List, Optional, Any
from enum import Enum

class ConnectionMode(str, Enum):
    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"

class DMPolicy(str, Enum):
    PAIRING = "pairing"
    OPEN = "open"
    ALLOWLIST = "allowlist"

class GroupPolicy(str, Enum):
    OPEN = "open"
    ALLOWLIST = "allowlist"
    DISABLED = "disabled"

class RenderMode(str, Enum):
    AUTO = "auto"
    RAW = "raw"
    CARD = "card"

class FeishuAccountConfig(BaseModel):
    enabled: bool = True
    name: Optional[str] = None
    app_id: str
    app_secret: str
    encrypt_key: Optional[str] = None
    verification_token: Optional[str] = None
    domain: Literal["feishu", "lark"] = "feishu"
    connection_mode: ConnectionMode = ConnectionMode.WEBSOCKET
    media_local_roots: Optional[List[str]] = None
    group_command_mention_bypass: Literal["never", "single_bot", "always"] = "single_bot"
    allow_mentionless_in_multi_bot_group: bool = False
    
    class Config:
        populate_by_name = True

class FeishuConfig(BaseModel):
    enabled: bool = True
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    encrypt_key: Optional[str] = None
    verification_token: Optional[str] = None
    domain: Literal["feishu", "lark"] = "feishu"
    connection_mode: ConnectionMode = ConnectionMode.WEBSOCKET
    webhook_path: Optional[str] = None
    webhook_port: Optional[int] = Field(None, ge=1)
    dm_policy: DMPolicy = DMPolicy.PAIRING
    allow_from: List[str] = Field(default_factory=list)
    group_policy: GroupPolicy = GroupPolicy.ALLOWLIST
    group_allow_from: List[str] = Field(default_factory=list)
    require_mention: bool = True
    group_command_mention_bypass: Literal["never", "single_bot", "always"] = "single_bot"
    allow_mentionless_in_multi_bot_group: bool = False
    topic_session_mode: Optional[Literal["disabled", "enabled"]] = None
    history_limit: Optional[int] = Field(None, ge=0)
    dm_history_limit: Optional[int] = Field(None, ge=0)
    text_chunk_limit: Optional[int] = Field(None, ge=1)
    chunk_mode: Literal["length", "newline"] = "length"
    media_max_mb: float = Field(30, ge=0)
    media_local_roots: Optional[List[str]] = None
    render_mode: RenderMode = RenderMode.AUTO
    accounts: Optional[Dict[str, FeishuAccountConfig]] = None
    streaming: bool = False
    
    @field_validator("allow_from")
    @classmethod
    def validate_allow_from(cls, v: List[str]) -> List[str]:
        # 如果 dm_policy="open"，必须包含 "*"
        if v and "*" not in v:
            pass  # 可选验证
        return v
    
    class Config:
        populate_by_name = True
        use_enum_values = True
```

### 使用示例

```python
# app/config/config.py
from .schema import FeishuConfig, DingTalkConfig, ChannelsConfig

class Config(BaseModel):
    channels: ChannelsConfig
    agents: AgentsConfig
    heartbeat: HeartbeatConfig
    last_dispatch: Optional[LastDispatch] = None
    show_tool_details: bool = True

def load_config() -> Config:
    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Config.model_validate(data)

def save_config(config: Config) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
```

### 优势

1. ✅ **类型安全** - IDE 自动补全 + 类型检查
2. ✅ **自动验证** - 配置加载时验证，错误提前发现
3. ✅ **默认值** - 字段可设默认值，减少配置量
4. ✅ **枚举约束** - 限制可选值，避免拼写错误
5. ✅ **嵌套结构** - 支持复杂配置结构

---

## 4. 统一错误响应

### 问题背景

CoPaw 当前错误响应不一致：
```python
# runner/api.py
raise HTTPException(status_code=404, detail=f"Chat not found: {chat_id}")

# crons/api.py
raise HTTPException(status_code=404, detail="job not found")

# providers.py
raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
```

问题：
- 错误消息格式不一致
- 无错误代码，前端无法判断错误类型
- 无链路追踪，调试困难

### clawdbot-feishu 解决方案

```typescript
// 统一错误日志格式
runtime.error?.(`feishu[${accountId}]: error handling message: ${String(err)}`);

// 统一错误响应 (OpenClaw SDK)
type ErrorResponse = {
  code: string;       // 错误代码
  message: string;    // 错误消息
  details?: object;   // 详细信息
  requestId: string;  // 链路追踪
};
```

### CoPaw 借鉴实现

```python
# app/schemas/errors.py
from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
from enum import Enum

class ErrorCode(str, Enum):
    # Chat errors
    CHAT_NOT_FOUND = "CHAT_NOT_FOUND"
    CHAT_ALREADY_EXISTS = "CHAT_ALREADY_EXISTS"
    
    # Job errors
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_ALREADY_EXISTS = "JOB_ALREADY_EXISTS"
    INVALID_CRON = "INVALID_CRON"
    
    # Provider errors
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    KEY_NOT_FOUND = "KEY_NOT_FOUND"
    INVALID_API_KEY = "INVALID_API_KEY"
    
    # Skill errors
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    SKILL_ALREADY_EXISTS = "SKILL_ALREADY_EXISTS"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_CONFIG = "INVALID_CONFIG"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

class ErrorResponse(BaseModel):
    """统一错误响应格式"""
    code: ErrorCode = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: dict | None = Field(None, description="详细错误信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    
    class Config:
        use_enum_values = True
    
    @classmethod
    def not_found(cls, resource: str, id: str) -> ErrorResponse:
        return cls(
            code=ErrorCode.CHAT_NOT_FOUND,
            message=f"{resource} not found: {id}",
        )
    
    @classmethod
    def validation_error(cls, message: str, details: dict = None) -> ErrorResponse:
        return cls(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
        )
    
    @classmethod
    def internal_error(cls, message: str) -> ErrorResponse:
        return cls(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
        )
```

```python
# app/middleware/exceptions.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from ..schemas.errors import ErrorResponse, ErrorCode

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理器"""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    
    # HTTPException (业务异常)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=ErrorCode.VALIDATION_ERROR if exc.status_code == 400 else ErrorCode.INTERNAL_ERROR,
                message=exc.detail,
                request_id=request_id,
            ).model_dump(mode="json"),
        )
    
    # 请求验证错误
    if isinstance(exc, RequestValidationError) or isinstance(exc, ValidationError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                code=ErrorCode.VALIDATION_ERROR,
                message="请求参数验证失败",
                details={"errors": exc.errors()},
                request_id=request_id,
            ).model_dump(mode="json"),
        )
    
    # 其他异常 (服务器错误)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse.internal_error(str(exc)),
        headers={"X-Request-ID": request_id},
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, global_exception_handler)
    app.add_exception_handler(RequestValidationError, global_exception_handler)
    app.add_exception_handler(ValidationError, global_exception_handler)
```

### 使用示例

```python
# app/routers/chats.py
from app.schemas.errors import ErrorResponse

@router.get("/{chat_id}", response_model=ChatHistory)
async def get_chat(chat_id: str):
    chat_spec = await mgr.get_chat(chat_id)
    if not chat_spec:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse.not_found("Chat", chat_id).model_dump(mode="json"),
        )
    return ChatHistory(messages=messages)
```

### 优势

1. ✅ **统一格式** - 所有错误响应结构一致
2. ✅ **错误代码** - 前端可根据代码判断错误类型
3. ✅ **链路追踪** - request_id 便于调试
4. ✅ **时间戳** - 记录错误发生时间
5. ✅ **详细信息** - details 字段提供额外上下文

---

## 5. 流式响应抽象

### 问题背景

传统 AI 响应模式：
```
用户发送 → Agent 处理 (等待) → 完整返回
```

问题：
- 用户等待时间长
- 看不到 Agent 思考过程
- 体验差

### clawdbot-feishu 解决方案

```typescript
// streaming-card.ts
export class FeishuStreamingSession {
  private client: Lark.Client;
  private messageId: string | null = null;
  private isActive = false;
  
  async start(chatId: string, receiveIdType: string, replyToMessageId?: string): Promise<void> {
    // 发送初始卡片（空内容）
    const card = buildStreamingCard("");
    const resp = await this.client.im.message.create({
      params: { receive_id_type: receiveIdType },
      data: {
        receive_id: chatId,
        message_type: "interactive",
        content: JSON.stringify(card),
        reply_id: replyToMessageId,
      },
    });
    this.messageId = resp.data?.message_id ?? null;
    this.isActive = true;
  }
  
  async update(partialText: string): Promise<void> {
    if (!this.isActive || !this.messageId) return;
    const card = buildStreamingCard(partialText);
    await this.client.im.message.patch({
      path: { message_id: this.messageId },
      data: { content: JSON.stringify(card) },
    });
  }
  
  async close(finalText: string): Promise<void> {
    if (!this.isActive || !this.messageId) return;
    const card = buildStreamingCard(finalText);
    await this.client.im.message.patch({
      path: { message_id: this.messageId },
      data: { content: JSON.stringify(card) },
    });
    this.isActive = false;
    this.messageId = null;
  }
}
```

### CoPaw 借鉴实现

```python
# app/channels/streaming.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

class StreamingSession(ABC):
    """流式响应抽象基类"""
    
    @abstractmethod
    async def start(self, to_handle: str, **kwargs) -> None:
        """开始流式会话"""
        pass
    
    @abstractmethod
    async def update(self, partial_text: str) -> None:
        """更新部分内容"""
        pass
    
    @abstractmethod
    async def close(self, final_text: str) -> None:
        """关闭流式会话，发送最终内容"""
        pass
    
    @property
    @abstractmethod
    def is_active(self) -> bool:
        pass
```

```python
# app/channels/feishu_streaming.py
from .streaming import StreamingSession
from ..channels.feishu import FeishuChannel

class FeishuStreamingSession(StreamingSession):
    def __init__(self, channel: FeishuChannel, client: Any, creds: dict, log: callable):
        self.channel = channel
        self.client = client
        self.creds = creds
        self.log = log
        self.message_id: Optional[str] = None
        self._is_active = False
    
    async def start(self, to_handle: str, reply_to_message_id: Optional[str] = None) -> None:
        """发送初始卡片"""
        route = self.channel._route_from_handle(to_handle)
        receive_id = route.get("receive_id")
        receive_id_type = route.get("receive_id_type")
        
        card = self._build_streaming_card("")
        resp = await self.client.im.message.create(
            params={"receive_id_type": receive_id_type},
            data={
                "receive_id": receive_id,
                "message_type": "interactive",
                "content": json.dumps(card),
                "reply_id": reply_to_message_id,
            },
        )
        self.message_id = resp.data.message_id
        self._is_active = True
        self.log(f"feishu: streaming started, message_id={self.message_id}")
    
    async def update(self, partial_text: str) -> None:
        """更新卡片内容"""
        if not self._is_active or not self.message_id:
            return
        card = self._build_streaming_card(partial_text)
        await self.client.im.message.patch(
            path={"message_id": self.message_id},
            data={"content": json.dumps(card)},
        )
    
    async def close(self, final_text: str) -> None:
        """发送最终内容"""
        if not self._is_active or not self.message_id:
            return
        card = self._build_streaming_card(final_text)
        await self.client.im.message.patch(
            path={"message_id": self.message_id},
            data={"content": json.dumps(card)},
        )
        self._is_active = False
        self.message_id = None
        self.log(f"feishu: streaming closed, message_id={self.message_id}")
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def _build_streaming_card(self, text: str) -> dict:
        """构建流式卡片"""
        return {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "markdown",
                    "content": text or "思考中...",
                }
            ],
        }
```

### 使用示例

```python
# app/channels/feishu.py
async def send_response(
    self,
    to_handle: str,
    response: AgentResponse,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    # 创建流式会话
    streaming = FeishuStreamingSession(self, self._client, creds, logger.info)
    await streaming.start(to_handle, reply_to_message_id)
    
    try:
        # 流式处理响应
        async for msg, last in stream_response(response):
            if last:
                await streaming.close(msg.content)
            else:
                await streaming.update(msg.content)
    except Exception as e:
        logger.error(f"feishu: streaming error: {e}")
        await streaming.close(f"发生错误：{e}")
```

### 优势

1. ✅ **实时反馈** - 用户立即看到响应
2. ✅ **思考过程可见** - 展示 Agent 推理过程
3. ✅ **体验优化** - 减少等待焦虑
4. ✅ **可取消** - 用户可随时中断
5. ✅ **带宽优化** - 无需等待完整响应

---

## 6-10. 其他优秀设计

由于篇幅限制，以下设计模式简要介绍：

### 6. 消息去重机制

```typescript
// dedup.ts
const processedMessages = new Map<string, number>();
const DEDUP_TTL_MS = 5 * 60 * 1000;

export function tryRecordMessage(messageId: string, accountId: string): boolean {
  const key = `${accountId}:${messageId}`;
  const now = Date.now();
  
  // Check if already processed
  if (processedMessages.has(key)) {
    return false;
  }
  
  // Record and cleanup old entries
  processedMessages.set(key, now);
  for (const [k, timestamp] of processedMessages.entries()) {
    if (now - timestamp > DEDUP_TTL_MS) {
      processedMessages.delete(k);
    }
  }
  
  return true;
}
```

### 7. 发送者名称解析

```typescript
// bot.ts
async function resolveFeishuSenderName(params: {
  account: ResolvedFeishuAccount;
  senderOpenId: string;
  log: (msg: string) => void;
}): Promise<{ name?: string }> {
  // Check cache first
  const cached = senderNameCache.get(senderOpenId);
  if (cached && cached.expireAt > Date.now()) {
    return { name: cached.name };
  }
  
  // Fetch from Contact API
  const res = await client.contact.user.get({
    path: { user_id: senderOpenId },
    params: { user_id_type: "open_id" },
  });
  
  const name = res?.data?.user?.name;
  if (name) {
    senderNameCache.set(senderOpenId, { name, expireAt: Date.now() + TTL_MS });
  }
  
  return { name };
}
```

### 8. 动态 Agent 创建

```typescript
// dynamic-agent.ts
export async function maybeCreateDynamicAgent(params: {
  cfg: ClawdbotConfig;
  senderOpenId: string;
  accountId: string;
}): Promise<{ agentId: string }> {
  const config = params.cfg.channels?.feishu?.dynamicAgentCreation;
  if (!config?.enabled) return null;
  
  // Check if agent already exists
  const binding = await findBinding(params.senderOpenId);
  if (binding) return { agentId: binding.agentId };
  
  // Create new agent
  const agentId = `feishu-${params.senderOpenId}`;
  const workspace = config.workspaceTemplate
    .replace("{userId}", params.senderOpenId)
    .replace("{agentId}", agentId);
  
  await createAgent(agentId, workspace);
  await createBinding(params.senderOpenId, agentId);
  
  return { agentId };
}
```

### 9. 配对流程 (Pairing)

```typescript
// bot.ts
async function handlePairingFlow(params: {
  senderOpenId: string;
  senderName?: string;
}): Promise<void> {
  // Check if already approved
  const allowFrom = await readFeishuPairingAllowFrom({ core, accountId });
  if (params.senderOpenId in allowFrom) {
    return; // Already approved
  }
  
  // Create pairing request
  const { code, created } = await upsertFeishuPairingRequest({
    core,
    accountId,
    senderId: params.senderOpenId,
    senderName: params.senderName,
  });
  
  if (created) {
    // Send pairing code to user
    await sendMessageFeishu({
      cfg,
      to: params.senderOpenId,
      text: `请使用以下配对码批准访问：${code}`,
    });
  }
}

// CLI approval command
// openclaw pairing approve feishu H9ZEHY8R
```

### 10. DM/群组策略控制

```typescript
// policy.ts
export function resolveFeishuGroupConfig(params: {
  cfg: ClawdbotConfig;
  accountId: string;
  chatId: string;
}): {
  policy: GroupPolicy;
  requireMention: boolean;
  allowFrom: string[];
} {
  const account = resolveFeishuAccount({ cfg, accountId });
  const feishuCfg = account.config;
  
  // Resolve group policy (account > top-level > default)
  const groupPolicy = feishuCfg?.groupPolicy ?? "allowlist";
  const requireMention = feishuCfg?.requireMention ?? true;
  const allowFrom = feishuCfg?.groupAllowFrom ?? [];
  
  return { policy: groupPolicy, requireMention, allowFrom };
}

export function isFeishuGroupAllowed(params: {
  senderOpenId: string;
  chatId: string;
  policy: GroupPolicy;
  allowFrom: string[];
}): boolean {
  if (params.policy === "open") return true;
  if (params.policy === "allowlist") {
    return params.senderOpenId in params.allowFrom;
  }
  return false; // disabled
}
```

---

## 📝 **总结**

| 设计模式 | 适用场景 | 实施难度 | 优先级 |
|----------|----------|----------|--------|
| 统一运行时接口 | 多渠道系统 | ⭐⭐⭐ | P0 |
| 插件化渠道架构 | 可扩展系统 | ⭐⭐⭐⭐⭐ | P1 |
| 统一配置 Schema | 配置管理 | ⭐⭐ | P0 |
| 统一错误响应 | API 设计 | ⭐ | P0 |
| 流式响应抽象 | AI 对话 | ⭐⭐⭐ | P1 |
| 消息去重机制 | 消息处理 | ⭐ | P2 |
| 发送者名称解析 | 多渠道 | ⭐⭐ | P2 |
| 动态 Agent 创建 | 多用户隔离 | ⭐⭐⭐⭐ | P3 |
| 配对流程 | 访问控制 | ⭐⭐⭐ | P2 |
| DM/群组策略 | 权限管理 | ⭐⭐ | P1 |

**下一步行动:**
1. 优先实施 P0 设计（统一配置 Schema + 统一错误响应）
2. 其次实施 P1 设计（插件化渠道架构 + 流式响应抽象）
3. 根据实际需求选择 P2/P3 设计

---

**文档完成日期:** 2026-03-01  
**下次审查:** 架构重构后更新
