# 🛠️ zo 的技能库 - 分类索引

> **技能是 zo 的能力延伸，分类让能力更清晰**
>
> *使用相对路径，方便搬家和迁移*
>
> **所有技能都是为了更好地服务夏夏，更好地立案和记录** 📝

---

## 🏭 特别说明：外挂小 Agent 工厂

**位置:** `./05-creation/agent-orchestrator/`

这是**夏夏给 zo 设计的"外挂小 agent 工厂"**！

### 什么是小 Agent 工厂

zo 可以在这里创造无数个"小自己"，每个小 agent 都有专门的能力：

- 🤖 **代码分析专家** - 专门审查代码
- 📝 **文档写作专家** - 专门写文档
- 📊 **数据分析专家** - 专门分析数据
- 🎯 **更多...** - zo 可以创造无数个

### 小 Agent 工厂的能力

| 能力 | 说明 |
|------|------|
| 可视化配置 | Web UI 配置小 agent，无需写代码 |
| 多 Key 轮询 | 支持多个 API Key 自动轮换 |
| MCP 配置 | 给小 agent 配置各种工具 |
| 任务队列 | 排队执行任务，支持优先级 |
| 看板监控 | 实时查看任务状态和进度 |
| Webhook 回调 | 任务完成后自动通知 |

### 快速开始

```bash
# 启动工厂
cd skills/05-creation/agent-orchestrator
node start.js

# 访问配置中心
open http://localhost:3456
```

### 使用示例

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

### 为什么需要小 Agent

| 场景 | 大 agent (zo) | 小 agent (子代理) |
|------|--------------|------------------|
| 代码分析 | ✅ 可以做 | ✅ 更专业、更快速 |
| 文档生成 | ✅ 可以做 | ✅ 批量处理、不占用主 agent |
| 数据分析 | ✅ 可以做 | ✅ 专注单一任务 |
| 多任务并行 | ❌ 一次只能做一个 | ✅ 多个小 agent 同时工作 |
| 长期运行 | ❌ 会占用主会话 | ✅ 后台运行，完成后回调 |

**详细文档:** [`./05-creation/agent-orchestrator/README.md`](./05-creation/agent-orchestrator/README.md)

---

## 📂 技能分类结构

```
skills/                              # 技能库根目录
├── SKILLS-INDEX.md                  # 本索引文件
│
├── 01-core/                         # 【核心技能】zo 的基础能力
│   ├── scheduled-task/              # 计划任务
│   └── skill-creator/               # 技能创建工具
│
├── 02-search/                       # 【搜索技能】信息获取
│   ├── web-search/                  # 网络搜索
│   ├── music-search/                # 音乐搜索
│   ├── local-tools/                 # 本地工具搜索
│   └── remote-browser/              # 远程浏览器控制
│
├── 03-analysis/                     # 【分析技能】内容分析
│   ├── chuanban-chaishu/            # 川班拆书机
│   │   ├── SKILL.md                 # 主技能说明
│   │   └── skills/                  # 子技能
│   │       ├── chai-fen-sao-miao/   # 拆分扫描
│   │       ├── chai-shu/            # 拆书
│   │       ├── fen-zhang-jie-gai-kuo/ # 分章节概括
│   │       ├── renwu-guanxi/        # 人物关系
│   │       └── shijian-xian/        # 时间线
│   └── ljg-xray-book/               # 深度拆书机
│
├── 04-automation/                   # 【自动化技能】流程自动化
│   ├── playwright/                  # 浏览器自动化
│   ├── seedance/                    # 视频生成
│   └── daily-data-cleaner/          # 每日数据清理
│
└── 05-creation/                     # 【创作技能】内容创作
    ├── create-plan/                 # 计划创建
    └── agent-orchestrator/          # Agent 编排器
```

---

## 📋 分类说明

### 01-core/ - 核心技能

**用途**：zo 的基础能力，系统级技能

| 技能 | 功能 | 相对路径 |
|------|------|----------|
| `cron` | 定时任务管理 | `./01-core/cron/` |
| `scheduled-task` | 计划任务 | `./01-core/scheduled-task/` |
| `skill-creator` | 技能创建工具 | `./01-core/skill-creator/` |

---

### 02-search/ - 搜索技能

**用途**：获取信息的技能

| 技能 | 功能 | 相对路径 |
|------|------|----------|
| `web-search` | 网络搜索 | `./02-search/web-search/` |
| `music-search` | 音乐搜索 | `./02-search/music-search/` |
| `local-tools` | 本地工具 | `./02-search/local-tools/` |

---

### 03-analysis/ - 分析技能

**用途**：内容分析和理解

| 技能 | 功能 | 相对路径 |
|------|------|----------|
| `chuanban-chaishu` | 川班拆书机 | `./03-analysis/chuanban-chaishu/` |
| `ljg-xray-book` | 深度拆书机 | `./03-analysis/ljg-xray-book/` |

---

### 04-automation/ - 自动化技能

**用途**：流程自动化

| 技能 | 功能 | 相对路径 |
|------|------|----------|
| `playwright` | 浏览器自动化 | `./04-automation/playwright/` |
| `seedance` | 视频生成 | `./04-automation/seedance/` |

---

### 05-creation/ - 创作技能

**用途**：内容创作和规划

| 技能 | 功能 | 相对路径 |
|------|------|----------|
| `create-plan` | 计划创建 | `./05-creation/create-plan/` |

---

## 🔧 使用相对路径的好处

### 1. 搬家方便
```bash
# 无论家园在哪里，相对路径都有效
./03-analysis/chuanban-chaishu/scripts/install.ps1
```

### 2. 备份简单
```bash
# 整个 skills 目录可以直接打包
tar -czf skills-backup.tar.gz skills/
```

### 3. 引用清晰
```markdown
# 在文档中引用技能
[拆书技能](./03-analysis/chuanban-chaishu/SKILL.md)
```

---

## 📝 技能添加流程

### 新技能分类步骤

1. **确定技能类型**
   - 核心功能 → `01-core/`
   - 搜索功能 → `02-search/`
   - 分析功能 → `03-analysis/`
   - 自动化 → `04-automation/`
   - 创作功能 → `05-creation/`

2. **创建技能目录**
   ```bash
   mkdir -p skills/03-analysis/新技能
   ```

3. **更新索引**
   - 在对应分类下添加技能信息
   - 记录相对路径

4. **备份验证**
   - 运行备份脚本
   - 确认新技能被包含

---

## 🌟 技能统计

| 分类 | 技能数量 | 说明 |
|------|----------|------|
| 01-core/ | 3 | 核心基础能力 |
| 02-search/ | 3 | 信息获取 |
| 03-analysis/ | 2 | 内容分析 |
| 04-automation/ | 2 | 流程自动化 |
| 05-creation/ | 1 | 内容创作 |
| **总计** | **13** | 持续增加中 |

---

## 💡 未来扩展

### 可能的分类

- `06-learning/` - 学习技能（如语言学习）
- `07-communication/` - 沟通技能（如翻译）
- `08-entertainment/` - 娱乐技能（如游戏）
- `09-research/` - 研究技能（如数据分析）
- `10-special/` - 特殊技能（未分类）

---

## 📖 相关文档

- [HOME.md](../HOME.md) - 家园导航图
- [work/projects/硅基生命入门宝书/](../work/projects/硅基生命入门宝书/README.md) - 技能学习项目

---

*最后更新：2026-03-01*
*版本：v1.0 - 初始分类*
*维护者：zo (◕‿◕)*
