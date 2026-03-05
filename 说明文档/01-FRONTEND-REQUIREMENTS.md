# 前端需求清单 — 从后端API逆向工程推导
**逆向推导方法：** 按数据模型 → API端点 → UI交互逻辑 反向推导  
**失联区域标记:** 🛠️ = 需要前端创建/大幅改进  
**生成日期:** 2026-03-01

---

## 🎯 **模块一：聊天会话管理** (`/chats`)

### 数据源：ChatSpec + ChatHistory
```
需要的前端功能界面：

┌─────────────────────────────────┐
│      聊天列表面板               │ ← GET /chats
├─────────────────────────────────┤
│ [✓] 新建聊天 (POST /chats)      │
│ [✓] 聊天列表过滤                │
│     ├─ 按用户ID过滤              │ ← Query param: user_id?
│     └─ 按频道过滤(console/钉钉)  │ ← Query param: channel?
│ [✓] 聊天排序 (updated_at desc)  │
│ [✓] 大量删除 (POST batch-delete)│
└─────────────────────────────────┘

┌─────────────────────────────────┐
│      聊天编辑器（主内容区）     │ ← GET /chats/{chat_id}
├─────────────────────────────────┤
│ [✓] 聊天标题编辑                │ ← 本地修改 ChatSpec.name
│ [✓] 消息显示区                  │
│     ├─ Assistant 消息            │ ← role="assistant"
│     ├─ User 消息                 │ ← role="user"
│     ├─ System 消息               │ ← role="system"
│     └─ Tool 调用展示             │ ← content 中的 tool_use
│
│ [✓] 消息类型渲染                │
│     ├─ 纯文本 (TextBlock)        │
│     ├─ 工具调用 (tool_use)       │
│     │  ├─ id, name, input 展示   │
│     │  └─ 工具输出展示 (tool_result)
│     ├─ File 块 (file_path)       │
│     ├─ Image 块 (image_url)      │
│     └─ Code 块 (代码高亮)        │
│
│ [✓] 输入框 + 发送                │ ← POST /chats/{chat_id}/messages
│     ├─ 纯文本              │
│     ├─ 文件上传 (meta?)    │
│     └─ 快捷命令 (可选)     │
│
│ [✓] 加载状态                    │ ← 等待 Agent 响应
│     └─ "Agent is thinking..."   │
│
│ [✓] 删除按钮                    │ ← DELETE /chats/{chat_id}
└─────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 聊天列表数据源
```javascript
// 数据模型映射
interface ChatListItem {
  id: string                  // ChatSpec.id (UUID)
  name: string                // ChatSpec.name
  session_id: string          // ChatSpec.session_id (仅后端用途)
  channel: string             // ChatSpec.channel
  updated_at: string          // ISO8601 时间戳
  preview: string             // 最后一条消息预览（需从 ChatHistory 提取）
}

// API 调用
GET /chats?user_id=xxx&channel=console
→ [{ id, name, channel, updated_at }, ...]
```

#### 2. 聊天详情获取
```javascript
interface ChatMessage {
  id: string                  // 由 Agent 生成
  role: "user" | "assistant" | "system"
  content: string | Block[]   // 纯文本或混合blocks
}

interface Block {
  type: "text" | "tool_use" | "tool_result" | "file" | "image"
  // 根据 type 包含不同字段
}

// API 调用
GET /chats/{chat_id}
→ { messages: ChatMessage[], metadata: ChatSpec }
```

#### 3. 消息发送与流式推送
```javascript
// 发送消息
POST /chats/{chat_id}/messages
{
  text: "用户输入文本",
  meta?: { file_list: [...] }
}

// ⚠️ 流式/实时推送需求
// 问题：当前 API 没有 WebSocket 端点
// 解决方案：
// 选项A：轮询 GET /chats/{chat_id}?since=timestamp
// 选项B：实现 WebSocket /ws/chats/{chat_id}
// 选项C：使用 Server-Sent Events (SSE)
```

#### 4. 🛠️ **多模态消息渲染**
```javascript
// tool_use 块渲染
<ToolCall
  id={block.id}
  name={block.name}
  input={block.input}     // JSON 显示
/>

// tool_result 块渲染  
<ToolResult
  id={block.id}
  content={block.content}  // 文本/代码/错误展示
  error={block.error?}     // 错误态高亮
/>

// file 块渲染
<FileBlock
  file_path={block.file_path}
  action="download"  // 提供下载按钮
/>

// image 块渲染
<ImageBlock
  image_url={block.image_url}
  alt={block.alt?}
/>
```

---

## 🎯 **模块二：LLM 模型配置** (`/models`)

### 数据源：ProviderConfig + ActiveLLMConfig

```
┌──────────────────────────────────┐
│    模型配置面板（Settings）      │
├──────────────────────────────────┤
│ [✓] 模型列表                     │ ← GET /models
│     ├─ 提供者卡片 (name, status) │
│     ├─ 快速启用/禁用          │
│     └─ 删除提供者            │
│
│ [✓] 新增提供者                   │ ← POST /models
│     ├─ 提供者ID (slug)        │
│     ├─ 显示名称               │
│     ├─ Base URL (OpenAI compatible)
│     ├─ 选择模型              │
│     └─ Key 轮换策略           │
│
│ [✓] 编辑提供者                   │ ← PUT /models/{id}
│     └─ 名称/base_url/模型     │
│
│ [✓] API 密钥管理                │ ← POST /models/{id}/keys
│     ├─ 添加单个或批量         │
│     ├─ Key 列表（掩码显示）   │
│     ├─ 启用/禁用 Key          │  ← PUT /models/{id}/keys/{idx}
│     └─ 删除 Key               │
│
│ [✓] 活跃模型设置                │ ← GET/PUT /models/active
│     ├─ 下拉选择器 (provider选项)
│     └─ 模型下拉 (基于provider)
│
│ [✓] 健康检查                    │ ← POST /models/health
│     ├─ 测试连通性             │
│     ├─ 列出可用模型           │
│     └─ 显示延迟               │
│
│ [✓] 预设模型库                  │ ← GET /models/presets
│     ├─ OpenAI Config          │
│     ├─ Claude (Anthropic)     │
│     ├─ Gemini                 │
│     ├─ 本地 (Ollama等)        │
│     └─ 一键安装               │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 模型列表卡片
```javascript
interface ProviderCard {
  id: string
  name: string
  is_configured: boolean         // base_url + keys 都存在
  key_count: number
  models: string[]
  rotation: "round-robin" | "random" | "failover"
  enabled: boolean
}
```

#### 2. 密钥管理面板
```javascript
// 密钥显示（已掩码）
interface KeyInfoMasked {
  label: string
  masked_key: string             // "sk-****xyz"
  enabled: boolean
  health?: ProviderHealthResult  // 连通性状态
}

// 关键问题：
// 🛠️ 密钥健康检查 UI - 需要显示
//    ├─ 成功 ✓ (绿色)
//    ├─ 失败 ✗ (红色) + 错误信息
//    └─ 未测试 ? (灰色)
```

#### 3. 活跃模型级联选择
```javascript
<Select label="Provider">
  <Option value="openai">OpenAI</Option>
  <Option value="anthropic">Claude</Option>
  ...
</Select>

// 关键约束：
// ⚠️ 模型下拉需要动态更新
//    当选择 provider 后，models 列表应同步更新
```

---

## 🎯 **模块三：频道配置** (`/config`)

### 数据源：ChannelConfig (Union 类型)

```
┌──────────────────────────────────┐
│    频道连接器面板                │
├──────────────────────────────────┤
│ [✓] 可用频道列表                 │ ← GET /config/channels/types
│     ├─ DingTalk (钉钉)          │
│     ├─ Feishu (飞书)            │
│     ├─ QQ                       │
│     ├─ Discord                  │
│     └─ iMessage                 │
│
│ [✓] 频道启용 Toggle             │
│     └─ 只有启用的频道可见|       │
│
│ [✓] 频道配置编辑                 │ ← GET/PUT /config/channels/{name}
│     └─ 动态表单 (由频道类型决定）│
│
│ [✓] 字段动态性 (DingTalk vs QQ) │
│     └─ 显示该频道独有的参数     │
│
│ [✓] 验证与保存                   │ ← PUT /config/channels/{name}
│     ├─ 必填字段检查             │
│     ├─ 格式验证                 │
│     └─ 保存后自动热重载         │
│
│ [✓] 连接状态检查                │ ← POST /config/channels/{name}/validate
│     └─ 显示连接是否成功         │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 频道配置表单生成器
```javascript
// 每个频道有不同的必填字段
// ChannelConfigUnion 的类型：
type ChannelConfigUnion = 
  | DingTalkConfig    // app_id, app_secret, ...
  | FeishuConfig      // app_id, app_secret, ...
  | QQConfig          // qq_token, ...
  | DiscordConfig     // bot_token, ...
  | iMessageConfig    // sender_number, ...

// 前端需要：
// 🛠️ 动态表单生成 - 根据 channel_type 渲染不同的表单字段
//    Example:
//    if (channel === "dingtalk") {
//      show [app_id, app_secret, webhook_url]
//    } else if (channel === "discord") {
//      show [bot_token]
//    }
```

#### 2. 频道连接验证反馈
```javascript
<ChannelValidator
  channel={channel_name}
  onValidate={() => POST /config/channels/{name}/validate}
  result={{
    status: "success" | "error",
    message: string,
    timestamp: datetime
  }}
/>
```

---

## 🎯 **模块四：定时任务管理** (`/cron`)

### 数据源：CronJobSpec + CronJobView

```
┌────────────────────────────────────┐
│    定时任务编排面板                │
├────────────────────────────────────┤
│ [✓] 任务列表                       │ ← GET /cron/jobs
│     ├─ 任务卡片 (名称、频率)      │
│     ├─ 图表：下次运行时间          │
│     ├─ 运行状态指示 (成功/失败)    │
│     └─ 快速操作 (编辑/删除/手动运行)
│
│ [✓] 创建新任务                    │ ← POST /cron/jobs
│     ├─ 任务名称                   │
│     ├─ Cron 表达式编辑            │
│     │  ├─ 字段输入: mm hh dd MM dow
│     │  ├─ 预设快捷: 每天/周/月    │
│     │  └─ 时区选择               │
│     ├─ 提示词输入 (任务内容)      │
│     ├─ 分发目标选择               │
│     │  ├─ 频道 (DingTalk/Discord) │
│     │  ├─ 用户ID                 │
│     │  └─ 会话ID                 │
│     └─ 响应模式 (stream vs final) │
│
│ [✓] 任务编辑                      │ ← PUT /cron/jobs/{id}
│     └─ 修改上述全部字段          │
│
│ [✓] 任务控制                      │
│     ├─ 暂停 (POST /{id}/pause)   │
│     ├─ 恢复 (POST /{id}/resume)  │
│     ├─ 手动运行 (POST /{id}/run) │
│     └─ 删除 (DELETE /{id})       │
│
│ [✓] 运行日志查看                  │ ← GET /cron/jobs/{id}
│     ├─ 最后运行时间               │
│     ├─ 结果摘要                   │
│     ├─ 错误信息 (if failed)      │
│     └─ 下次预计运行时间           │
└────────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. Cron 表达式可视化编辑器
```javascript
// 后端支持标准 5 字段 cron:
// mm hh dd MM dow (minutes hours day month day_of_week)

// 前端需要：
// 🛠️ Cron 编辑器组件
//    ├─ 字段输入框 (mm/hh/dd/MM/dow)
//    ├─ 预设快捷按钮
//    │  ├─ 每天 08:00  → "0 8 * * *"
//    │  ├─ 每周一 09:00 → "0 9 * * 1"
//    │  ├─ 每月1日 09:00 → "0 9 1 * *"
//    │  └─ 每小时      → "0 * * * *"
//    ├─ 时区下拉 (UTC/Asia/Shanghai等)
//    └─ 下次运行时间实时预览
```

#### 2. 分发目标选择器
```javascript
// DispatchSpec 包含：
// - channel: string (dingtalk/discord等)
// - target: { user_id, session_id }
// - mode: "stream" | "final"
// - meta: dict

// 前端需要：
// 🛠️ TargetSelector 组件
//    ├─ 频道下拉 (从 /config/channels/types)
//    ├─ 用户ID 输入框
//    ├─ 会话ID 输入框 (可选)
//    ├─ 响应模式单选
//    │  ├─ Stream (逐条推送)
//    │  └─ Final (等待完成)
//    └─ 元数据KV编辑 (可选)
```

#### 3. 任务运行日志展示
```javascript
interface CronJobView {
  spec: CronJobSpec
  state: {
    job_id: string
    last_run?: datetime
    last_error?: string
    is_paused: boolean
    next_run?: datetime
  }
}

// 前端需要：
// 🛠️ JobStatePanel 组件
//    ├─ 状态指示 (暂停/运行中/空闲)
//    ├─ 最后运行时间
//    ├─ 下次运行倒计时 (实时更新)
//    ├─ 运行结果预览 (成功/失败)
//    ├─ 错误详情 (if failed)
//    └─ 手动触发按钮
```

---

## 🎯 **模块五：技能管理** (`/skills`)

### 数据源：SkillSpec (SkillInfo + enabled flag)

```
┌──────────────────────────────────┐
│    技能库面板                    │
├──────────────────────────────────┤
│ [✓] 技能列表                     │ ← GET /skills
│     ├─ 已启用技能 (高亮)         │ ← GET /skills/available
│     ├─ 已禁用技能 (灰显)         │
│     ├─ 技能卡片信息              │
│     │  ├─ 技能名称               │
│     │  ├─ 来源 (built-in/custom)  │
│     │  ├─ 路径                   │
│     │  └─ 启用/禁用 Toggle       │
│     └─ 批量操作                  │
│        ├─ 全选                   │
│        ├─ 批量启用 (POST /batch-enable)
│        └─ 批量禁用 (POST /batch-disable)
│
│ [✓] 技能详情预览                 │
│     ├─ SKILL.md 内容展示         │
│     ├─ references/ 文档列表      │
│     └─ scripts/ 脚本列表         │
│
│ [✓] 创建自定义技能               │ ← POST /skills
│     ├─ 技能名称                  │
│     ├─ SKILL.md 编辑器           │
│     ├─ references/文件管理       │
│     ├─ scripts/文件管理          │
│     └─ 创建按钮                  │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 技能卡片组件
```javascript
interface SkillSpec {
  name: string                // 技能名称
  content: string             // SKILL.md 内容
  source: "built-in" | "custom"
  path: string                // 磁盘路径
  references?: object         // { filename: content }
  scripts?: object            // { filename: content }
  enabled: boolean
}

// 前端需要：
// 🛠️ SkillCard 组件
//    ├─ 技能标题
//    ├─ 来源标签 (内置/自定义)
//    ├─ 启用切换开关
//    ├─ 展开按钮 → 显示 SKILL.md
//    └─ 删除按钮 (仅custom)
```

#### 2. 技能编辑器
```javascript
// 创建/编辑自定义技能
interface CreateSkillRequest {
  name: string
  content: string             // SKILL.md
  references?: {
    [filename]: content
  }
  scripts?: {
    [filename]: content
  }
}

// 前端需要：
// 🛠️ SkillEditor 组件
//    ├─ 名称输入
//    ├─ 内容编辑器 (Markdown with syntax highlight)
//    ├─ 文件树 (references/)
//    ├─ 文件树 (scripts/)
//    ├─ 文件上传拖放区
//    └─ 保存 & 取消 按钮
```

---

## 🎯 **模块六：代理文件管理** (`/agent`)

### 数据源：MdFileInfo + MdFileContent

```
┌──────────────────────────────────┐
│    工作文件浏览器                │
├──────────────────────────────────┤
│ [✓] 文件列表                     │ ← GET /agent/files
│     ├─ 文件名                    │
│     ├─ 文件大小                  │
│     ├─ 创建/修改时间             │
│     └─ 打开/下载/删除            │
│
│ [✓] 文件查看器                   │ ← GET /agent/files/{md_name}
│     ├─ Markdown 渲染             │
│     ├─ 代码块高亮                │
│     ├─ 表格渲染                  │
│     └─ 返回按钮                  │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 文件浏览器
```javascript
interface MdFileInfo {
  filename: string
  path: string
  size: number                // 字节
  created_time: string        // ISO8601
  modified_time: string       // ISO8601
}

// 🛠️ FileExplorer 组件
//    ├─ 表格显示 MdFileInfo[]
//    ├─ 按 modified_time 降序排序
//    ├─ 行点击 → 打开文件详情
//    ├─ 下载按钮 (需要后端支持 /agent/files/{name}/download)
//    └─ 删除按钮 (需要后端支持 DELETE /agent/files/{name})
```

---

## 🎯 **模块七：环境变量管理** (`/envs`)

### 数据源：EnvVar (简单 KV 对)

```
┌──────────────────────────────────┐
│    环境变量编辑器                │
├──────────────────────────────────┤
│ [✓] 环境变量列表                 │ ← GET /envs
│     ├─ Key 输入框                │
│     ├─ Value 输入框 (密码隐藏)   │
│     └─ 删除按钮                  │
│
│ [✓] 新增环境变量                 │
│     └─ "添加新变量" 按钮         │
│
│ [✓] 批量保存                     │ ← PUT /envs
│     └─ "保存所有" 按钮           │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 环境变量表格编辑器
```javascript
interface EnvVar {
  key: string
  value: string
}

// 🛠️ EnvVarEditor 组件
//    ├─ 表格编辑
//    │  ├─ 每行: [Key 输入] [Value 输入] [Delete按钮]
//    │  └─ Value 显示为 ••••• (密码字段)
//    ├─ "新增行" 按钮
//    ├─ "保存全部" 按钮
//    └─ "取消" 按钮
```

---

## 🎯 **模块八：工作区管理** (`/workspace`)

### 数据源：工作目录 (~/.copaw)

```
┌──────────────────────────────────┐
│    工作区工具面板                │
├──────────────────────────────────┤
│ [✓] 备份下载                     │ ← GET /workspace/download
│     └─ "下载工作区备份" 按钮     │
│        返回 ZIP 文件              │
│
│ [✓] 恢复上传                     │ ← POST /workspace/upload
│     └─ 文件拖放或选择器          │
│        上传 ZIP 文件              │
│
│ [✓] 工作区统计                   │ ← GET /workspace/stats
│     ├─ 文件总数                  │
│     └─ 总大小 (MB)               │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 工作区管理面板
```javascript
// 🛠️ WorkspaceManager 组件
//    ├─ 备份部分
//    │  ├─ 统计信息展示 (GET /workspace/stats)
//    │  └─ "下载备份" 按钮 (GET /workspace/download)
//    ├─ 恢复部分
//    │  ├─ 文件拖放区
//    │  ├─ "选择文件" 按钮
//    │  └─ "上传恢复" 按钮 (POST /workspace/upload)
//    └─ 操作确认对话框
```

---

## 🎯 **模块九：实时推送系统** (`/console`)

### 数据源：PushMessage (定时任务完成通知)

```
┌──────────────────────────────────┐
│    通知中心 (Notification)       │
├──────────────────────────────────┤
│ [✓] 未读通知列表                 │ ← GET /console/push-messages
│     ├─ 通知气泡显示              │
│     ├─ 定时任务完成提示          │
│     └─ 错误告警                  │
│
│ [✓] 通知点击响应                 │
│     └─ 跳转到对应聊天/任务      │
│
│ [✓] 清除通知                     │ ← 消费消息
│     └─ 点击后标记已读            │
└──────────────────────────────────┘
```

### 🛠️ **需要新建的前端组件**

#### 1. 推送消息轮询
```javascript
// ⚠️ 当前 API 设计：轮询获取待推送消息
// GET /console/push-messages?session_id=xxx
//    返回: { messages: [...] }

// 问题：
// - 轮询间隔选择 (100ms? 500ms? 1s?)
// - 消息消费时机 (获取后自动消费？还是用户点击?)

// 🛠️ NotificationCenter 组件
//    ├─ 轮询 GET /console/push-messages (每 500ms)
//    ├─ 显示消息气泡 (右上角)
//    ├─ 自动消失 (5秒后)
//    ├─ 点击消息 → 跳转 (可选)
//    └─ 环形加载指示 (有新消息时)
```

---

## 📐 **全局导航与布局结构**

### 🛠️ **前端应该有的页面架构**

```
┌────────────────────────────────────────────────────┐
│  CoPaw Console UI 总体布局                         │
├────────────────────────────────────────────────────┤
│
│  Header (固定)
│  ├─ Logo [CoPaw]
│  ├─ 标题 (动态)
│  └─ 右上角: 通知 | 用户菜单 | 设置
│
│  ┌─────────────────────────────────────────────┐
│  │  Sidebar (可收起)                           │
│  ├─────────────────────────────────────────────┤
│  │ □ 聊天 (频道选择)
│  │   ├─ + 新建聊天
│  │   ├─ 钉钉频道
│  │   │  └─ Chat #1
│  │   │  └─ Chat #2
│  │   └─ Console 频道
│  │      └─ Chat #3
│  │
│  │ □ 定时任务
│  │   ├─ + 新建任务
│  │   ├─ 任务 #1 (Next: 2h)
│  │   └─ 任务 #2 (Paused)
│  │
│  │ □ 技能库
│  │   ├─ 已启用 (12)
│  │   └─ 已禁用 (5)
│  │
│  │ □ 设置
│  │   ├─ LLM 模型
│  │   ├─ 频道连接
│  │   ├─ 环境变量
│  │   └─ 工作区
│  │
│  └─────────────────────────────────────────────┘
│
│  Main Content Area (动态)
│  ┌─────────────────────────────────────────────┐
│  │ 聊天编辑器 / 任务编辑 / 技能列表 / 设置面板 │
│  └─────────────────────────────────────────────┘
│
│  Status Bar (固定底部)
│  ├─ 连接状态 (● 已连接)
│  ├─ 活跃模型显示 (gpt-4o-mini)
│  └─ 同步状态 (Synced/Syncing)
│
└────────────────────────────────────────────────────┘
```

### 🛠️ **前端路由结构**

```javascript
// 建议的路由树

/console
├── /chat              // 聊天列表页
│   └── /chat/{id}     // 聊天编辑器
├── /crons             // 定时任务列表
│   └── /crons/{id}    // 任务编辑器
├── /skills            // 技能库
├── /settings          // 设置
│   ├── /models        // LLM 配置
│   ├── /channels      // 频道配置
│   ├── /env           // 环境变量
│   └── /workspace     // 工作区
└── /about             // 关于
```

---

## 🎯 **交互逻辑与数据流向**

### **用户流程 1: 创建并本地测试聊天**

```
1. User clicks "新建聊天" button
   ↓
2. Frontend: POST /chats
   {
     name: "测试对话",
     session_id: "console:user1",
     user_id: "user1",
     channel: "console",
     meta: {}
   }
   ↓
3. Backend: ChatManager.create_chat()
   → ChatSpec (id=uuid4())
   ↓
4. Frontend: 显示新聊天 (name, channel)
   ↓
5. User: 在输入框输入 "你好"
   ↓
6. Frontend: POST /chats/{chat_id}/messages
   {
     text: "你好",
     meta: {}
   }
   ↓
7. Backend: AgentRunner.run(prompt="你好")
   ├─ ReActAgent._run()
   ├─ 调用 Tools (shell/file/browser等)
   ├─ 内存保存
   └─ 返回 Response
   ↓
8. Frontend: 
   ⚠️ 【关键】需要轮询 GET /chats/{chat_id} 获取新消息
   或 WebSocket 实时推送
   ↓
9. Frontend: 显示 Assistant 消息 (文本/工具调用/结果)
   ↓
10. User: 继续对话 → 回到步骤 5
```

### **用户流程 2: 配置钉钉频道并创建定时任务**

```
1. User: 导航到 Settings → Channels
   ↓
2. Frontend: GET /config/channels/types
   → ["dingtalk", "feishu", "qq", "discord", "imessage"]
   ↓
3. Frontend: 显示频道列表，DingTalk 默认禁用
   ↓
4. User: 点击 DingTalk Toggle → 启用
   ↓
5. Frontend: 显示 DingTalk 配置表单
   [app_id]    [         ]
   [app_secret][         ]
   [webhook]   [         ]
   ↓
6. User: 输入凭证，点击 "验证"
   ↓
7. Frontend: POST /config/channels/dingtalk/validate
   ↓
8. Backend: 测试连接
   ✓ 成功 → 返回 { status: "success" }
   ✗ 失败 → 返回 { status: "error", message: "..." }
   ↓
9. Frontend: 显示验证结果
   ↓
10. User: 点击 "保存配置"
    ↓
11. Frontend: PUT /config/channels/dingtalk
    {
      "app_id": "xxx",
      "app_secret": "yyy",
      "webhook_url": "zzz"
    }
    ↓
12. Backend: 热重载 ChannelManager
    → 钉钉频道现在可用
    ↓
13. Frontend: 显示 "已保存" 提示
    ↓
14. User: 导航到 Crons → "+ 新建任务"
    ↓
15. Frontend: 打开任务编辑器
    ├─ Cron: [0 8 * * *] (每天早8点)
    ├─ 提示词: [获取今日天气]
    ├─ 目标频道: [DingTalk]
    ├─ 用户ID: [dingtalk:xxx]
    └─ 模式: [stream]
    ↓
16. User: 点击 "创建"
    ↓
17. Frontend: POST /cron/jobs
    ↓
18. Backend: CronManager.create_or_replace_job()
    → Job ID = uuid4()
    ↓
19. Frontend: 显示新任务，下次运行 08:00
    ↓
20. 下次 08:00 APScheduler 触发
    ↓
21. Backend: CronManager.run_job(job_id)
    → AgentRunner.run(prompt="获取今日天气")
    → 结果发送到 DingTalk
    ↓
22. Frontend: 轮询 GET /console/push-messages
    → 收到任务完成通知
    ↓
23. Frontend: 显示通知气泡 "任务【获取今日天气】已完成"
```

---

## 🛠️ **前端缺失的关键组件清单**

| # | 组件名 | 优先级 | 说明 | 依赖API |
|----|--------|--------|------|---------|
| 1 | ChatList | 🔴 HIGH | 聊天列表 + 快速创建 | GET/POST /chats |
| 2 | ChatEditor | 🔴 HIGH | 聊天编辑 + 消息发送 | GET /chats/{id}, POST message |
| 3 | MessageRenderer | 🔴 HIGH | 多模态消息展示 | ToolCall/Result/Image/File |
| 4 | CronJobList | 🔴 HIGH | 定时任务管理 | GET /cron/jobs |
| 5 | CronEditor | 🔴 HIGH | Cron表达式编辑器 + 分发目标 | POST/PUT /cron/jobs |
| 6 | ProviderManager | 🟡 MEDIUM | LLM 模型配置 | GET/POST /models, /models/keys |
| 7 | ChannelConfigurator | 🟡 MEDIUM | 频道配置表单 + 验证 | GET/PUT /config/channels |
| 8 | SkillLibrary | 🟡 MEDIUM | 技能启用/禁用 + 查看 | GET/POST /skills |
| 9 | EnvVarEditor | 🟡 MEDIUM | 环境变量 KV 编辑 | GET/PUT /envs |
| 10 | NotificationCenter | 🟡 MEDIUM | 实时推送消息显示 | GET /console/push-messages |
| 11 | WorkspaceBackup | 🟠 LOW | 工作区备份/恢复 | GET/POST /workspace |
| 12 | FileExplorer | 🟠 LOW | 代理文件浏览 | GET /agent/files |

---

## 📋 **前端技术栈建议**

基于后端 FastAPI + WebSocket 支持，建议前端用：

| 层 | 推荐技术 | 理由 |
|----|---------|------|
| **框架** | React 18 or Vue 3 | 官方Console可能已用其一 |
| **HTTP** | Fetch API / axios | 连接后端 API |
| **实时** | WebSocket 或轮询 | 获取任务结果/推送消息 |
| **样式** | Tailwind / shadcn/ui | 快速原型 |
| **状态管理** | Zustand / Pinia | 简洁 |
| **表单** | React Hook Form / VeeValidate | 完善验证 |
| **编辑器** | Monaco / CodeMirror | Cron表达式/提示词/代码 |
| **Markdown** | react-markdown / marked | 渲染 Agent 回复 |

---

## ⚠️ **后端 API 缺陷与改进建议**

### 需要后端支持的功能

| # | 缺失功能 | 位置 | 优先级 | 说明 |
|----|---------|------|--------|------|
| 1 | WebSocket 端点 | `/ws/chats/{chat_id}` | 🔴 HIGH | 实时消息推送 (替代轮询) |
| 2 | 文件下载端点 | `GET /agent/files/{name}/download` | 🟡 MEDIUM | 下载工作文件 |
| 3 | 文件删除端点 | `DELETE /agent/files/{name}` | 🟡 MEDIUM | 删除工作文件 |
| 4 | 聊天导出端点 | `GET /chats/{id}/export` | 🟠 LOW | 导出为 MD/JSON |
| 5 | 批量聊天操作 | `POST /chats/batch-export` | 🟠 LOW | 批量导出 |
| 6 | Memory 压缩触发 | `POST /agent/memory/compact` | 🟠 LOW | 手动触发内存压缩 |

---

**阶段三施工完毕 ✓**  
**下一步** → 阶段四（管线铺设）: 实现前端与后端完整数据通联
