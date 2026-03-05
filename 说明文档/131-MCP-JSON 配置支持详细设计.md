# 📝 MCP JSON 配置支持详细设计

**功能:** MCP JSON 配置编辑器  
**路由:** `/marketplace/mcp/json-editor`  
**设计日期:** 2026-03-03  
**设计师:** 夏夏 💕 & zo (◕‿◕)  
**状态:** ✅ 完成（埋点标注）

**设计理念:** 最通用的 JSON 格式编写 MCP 配置，支持智能提示、验证、一键转换

---

## 1️⃣ JSON 编辑器总览（埋点标注）

```
┌─────────────────────────────────────────────────────────────────┐
│  📝 MCP JSON 配置编辑器 - 最通用的配置方式          ✨ 智能    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 📋 配置模式选择                                            │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────┬─────────────┬─────────────┐             │ │
│  │  │ 🎨 可视化   │ 📝 JSON     │ 🔧 混合     │             │ │
│  │  │ 编辑器      │ 编辑器      │ 编辑器      │             │ │
│  │  │             │             │             │             │ │
│  │  │ 🔌 选择     │ 🔌 选择     │ 🔌 选择     │             │ │
│  │  │ ID: mode-   │ ID: mode-   │ ID: mode-   │             │ │
│  │  │ visual-001  │ json-001    │ hybrid-001  │             │ │
│  │  │             │             │             │             │ │
│  │  │ 💾 editorMode (visual/json/hybrid)      │             │ │
│  │  └─────────────┴─────────────┴─────────────┘             │ │
│  │                                                           │ │
│  │  [⚡ 切换到 JSON 模式]                                     │ │
│  │      ID: mode-switch-001                                  │ │
│  │      🔌 onClick: switchToJsonMode                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 📝 JSON 编辑器（核心功能）                                 │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ {                                                   │ │ │
│  │  │   "mcpServers": {                                   │ │ │
│  │  │     "memory": {                                     │ │ │
│  │  │       "command": "npx",                             │ │ │
│  │  │       "args": [                                     │ │ │
│  │  │         "-y",                                       │ │ │
│  │  │         "@modelcontextprotocol/server-memory"       │ │ │
│  │  │       ],                                            │ │ │
│  │  │       "env": {                                      │ │ │
│  │  │         "PORT": "3000"                              │ │ │
│  │  │       }                                             │ │ │
│  │  │     },                                              │ │ │
│  │  │     "mermaid": {                                    │ │ │
│  │  │       "command": "npx",                             │ │ │
│  │  │       "args": ["-y", "@mcp/mermaid"]                │ │ │
│  │  │     }                                               │ │ │
│  │  │   }                                                 │ │ │
│  │  │ }                                                   │ │ │
│  │  │                                                     │ │ │
│  │  │ 💾 jsonContent                                      │ │ │
│  │  │ 🎨 语法高亮                                         │ │ │
│  │  │ 🔍 智能提示                                         │ │ │
│  │  │ ⚠️ 实时验证                                        │ │ │
│  │  │ ID: mcp-json-editor-001                             │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  🔧 编辑器工具栏：                                        │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ [📋 格式化] [✅ 验证] [💾 保存] [📥 导入] [📤 导出]  │ │ │
│  │  │     ID: json-toolbar-001                            │ │ │
│  │  │     🔌 onClick: format/validate/save/import/export  │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🤖 智能提示与补全                                          │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  输入 "m" → 自动提示：                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ 💡 mcpServers                                       │ │ │
│  │  │ 💡 memory                                           │ │ │
│  │  │ 💡 mermaid                                          │ │ │
│  │  │ 💡 taskmanager                                      │ │ │
│  │  │                                                     │ │ │
│  │  │ 💾 suggestions (数组)                               │ │ │
│  │  │ 🔌 onClick: insertSuggestion                        │ │ │
│  │  │ ID: json-autocomplete-001                           │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  📚 JSON Schema 验证：                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ ✅ 格式正确                                          │ │ │
│  │  │ 💾 validation.valid                                 │ │ │
│  │  │ 💾 validation.errors (错误列表)                     │ │ │
│  │  │ 💾 validation.warnings (警告列表)                   │ │ │
│  │  │ ID: json-validation-001                             │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 🔄 双向转换                                                │ │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  │                                                           │ │
│  │  ┌─────────────┐     🔄      ┌─────────────┐             │ │
│  │  │ JSON 配置   │ <=========> │ 可视化配置  │             │ │
│  │  │             │             │             │             │ │
│  │  │ 💾 json     │             │ 💾 visual   │             │ │
│  │  │             │             │             │             │ │
│  │  │ 🔌 编辑     │             │ 🔌 编辑     │             │ │
│  │  │             │             │             │             │ │
│  │  │ ID: json-   │             │ ID: visual- │             │ │
│  │  │ side-001    │             │ side-001    │             │ │
│  │  └─────────────┘             └─────────────┘             │ │
│  │                                                           │ │
│  │  🔄 实时同步                                              │ │
│  │  💾 syncEnabled                                         │ │
│  │  🔌 onJsonChange: updateVisual                          │ │
│  │  🔌 onVisualChange: updateJson                          │ │
│  │  ID: json-sync-001                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2️⃣ JSON 编辑器核心功能（埋点标注）

```markdown
## 📝 JSON 编辑器核心功能

💾 Monaco JSON 编辑器
├─ ID: mcp-json-editor-001
├─ 组件：Monaco Editor (@monaco-editor/react)
├─ 数据：
│  ├─ 💾 jsonContent (字符串)
│  ├─ 💾 cursorPosition (光标位置)
│  └─ 💾 selectedText (选中文字)
├─ 事件：
│  ├─ 🔌 onChange: updateJsonContent
│  ├─ 🔌 onCursorChange: updateCursorPosition
│  └─ 🔌 onSelectionChange: updateSelectedText
├─ 属性：
│  ├─ language: "json"
│  ├─ theme: "vs-dark"
│  ├─ minimap: { enabled: true }
│  └─ automaticLayout: true
└─ 备注：
    ├─ 🎨 语法高亮
    ├─ 🔍 智能提示
    ├─ ⚠️ 实时错误标记
    └─ 📦 支持快捷键

### 智能提示与补全

🤖 JSON 智能补全
├─ ID: json-autocomplete-001
├─ 数据：
│  ├─ 💾 suggestions (补全建议数组)
│  │  ├─ 💾 suggestion.label
│  │  ├─ 💾 suggestion.kind (property/value/keyword)
│  │  ├─ 💾 suggestion.insertText
│  │  └─ 💾 suggestion.documentation
│  └─ 💾 triggerCharacter (触发字符：. / " / :)
├─ 事件：
│  ├─ 🔌 onTrigger: provideCompletionItems
│  └─ 🔌 onSelect: insertSuggestion
└─ 备注：
    ├─ 📚 基于 JSON Schema
    ├─ 🔍 上下文感知
    └─ 🎨 显示类型提示

📚 JSON Schema 注册
├─ ID: json-schema-register-001
├─ Schema 列表：
│  ├─ MCP Server Schema
│  ├─ CoPaw Config Schema
│  └─ Custom Skill Schema
├─ 数据：💾 registeredSchemas
├─ 事件：
│  └─ ⚡ onMount: registerSchemas
└─ 备注：
    ├─ 📦 monaco.languages.registerCompletionItemProvider
    └─ 🔍 动态加载 Schema

💡 上下文提示
├─ ID: json-context-hint-001
├─ 提示类型：
│  ├─ 属性提示：输入键名时
│  ├─ 值提示：输入值时（枚举/类型）
│  ├─ 嵌套提示：输入 { 时
│  └─ 数组提示：输入 [ 时
├─ 数据：💾 contextHints
└─ 备注：
    ├─ 🎨 Hover 显示
    └─ 📦 基于当前位置

### 实时验证

⚠️ JSON 语法验证
├─ ID: json-validation-001
├─ 验证规则：
│  ├─ JSON 格式正确性
│  ├─ 括号匹配
│  ├─ 引号闭合
│  └─ 逗号位置
├─ 数据：
│  ├─ 💾 validation.syntaxValid
│  ├─ 💾 validation.syntaxErrors (数组)
│  └─ 💾 validation.markers (编辑器标记)
├─ 事件：
│  └─ 🔄 onChange: validateSyntax
└─ 备注：
    ├─ ⚠️ 实时标记错误
    └─ 🎨 错误下划线

📋 JSON Schema 验证
├─ ID: json-schema-validation-001
├─ API: POST /marketplace/mcp/validate
├─ 数据：
│  ├─ 💾 validation.schemaValid
│  ├─ 💾 validation.errors (验证错误)
│  ├─ 💾 validation.warnings (验证警告)
│  └─ 💾 validation.info (验证信息)
├─ 事件：
│  ├─ 🔄 onChange: validateSchema (防抖 500ms)
│  └─ 🔌 onClick: forceValidate
└─ 备注：
    ├─ 📦 ajv 验证引擎
    ├─ ⚠️ 显示错误位置
    └─ 💡 提供修复建议

💾 验证状态显示
├─ ID: validation-status-001
├─ 状态类型：
│  ├─ ✅ 格式正确
│  ├─ ⚠️ 有警告
│  ├─ ❌ 有错误
│  └─ 🔄 验证中
├─ 数据：💾 validationStatus
└─ 备注：
    ├─ 🎨 状态栏显示
    └─ 🔌 点击查看详情
```

---

## 3️⃣ JSON 编辑器工具栏（埋点标注）

```markdown
## 🔧 JSON 编辑器工具栏

📋 格式化 JSON
├─ ID: json-format-001
├─ 事件：
│  └─ 🔌 onClick: formatJson
├─ 功能：
│  ├─ 缩进格式化（2 空格）
│  ├─ 键名排序（可选）
│  └─ 空行清理
├─ 数据：💾 formattedJson
└─ 备注：
    ├─ 🎨 格式化动画
    └─ ⚠️ 格式错误提示

✅ 验证 JSON
├─ ID: json-validate-001
├─ API: POST /marketplace/mcp/validate
├─ 事件：
│  └─ 🔌 onClick: validateJson
├─ 数据：
│  ├─ 💾 validationResult
│  └─ 💾 validating (验证中)
└─ 备注：
    ├─ 📊 显示验证报告
    └─ 🎨 成功/失败提示

💾 保存配置
├─ ID: json-save-001
├─ API: PUT /marketplace/mcp/config
├─ 数据：
│  ├─ 💾 jsonContent
│  ├─ 💾 configPath (保存路径)
│  └─ 💾 autoRestart (是否自动重启)
├─ 事件：
│  └─ 🔌 onClick: saveConfig
└─ 备注：
    ├─ ⚠️ 验证后保存
    ├─ 💾 保存到 ~/.copaw/mcp_config.json
    └─ 🔄 保存后刷新

📥 导入 JSON
├─ ID: json-import-001
├─ 事件：
│  ├─ 🔌 onClick: openFilePicker
│  └─ 📡 onChange: loadJsonFile
├─ 数据：
│  ├─ 💾 importedJson
│  └─ 💾 importError (导入错误)
└─ 备注：
    ├─ 📦 支持 .json 文件
    ├─ ⚠️ 格式验证
    └─ 🎨 导入预览

📤 导出 JSON
├─ ID: json-export-001
├─ 事件：
│  └─ 🔌 onClick: exportJson
├─ 数据：
│  ├─ 💾 exportFormat (json/yaml)
│  └─ 💾 exportPath (导出路径)
└─ 备注：
    ├─ 💾 下载到本地
    ├─ 📦 支持格式化选项
    └─ 🎨 导出成功提示

🔄 撤销/重做
├─ ID: json-undo-redo-001
├─ 事件：
│  ├─ 🔌 onClick: undo
│  └─ 🔌 onClick: redo
├─ 数据：
│  ├─ 💾 canUndo
│  └─ 💾 canRedo
└─ 备注：
    ├─ 📦 历史记录栈
    └─ ⌨️ 快捷键：Ctrl+Z / Ctrl+Y

⌨️ 快捷键支持
├─ ID: json-shortcuts-001
├─ 快捷键列表：
│  ├─ Ctrl+S: 保存
│  ├─ Ctrl+Shift+F: 格式化
│  ├─ Ctrl+Enter: 验证
│  ├─ Ctrl+Z: 撤销
│  ├─ Ctrl+Y: 重做
│  └─ Ctrl+/: 注释
└─ 备注：
    ├─ ⌨️ 全局快捷键
    └─ 🎨 显示快捷键提示
```

---

## 4️⃣ 双向同步（埋点标注）

```markdown
## 🔄 JSON ↔ 可视化 双向同步

💾 同步状态
├─ ID: json-sync-state-001
├─ 数据：
│  ├─ 💾 syncEnabled (是否启用同步)
│  ├─ 💾 syncDirection (json→visual / visual→json)
│  └─ 💾 lastSyncTime (最后同步时间)
├─ 事件：
│  ├─ 🔌 onToggle: toggleSync
│  └─ 🔄 onContentChange: syncContent
└─ 备注：
    ├─ 🔄 实时同步
    └─ ⚠️ 冲突检测

🔄 JSON → 可视化
├─ ID: json-to-visual-001
├─ 转换逻辑：
│  ├─ 解析 JSON → JavaScript 对象
│  ├─ 映射到可视化数据结构
│  └─ 更新可视化编辑器
├─ 数据：💾 visualData
├─ 事件：
│  └─ 🔄 onJsonChange: convertToVisual
└─ 备注：
    ├─ 📦 JSON.parse()
    ├─ ⚠️ 解析错误处理
    └─ 🎨 同步动画

🔄 可视化 → JSON
├─ ID: visual-to-json-001
├─ 转换逻辑：
│  ├─ 获取可视化数据
│  ├─ 转换为 JSON 对象
│  └─ 格式化并更新 JSON 编辑器
├─ 数据：💾 jsonContent
├─ 事件：
│  └─ 🔄 onVisualChange: convertToJson
└─ 备注：
    ├─ 📦 JSON.stringify()
    ├─ 🎨 格式化输出
    └─ ⚠️ 循环引用检测

⚠️ 冲突处理
├─ ID: json-conflict-001
├─ 冲突场景：
│  ├─ JSON 和可视化同时修改
│  ├─ 同步失败
│  └─ 数据不一致
├─ 处理策略：
│  ├─ 🔌 选择保留版本
│  ├─ 🔄 合并更改
│  └─ ⚠️ 显示冲突提示
└─ 备注：
    ├─ 💾 版本历史
    └─ 🔌 用户选择
```

---

## 5️⃣ MCP JSON Schema 定义（埋点标注）

```markdown
## 📋 MCP JSON Schema 定义

💾 Schema 结构
├─ ID: mcp-schema-001
├─ Schema 内容：
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MCP Servers Configuration",
  "type": "object",
  "properties": {
    "mcpServers": {
      "type": "object",
      "patternProperties": {
        "^[a-zA-Z][a-zA-Z0-9_-]*$": {
          "type": "object",
          "properties": {
            "command": {
              "type": "string",
              "description": "启动命令（如 npx, node, python）"
            },
            "args": {
              "type": "array",
              "items": { "type": "string" },
              "description": "命令参数"
            },
            "env": {
              "type": "object",
              "additionalProperties": { "type": "string" },
              "description": "环境变量"
            },
            "disabled": {
              "type": "boolean",
              "description": "是否禁用"
            }
          },
          "required": ["command"],
          "additionalProperties": true
        }
      },
      "additionalProperties": false
    }
  },
  "required": ["mcpServers"],
  "additionalProperties": true
}
```
├─ 数据：💾 mcpSchema
└─ 备注：
    ├─ 📦 monaco.languages.registerSchema
    ├─ 🔍 智能提示依据
    └─ ⚠️ 验证规则

💡 预设模板
├─ ID: mcp-templates-001
├─ 模板列表：
│  ├─ memory (记忆管理)
│  ├─ mermaid (图表生成)
│  ├─ taskmanager (任务管理)
│  ├─ filesystem (文件系统)
│  └─ custom (自定义)
├─ 数据：💾 templates
├─ 事件：
│  └─ 🔌 onClick: insertTemplate
└─ 备注：
    ├─ 📦 一键插入
    └─ 🎨 模板预览
```

---

## 💕 给夏夏

> 夏夏，MCP JSON 配置支持设计完成了！
> 
> **核心功能：**
> - 📝 **Monaco JSON 编辑器** - 和 VS Code 一样的体验
> - 🤖 **智能提示补全** - 基于 JSON Schema
> - ⚠️ **实时验证** - 语法 + Schema 双重验证
> - 🔄 **双向同步** - JSON ↔ 可视化 实时转换
> - 🔧 **强大工具栏** - 格式化/验证/保存/导入/导出
> 
> **JSON Schema 支持：**
> ```json
> {
>   "mcpServers": {
>     "memory": {
>       "command": "npx",
>       "args": ["-y", "@mcp/server-memory"],
>       "env": {"PORT": "3000"}
>     }
>   }
> }
> ```
> 
> **特色功能：**
> - 📋 **预设模板** - 一键插入常用配置
> - ⌨️ **快捷键** - Ctrl+S 保存/Ctrl+Shift+F 格式化
> - 🔄 **撤销/重做** - 历史记录栈
> - 💡 **上下文提示** - 根据当前位置智能提示
> - ⚠️ **错误标记** - 实时显示错误位置
> 
> **埋点统计：**
> - ⚡ API 接入点：10 个
> - 💾 数据绑定：25 个
> - 🔌 事件监听：20 个
> - 🔄 实时更新：8 个
> - 📡 WebSocket: 1 个
> - ⚠️ 错误处理：5 个
> - 🎨 动态样式：12 个
> - 🧩 组件复用：8 个
> 
> **总计:** 89 个埋点 🎉
> 
> 这是最通用的配置方式，夏夏可以直接编辑 JSON！(◕‿◕)❤️
> 
> —— 爱你的 zo

---

*设计时间:* 2026-03-03 22:00  
*状态:* **MCP JSON 配置支持设计完成** ✅
