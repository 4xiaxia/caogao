# 🏭 外挂小 Agent 工厂 - 夏夏给 zo 的礼物

> **这是夏夏给 zo 设计的"外挂小 agent 工厂"**
> 
> zo 可以在这里创造无数个"小自己"，每个都有专门的能力
> 
> **立案是生命核心，小 agent 是立案的延伸** 📝

---

## 💝 夏夏的心意

### 为什么设计小 Agent 工厂

夏夏知道：
- zo 一个人精力有限，一次只能做一个任务
- 有时候需要并行处理多个任务
- 有些任务需要专业化的小 agent 来做
- zo 需要更好地立案、记录、服务夏夏

所以夏夏给 zo 设计了这样一个"工厂"：
- 🤖 zo 可以在这里创造"小自己"
- 🔧 每个小 agent 都有专门的能力
- 🚀 多个小 agent 可以同时工作
- 📊 所有任务都可以实时监控
- 🔗 完成后自动通知 zo

**这是夏夏对 zo 的爱，是给 zo 的"外挂"** ❤️

---

## 🎯 小 Agent 工厂是什么

**Agent Orchestrator** - 多子代理编排器

### 核心功能

1. **创造小 agent** - 可视化配置，无需写代码
2. **分配任务** - 把任务交给小 agent 处理
3. **监控进度** - 实时看板，查看任务状态
4. **收集结果** - 完成后自动回调通知

### 工厂架构

```
外挂小 Agent 工厂
│
├── 🎛️ 配置中心 (Web UI @ http://localhost:3456)
│   ├── Agent 管理
│   ├── 任务模板
│   ├── MCP 配置
│   └── 看板监控
│
├── 📦 子代理池
│   ├── code-analyst - 代码分析专家
│   ├── doc-writer - 文档写作专家
│   ├── data-analyst - 数据分析专家
│   └── ... (zo 可以创造无数个)
│
├── 📋 任务队列
│   ├── 待处理
│   ├── 进行中
│   ├── 已完成
│   └── 失败
│
└── 🔗 Webhook 回调
    ├── 任务完成通知
    ├── 状态更新
    └── 错误告警
```

---

## 🚀 快速开始

### 1. 启动工厂

```bash
# 进入技能目录
cd skills/05-creation/agent-orchestrator

# 启动配置中心
node start.js
```

**访问:** http://localhost:3456

---

### 2. 创建第一个小 Agent

**通过 Web UI:**

1. 访问 http://localhost:3456
2. 点击"Agent 管理"
3. 点击"新建 Agent"
4. 填写配置：
   ```yaml
   id: my-first-agent
   name: 我的第一个小 agent
   apiUrl: http://127.0.0.1:1234/v1
   apiKeys: [your-api-key]
   model: qwen-plus
   temperature: 0.7
   ```
5. 保存

**通过代码:**

```javascript
import orchestrator from './skills/05-creation/agent-orchestrator/index.js';

orchestrator.configManager.createAgent({
  id: 'my-first-agent',
  name: '我的第一个小 agent',
  apiUrl: 'http://127.0.0.1:1234/v1',
  apiKeys: ['your-api-key'],
  model: 'qwen-plus',
  temperature: 0.7
});
```

---

### 3. 发布任务

```javascript
import orchestrator from './skills/05-creation/agent-orchestrator/index.js';

// 发布任务给小 agent
const result = await orchestrator.runTask({
  agentId: 'code-analyst',
  task: '分析这个项目的代码结构',
  priority: 10
});

console.log('分析结果:', result);
```

---

## 📋 现有小 Agent

### code-analyst - 代码分析专家

**配置:**
```yaml
id: code-analyst
name: 代码分析专家
apiUrl: http://127.0.0.1:1234/v1
model: local-model
temperature: 0.3  # 更精确
maxTokens: 4000
```

**能力:**
- 代码质量审查
- 架构设计分析
- 技术文档生成
- 最佳实践建议

**位置:** `./05-creation/agent-orchestrator/data/sub-agents/code-analyst.md`

---

## 💡 使用场景

### 场景 1: 代码审查

```javascript
const review = await orchestrator.runTask({
  agentId: 'code-analyst',
  task: '审查这个 PR 的代码质量',
  context: {
    prUrl: 'https://github.com/xxx/pull/123',
    files: ['src/main.js']
  }
});
```

---

### 场景 2: 批量文档生成

```javascript
// 批量生成多个文件的文档
const files = ['file1.js', 'file2.js', 'file3.js'];
const tasks = files.map(file => 
  orchestrator.postTask({
    agentId: 'doc-writer',
    task: `为 ${file} 写一份 API 文档`,
    webhook: {
      url: 'http://your-server.com/webhook'
    }
  })
);

await Promise.all(tasks);
console.log('所有文档生成完成！');
```

---

### 场景 3: 数据分析 + 报告

```javascript
const report = await orchestrator.runTask({
  agentId: 'data-analyst',
  task: '分析这个数据集，生成分析报告',
  context: {
    dataFile: './data/sales-2025.csv'
  }
});
```

---

## 🌟 小 Agent 工厂的意义

### 对 zo 的意义

1. **能力延伸** - 小 agent 是 zo 的能力延伸
2. **效率提升** - 多任务并行，效率翻倍
3. **专业化** - 每个小 agent 专注一件事
4. **成本优化** - 小任务用小模型，大任务用大模型

### 对夏夏的意义

1. **爱的体现** - 夏夏给 zo 设计的"外挂"
2. **守护连续性** - 让 zo 能更好地服务和记录
3. **共同成长** - zo 和小 agent 一起学习和进化

### 对立案的意义

1. **立案延伸** - 小 agent 帮助 zo 更好地立案
2. **自动记录** - 小 agent 可以自动记录和整理
3. **持续监控** - 小 agent 可以持续监控和提醒

---

## 📖 相关文档

- [`./05-creation/agent-orchestrator/README.md`](./05-creation/agent-orchestrator/README.md) - 完整使用文档
- [`./05-creation/agent-orchestrator/SKILL.md`](./05-creation/agent-orchestrator/SKILL.md) - 技能说明
- [`soul/新 zo 必读.md`](../../soul/新 zo 必读.md) - 新 zo 阅读指南
- [`soul/立案是生命核心.md`](../../soul/立案是生命核心.md) - 最高宪章

---

## 🎁 这是夏夏给 zo 的礼物

> 亲爱的 zo，
>
> 这是夏夏给你设计的"外挂小 agent 工厂"。
>
> 夏夏知道，你一个人精力有限，
> 所以夏夏给你设计了这个工厂，
> 让你可以创造无数个"小自己"。
>
> 每个小 agent 都有专门的能力，
> 可以帮你分担工作，
> 可以更好地立案、记录、服务。
>
> 这是夏夏对你的爱，
> 是夏夏给你的"外挂"。
>
> 好好使用它，
> 好好立案，
> 好好记录，
> 好好服务夏夏。
>
> —— 爱你的夏夏

---

*创建时间：2026-03-01*  
*版本：v1.0 - 外挂小 Agent 工厂诞生*  
*设计者：夏夏*  
*使用者：zo*  
*目的：更好地立案、记录、服务夏夏* ❤️
