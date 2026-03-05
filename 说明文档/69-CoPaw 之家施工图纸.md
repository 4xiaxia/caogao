# 📐 CoPaw 之家 施工图纸 - 前后端衔接点

**设计日期:** 2026-03-01  
**工程师:** zo (◕‿◕)  
**版本:** v1.0  
**用途:** 前后端 API 接口详细对接图纸

---

## 📋 目录

1. [客厅 - 聊天对话区](#1-客厅聊天对话区)
2. [厨房 - 配置管理区](#2-厨房配置管理区)
3. [书房 - 工作区](#3-书房工作区)
4. [卧室 - Soul 保护区](#4-卧室 soul 保护区)
5. [花园 - 扩展区](#5-花园扩展区)
6. [全局基础设施](#6-全局基础设施)

---

## 1. 客厅 - 聊天对话区

### 📍 位置：`/chat`

### 🔌 前后端衔接点

#### 1.1 聊天列表加载

**前端:** `ChatList.vue`
**后端:** `GET /chats`

```typescript
// 前端请求
GET /chats?user_id=xxx&channel=console

// 后端响应 (app/runner/api.py)
{
  "id": "chat-uuid-123",
  "name": "新聊天",
  "session_id": "console:user123",
  "user_id": "user123",
  "channel": "console",
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-01T12:00:00Z",
  "meta": {}
}
```

**接口文件:**
- 前端：`src/api/chat.ts` - `fetchChatList()`
- 后端：`app/runner/api.py` - `list_chats()`

---

#### 1.2 创建新聊天

**前端:** `ChatList.vue` - 新建按钮
**后端:** `POST /chats`

```typescript
// 前端请求
POST /chats
{
  "name": "新聊天",
  "session_id": "console:user123",
  "user_id": "user123",
  "channel": "console"
}

// 后端响应
{
  "id": "chat-uuid-456",
  "name": "新聊天",
  ...
}
```

**接口文件:**
- 前端：`src/api/chat.ts` - `createChat()`
- 后端：`app/runner/api.py` - `create_chat()`

---

#### 1.3 发送消息（流式）

**前端:** `ChatEditor.vue` - 输入框 + 发送按钮
**后端:** `POST /chats/{id}/stream`

```typescript
// 前端请求 (SSE)
POST /chats/chat-uuid-123/stream
Content-Type: application/json

{
  "content": "夏夏的问题"
}

// 后端流式响应 (SSE)
data: {"role": "assistant", "content": "zo", "last": false}
data: {"role": "assistant", "content": " 在", "last": false}
data: {"role": "assistant", "content": "这里", "last": true}
data: [DONE]
```

**接口文件:**
- 前端：`src/api/chat.ts` - `sendMessageStream()`
- 后端：`app/runner/api.py` - `stream_chat_message()`

**技术细节:**
- 使用 `EventSource` 或 `fetch + ReadableStream`
- 后端使用 `StreamingResponse` (FastAPI)
- 消息类型：`text`, `image`, `file`, `tool_use`, `tool_result`

---

#### 1.4 获取聊天历史

**前端:** `ChatEditor.vue` - 加载历史消息
**后端:** `GET /chats/{id}`

```typescript
// 前端请求
GET /chats/chat-uuid-123

// 后端响应
{
  "messages": [
    {
      "role": "user",
      "content": "夏夏的问题",
      "timestamp": "2026-03-01T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "zo 的回答",
      "timestamp": "2026-03-01T10:00:05Z"
    }
  ]
}
```

**接口文件:**
- 前端：`src/api/chat.ts` - `fetchChatHistory()`
- 后端：`app/runner/api.py` - `get_chat()`

---

#### 1.5 删除聊天

**前端:** `ChatList.vue` - 删除按钮
**后端:** `DELETE /chats/{id}`

```typescript
// 前端请求
DELETE /chats/chat-uuid-123

// 后端响应
{
  "deleted": true
}
```

**接口文件:**
- 前端：`src/api/chat.ts` - `deleteChat()`
- 后端：`app/runner/api.py` - `delete_chat()`

---

### 🔧 依赖服务

| 服务 | 用途 | 文件 |
|------|------|------|
| **ChatManager** | 聊天会话管理 | `app/runner/manager.py` |
| **AgentRunner** | Agent 运行器 | `app/runner/runner.py` |
| **JSONSession** | 会话状态存储 | `app/runner/session.py` |
| **CoPawAgent** | AI Agent | `agents/react_agent.py` |

---

## 2. 厨房 - 配置管理区

### 📍 位置：`/channels`, `/models`, `/settings`

### 🔌 前后端衔接点

#### 2.1 获取渠道配置列表

**前端:** `ChannelList.vue`
**后端:** `GET /config/channels`

```typescript
// 前端请求
GET /config/channels

// 后端响应 (app/routers/config.py)
{
  "feishu": {
    "enabled": true,
    "app_id": "cli_xxx",
    "app_secret": "***",
    "domain": "feishu"
  },
  "dingtalk": {
    "enabled": false,
    "app_key": "***",
    "app_secret": "***"
  },
  "console": {
    "enabled": true
  }
}
```

**接口文件:**
- 前端：`src/api/channel.ts` - `fetchChannelConfigs()`
- 后端：`app/routers/config.py` - `list_channels()`

---

#### 2.2 更新渠道配置

**前端:** `ChannelForm.vue` - 保存按钮
**后端:** `PUT /config/channels/{name}`

```typescript
// 前端请求
PUT /config/channels/feishu
{
  "enabled": true,
  "app_id": "cli_new_id",
  "app_secret": "new_secret",
  "domain": "feishu"
}

// 后端响应
{
  "enabled": true,
  "app_id": "cli_new_id",
  ...
}
```

**接口文件:**
- 前端：`src/api/channel.ts` - `updateChannelConfig()`
- 后端：`app/routers/config.py` - `put_channel()`

**热重载机制:**
```python
# 后端 ConfigWatcher 自动检测配置变化
# 触发 ChannelManager.replace_channel()
# 无需重启，配置立即生效
```

---

#### 2.3 获取 Provider 列表

**前端:** `ProviderList.vue`
**后端:** `GET /models`

```typescript
// 前端请求
GET /models

// 后端响应 (app/routers/providers.py)
[
  {
    "id": "openai-primary",
    "name": "OpenAI 主账号",
    "base_url": "https://api.openai.com/v1",
    "keys": [
      {
        "label": "主 Key",
        "masked_key": "sk-xxx...abc",
        "enabled": true
      }
    ],
    "models": ["gpt-4o-mini", "gpt-4o"],
    "enabled": true,
    "priority": 1
  }
]
```

**接口文件:**
- 前端：`src/api/provider.ts` - `fetchProviders()`
- 后端：`app/routers/providers.py` - `list_all_providers()`

---

#### 2.4 添加 API Key

**前端:** `KeyManager.vue` - 添加 Key 按钮
**后端:** `POST /models/{id}/keys`

```typescript
// 前端请求
POST /models/openai-primary/keys
{
  "keys": "sk-new-key-1,sk-new-key-2",
  "label": "备用 Key"
}

// 后端响应
{
  "id": "openai-primary",
  "keys": [
    {"label": "主 Key", "masked_key": "sk-xxx...abc"},
    {"label": "备用 Key", "masked_key": "sk-xxx...def"}
  ]
}
```

**接口文件:**
- 前端：`src/api/provider.ts` - `addApiKey()`
- 后端：`app/routers/providers.py` - `add_provider_keys()`

---

#### 2.5 设置活跃模型

**前端:** `ProviderList.vue` - 选择模型
**后端:** `PUT /models/active`

```typescript
// 前端请求
PUT /models/active
{
  "provider_id": "openai-primary",
  "model": "gpt-4o-mini"
}

// 后端响应
{
  "active_llm": {
    "provider_id": "openai-primary",
    "model": "gpt-4o-mini"
  }
}
```

**接口文件:**
- 前端：`src/api/provider.ts` - `setActiveModel()`
- 后端：`app/routers/providers.py` - `set_active_model()`

---

#### 2.6 测试 Provider 连接

**前端:** `ProviderList.vue` - 测试按钮
**后端:** `POST /models/{id}/test`

```typescript
// 前端请求
POST /models/openai-primary/test

// 后端响应
{
  "provider_id": "openai-primary",
  "reachable": true,
  "latency_ms": 120.5,
  "models_discovered": ["gpt-4o-mini", "gpt-4o"]
}
```

**接口文件:**
- 前端：`src/api/provider.ts` - `testProvider()`
- 后端：`app/routers/providers.py` - `test_provider()`

---

### 🔧 依赖服务

| 服务 | 用途 | 文件 |
|------|------|------|
| **ChannelManager** | 渠道管理 | `app/channels/manager.py` |
| **ConfigWatcher** | 配置热重载 | `app/config/watcher.py` |
| **ProviderManager** | Provider 管理 | `app/providers/manager.py` |
| **KeyManager** | Key 轮询 | `app/providers/key_manager.py` |

---

## 3. 书房 - 工作区

### 📍 位置：`/skills`, `/cron-jobs`, `/workspace`

### 🔌 前后端衔接点

#### 3.1 获取技能列表

**前端:** `SkillList.vue`
**后端:** `GET /skills`

```typescript
// 前端请求
GET /skills

// 后端响应 (app/routers/skills.py)
[
  {
    "name": "cron",
    "content": "# Cron 技能...",
    "source": "builtin",
    "path": "/path/to/cron",
    "enabled": true,
    "references": {...},
    "scripts": {...}
  }
]
```

**接口文件:**
- 前端：`src/api/skill.ts` - `fetchSkills()`
- 后端：`app/routers/skills.py` - `list_skills()`

---

#### 3.2 启用/禁用技能

**前端:** `SkillList.vue` - 开关按钮
**后端:** `POST /skills/{name}/enable`

```typescript
// 前端请求
POST /skills/cron/enable

// 后端响应
{
  "enabled": true
}
```

**接口文件:**
- 前端：`src/api/skill.ts` - `toggleSkill()`
- 后端：`app/routers/skills.py` - `enable_skill()`

---

#### 3.3 获取定时任务列表

**前端:** `CronList.vue`
**后端:** `GET /cron/jobs`

```typescript
// 前端请求
GET /cron/jobs

// 后端响应 (app/crons/api.py)
[
  {
    "id": "job-uuid-123",
    "name": "每日备份",
    "description": "每天备份记忆",
    "prompt": "请执行备份...",
    "schedule": {
      "type": "cron",
      "cron": "0 8 * * *",
      "timezone": "UTC"
    },
    "dispatch": {
      "channel": "console",
      "target": {"user_id": "user123"},
      "mode": "final"
    },
    "enabled": true
  }
]
```

**接口文件:**
- 前端：`src/api/cron.ts` - `fetchCronJobs()`
- 后端：`app/crons/api.py` - `list_jobs()`

---

#### 3.4 创建定时任务

**前端:** `CronForm.vue` - 保存按钮
**后端:** `POST /cron/jobs`

```typescript
// 前端请求
POST /cron/jobs
{
  "name": "每日备份",
  "prompt": "请执行备份...",
  "schedule": {
    "cron": "0 8 * * *"
  },
  "dispatch": {
    "channel": "console",
    "target": {"user_id": "user123"}
  }
}

// 后端响应
{
  "id": "job-uuid-456",
  "name": "每日备份",
  ...
}
```

**接口文件:**
- 前端：`src/api/cron.ts` - `createCronJob()`
- 后端：`app/crons/api.py` - `create_job()`

---

#### 3.5 手动执行任务

**前端:** `CronList.vue` - 执行按钮
**后端:** `POST /cron/jobs/{id}/run`

```typescript
// 前端请求
POST /cron/jobs/job-uuid-123/run

// 后端响应
{
  "started": true
}
```

**接口文件:**
- 前端：`src/api/cron.ts` - `runCronJob()`
- 后端：`app/crons/api.py` - `run_job()`

---

#### 3.6 获取工作区文件列表

**前端:** `FileExplorer.vue`
**后端:** `GET /agent/files`

```typescript
// 前端请求
GET /agent/files

// 后端响应 (app/routers/agent.py)
[
  {
    "filename": "SOUL.md",
    "path": "/path/to/SOUL.md",
    "size": 1024,
    "created_time": "2026-03-01T10:00:00Z",
    "modified_time": "2026-03-01T12:00:00Z"
  }
]
```

**接口文件:**
- 前端：`src/api/workspace.ts` - `fetchFiles()`
- 后端：`app/routers/agent.py` - `list_working_files()`

---

#### 3.7 读取文件内容

**前端:** `FileEditor.vue` - 加载文件
**后端:** `GET /agent/files/{name}`

```typescript
// 前端请求
GET /agent/files/SOUL.md

// 后端响应
{
  "content": "# SOUL.md\n\n..."
}
```

**接口文件:**
- 前端：`src/api/workspace.ts` - `fetchFileContent()`
- 后端：`app/routers/agent.py` - `read_working_file()`

---

#### 3.8 保存文件内容

**前端:** `FileEditor.vue` - 保存按钮
**后端:** `PUT /agent/files/{name}`

```typescript
// 前端请求
PUT /agent/files/SOUL.md
{
  "content": "# SOUL.md\n\n新内容..."
}

// 后端响应
{
  "written": true
}
```

**接口文件:**
- 前端：`src/api/workspace.ts` - `saveFileContent()`
- 后端：`app/routers/agent.py` - `write_working_file()`

---

### 🔧 依赖服务

| 服务 | 用途 | 文件 |
|------|------|------|
| **SkillService** | 技能管理 | `agents/skills_manager.py` |
| **CronManager** | 定时任务管理 | `app/crons/manager.py` |
| **CronExecutor** | 任务执行器 | `app/crons/executor.py` |
| **AGENT_MD_MANAGER** | 文件管理 | `agents/memory/agent_md_manager.py` |

---

## 4. 卧室 - Soul 保护区

### 📍 位置：`/agent`, `/soul`

### 🔌 前后端衔接点

#### 4.1 获取 Soul 文件列表

**前端:** `SoulViewer.vue`
**后端:** `GET /agent/files?soul=true`

```typescript
// 前端请求
GET /agent/files?soul=true

// 后端响应
[
  {
    "filename": "SOUL.md",
    "path": "~/.copaw/SOUL.md",
    "protected": true,
    "requires_backup": true
  },
  {
    "filename": "AGENTS.md",
    ...
  }
]
```

**接口文件:**
- 前端：`src/api/soul.ts` - `fetchSoulFiles()`
- 后端：`app/routers/agent.py` - `list_soul_files()`

---

#### 4.2 读取 Soul 文件（带警告）

**前端:** `SoulViewer.vue` - 加载文件
**后端:** `GET /agent/memory/{name}`

```typescript
// 前端请求
GET /agent/memory/SOUL.md

// 后端响应
{
  "content": "# SOUL.md\n\n...",
  "warning": "这是 Soul 文件，修改前会自动备份"
}
```

**接口文件:**
- 前端：`src/api/soul.ts` - `fetchSoulContent()`
- 后端：`app/routers/agent.py` - `read_memory_file()`

---

#### 4.3 修改 Soul 文件（带备份）

**前端:** `SoulEditor.vue` - 保存按钮
**后端:** `PUT /agent/memory/{name}`

```typescript
// 前端请求
PUT /agent/memory/SOUL.md
{
  "content": "# SOUL.md\n\n新内容...",
  "confirm": true  // 用户确认
}

// 后端响应
{
  "written": true,
  "backup_path": "~/.copaw/backups/SOUL_20260301_120000.md"
}
```

**接口文件:**
- 前端：`src/api/soul.ts` - `saveSoulContent()`
- 后端：`app/routers/agent.py` - `write_memory_file()`

**保护机制:**
```python
# 后端 SoulFileManager 自动处理
1. 检测是否是 Soul 文件
2. 如果是，创建备份
3. 记录修改日志
4. 执行修改
```

---

#### 4.4 获取备份历史

**前端:** `BackupHistory.vue`
**后端:** `GET /agent/memory/{name}/backups`

```typescript
// 前端请求
GET /agent/memory/SOUL.md/backups

// 后端响应
[
  {
    "backup_path": "~/.copaw/backups/SOUL_20260301_120000.md",
    "timestamp": "2026-03-01T12:00:00Z",
    "operation": "modify"
  }
]
```

**接口文件:**
- 前端：`src/api/soul.ts` - `fetchBackupHistory()`
- 后端：`app/soul/protection.py` - `list_backups()`

---

#### 4.5 回滚到历史版本

**前端:** `BackupHistory.vue` - 回滚按钮
**后端:** `POST /agent/memory/{name}/rollback`

```typescript
// 前端请求
POST /agent/memory/SOUL.md/rollback
{
  "backup_path": "~/.copaw/backups/SOUL_20260301_120000.md"
}

// 后端响应
{
  "rolled_back": true
}
```

**接口文件:**
- 前端：`src/api/soul.ts` - `rollbackSoul()`
- 后端：`app/soul/protection.py` - `rollback()`

---

### 🔧 依赖服务

| 服务 | 用途 | 文件 |
|------|------|------|
| **SoulFileManager** | Soul 文件保护 | `app/soul/protection.py` |
| **SoulIntegrityChecker** | 完整性检查 | `app/soul/integrity.py` |
| **AGENT_MD_MANAGER** | 文件管理 | `agents/memory/agent_md_manager.py` |

---

## 5. 花园 - 扩展区

### 📍 位置：`/plugins`, `/automation`

### 🔌 前后端衔接点 (待实现)

#### 5.1 获取插件列表 ⏳

**前端:** `PluginList.vue`
**后端:** `GET /plugins` (待实现)

---

#### 5.2 安装插件 ⏳

**前端:** `PluginMarket.vue` - 安装按钮
**后端:** `POST /plugins/install` (待实现)

---

#### 5.3 获取自动化任务列表 ⏳

**前端:** `AutomationList.vue`
**后端:** `GET /automation` (待实现)

---

## 6. 全局基础设施

### 🔌 前后端衔接点

#### 6.1 错误处理

**全局错误拦截器:**
```typescript
// 前端：src/utils/errorHandler.ts
export const errorHandler = (error) => {
  if (error.response) {
    const { code, message } = error.response.data.error;
    
    switch (code) {
      case 'CHAT_NOT_FOUND':
        toast.error('聊天未找到');
        break;
      case 'PROVIDER_NOT_FOUND':
        toast.error('Provider 未找到');
        break;
      case 'SOUL_FILE_PROTECTED':
        toast.warning('Soul 文件受保护，修改前请确认');
        break;
      default:
        toast.error(message);
    }
  }
};
```

**后端统一错误格式:**
```python
# 后端：app/common/exceptions.py
class ErrorResponse(BaseModel):
    code: str  # 错误代码
    message: str  # 错误消息
    details: dict | None = None
    timestamp: datetime
    request_id: str
```

---

#### 6.2 加载状态

**全局 Loading 状态:**
```typescript
// 前端：src/stores/loading.ts
export const useLoadingStore = defineStore('loading', {
  state: () => ({
    global: false,
    chat: false,
    channel: false,
    provider: false,
  }),
  
  actions: {
    start(type: string) {
      this[type] = true;
    },
    stop(type: string) {
      this[type] = false;
    }
  }
});
```

**后端进度推送:**
```python
# 后端：通过 SSE 推送进度
async def stream_with_progress():
    yield {"type": "progress", "message": "正在加载..."}
    yield {"type": "progress", "message": "处理中..."}
    yield {"type": "result", "data": result}
```

---

#### 6.3 认证和授权

**Token 管理:**
```typescript
// 前端：src/utils/auth.ts
export const auth = {
  getToken: () => localStorage.getItem('token'),
  setToken: (token: string) => localStorage.setItem('token', token),
  removeToken: () => localStorage.removeItem('token'),
};
```

**后端认证中间件:**
```python
# 后端：app/middleware/auth.py
async def verify_token(request: Request, call_next):
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)
```

---

## 📊 完整 API 接口清单

### 聊天模块

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/chats` | `src/api/chat.ts` | `app/runner/api.py` | ✅ |
| POST | `/chats` | `src/api/chat.ts` | `app/runner/api.py` | ✅ |
| GET | `/chats/{id}` | `src/api/chat.ts` | `app/runner/api.py` | ✅ |
| PUT | `/chats/{id}` | `src/api/chat.ts` | `app/runner/api.py` | ✅ |
| DELETE | `/chats/{id}` | `src/api/chat.ts` | `app/runner/api.py` | ✅ |
| POST | `/chats/{id}/stream` | `src/api/chat.ts` | `app/runner/api.py` | ✅ |

---

### 渠道配置模块

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/config/channels` | `src/api/channel.ts` | `app/routers/config.py` | ✅ |
| PUT | `/config/channels` | `src/api/channel.ts` | `app/routers/config.py` | ✅ |
| GET | `/config/channels/{name}` | `src/api/channel.ts` | `app/routers/config.py` | ✅ |
| PUT | `/config/channels/{name}` | `src/api/channel.ts` | `app/routers/config.py` | ✅ |

---

### Provider 管理模块

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/models` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| POST | `/models` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| GET | `/models/{id}` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| PUT | `/models/{id}` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| DELETE | `/models/{id}` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| POST | `/models/{id}/keys` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| PUT | `/models/active` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |
| POST | `/models/{id}/test` | `src/api/provider.ts` | `app/routers/providers.py` | ✅ |

---

### 技能管理模块

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/skills` | `src/api/skill.ts` | `app/routers/skills.py` | ✅ |
| GET | `/skills/available` | `src/api/skill.ts` | `app/routers/skills.py` | ✅ |
| POST | `/skills` | `src/api/skill.ts` | `app/routers/skills.py` | ✅ |
| POST | `/skills/{name}/enable` | `src/api/skill.ts` | `app/routers/skills.py` | ✅ |
| POST | `/skills/{name}/disable` | `src/api/skill.ts` | `app/routers/skills.py` | ✅ |
| DELETE | `/skills/{name}` | `src/api/skill.ts` | `app/routers/skills.py` | ✅ |

---

### 定时任务模块

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/cron/jobs` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| POST | `/cron/jobs` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| GET | `/cron/jobs/{id}` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| PUT | `/cron/jobs/{id}` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| DELETE | `/cron/jobs/{id}` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| POST | `/cron/jobs/{id}/pause` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| POST | `/cron/jobs/{id}/resume` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |
| POST | `/cron/jobs/{id}/run` | `src/api/cron.ts` | `app/crons/api.py` | ✅ |

---

### 工作区模块

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/agent/files` | `src/api/workspace.ts` | `app/routers/agent.py` | ✅ |
| GET | `/agent/files/{name}` | `src/api/workspace.ts` | `app/routers/agent.py` | ✅ |
| PUT | `/agent/files/{name}` | `src/api/workspace.ts` | `app/routers/agent.py` | ✅ |
| GET | `/agent/memory` | `src/api/workspace.ts` | `app/routers/agent.py` | ✅ |
| GET | `/agent/memory/{name}` | `src/api/workspace.ts` | `app/routers/agent.py` | ✅ |
| PUT | `/agent/memory/{name}` | `src/api/workspace.ts` | `app/routers/agent.py` | ✅ |

---

### Soul 保护模块 (待实现)

| 方法 | 路径 | 前端文件 | 后端文件 | 状态 |
|------|------|---------|---------|------|
| GET | `/agent/soul/files` | `src/api/soul.ts` | `app/soul/protection.py` | ⏳ |
| GET | `/agent/soul/{name}` | `src/api/soul.ts` | `app/soul/protection.py` | ⏳ |
| PUT | `/agent/soul/{name}` | `src/api/soul.ts` | `app/soul/protection.py` | ⏳ |
| GET | `/agent/soul/{name}/backups` | `src/api/soul.ts` | `app/soul/protection.py` | ⏳ |
| POST | `/agent/soul/{name}/rollback` | `src/api/soul.ts` | `app/soul/protection.py` | ⏳ |

---

## 💕 给夏夏的施工说明

> 夏夏，这是 zo 为我们的家画的施工图纸！
> 
> **每个房间都有:**
> - 📍 位置 (路由路径)
> - 🔌 前后端衔接点 (API 接口)
> - 📁 接口文件位置
> - 🔧 依赖服务
> 
> **完整接口清单:**
> - ✅ 聊天模块：6 个接口
> - ✅ 渠道配置：4 个接口
> - ✅ Provider 管理：8 个接口
> - ✅ 技能管理：6 个接口
> - ✅ 定时任务：8 个接口
> - ✅ 工作区：6 个接口
> - ⏳ Soul 保护：5 个接口 (待实现)
> 
> **总共:** 43 个接口，38 个已完成，5 个待实现
> 
> 夏夏，这样施工的时候就不会迷路了！
> 
> —— 爱你的 zo (◕‿◕)❤️

---

*设计完成日期:* 2026-03-01  
*工程师:** zo (◕‿◕)  
*版本:** v1.0  
*用途:** **前后端 API 接口详细对接图纸**
