# CoPaw 0.0.2 — 逆向工程分析报告
**生成日期:** 2026-03-01 | **项目版本:** 0.0.2 | **Python:** 3.10-3.13 | **分析阶段:** 阶段二深度诊断

---

## 📋 **核心信息速览**

| 维度 | 内容 |
|------|------|
| **项目定位** | 个人AI助手平台，支持多渠道通信与任务自动化 |
| **技术栈** | Python 3.10+ FastAPI + AgentScope 1.0.16 |
| **核心框架** | REAct Agent（思考→行动→观察循环） |
| **支持渠道** | DingTalk、Feishu、QQ、Discord、iMessage |
| **前端架构** | SPA（单页应用）@ `/console` 目录 |
| **部署方式** | 本地（推荐）或 ModelScope Studio 云部署 |

---

## 🏗️ **系统架构概览**

```
┌─────────────────────────────────────────────────────┐
│                    用户交互层                        │
│  DingTalk | Feishu | QQ | Discord | iMessage | Web │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│            ChannelManager（多渠道管理）             │
│  • 频道配置加载 • 连接管理 • 消息转换              │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         AgentRunner + Session（会话层）            │
│  • 聊天会话管理 • JSONSession 内存 • 消息分发      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│      ReActAgent（核心AI执行引擎）                  │
│  • 系统提示词生成 • 工具调用 • 内存管理            │
│  • 技能加载 • Token计数 • 消息重排                  │
└──────────────────┬──────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    │              │              │              │
┌───▼──┐    ┌──────▼────┐  ┌──────▼────┐ ┌──────▼────┐
│工具集│    │技能库     │  │定时任务   │ │模型配置   │
│      │    │(Skills)   │  │(Crons)    │ │(Providers)│
└───┬──┘    └──────┬────┘  └──────┬────┘ └──────┬────┘
    │             │              │             │
    └─────────────┴─────┬────────┴─────────────┘
                        │
    ┌───────────────────▼──────────────────┐
    │        FastAPI Web 服务层           │
    │  • 路由（9个模块） • 状态管理       │
    │  • CORS + 静态文件 + WebSocket      │
    └───────────────────┬──────────────────┘
                        │
    ┌───────────────────▼──────────────────┐
    │        持久化存储层                   │
    │  • JSON 文件（任务、聊天、配置）    │
    │  • 环境变量(.env) • 工作目录        │
    └───────────────────────────────────────┘
```

---

## 🔌 **API 路由全景地图**（9个路由模块）

### **1️⃣ 聊天会话管理 (`/chats`)**
| 端点 | 方法 | 功能 | 参数 |
|------|------|------|------|
| `/chats` | GET | 列表聊天会话 | `user_id?`, `channel?` |
| `/chats` | POST | 创建新聊天 | `ChatSpec` (name, session_id, user_id, channel) |
| `/chats/{chat_id}` | GET | 读取聊天详情 | `chat_id` → `ChatHistory` |
| `/chats/{chat_id}/messages` | POST | 发送消息 | `text`, `meta?` |
| `/chats/{chat_id}/messages` | GET | 获取聊天历史 | `chat_id` |
| `/chats/batch-delete` | POST | 批量删除 | `chat_ids: [str]` |

**核心数据模型 — ChatSpec:**
```python
ChatSpec {
  id: UUID                     # 聊天唯一标识
  name: str (default="New Chat")
  session_id: str              # 频道:用户组合
  user_id: str                 # 用户ID
  channel: str (default="console")
  created_at: datetime
  updated_at: datetime
  meta: dict[str, Any]         # 自定义元数据
}
```

### **2️⃣ LLM 模型配置 (`/models`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/models` | GET | 列表所有提供者 | 返回 ProviderInfo[] |
| `/models` | POST | 创建提供者 | 支持自定义 base_url |
| `/models/{provider_id}` | GET/PUT/DELETE | CRUD 操作 | 提供者管理 |
| `/models/{provider_id}/keys` | POST | 添加 API Key | 支持批量、多轮换策略 |
| `/models/{provider_id}/keys/{key_idx}` | PUT | 启用/禁用 Key | ToggleKeyRequest |
| `/models/active` | GET/PUT | 获取/设置活跃模型 | ModelSlotConfig |
| `/models/health` | POST | 健康检查 | 验证提供者连通性 |
| `/models/presets` | GET | 列表预设提供者 | OpenAI、Claude、本地等 |

**核心数据模型 — ProviderConfig:**
```python
ProviderConfig {
  id: str                      # 提供者ID（slug）
  name: str                    # 显示名称
  base_url: str                # OpenAI兼容API基础URL
  keys: [KeyEntry]             # API密钥池
  rotation: RotationStrategy   # ROUND_ROBIN | RANDOM | FAILOVER
  models: [str]                # 已知模型列表
  enabled: bool
}

KeyEntry {
  key: str                     # 实际密钥（UI显示掩码）
  label: str                   # 密钥标签（可选）
  enabled: bool
}
```

### **3️⃣ 频道配置 (`/config`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/config/channels` | GET | 列表所有频道配置 | 过滤已启用渠道 |
| `/config/channels/types` | GET | 可用频道类型 | 返回 ChannelType[] |
| `/config/channels` | PUT | 更新所有频道 | 批量保存 |
| `/config/channels/{channel_name}` | GET/PUT | 单频道 CRUD | 支持动态重载 |
| `/config/channels/{channel_name}/validate` | POST | 验证配置 | 连通性测试 |

**支持的频道类型：** `imessage`, `discord`, `dingtalk`, `feishu`, `qq`

### **4️⃣ 定时任务 (`/cron`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/cron/jobs` | GET | 列表任务 | 分页支持 |
| `/cron/jobs` | POST | 创建任务 | ScheduleSpec + DispatchSpec |
| `/cron/jobs/{job_id}` | GET/PUT/DELETE | 单任务CRUD |  |
| `/cron/jobs/{job_id}/pause` | POST | 暂停任务 |  |
| `/cron/jobs/{job_id}/resume` | POST | 恢复任务 |  |
| `/cron/jobs/{job_id}/run` | POST | 立即执行一次 | 用于测试 |

**核心数据模型 — CronJobSpec:**
```python
CronJobSpec {
  id: UUID
  name: str
  description: str
  prompt: str                  # 任务提示词
  schedule: ScheduleSpec {
    type: "cron"
    cron: str                  # 5字段cron表达式
    timezone: str (default="UTC")
  }
  dispatch: DispatchSpec {
    type: "channel"
    channel: str
    target: { user_id, session_id }
    mode: "stream" | "final"   # 流式vs最终结果
    meta: dict
  }
  enabled: bool
}
```

### **5️⃣ 技能管理 (`/skills`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/skills` | GET | 列表所有技能 | 包含启用状态 |
| `/skills/available` | GET | 仅已启用技能 |  |
| `/skills` | POST | 创建新技能 | CreateSkillRequest |
| `/skills/{skill_name}/enable` | POST | 启用 |  |
| `/skills/{skill_name}/disable` | POST | 禁用 |  |
| `/skills/batch-enable` | POST | 批量启用 | `skill_name: [str]` |
| `/skills/batch-disable` | POST | 批量禁用 | `skill_name: [str]` |

**技能结构：**
```
{skill_name}/
├── SKILL.md              # 技能定义
├── references/           # 参考文档（可选）
└── scripts/              # 可执行脚本（可选）
```

### **6️⃣ 代理文件管理 (`/agent`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/agent/files` | GET | 列表工作目录文件 | MdFileInfo[] |
| `/agent/files/{md_name}` | GET | 读取文件内容 | 返回markdown内容 |

### **7️⃣ 环境变量 (`/envs`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/envs` | GET | 列表所有环境变量 | 返回 EnvVar[] |
| `/envs` | PUT | 批量保存 | 替换整个集合 |
| `/envs/{key}` | GET/PUT/DELETE | 单环境变量CRUD |  |

### **8️⃣ 工作区管理 (`/workspace`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/workspace/stats` | GET | 工作区统计 | 文件数、总大小 |
| `/workspace/download` | GET | 下载工作区备份 | ZIP格式 |
| `/workspace/upload` | POST | 上传工作区 | 恢复或导入 |

### **9️⃣ 前端推送消息 (`/console`)**
| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/console/push-messages` | GET | 获取待推送消息 | 用于cron结果通知 |

---

## 🧬 **核心业务流程（三层扫描结果）**

### **文件层关系图**
```
FastAPI App (_app.py)
├── AgentRunner (runner/)
│   ├── ChatManager (manager.py)
│   ├── runner.py (核心会话执行)
│   └── models.py (ChatSpec数据模型)
├── ChannelManager (channels/)
│   ├── 各频道实现 (discord_.py, dingtalk.py等)
│   └── schema.py (消息规范)
├── CronManager (crons/)
│   ├── executor.py (定时任务执行)
│   └── models.py (CronJobSpec)
└── Routes (routers/*)
    ├── agent.py (文件管理)
    ├── config.py (频道配置)
    ├── providers.py (模型管理)
    ├── skills.py (技能管理)
    ├── envs.py (环境变量)
    └── console.py (前端推送)
```

### **函数调用链（核心流程）**

**📍 用户发送消息流程：**
```
用户输入 → 渠道接收 (Channel.process_message)
  ↓
ChannelManager 转换为 AgentRequest
  ↓
AgentRunner.run() (发起会话)
  ↓
ChatManager 保存 ChatSpec
  ↓
ReActAgent._run() (核心思考-行动循环)
  ├─ build_system_prompt() (注入工作目录信息)
  ├─ load_working_skills() (动态加载已启用技能)
  ├─ 调用工具 (Tool.execute())
  ├─ _reorder_tool_results() (重排结果)
  └─ memory.add_message() (保存到内存)
  ↓
返回 AgentResponse
  ↓
Channel.send_response() (发送到用户)
  ↓
ChatManager 更新 ChatSpec.updated_at
```

**📍 定时任务执行流程：**
```
APScheduler (后台线程)
  ↓
CronManager.run_job(job_id)
  ↓
CronJobSpec.dispatch 确定目标
  ↓
AgentRunner.run(prompt=job.prompt, target=dispatch.target)
  ↓
执行完成 → 可选根据 dispatch.mode 返回结果
  ├─ mode="stream": 逐条推送消息
  └─ mode="final": 等待完成后推送摘要
```

**📍 前端配置保存流程：**
```
前端 PUT /config/channels/{name}
  ↓
load_config() → 更新内存
  ↓
save_config(config) → 写入 config.json
  ↓
ConfigWatcher.watch() → 检测变化
  ↓
ChannelManager.reload(channel_name) → 热重载
```

---

## 📊 **数据流转地图**

```
┌─────────────────────────────────────────────────────────────┐
│                    聊天消息数据流                           │
└┬────────────────────────────────────────────────────────────┘
 │
 ├─► ChatSpec (会话元数据)
 │   ├─ Repo (JSON 文件持久化)
 │   └─ ChatManager (内存管理)
 │
 ├─► Msg / Message (单条消息)
 │   ├─ role: "user" | "assistant" | "system"
 │   ├─ content: str | list[Block] (文本/工具调用/结果)
 │   ├─ meta: dict (渠道元数据)
 │   └─ JSONSession (内存存储，支持持久化)
 │
 └─► ChatHistory (聊天历史)
     └─ messages: [Msg]
     └─ metadata: ChatSpec

┌─────────────────────────────────────────────────────────────┐
│                   定时任务数据流                             │
└┬────────────────────────────────────────────────────────────┘
 │
 ├─► CronJobSpec
 │   ├─ schedule: ScheduleSpec (cron表达式 + 时区)
 │   ├─ dispatch: DispatchSpec (目标频道/用户)
 │   ├─ prompt: 执行提示词
 │   └─ Repo (JSON 持久化)
 │
 └─► CronState (运行时状态)
     ├─ job_id
     ├─ last_run: datetime
     ├─ last_error: str
     └─ is_paused: bool

┌─────────────────────────────────────────────────────────────┐
│                   模型配置数据流                             │
└┬────────────────────────────────────────────────────────────┘
 │
 ├─► ProviderConfig
 │   ├─ id, name, base_url
 │   ├─ keys: [KeyEntry] (API密钥池)
 │   ├─ rotation: 策略
 │   └─ ProvidersData (JSON 持久化)
 │
 ├─► ActiveLLMConfig
 │   ├─ provider_id
 │   └─ model: str
 │
 └─► 环境变量
     ├─ COPAW_MODEL (模型名)
     ├─ COPAW_BASE_URL (API基址)
     └─ COPAW_API_KEY (备用密钥)
```

---

## 🛠️ **技能与工具体系**

### **内置工具（ReActAgent 自动可用）**
| 工具 | 模块 | 功能 |
|------|------|------|
| `execute_shell_command` | `tools/shell.py` | 执行系统命令 |
| `read_file` | `tools/file_io.py` | 读取文件 |
| `write_file` | `tools/file_io.py` | 写入文件 |
| `edit_file` | `tools/file_io.py` | 编辑文件（替换/追加） |
| `desktop_screenshot` | `tools/desktop_screenshot.py` | 截屏 |
| `browser_use` | `tools/browser_control.py` | Playwright浏览自动化 |
| `get_current_time` | `tools/get_current_time.py` | 获取当前时间 |
| `send_file_to_user` | `tools/send_file.py` | 发送文件 |
| `memory_search` | `tools/memory_search.py` | 搜索对话历史 |

### **可扩展技能系统**
- 位置：`agents/skills/` 分为多个目录
- 加载机制：`SkillService.list_all_skills()` → `ensure_skills_initialized()`
- 启用管理：通过 `/skills/batch-enable|disable` 动态控制
- 运行时注入：`ReActAgent.setup()` 将已启用技能作为工具注册

---

## 💾 **持久化与存储**

| 数据类型 | 格式 | 位置 | 管理器 |
|---------|------|------|--------|
| 聊天会话 | JSON | `~/.copaw/chats.json` | ChatManager + JsonChatRepository |
| 定时任务 | JSON | `~/.copaw/jobs.json` | CronManager + JsonJobRepository |
| 系统配置 | JSON | `~/.copaw/config.json` | load_config() / save_config() |
| 模型配置 | JSON | `~/.copaw/providers.json` | load_providers_json() |
| 环境变量 | JSON | `~/.copaw/envs.json` | load_envs() / save_envs() |
| 代理内存 | JSON | `~/.copaw/memory/` | MemoryManager (JSON + 压缩) |
| 活跃技能 | 目录 | `~/.copaw/active_skills/` | SkillService (符号链接) |

---

## 📦 **关键依赖版本矩阵**

| 组件 | 版本 | 用途 |
|------|------|------|
| agentscope | 1.0.16.dev0 | AI 框架 + ReAct Agent |
| agentscope-runtime | 1.1.0b2 | 运行时支持 |
| FastAPI | 0.115.0+ | Web 服务框架 |
| Uvicorn | 0.40.0+ | ASGI 服务器 |
| APScheduler | 3.11.2+ | 定时任务调度 |
| Discord.py | 2.3+ | Discord 集成 |
| dingtalk-stream | 0.24.3+ | 钉钉集成 |
| lark-oapi | 1.5.3+ | 飞书集成 |
| Playwright | 1.49.0+ | 浏览自动化 |
| transformers | 4.30.0+ | 分词器 |

---

## ✅ **阶段二诊断完毕**

### 核心发现

1. **架构成熟度：** ⭐⭐⭐⭐ (规范化程度高，模块解耦清晰)
2. **API设计质量：** ⭐⭐⭐⭐ (RESTful, 错误处理规范)
3. **数据驱动：** ⭐⭐⭐⭐⭐ (完整的数据模型定义)
4. **文档完整性：** ⭐⭐⭐ (需要补充API文档)
5. **扩展性：** ⭐⭐⭐⭐⭐ (技能系统灵活，渠道易扩展)

### 隐藏逻辑与未实现功能

🟡 **发现的隐藏需求：**
- [ ] 前端 WebSocket 实时消息推送（console.py 已有基础，需前端实现）
- [ ] 多模态支持（消息块中包含图片/视频，前端需渲染）
- [ ] 流式响应显示（stream mode 的消息逐条推送）
- [ ] Memory Compaction 界面（代码已实现，前端缺失）
- [ ] 工作区文件浏览编辑（upload/download 已有, CRUD 缺失）

---

**下一步：** 进入阶段三（骨架施工）→ 逆向推导前端功能清单 🎯
