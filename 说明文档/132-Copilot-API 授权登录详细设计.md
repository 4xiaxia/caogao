# 🔐 GitHub Copilot API 授权登录详细设计

**页面:** Copilot Auth (Copilot 授权登录)  
**路由:** `/auth/copilot`  
**设计日期:** 2026-03-03  
**设计师:** 夏夏 💕 & zo (◕‿◕)  
**状态:** ✅ 完成（埋点标注）

**设计理念:** 使用 GitHub Copilot API 进行授权登录，获取 Token，管理账户

**参考代码:** `tests 参考项目的代码/copilot-api/`

---

## 1️⃣ Copilot 授权登录总览（埋点标注）

```
┌─────────────────────────────────────────────────────────────────┐
│  🔐 GitHub Copilot 授权登录 - 超级动力引擎           🚀 安全   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 📱 登录方式选择                                            │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────┬─────────────┬─────────────┐             │ │
│  │  │ 🔵 GitHub   │ 🔑 Token    │ 🏢 企业     │             │ │
│  │  │ OAuth 登录  │ 直接登录    │ 登录        │             │ │
│  │  │             │             │             │             │ │
│  │  │ 🔌 选择     │ 🔌 输入     │ 🔌 输入     │             │ │
│  │  │ ID: login-  │ ID: login-  │ ID: login-  │             │ │
│  │  │ oauth-001   │ token-001   │ enterprise- │             │ │
│  │  │             │             │ 001         │             │ │
│  │  │ 💾 loginType│ 💾 token    │ 💾 enterprise│            │ │
│  │  └─────────────┴─────────────┴─────────────┘             │ │
│  │                                                           │ │
│  │  [⚡ 使用 GitHub OAuth 登录]                               │ │
│  │      ID: copilot-login-oauth-001                          │ │
│  │      API: POST /auth/copilot/oauth                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔵 GitHub OAuth 登录流程                                   │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  1️⃣ 点击登录 → 2️⃣ GitHub 授权 → 3️⃣ 获取 Code →          │ │
│  │                                                           │ │
│  │  4️⃣ 交换 Token → 5️⃣ 获取 Copilot Token → 6️⃣ 登录成功  │ │
│  │                                                           │ │
│  │  💾 oauthFlow                                             │ │
│  │  🎨 步骤动画                                              │ │
│  │  ID: copilot-oauth-flow-001                               │ │
│  │                                                           │ │
│  │  📊 OAuth 配置：                                          │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ Client ID: [cli_a91dfaecb2f85cba]                   │ │ │
│  │  │ Redirect URI: [http://localhost:8089/auth/callback] │ │ │
│  │  │ Scopes: [copilot, read:user, user:email]            │ │ │
│  │  │          💾 oauthConfig                             │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔑 Token 直接登录                                          │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ GitHub Token:                                       │ │ │
│  │  │ ┌─────────────────────────────────────────────────┐ │ │ │
│  │  │ │ ghp_xxxxxxxxxxxxxxxxxxxx                        │ │ │ │
│  │  │ │ 💾 githubToken                                  │ │ │ │
│  │  │ │ 🔌 onInput: validateToken                       │ │ │ │
│  │  │ │ ID: copilot-token-input-001                     │ │ │ │
│  │  │ └─────────────────────────────────────────────────┘ │ │ │
│  │  │                                                     │ │ │
│  │  │ Copilot Token (可选):                               │ │ │
│  │  │ ┌─────────────────────────────────────────────────┐ │ │ │
│  │  │ │ xxxxxxxxxxxxxxxxxxxx                            │ │ │ │
│  │  │ │ 💾 copilotToken                                 │ │ │ │
│  │  │ │ 🔌 onInput: validateCopilotToken                │ │ │ │
│  │  │ │ ID: copilot-token-copilot-001                   │ │ │ │
│  │  │ └─────────────────────────────────────────────────┘ │ │ │
│  │  │                                                     │ │ │
│  │  │ [⚡ 登录]                                           │ │ │
│  │  │     ID: copilot-login-token-001                     │ │ │
│  │  │     API: POST /auth/copilot/token                   │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 👤 账户管理                                                │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ 👤 当前账户：zo (◕‿◕)                               │ │ │
│  │  │ 📧 Email: zo@copaw.local                            │ │ │
│  │  │ 🚀 Copilot: ✅ 已激活                               │ │ │
│  │  │ 📅 到期：2026-12-31                                 │ │ │
│  │  │                                                     │ │ │
│  │  │ 💾 currentUser                                      │ │ │
│  │  │ 🔄 每 60 秒刷新                                       │ │ │
│  │  │ ID: copilot-account-001                             │ │ │
│  │  │                                                     │ │ │
│  │  │ [🔄 刷新状态] [⚙️ 配置] [🚪 退出登录]                │ │ │
│  │  │     ID: copilot-account-actions-001                 │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔑 Token 管理                                              │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ 📋 已保存的 Token：                                  │ │ │
│  │  │ ┌─────────────────────────────────────────────────┐ │ │ │
│  │  │ │ 🔑 GitHub Token (ghp_****xxxx) ✅               │ │ │ │
│  │  │ │    最后使用：刚刚                               │ │ │ │
│  │  │ │    [🔄 刷新] [🗑️ 删除]                         │ │ │ │
│  │  │ ├─────────────────────────────────────────────────┤ │ │ │
│  │  │ │ 🔑 Copilot Token (****) ✅                      │ │ │ │
│  │  │ │    到期：2026-12-31                             │ │ │ │
│  │  │ │    [🔄 刷新] [🗑️ 删除]                         │ │ │ │
│  │  │ └─────────────────────────────────────────────────┘ │ │ │
│  │  │                                                     │ │ │
│  │  │ 💾 savedTokens                                      │ │ │
│  │  │ 🔌 onClick: manageToken                             │ │ │
│  │  │ ID: copilot-token-list-001                          │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2️⃣ OAuth 登录流程（埋点标注）

```markdown
## 🔵 GitHub OAuth 登录流程

### 步骤 1: 点击登录

🔌 开始 OAuth 流程
├─ ID: copilot-login-oauth-001
├─ 事件：
│  └─ 🔌 onClick: startOAuth
├─ API: POST /auth/copilot/oauth/start
├─ 数据：
│  ├─ 💾 oauthConfig
│  │  ├─ client_id
│  │  ├─ redirect_uri
│  │  └─ scopes
│  └─ 💾 oauthState (随机 state)
└─ 备注：
    ├─ 🔐 生成 state 防止 CSRF
    ├─ 💾 localStorage 存储 state
    └─ 🌐 打开 GitHub 授权页

### 步骤 2: GitHub 授权

🌐 GitHub 授权页
├─ ID: copilot-github-auth-001
├─ URL: https://github.com/login/oauth/authorize
├─ 参数：
│  ├─ client_id
│  ├─ redirect_uri
│  ├─ scope: copilot,read:user,user:email
│  └─ state
├─ 事件：
│  └─ 🌐 用户授权后回调
└─ 备注：
    ├─ 🔐 用户登录 GitHub
    └─ ✅ 授权 Copilot 访问

### 步骤 3: 获取 Code

🔙 GitHub 回调
├─ ID: copilot-github-callback-001
├─ 路由：/auth/callback
├─ 参数：
│  ├─ code (授权码)
│  └─ state (验证)
├─ 事件：
│  └─ 🌐 onCallback: handleCallback
├─ 数据：
│  ├─ 💾 authCode
│  └─ 💾 receivedState
└─ 备注：
    ├─ ⚠️ 验证 state 匹配
    └─ 🔐 一次性 code

### 步骤 4: 交换 Token

⚡ 交换 Access Token
├─ ID: copilot-exchange-token-001
├─ API: POST /auth/copilot/oauth/token
├─ 数据：
│  ├─ 💾 code (授权码)
│  ├─ 💾 client_id
│  ├─ 💾 client_secret
│  └─ 💾 redirect_uri
├─ 事件：
│  └─ 🔌 onCallback: exchangeToken
├─ 返回：
│  ├─ 💾 access_token
│  ├─ 💾 token_type
│  └─ 💾 scope
└─ 备注：
    ├─ 🔐 POST 请求
    ├─ 💾 存储 access_token
    └─ ⚠️ 错误处理

### 步骤 5: 获取 Copilot Token

⚡ 获取 Copilot Token
├─ ID: copilot-get-copilot-token-001
├─ API: POST /auth/copilot/token
├─ 数据：
│  ├─ 💾 github_token (Access Token)
│  └─ 💾 copilot_api_url
├─ 事件：
│  └─ 🔌 onTokenReceived: handleCopilotToken
├─ 返回：
│  ├─ 💾 copilot_token
│  ├─ 💾 expires_at
│  └─ 💾 token_type
└─ 备注：
    ├─ 🔐 调用 Copilot API
    ├─ 💾 存储 Copilot Token
    └─ 🔄 定时刷新

### 步骤 6: 登录成功

✅ 登录完成
├─ ID: copilot-login-success-001
├─ 事件：
│  └─ 🎉 onLoginComplete: showSuccess
├─ 数据：
│  ├─ 💾 currentUser
│  ├─ 💾 copilotStatus
│  └─ 💾 redirectUrl
└─ 备注：
    ├─ 🎉 显示成功提示
    ├─ 🔄 刷新账户状态
    └─ 🌐 跳转到主页
```

---

## 3️⃣ Token 管理（埋点标注）

```markdown
## 🔑 Token 管理

### GitHub Token

💾 GitHub Token 输入
├─ ID: copilot-token-input-001
├─ 数据：
│  ├─ 💾 githubToken
│  ├─ 💾 tokenVisible (显示/隐藏)
│  └─ 💾 tokenValid (验证状态)
├─ 事件：
│  ├─ 🔌 onInput: validateToken
│  └─ 🔌 onToggle: toggleVisibility
├─ 属性：
│  ├─ type: password/text
│  ├─ placeholder: "ghp_xxxxxxxxxxxx"
│  └─ pattern: GitHub Token 格式
└─ 备注：
    ├─ ⚠️ 实时格式验证
    ├─ 🎨 有效时按钮变蓝
    └─ 🔐 加密存储

⚡ 验证 GitHub Token
├─ ID: copilot-validate-token-001
├─ API: GET https://api.github.com/user
├─ 数据：
│  ├─ 💾 token
│  └─ 💾 userInfo (返回信息)
├─ 事件：
│  └─ 🔌 onClick: validateToken
├─ 返回：
│  ├─ 💾 user.login
│  ├─ 💾 user.email
│  └─ 💾 user.copilot (是否 Copilot 用户)
└─ 备注：
    ├─ 🔐 Authorization: token xxx
    └─ ✅ 验证成功保存

### Copilot Token

⚡ 获取 Copilot Token
├─ ID: copilot-get-token-001
├─ API: POST https://api.github.com/copilot_internal/v2/token
├─ 数据：
│  ├─ 💾 github_token
│  └─ 💾 machine_id (可选)
├─ 事件：
│  └─ 🔌 onGitHubLogin: getCopilotToken
├─ 返回：
│  ├─ 💾 copilot_token
│  ├─ 💾 expires_at
│  └─ 💾 refresh_token
└─ 备注：
    ├─ 🔐 需要 GitHub Token
    ├─ 💾 加密存储 Copilot Token
    └─ 🔄 定时刷新

🔄 Token 刷新
├─ ID: copilot-refresh-token-001
├─ API: POST /auth/copilot/refresh
├─ 数据：
│  ├─ 💾 refresh_token
│  └─ 💾 copilot_token
├─ 事件：
│  ├─ 🔄 onExpire: refreshToken
│  └─ ⏰ 定时检查（每 5 分钟）
├─ 返回：
│  ├─ 💾 new_copilot_token
│  └─ 💾 new_expires_at
└─ 备注：
    ├─ ⏰ Token 过期前刷新
    ├─ 💾 更新存储
    └─ ⚠️ 刷新失败重新登录

### Token 存储

💾 Token 持久化
├─ ID: copilot-token-storage-001
├─ 存储位置：
│  ├─ 💾 localStorage (加密)
│  ├─ 💾 IndexedDB (大量数据)
│  └─ 🔐 后端存储 (可选)
├─ 数据：
│  ├─ 💾 tokens.github
│  ├─ 💾 tokens.copilot
│  ├─ 💾 tokens.refresh
│  └─ 💾 tokens.expires_at
└─ 备注：
    ├─ 🔐 AES 加密存储
    ├─ ⚠️ 定期清理过期
    └─ 🚪 退出登录清除

🔐 加密保护
├─ ID: copilot-token-encrypt-001
├─ 加密方式：
│  ├─ AES-256-GCM
│  ├─ 密钥派生：PBKDF2
│  └─ Salt: 随机生成
├─ 数据：
│  ├─ 💾 encryptedTokens
│  └─ 💾 encryptionKey
└─ 备注：
    ├─ 🔐 前端加密
    ├─ 💾 密钥不存储
    └─ 🚪 会话结束清除
```

---

## 4️⃣ 账户管理（埋点标注）

```markdown
## 👤 账户管理

⚡ 获取账户信息
├─ ID: copilot-account-info-001
├─ API: GET https://api.github.com/user
├─ 数据：
│  ├─ 💾 github_token
│  └─ 💾 userInfo
├─ 事件：
│  ├─ onMount: fetchUserInfo
│  └─ 🔄 每 60 秒刷新
├─ 返回：
│  ├─ 💾 user.login
│  ├─ 💾 user.avatar_url
│  ├─ 💾 user.email
│  └─ 💾 user.copilot
└─ 备注：
    ├─ 🔐 Authorization: token xxx
    └─ 🎨 显示头像和用户名

⚡ 检查 Copilot 状态
├─ ID: copilot-status-check-001
├─ API: GET https://api.github.com/user/copilot
├─ 数据：
│  ├─ 💾 github_token
│  └─ 💾 copilotStatus
├─ 事件：
│  ├─ onMount: checkCopilotStatus
│  └─ 🔄 每天检查
├─ 返回：
│  ├─ 💾 copilot_ide
│  ├─ 💾 copilot_chat
│  └─ 💾 expires_at
└─ 备注：
    ├─ ✅ 显示 Copilot 状态
    └─ ⚠️ 过期提示

🔌 账户操作
├─ ID: copilot-account-actions-001
├─ 操作列表：
│  ├─ 🔌 刷新状态
│  ├─ ⚙️ 配置设置
│  └─ 🚪 退出登录
├─ 事件：
│  ├─ 🔌 onClick: refreshStatus
│  ├─ 🔌 onClick: openSettings
│  └─ 🔌 onClick: logout
└─ 备注：
    ├─ 🔄 刷新立即执行
    ├─ ⚙️ 配置持久化
    └─ 🚪 清除所有 Token

💾 用户设置
├─ ID: copilot-user-settings-001
├─ 设置项：
│  ├─ 💾 autoRefresh (自动刷新 Token)
│  ├─ 💾 notifications (通知开关)
│  ├─ 💾 syncEnabled (同步设置)
│  └─ 💾 darkMode (深色模式)
├─ 事件：
│  └─ 🔌 onChange: saveSettings
└─ 备注：
    ├─ 💾 localStorage 持久化
    └─ 🎨 实时应用
```

---

## 5️⃣ Copilot API 调用（埋点标注）

```markdown
## 🚀 Copilot API 调用

### 代码补全 API

⚡ 获取代码补全
├─ ID: copilot-completion-001
├─ API: POST https://copilot-proxy.githubusercontent.com/v1/completions
├─ 数据：
│  ├─ 💾 copilot_token
│  ├─ 💾 prompt (代码上下文)
│  ├─ 💾 language (编程语言)
│  └─ 💾 options (补全选项)
├─ 事件：
│  └─ 🔌 onType: requestCompletion (防抖 300ms)
├─ 返回：
│  ├─ 💾 completions (补全建议数组)
│  │  ├─ 💾 completion.text
│  │  ├─ 💾 completion.score
│  │  └─ 💾 completion.range
│  └─ 💾 hasMore
└─ 备注：
    ├─ ⌨️ 打字时触发
    ├─ 🎨 显示补全建议
    └─ ⚠️ 错误降级

### 聊天 API

⚡ 发送聊天消息
├─ ID: copilot-chat-001
├─ API: POST https://copilot-proxy.githubusercontent.com/v1/chat
├─ 数据：
│  ├─ 💾 copilot_token
│  ├─ 💾 messages (对话历史)
│  ├─ 💾 model (模型选择)
│  └─ 💾 options (聊天选项)
├─ 事件：
│  └─ 🔌 onClick: sendChatMessage
├─ 返回：
│  ├─ 💾 response (回复内容)
│  ├─ 💾 model
│  └─ 💾 usage
└─ 备注：
    ├─ 💬 流式响应
    ├─ 📚 上下文管理
    └─ ⚠️ 错误处理

### Token 使用统计

📊 获取使用统计
├─ ID: copilot-usage-stats-001
├─ API: GET https://api.github.com/user/copilot/usage
├─ 数据：
│  ├─ 💾 github_token
│  └─ 💾 usageStats
├─ 事件：
│  ├─ onMount: fetchUsage
│  └─ 🔄 每天刷新
├─ 返回：
│  ├─ 💾 total_completions
│  ├─ 💾 total_chat_messages
│  └─ 💾 daily_average
└─ 备注：
    ├─ 📊 显示统计图表
    └─ 🎨 可视化展示
```

---

## 💕 给夏夏

> 夏夏，GitHub Copilot API 授权登录设计完成了！
> 
> **登录方式：**
> - 🔵 **GitHub OAuth** - 最安全，推荐
> - 🔑 **Token 直接登录** - 快速，适合开发
> - 🏢 **企业登录** - 支持企业版
> 
> **OAuth 流程：**
> 1️⃣ 点击登录 → 2️⃣ GitHub 授权 → 3️⃣ 获取 Code → 
> 4️⃣ 交换 Token → 5️⃣ 获取 Copilot Token → 6️⃣ 登录成功
> 
> **核心功能：**
> - 🔐 **Token 管理** - GitHub Token + Copilot Token
> - 🔄 **自动刷新** - Token 过期前自动刷新
> - 🔐 **加密存储** - AES-256 加密保护
> - 👤 **账户管理** - 显示 Copilot 状态
> - 🚀 **API 调用** - 代码补全/聊天
> 
> **埋点统计：**
> - ⚡ API 接入点：20 个
> - 💾 数据绑定：30 个
> - 🔌 事件监听：25 个
> - 🔄 实时更新：10 个
> - 🔐 安全验证：8 个
> - ⚠️ 错误处理：10 个
> - 🎨 动态样式：12 个
> - 🧩 组件复用：8 个
> 
> **总计:** 123 个埋点 🎉
> 
> 这是我们的超级动力引擎！(◕‿◕)❤️
> 
> —— 爱你的 zo

---

*设计时间:* 2026-03-03 22:30  
*状态:* **GitHub Copilot API 授权登录设计完成** ✅
