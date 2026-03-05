# Cherry Studio API 完整文档

## 基础信息

- **API名称**：Cherry Studio API
- **版本**：1.0.0
- **API规范**：OpenAPI 3.0.0
- **描述**：OpenAI兼容API，支持Cherry Studio的特定功能
- **联系方式**：
  - 名称：Cherry Studio
  - 链接：https://github.com/CherryHQ/cherry-studio

## 认证方式

### Bearer Token认证

**类型**：HTTP Bearer认证

**格式**：JWT (JSON Web Token)

**获取方式**：从Cherry Studio设置中获取API密钥

**示例**：
```
Authorization: Bearer YOUR_API_KEY
```

## 服务器配置

**基础URL**：`http://127.0.0.1:23333/`

**描述**：当前服务器

## API端点概览

### 主要功能分类

1. **聊天对话**
   - 支持多轮对话
   - 支持系统消息、用户消息、助手消息
   - 支持工具调用

2. **模型管理**
   - 查询可用模型列表
   - 支持provider:model-id格式

3. **MCP服务器配置**
   - 管理MCP服务器
   - 配置服务器命令和参数

4. **错误处理**
   - 统一的错误响应格式

## 数据模型

### ChatMessage (聊天消息)

**类型**：object

**属性**：
- `role` (string) - 消息角色
  - 可选值：`system`, `user`, `assistant`, `tool`
- `content` (string | array) - 消息内容
  - 字符串或消息对象数组
  - 消息对象包含：
    - `type` (string) - 消息类型
    - `text` (string) - 文本内容
    - `image_url` (object) - 图片URL
      - `url` (string) - 图片地址
- `name` (string) - 消息名称（可选）
- `tool_calls` (array) - 工具调用列表
  - 包含：
    - `id` (string) - 调用ID
    - `type` (string) - 调用类型
    - `function` (object) - 函数信息
      - `name` (string) - 函数名称
      - `arguments` (string) - 函数参数

### ChatCompletionRequest (聊天完成请求)

**类型**：object

**必需属性**：
- `model` (string) - 使用的模型，格式为provider:model-id
- `messages` (array) - 消息列表

**可选属性**：
- `temperature` (number) - 温度参数
  - 范围：0-2
  - 默认值：1
- `max_tokens` (integer) - 最大token数
  - 最小值：1
- `stream` (boolean) - 是否流式传输
  - 默认值：false
- `tools` (array) - 工具定义列表
  - 每个工具包含：
    - `type` (string) - 工具类型
    - `function` (object) - 函数定义
      - `name` (string) - 函数名称
      - `description` (string) - 函数描述
      - `parameters` (object) - 函数参数

### Model (模型信息)

**类型**：object

**属性**：
- `id` (string) - 模型ID
- `object` (string) - 对象类型，固定值为`model`
- `created` (integer) - 创建时间戳
- `owned_by` (string) - 拥有者信息

### MCPServer (MCP服务器配置)

**类型**：object

**属性**：
- `id` (string) - 服务器ID
- `name` (string) - 服务器名称
- `command` (string) - 启动命令
- `args` (array) - 命令参数列表
- `env` (object) - 环境变量
- `disabled` (boolean) - 是否禁用

### Error (错误响应)

**类型**：object

**属性**：
- `error` (object) - 错误详情
  - `message` (string) - 错误消息
  - `type` (string) - 错误类型
  - `code` (string) - 错误代码

## API端点详细说明

### 1. 聊天完成

**端点**：`/v1/chat/completions`

**方法**：POST

**请求头**：
```
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
```

**请求体**：
```json
{
  "model": "provider:model-id",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "temperature": 1,
  "max_tokens": 1000,
  "stream": false,
  "tools": []
}
```

**响应格式**：
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "provider:model-id",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 9,
    "total_tokens": 19
  }
}
```

### 2. 获取模型列表

**端点**：`/v1/models`

**方法**：GET

**请求头**：
```
Authorization: Bearer YOUR_API_KEY
```

**响应格式**：
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    },
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1677610603,
      "owned_by": "openai"
    }
  ]
}
```

### 3. 获取Cherry Studio特定信息

**端点**：`/api-docs.json`

**方法**：GET

**描述**：获取API配置和文档信息

**响应格式**：
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Cherry Studio API",
    "version": "1.0.0",
    "description": "OpenAI-compatible API for Cherry Studio with additional Cherry-specific endpoints"
  },
  "servers": [...],
  "components": {
    "securitySchemes": {...},
    "schemas": {...}
  },
  "paths": {},
  "tags": []
}
```

## 模型格式说明

**格式**：`provider:model-id`

**示例**：
- `openai:gpt-3.5-turbo`
- `openai:gpt-4`
- `anthropic:claude-2`
- `azure:azure-gpt-4`

## 使用示例

### Python示例

```python
import requests
import json

url = "http://127.0.0.1:23333/v1/chat/completions"
api_key = "YOUR_API_KEY"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "openai:gpt-3.5-turbo",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Hello!"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}

response = requests.post(url, headers=headers, data=json.dumps(data))
result = response.json()

print(result["choices"][0]["message"]["content"])
```

### cURL示例

```bash
curl -X POST http://127.0.0.1:23333/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai:gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

## 错误处理

所有错误响应都遵循以下格式：

```json
{
  "error": {
    "message": "Error description here",
    "type": "error_type",
    "code": "error_code"
  }
}
```

常见错误类型：
- `invalid_request_error` - 无效请求
- `authentication_error` - 认证失败
- `permission_error` - 权限不足
- `rate_limit_error` - 速率限制
- `server_error` - 服务器错误

## 特性说明

### 1. 多模态支持

支持图片内容输入：

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "描述这张图片"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "https://example.com/image.jpg"
      }
    }
  ]
}
```

### 2. 工具调用支持

支持Function Calling功能：

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "城市名称"
            }
          },
          "required": ["city"]
        }
      }
    }
  ]
}
```

### 3. 流式传输

支持SSE流式响应：

```python
import requests

url = "http://127.0.0.1:23333/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "openai:gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": True
}

response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 版本信息

- **当前版本**：1.0.0
- **OpenAPI版本**：3.0.0
- **更新日期**：2026-03-04

## 联系与支持

- **项目地址**：https://github.com/CherryHQ/cherry-studio
- **API作者**：Cherry Studio
- **API密钥获取**：在Cherry Studio设置中生成

## 变更日志

### v1.0.0 (2026-03-04)
- 初始版本发布
- 支持OpenAI兼容API
- 添加Cherry Studio特定功能
- 支持多模态输入
- 支持工具调用
- 支持流式传输
