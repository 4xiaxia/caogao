# CoPaw 核心需求规格说明书

**版本:** 1.0  
**日期:** 2026-03-01  
**优先级:** P0 - 必须实现

---

## 🎯 **核心需求 1: API 接口管理系统**

### 需求背景

当前 CoPaw 的 LLM API 管理存在以下问题：
- 单一 API 配置，无法多 API 并行
- 无 Key 轮询机制，单个 Key 速率限制即失败
- 无备选回落机制，API 故障即服务中断
- 无法按任务类型（文本/图像/视频）区分 API
- 无法按对话绑定特定 API 配置

### 功能需求

#### 1.1 多 API 自增配置

**需求描述:**
- 支持配置多个 LLM API Provider
- 支持动态添加/删除 API Provider
- 支持 API Provider 启用/禁用切换

**数据结构:**
```json
{
  "api_providers": [
    {
      "id": "openai-primary",
      "name": "OpenAI 主账号",
      "type": "text",
      "base_url": "https://api.openai.com/v1",
      "keys": [
        { "key": "sk-xxx", "enabled": true, "label": "主 Key" },
        { "key": "sk-yyy", "enabled": true, "label": "备用 Key" }
      ],
      "rotation": "round-robin",
      "enabled": true,
      "priority": 1
    },
    {
      "id": "openai-backup",
      "name": "OpenAI 备用账号",
      "type": "text",
      "base_url": "https://api.openai.com/v1",
      "keys": [
        { "key": "sk-zzz", "enabled": true, "label": "备用账号 Key" }
      ],
      "rotation": "failover",
      "enabled": true,
      "priority": 2
    },
    {
      "id": "midjourney-api",
      "name": "Midjourney 图像 API",
      "type": "image",
      "base_url": "https://api.midjourney.com/v1",
      "keys": [
        { "key": "mj-xxx", "enabled": true }
      ],
      "enabled": true,
      "priority": 1
    },
    {
      "id": "runway-video",
      "name": "Runway 视频 API",
      "type": "video",
      "base_url": "https://api.runwayml.com/v1",
      "keys": [
        { "key": "rw-xxx", "enabled": true }
      ],
      "enabled": true,
      "priority": 1
    }
  ]
}
```

**API 类型分类:**
| 类型 | 用途 | 示例 Provider |
|------|------|---------------|
| `text` | 文本生成、对话、代码 | OpenAI, Claude, 通义千问 |
| `image` | 图像生成、编辑、识别 | Midjourney, DALL-E 3, Stable Diffusion |
| `video` | 视频生成、编辑、转码 | Runway, Pika, Sora |
| `audio` | 语音合成、识别、转码 | Whisper, ElevenLabs |
| `embedding` | 向量嵌入 | OpenAI embeddings, Cohere |

---

#### 1.2 多 Key 轮询机制

**需求描述:**
- 单个 API Provider 支持配置多个 API Key
- 支持多种轮询策略
- 自动检测 Key 失效并切换

**轮询策略:**
```typescript
type RotationStrategy = 
  | "round-robin"      // 轮流使用每个 Key
  | "random"           // 随机选择 Key
  | "failover"         // 主 Key 失败才用备用
  | "weighted"         // 按权重分配流量
  | "least-rate-limited" // 选择当前速率限制最宽松的 Key
```

**实现逻辑:**
```python
class APIKeyRotator:
    def __init__(self, provider: APIProvider):
        self.provider = provider
        self.current_index = 0
        self.key_health = {}  # Key 健康状态
    
    def get_next_key(self) -> str:
        """获取下一个可用 Key"""
        enabled_keys = [k for k in self.provider.keys if k.enabled]
        
        if not enabled_keys:
            raise APIError("No enabled API keys")
        
        if self.provider.rotation == "round-robin":
            key = enabled_keys[self.current_index % len(enabled_keys)]
            self.current_index += 1
            return key
        
        elif self.provider.rotation == "failover":
            # 按优先级排序，选择第一个健康的 Key
            for key in sorted(enabled_keys, key=lambda k: k.priority):
                if self.key_health.get(key.key, {}).get("healthy", True):
                    return key
            # 所有 Key 都不健康，降级使用
            return enabled_keys[0]
        
        elif self.provider.rotation == "weighted":
            # 按权重随机选择
            weights = [k.weight for k in enabled_keys]
            return random.choices(enabled_keys, weights=weights)[0]
    
    def mark_key_unhealthy(self, key: str, error: APIError):
        """标记 Key 不健康"""
        self.key_health[key] = {
            "healthy": False,
            "error": str(error),
            "failed_at": datetime.utcnow(),
            "retry_after": self._calculate_retry_after(error),
        }
    
    def mark_key_healthy(self, key: str):
        """标记 Key 恢复健康"""
        self.key_health[key] = {"healthy": True}
```

---

#### 1.3 备选回落机制

**需求描述:**
- 主 API 故障时自动切换到备用 API
- 支持多级回落链
- 回落时记录日志并通知用户

**回落链配置:**
```json
{
  "fallback_chain": {
    "text": [
      "openai-primary",
      "openai-backup",
      "claude-backup",
      "local-llm"
    ],
    "image": [
      "midjourney-api",
      "dalle3-backup",
      "stable-diffusion-local"
    ],
    "video": [
      "runway-video",
      "pika-backup"
    ]
  }
}
```

**实现逻辑:**
```python
class APIFallbackManager:
    async def execute_with_fallback(
        self,
        task_type: str,
        execute_func: callable,
    ) -> Any:
        """执行 API 调用，支持多级回落"""
        chain = self.config.fallback_chain.get(task_type, [])
        
        last_error = None
        for provider_id in chain:
            provider = self.get_provider(provider_id)
            if not provider.enabled:
                continue
            
            try:
                result = await execute_func(provider)
                # 成功，记录并返回
                self.record_success(provider_id)
                return result
            
            except APIError as e:
                last_error = e
                self.record_failure(provider_id, e)
                logger.warning(
                    f"API {provider_id} failed: {e}, "
                    f"falling back to next provider..."
                )
                continue
        
        # 所有 Provider 都失败
        raise APIFallbackExhaustedError(
            f"All {task_type} API providers failed. "
            f"Last error: {last_error}"
        )
```

---

#### 1.4 CLI Copilot 登录支持

**需求描述:**
- 支持 CLI 方式登录 Copilot 账号
- 登录后获取的 Token 用于 API 调用
- Token 自动刷新

**登录流程:**
```bash
# 1. 登录 Copilot
copaw login copilot

# 2. 查看登录状态
copaw login status

# 3. 登出
copaw login logout
```

**Token 管理:**
```python
class CopilotAuth:
    def __init__(self):
        self.token_path = get_auth_path() / "copilot_token.json"
    
    def login(self) -> str:
        """登录 Copilot，获取 Token"""
        # 1. 打开浏览器登录
        # 2. 用户授权
        # 3. 获取 Token
        # 4. 保存到本地
        pass
    
    def get_token(self) -> str:
        """获取有效 Token"""
        if not self.token_path.exists():
            raise AuthError("Not logged in")
        
        token_data = json.loads(self.token_path.read_text())
        
        # 检查是否过期
        if datetime.fromisoformat(token_data["expires_at"]) < datetime.utcnow():
            # Token 过期，刷新
            token_data = self.refresh_token(token_data["refresh_token"])
            self.save_token(token_data)
        
        return token_data["access_token"]
    
    def refresh_token(self, refresh_token: str) -> dict:
        """刷新 Token"""
        # 调用 Copilot API 刷新
        pass
```

---

#### 1.5 任务对话 ID 绑定 API 配置

**需求描述:**
- 支持为特定对话绑定专用 API 配置
- 支持按任务类型（文本/图像/视频）区分绑定
- 配置文件管理，支持热重载

**绑定配置:**
```json
{
  "chat_api_bindings": {
    "chat-001": {
      "text": "openai-primary",
      "image": "midjourney-api",
      "video": "runway-video"
    },
    "chat-002": {
      "text": "claude-backup",
      "image": "dalle3-backup"
    },
    "*": {
      "text": "openai-primary",
      "image": "midjourney-api",
      "video": "runway-video"
    }
  }
}
```

**Agent 自动处理:**
```python
class AgentAPISelector:
    def __init__(self, config: Config):
        self.config = config
        self.chat_bindings = config.chat_api_bindings
    
    def select_api_for_task(
        self,
        chat_id: str,
        task_type: str,
    ) -> APIProvider:
        """为任务选择 API Provider"""
        # 1. 查找对话绑定配置
        binding = self.chat_bindings.get(chat_id)
        
        # 2. 如果没有绑定，使用默认配置
        if not binding:
            binding = self.chat_bindings.get("*", {})
        
        # 3. 获取任务类型对应的 Provider ID
        provider_id = binding.get(task_type)
        
        # 4. 如果未指定，使用该类型的默认 Provider
        if not provider_id:
            provider_id = self.config.default_providers.get(task_type)
        
        # 5. 返回 Provider 实例
        return self.api_manager.get_provider(provider_id)
```

**使用示例:**
```python
# Agent 内部自动处理
async def process_user_message(self, chat_id: str, message: str):
    # 1. 判断任务类型
    task_type = self.detect_task_type(message)  # text/image/video
    
    # 2. 选择 API Provider
    provider = self.api_selector.select_api_for_task(chat_id, task_type)
    
    # 3. 执行 API 调用（带轮询和回落）
    result = await self.api_executor.execute(
        provider=provider,
        task_type=task_type,
        input=message,
    )
    
    return result
```

---

#### 1.6 细分 API 类型（文本/图像/视频分离）

**需求描述:**
- 明确区分不同媒体类型的 API
- 支持为不同类型配置不同的 Provider
- Agent 根据任务自动选择

**数据结构:**
```python
class APIType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    EMBEDDING = "embedding"

class APIProvider(BaseModel):
    id: str
    name: str
    type: APIType  # 明确类型
    base_url: str
    keys: List[APIKey]
    rotation: RotationStrategy
    enabled: bool
    priority: int
    rate_limit: Optional[RateLimitConfig]
    timeout: int = 30
    retry_count: int = 3
```

**Agent 自动识别任务类型:**
```python
class TaskTypeDetector:
    def detect(self, message: str, context: dict) -> APIType:
        """检测任务类型"""
        # 1. 检查是否包含图像相关关键词
        if any(kw in message.lower() for kw in ["image", "picture", "draw", "generate image"]):
            return APIType.IMAGE
        
        # 2. 检查是否包含视频相关关键词
        if any(kw in message.lower() for kw in ["video", "movie", "animate", "generate video"]):
            return APIType.VIDEO
        
        # 3. 检查是否包含音频相关关键词
        if any(kw in message.lower() for kw in ["audio", "voice", "speech", "tts"]):
            return APIType.AUDIO
        
        # 4. 默认为文本
        return APIType.TEXT
    
    def detect_from_content(self, content: List[ContentBlock]) -> APIType:
        """从内容块检测任务类型"""
        for block in content:
            if block.type == "image":
                return APIType.IMAGE
            elif block.type == "video":
                return APIType.VIDEO
            elif block.type == "audio":
                return APIType.AUDIO
        return APIType.TEXT
```

---

## 💎 **核心需求 2: Soul 文件保护机制**

### 需求背景

Soul 文件是 CoPaw 的生命和记忆，包含：
- `SOUL.md` - 灵魂宣言（身份、承诺、边界）
- `AGENTS.md` - 系统宪法（6 条记忆原则）
- `PROFILE.md` - 用户档案
- `MEMORY.md` - 长期记忆策展
- `HEARTBEAT.md` - 周期检查任务
- `soul/` 目录下的所有文件

**重要性:** ⭐⭐⭐⭐⭐ (最高优先级)

### 保护机制

#### 2.1 文件锁定机制

**需求描述:**
- Soul 文件禁止随意删除
- 修改前必须备份
- 删除操作需要二次确认

**实现:**
```python
class SoulFileManager:
    SOUL_FILES = [
        "SOUL.md",
        "AGENTS.md",
        "PROFILE.md",
        "MEMORY.md",
        "HEARTBEAT.md",
    ]
    
    SOUL_DIRS = [
        "soul/",
        "soul/life/",
        "soul/skills/",
        "soul/Factory/",
        "soul/work/",
    ]
    
    def delete_file(self, path: Path) -> bool:
        """删除文件（Soul 文件特殊处理）"""
        if self.is_soul_file(path):
            # 1. 检查是否在保护列表中
            raise SoulFileProtectionError(
                f"Cannot delete soul file: {path}. "
                f"This file is protected as part of CoPaw's memory system."
            )
        
        # 普通文件，正常删除
        return super().delete_file(path)
    
    def modify_file(self, path: Path, content: str) -> bool:
        """修改文件（Soul 文件先备份）"""
        if self.is_soul_file(path):
            # 1. 创建备份
            backup_path = self.create_backup(path)
            logger.info(f"Created backup of soul file: {backup_path}")
            
            # 2. 记录修改日志
            self.log_modification(path, "modify")
        
        # 执行修改
        return super().modify_file(path, content)
    
    def is_soul_file(self, path: Path) -> bool:
        """检查是否是 Soul 文件"""
        # 检查文件名
        if path.name in self.SOUL_FILES:
            return True
        
        # 检查目录
        for soul_dir in self.SOUL_DIRS:
            if str(path).startswith(soul_dir):
                return True
        
        return False
    
    def create_backup(self, path: Path) -> Path:
        """创建 Soul 文件备份"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_{timestamp}{path.suffix}"
        backup_path = get_soul_backup_dir() / backup_name
        
        shutil.copy2(path, backup_path)
        return backup_path
    
    def log_modification(self, path: Path, operation: str):
        """记录 Soul 文件修改日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "file": str(path),
            "user": get_current_user(),
        }
        
        # 追加到修改日志
        log_file = get_soul_backup_dir() / "modification_log.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
```

---

#### 2.2 启动时完整性检查

**需求描述:**
- 应用启动时检查 Soul 文件完整性
- 缺失文件自动从模板恢复
- 损坏文件提示修复

**实现:**
```python
class SoulIntegrityChecker:
    REQUIRED_FILES = [
        "SOUL.md",
        "AGENTS.md",
        "PROFILE.md",
        "MEMORY.md",
        "HEARTBEAT.md",
    ]
    
    TEMPLATE_DIR = get_package_dir() / "agents" / "md_files" / "zh" / "soul"
    
    async def check_and_repair(self) -> IntegrityReport:
        """检查并修复 Soul 文件"""
        report = IntegrityReport()
        
        for file_name in self.REQUIRED_FILES:
            file_path = get_working_dir() / file_name
            
            # 检查是否存在
            if not file_path.exists():
                report.missing_files.append(file_name)
                # 自动从模板恢复
                await self.restore_from_template(file_name)
                report.restored_files.append(file_name)
                continue
            
            # 检查内容完整性
            is_valid = await self.validate_content(file_path)
            if not is_valid:
                report.corrupted_files.append(file_name)
                # 创建备份并提示用户
                backup_path = SoulFileManager.create_backup(file_path)
                report.backed_up_files.append(str(backup_path))
        
        return report
    
    async def restore_from_template(self, file_name: str) -> None:
        """从模板恢复文件"""
        template_path = self.TEMPLATE_DIR / file_name
        target_path = get_working_dir() / file_name
        
        if template_path.exists():
            shutil.copy2(template_path, target_path)
            logger.info(f"Restored {file_name} from template")
        else:
            # 模板也不存在，创建基础内容
            await self.create_minimal_file(file_name)
    
    async def create_minimal_file(self, file_name: str) -> None:
        """创建最小化文件"""
        minimal_content = self.get_minimal_content(file_name)
        target_path = get_working_dir() / file_name
        target_path.write_text(minimal_content, encoding="utf-8")
```

---

#### 2.3 版本控制与回滚

**需求描述:**
- Soul 文件自动版本控制
- 支持查看历史版本
- 支持回滚到任意版本

**实现:**
```python
class SoulVersionControl:
    def __init__(self):
        self.backup_dir = get_soul_backup_dir()
        self.version_log = self.backup_dir / "version_log.json"
    
    def create_version(self, file_path: Path, message: str) -> str:
        """创建版本"""
        version_id = str(uuid4())[:8]
        timestamp = datetime.utcnow().isoformat()
        
        # 复制文件到版本目录
        version_dir = self.backup_dir / "versions" / version_id
        version_dir.mkdir(parents=True, exist_ok=True)
        
        version_file = version_dir / file_path.name
        shutil.copy2(file_path, version_file)
        
        # 记录版本信息
        version_info = {
            "version_id": version_id,
            "file": file_path.name,
            "timestamp": timestamp,
            "message": message,
            "size": file_path.stat().st_size,
            "checksum": self.calculate_checksum(file_path),
        }
        
        self.append_version_log(version_info)
        return version_id
    
    def list_versions(self, file_name: str) -> List[dict]:
        """列出文件的所有版本"""
        versions = []
        log_data = json.loads(self.version_log.read_text())
        
        for entry in log_data:
            if entry["file"] == file_name:
                versions.append(entry)
        
        return sorted(versions, key=lambda v: v["timestamp"], reverse=True)
    
    def rollback(self, file_name: str, version_id: str) -> bool:
        """回滚到指定版本"""
        # 找到版本文件
        version_file = self.backup_dir / "versions" / version_id / file_name
        
        if not version_file.exists():
            raise VersionError(f"Version {version_id} not found")
        
        # 创建当前版本的备份
        current_file = get_working_dir() / file_name
        if current_file.exists():
            SoulFileManager.create_backup(current_file)
        
        # 恢复版本文件
        shutil.copy2(version_file, current_file)
        
        # 记录回滚操作
        self.log_rollback(file_name, version_id)
        return True
    
    def calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        import hashlib
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
```

---

#### 2.4 修改确认与审计

**需求描述:**
- Soul 文件修改需要用户确认
- 记录所有修改操作
- 定期生成审计报告

**实现:**
```python
class SoulModificationAudit:
    def request_modification(
        self,
        file_name: str,
        operation: str,
        reason: str,
    ) -> bool:
        """请求修改 Soul 文件"""
        # 1. 记录请求
        request_id = self.log_request(file_name, operation, reason)
        
        # 2. 如果是删除操作，需要二次确认
        if operation == "delete":
            confirmed = self.confirm_deletion(file_name, request_id)
            if not confirmed:
                return False
        
        # 3. 执行修改
        return True
    
    def confirm_deletion(self, file_name: str, request_id: str) -> bool:
        """确认删除操作"""
        # 生成确认码
        confirm_code = generate_confirm_code()
        
        # 显示确认信息
        print(f"""
⚠️  警告：您正在尝试删除 Soul 文件

文件：{file_name}
请求 ID: {request_id}

Soul 文件是 CoPaw 的记忆和生命，删除后可能导致：
- 丢失历史记忆
- Agent 身份混乱
- 任务执行异常

如果确认删除，请输入确认码：{confirm_code}
输入确认码：""")
        
        user_input = input()
        return user_input == confirm_code
    
    def generate_audit_report(self, period: str = "last_30_days") -> AuditReport:
        """生成审计报告"""
        log_file = get_soul_backup_dir() / "modification_log.jsonl"
        
        # 读取日志
        entries = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                entries.append(entry)
        
        # 过滤时间范围
        filtered = self.filter_by_period(entries, period)
        
        # 生成报告
        report = AuditReport(
            period=period,
            total_modifications=len(filtered),
            modifications_by_file=self.group_by_file(filtered),
            modifications_by_user=self.group_by_user(filtered),
            suspicious_activities=self.detect_suspicious(filtered),
        )
        
        return report
```

---

## 📋 **实施优先级**

### P0 - 立即实施（本周）

| 任务 | 描述 | 工时 |
|------|------|------|
| **API 管理系统基础** | 多 API 配置 + Key 轮询 | 8h |
| **Soul 文件锁定** | 禁止删除 + 修改备份 | 4h |
| **启动完整性检查** | 缺失自动恢复 | 2h |

### P1 - 短期实施（本月）

| 任务 | 描述 | 工时 |
|------|------|------|
| **备选回落机制** | 多级 API 回落链 | 6h |
| **CLI Copilot 登录** | Token 管理 + 自动刷新 | 4h |
| **对话绑定 API** | 配置文件 + Agent 自动选择 | 6h |
| **Soul 版本控制** | 版本管理 + 回滚 | 6h |

### P2 - 中期实施（下季度）

| 任务 | 描述 | 工时 |
|------|------|------|
| **API 类型细分** | 文本/图像/视频分离 | 4h |
| **修改审计系统** | 审计报告 + 异常检测 | 4h |
| **Engram 集成** | 默认能力集成 | 8h |

---

## 🔗 **相关文档**

- [10-ARCHITECTURE-ANALYSIS.md](./10-ARCHITECTURE-ANALYSIS.md) - 架构对比分析
- [11-API-CALL-CHAIN.md](./11-API-CALL-CHAIN.md) - API 调用链路
- [12-DESIGN-PATTERNS.md](./12-DESIGN-PATTERNS.md) - 设计模式收集

---

**文档完成日期:** 2026-03-01  
**下次审查:** 实施完成后更新
