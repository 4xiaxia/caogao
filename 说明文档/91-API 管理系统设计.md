# 🎯 CoPaw API 管理系统设计

**参考来源:** clawdbot-feishu/chatgpt-on-wechat-master  
**设计日期:** 2026-03-01  
**设计目标:** 多 API 配置、Key 轮询、错误处理、 fallback 机制

---

## 📊 参考代码分析

### 1. API 配置管理 ✅

**参考文件:** `models/chatgpt/chat_gpt_bot.py`

**特点:**
- 从配置文件统一获取 API Key
- 支持 api_base 自定义
- 支持上下文传递 API Key

**代码:**
```python
def __init__(self):
    super().__init__()
    # set the default api_key
    openai.api_key = conf().get("open_ai_api_key")
    if conf().get("open_ai_api_base"):
        openai.api_base = conf().get("open_ai_api_base")
    
    # 部分模型特殊处理
    self.args = {
        "model": conf().get("model"),
        "temperature": conf().get("temperature", 0.9),
        "request_timeout": conf().get("request_timeout", None),
    }

def get_api_config(self):
    """Get API configuration for OpenAI-compatible base class"""
    return {
        'api_key': conf().get("open_ai_api_key"),
        'api_base': conf().get("open_ai_api_base"),
        'model': conf().get("model", "gpt-3.5-turbo"),
        'default_temperature': conf().get("temperature", 0.9),
    }
```

**CoPaw 借鉴:**
```python
# app/providers/manager.py
from config import conf

class APIProviderManager:
    def __init__(self):
        self.providers = {}
        self.current_provider = None
    
    def get_provider(self, provider_id: str):
        """获取 API Provider 配置"""
        return conf().get(f"providers.{provider_id}")
    
    def get_api_config(self, provider_id: str):
        """获取 API 配置"""
        provider = self.get_provider(provider_id)
        return {
            'api_key': provider.get('api_key'),
            'api_base': provider.get('base_url'),
            'model': provider.get('model'),
            'temperature': provider.get('temperature', 0.9),
        }
```

---

### 2. 多 Key 支持 ✅

**参考文件:** `common/cloud_client.py`

**特点:**
- 支持多个 API Key
- 通过环境变量管理
- 支持 fallback 机制

**代码:**
```python
# agent/tools/env_config/env_config.py
API_KEY_REGISTRY = {
    "OPENAI_API_KEY": "OpenAI API 密钥 (用于 GPT 模型)",
    "GEMINI_API_KEY": "Google Gemini API 密钥",
    "CLAUDE_API_KEY": "Claude API 密钥",
    "LINKAI_API_KEY": "LinkAI 智能体平台 API 密钥",
    "BOCHA_API_KEY": "博查 AI 搜索 API 密钥",
}

# agent/tools/web_search/web_search.py
def has_api_keys(self) -> bool:
    return bool(os.environ.get("BOCHA_API_KEY") or os.environ.get("LINKAI_API_KEY"))

def search_with_fallback(self, query):
    # 优先使用 Bocha
    if os.environ.get("BOCHA_API_KEY"):
        return self._search_bocha(query)
    
    # fallback 到 LinkAI
    if os.environ.get("LINKAI_API_KEY"):
        return self._search_linkai(query)
    
    return None
```

**CoPaw 借鉴:**
```python
# app/providers/key_manager.py
import os
from typing import List, Optional

class APIKeyManager:
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.keys = []
        self.current_index = 0
    
    def load_keys(self):
        """加载多个 API Keys"""
        # 从配置加载
        keys_config = conf().get(f"providers.{self.provider_id}.keys", [])
        for key_config in keys_config:
            if key_config.get("enabled", True):
                self.keys.append({
                    "key": key_config["key"],
                    "label": key_config.get("label", ""),
                    "weight": key_config.get("weight", 1),
                })
        
        # 如果配置为空，尝试从环境变量加载
        if not self.keys:
            env_key = os.environ.get(f"{self.provider_id.upper()}_API_KEY")
            if env_key:
                self.keys.append({"key": env_key, "label": "Env Key"})
    
    def get_next_key(self) -> Optional[dict]:
        """获取下一个 API Key (轮询)"""
        if not self.keys:
            return None
        
        # 轮询
        key = self.keys[self.current_index % len(self.keys)]
        self.current_index += 1
        return key
    
    def get_weighted_key(self) -> Optional[dict]:
        """按权重随机选择 API Key"""
        import random
        if not self.keys:
            return None
        
        weights = [k["weight"] for k in self.keys]
        return random.choices(self.keys, weights=weights)[0]
```

---

### 3. OpenAI 兼容层 ✅

**参考文件:** `models/openai_compatible_bot.py`

**特点:**
- 统一的 API 调用接口
- 支持多种 OpenAI 兼容提供商
- 支持流式和同步响应

**代码:**
```python
class OpenAICompatibleBot:
    def call_with_tools(self, messages, tools=None, stream=False, **kwargs):
        """Call OpenAI-compatible API with tool support"""
        try:
            # Get API configuration
            api_config = self.get_api_config()
            
            # Build request parameters
            request_params = {
                "model": kwargs.get("model", api_config.get('model')),
                "messages": messages,
                "temperature": kwargs.get("temperature", api_config.get('default_temperature')),
                "stream": stream
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
            
            # Make API call
            api_key = api_config.get('api_key')
            api_base = api_config.get('api_base')
            
            if stream:
                return self._handle_stream_response(request_params, api_key, api_base)
            else:
                return self._handle_sync_response(request_params, api_key, api_base)
        
        except Exception as e:
            logger.error(f"API call error: {e}")
            return {"error": True, "message": str(e)}
```

**CoPaw 借鉴:**
```python
# app/providers/base_provider.py
from abc import ABC, abstractmethod

class BaseAPIProvider(ABC):
    """API Provider 基类"""
    
    @abstractmethod
    def get_api_config(self) -> dict:
        """获取 API 配置"""
        pass
    
    @abstractmethod
    def chat(self, messages: list, **kwargs) -> dict:
        """聊天接口"""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: list, **kwargs):
        """流式聊天接口"""
        pass
    
    def _handle_error(self, error: Exception) -> dict:
        """统一错误处理"""
        logger.error(f"API error: {error}")
        return {
            "success": False,
            "error": {
                "message": str(error),
                "type": type(error).__name__,
            }
        }
```

---

### 4. 错误处理与 Fallback ✅

**参考文件:** `models/openai/openai_compat.py`

**特点:**
- 兼容不同版本的 OpenAI SDK
- 统一的错误类型定义
- 自动 fallback 机制

**代码:**
```python
# 兼容 OpenAI < 1.0 和 >= 1.0
try:
    # Try new OpenAI >= 1.0 API
    from openai import (
        OpenAIError,
        RateLimitError,
        APIError,
        APIConnectionError,
        AuthenticationError,
        APITimeoutError,
    )
except ImportError:
    # Fall back to old OpenAI < 1.0 API
    import openai.error as error
    OpenAIError = error.OpenAIError
    RateLimitError = error.RateLimitError
    # ...

# 使用示例
def call_api(self, messages):
    try:
        response = openai.ChatCompletion.create(**params)
        return response
    except RateLimitError as e:
        # 速率限制，切换到备用 Key
        logger.warning(f"Rate limit hit, switching to backup key")
        return self._retry_with_backup_key(messages)
    except AuthenticationError as e:
        # 认证失败，Key 无效
        logger.error(f"Invalid API key: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

**CoPaw 借鉴:**
```python
# app/providers/error_handler.py
from enum import Enum

class ErrorType(str, Enum):
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"

class APIErrorHandler:
    """API 错误处理器"""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return ErrorType.RATE_LIMIT
        elif "authentication" in error_str or "401" in error_str:
            return ErrorType.AUTH_ERROR
        elif "timeout" in error_str or "408" in error_str:
            return ErrorType.TIMEOUT
        elif "connection" in error_str or "503" in error_str:
            return ErrorType.CONNECTION_ERROR
        else:
            return ErrorType.UNKNOWN
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """判断是否应该重试"""
        error_type = APIErrorHandler.classify_error(error)
        return error_type in [
            ErrorType.RATE_LIMIT,
            ErrorType.TIMEOUT,
            ErrorType.CONNECTION_ERROR,
        ]
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int) -> int:
        """获取重试延迟（指数退避）"""
        error_type = APIErrorHandler.classify_error(error)
        
        if error_type == ErrorType.RATE_LIMIT:
            # 速率限制，等待更长时间
            return min(60, 10 * (2 ** attempt))
        else:
            # 其他错误，指数退避
            return min(30, 2 ** attempt)
```

---

## 🎯 CoPaw API 管理系统设计

### 架构设计

```
app/providers/
├── manager.py              # API Provider 管理器（单例）
├── base_provider.py        # Provider 基类
├── key_manager.py          # API Key 管理器（轮询）
├── error_handler.py        # 错误处理器
├── fallback.py             # Fallback 机制
└── providers/
    ├── openai_provider.py  # OpenAI Provider
    ├── claude_provider.py  # Claude Provider
    └── qwen_provider.py    # 通义千问 Provider
```

---

### 1. Provider 管理器

```python
# app/providers/manager.py
from common.singleton import singleton
from common.log import logger
from typing import Dict, List, Optional

@singleton
class APIProviderManager:
    """API Provider 管理器（单例）"""
    
    def __init__(self):
        self.providers: Dict[str, BaseAPIProvider] = {}
        self.provider_configs = {}
        self.key_managers: Dict[str, APIKeyManager] = {}
        self.fallback_chain: List[str] = []
    
    def initialize(self):
        """初始化所有 Provider"""
        # 从配置加载
        configs = conf().get("api_providers", [])
        for config in configs:
            self.register_provider(config)
        
        # 设置 fallback 链
        self.fallback_chain = conf().get("api_fallback_chain", [])
    
    def register_provider(self, config: dict):
        """注册 Provider"""
        provider_id = config["id"]
        provider_type = config["type"]
        
        # 创建 Provider 实例
        provider = self._create_provider(provider_type, config)
        self.providers[provider_id] = provider
        
        # 创建 Key 管理器
        key_manager = APIKeyManager(provider_id)
        key_manager.load_keys()
        self.key_managers[provider_id] = key_manager
        
        logger.info(f"Registered API provider: {provider_id}")
    
    def get_provider(self, provider_id: str) -> Optional[BaseAPIProvider]:
        """获取 Provider"""
        return self.providers.get(provider_id)
    
    def get_next_key(self, provider_id: str) -> Optional[dict]:
        """获取下一个 API Key"""
        key_manager = self.key_managers.get(provider_id)
        if key_manager:
            return key_manager.get_next_key()
        return None
    
    def execute_with_fallback(self, func, *args, **kwargs):
        """执行 API 调用，支持 fallback"""
        last_error = None
        
        for provider_id in self.fallback_chain:
            try:
                return func(provider_id, *args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_id} failed: {e}, trying next...")
                continue
        
        # 所有 Provider 都失败
        raise APIFallbackExhaustedError(
            f"All providers failed. Last error: {last_error}"
        )
```

---

### 2. Key 轮询管理器

```python
# app/providers/key_manager.py
import random
from typing import List, Optional, Dict

class APIKeyManager:
    """API Key 管理器"""
    
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.keys: List[Dict] = []
        self.current_index = 0
        self.key_health: Dict[str, Dict] = {}
    
    def load_keys(self):
        """加载多个 API Keys"""
        configs = conf().get(f"api_providers.{self.provider_id}.keys", [])
        
        for config in configs:
            if config.get("enabled", True):
                self.keys.append({
                    "key": config["key"],
                    "label": config.get("label", ""),
                    "rotation": config.get("rotation", "round-robin"),
                    "weight": config.get("weight", 1),
                })
        
        # 如果没有配置，尝试环境变量
        if not self.keys:
            env_key = os.environ.get(f"{self.provider_id.upper()}_API_KEY")
            if env_key:
                self.keys.append({"key": env_key, "label": "Env Key"})
    
    def get_next_key(self) -> Optional[Dict]:
        """获取下一个 API Key"""
        if not self.keys:
            return None
        
        # 过滤健康的 Key
        healthy_keys = [
            k for k in self.keys
            if self.key_health.get(k["key"], {}).get("healthy", True)
        ]
        
        if not healthy_keys:
            # 所有 Key 都不健康，降级使用所有 Key
            healthy_keys = self.keys
        
        # 轮询
        key = healthy_keys[self.current_index % len(healthy_keys)]
        self.current_index += 1
        
        return key
    
    def mark_key_unhealthy(self, key: str, error: Exception):
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

### 3. Fallback 机制

```python
# app/providers/fallback.py
from enum import Enum

class FallbackStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"      # 轮询
    PRIORITY = "priority"            # 优先级
    WEIGHTED = "weighted"            # 权重
    LEAST_LATENCY = "least_latency"  # 最低延迟

class APIFallbackManager:
    """API Fallback 管理器"""
    
    def __init__(self):
        self.providers = []
        self.strategy = FallbackStrategy.PRIORITY
        self.latency_stats: Dict[str, float] = {}
    
    def add_provider(self, provider_id: str, priority: int = 0, weight: int = 1):
        """添加 Provider"""
        self.providers.append({
            "id": provider_id,
            "priority": priority,
            "weight": weight,
        })
        # 按优先级排序
        self.providers.sort(key=lambda x: x["priority"], reverse=True)
    
    def execute(self, func, *args, **kwargs):
        """执行 API 调用，支持 fallback"""
        last_error = None
        
        for provider in self.providers:
            provider_id = provider["id"]
            try:
                start_time = time.time()
                result = func(provider_id, *args, **kwargs)
                elapsed = time.time() - start_time
                
                # 记录延迟
                self.latency_stats[provider_id] = elapsed
                
                return result
            
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_id} failed: {e}")
                continue
        
        # 所有 Provider 都失败
        raise Exception(f"All providers failed. Last error: {last_error}")
```

---

### 4. 统一错误处理

```python
# app/providers/error_handler.py
from enum import Enum

class ErrorType(str, Enum):
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"

class APIErrorHandler:
    """API 错误处理器"""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """分类错误类型"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return ErrorType.RATE_LIMIT
        elif "authentication" in error_str or "401" in error_str:
            return ErrorType.AUTH_ERROR
        elif "timeout" in error_str or "408" in error_str:
            return ErrorType.TIMEOUT
        elif "connection" in error_str or "503" in error_str:
            return ErrorType.CONNECTION_ERROR
        else:
            return ErrorType.UNKNOWN
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """判断是否应该重试"""
        error_type = APIErrorHandler.classify_error(error)
        return error_type in [
            ErrorType.RATE_LIMIT,
            ErrorType.TIMEOUT,
            ErrorType.CONNECTION_ERROR,
        ]
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int) -> int:
        """获取重试延迟（指数退避）"""
        error_type = APIErrorHandler.classify_error(error)
        
        if error_type == ErrorType.RATE_LIMIT:
            return min(60, 10 * (2 ** attempt))
        else:
            return min(30, 2 ** attempt)
```

---

## 📊 配置示例

```json
{
  "api_providers": [
    {
      "id": "openai-primary",
      "type": "openai",
      "base_url": "https://api.openai.com/v1",
      "keys": [
        {"key": "sk-xxx", "label": "主 Key", "rotation": "round-robin"},
        {"key": "sk-yyy", "label": "备用 Key", "rotation": "round-robin"}
      ],
      "model": "gpt-4o-mini",
      "enabled": true,
      "priority": 1
    },
    {
      "id": "openai-backup",
      "type": "openai",
      "base_url": "https://api2.openai.com/v1",
      "keys": [
        {"key": "sk-zzz", "label": "备用账号"}
      ],
      "model": "gpt-4o-mini",
      "enabled": true,
      "priority": 2
    },
    {
      "id": "claude-api",
      "type": "claude",
      "base_url": "https://api.anthropic.com/v1",
      "keys": [
        {"key": "sk-claude-xxx"}
      ],
      "model": "claude-sonnet-4-5-20250929",
      "enabled": true,
      "priority": 3
    }
  ],
  "api_fallback_chain": [
    "openai-primary",
    "openai-backup",
    "claude-api"
  ]
}
```

---

## 🚀 实施计划

### Phase 1: 基础架构 (4h)

- [ ] 创建 `app/providers/manager.py`
- [ ] 创建 `app/providers/base_provider.py`
- [ ] 创建 `app/providers/key_manager.py`

### Phase 2: 错误处理 (2h)

- [ ] 创建 `app/providers/error_handler.py`
- [ ] 创建 `app/providers/fallback.py`

### Phase 3: Provider 实现 (4h)

- [ ] 实现 `OpenAIProvider`
- [ ] 实现 `ClaudeProvider`
- [ ] 实现 `QwenProvider`

### Phase 4: 集成测试 (2h)

- [ ] 测试 Key 轮询
- [ ] 测试 Fallback 机制
- [ ] 测试错误处理

---

*设计完成日期:* 2026-03-01  
*设计者:* zo (◕‿◕)  
*参考:* clawdbot-feishu/chatgpt-on-wechat-master
