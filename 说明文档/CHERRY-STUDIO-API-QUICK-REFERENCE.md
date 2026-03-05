# Cherry Studio API 快速参考

## API信息

- **基础URL**：`http://127.0.0.1:23333`
- **API密钥**：从Cherry Studio设置中获取
- **认证**：Bearer Token (JWT)

## 核心端点

### 1. 聊天完成
```
POST /v1/chat/completions
```

### 2. 获取模型列表
```
GET /v1/models
```

### 3. 获取API文档
```
GET /api-docs.json
```

## 模型格式

`provider:model-id`

示例：
- `openai:gpt-3.5-turbo`
- `openai:gpt-4`
- `anthropic:claude-2`

## 消息格式

```json
{
  "role": "user|assistant|system|tool",
  "content": "消息内容"
}
```

支持多模态：
```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "文本描述"},
    {"type": "image_url", "image_url": {"url": "图片URL"}}
  ]
}
```

## 常用请求参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model` | string | 是 | - | provider:model-id |
| `messages` | array | 是 | - | 消息列表 |
| `temperature` | number | 否 | 1 | 0-2，控制创造性 |
| `max_tokens` | integer | 否 | - | 最大token数 |
| `stream` | boolean | 否 | false | 是否流式输出 |
| `tools` | array | 否 | [] | 工具定义 |

## 使用示例

### 基础聊天

```bash
curl -X POST http://127.0.0.1:23333/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai:gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### 多模态输入

```bash
curl -X POST http://127.0.0.1:23333/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai:gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "描述这张图片"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ]
  }'
```

### 工具调用

```bash
curl -X POST http://127.0.0.1:23333/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai:gpt-4",
    "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "获取城市天气",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string", "description": "城市名"}
          }
        }
      }
    }]
  }'
```

### 流式输出

```python
import requests

response = requests.post(
    "http://127.0.0.1:23333/v1/chat/completions",
    headers={
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai:gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 响应格式

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "openai:gpt-3.5-turbo",
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

## 错误响应

```json
{
  "error": {
    "message": "Error description",
    "type": "error_type",
    "code": "error_code"
  }
}
```

## 常见错误

| 错误代码 | 说明 |
|----------|------|
| `invalid_request_error` | 请求参数无效 |
| `authentication_error` | 认证失败 |
| `rate_limit_error` | 速率限制 |
| `server_error` | 服务器错误 |

## 支持的消息类型

- `system` - 系统消息（设定角色）
- `user` - 用户消息
- `assistant` - 助手消息
- `tool` - 工具调用消息

## 支持的温度值

- 0: 确定性输出
- 0.7: 平衡创造性和一致性
- 1: 创造性输出
- 2: 高度创造性（可能不稳定）

## Python SDK使用

```python
import openai

client = openai.OpenAI(
    base_url="http://127.0.0.1:23333",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="openai:gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

## 安全提示

1. **API密钥安全**：不要将API密钥提交到版本控制系统
2. **HTTPS**：在生产环境中使用HTTPS保护传输
3. **速率限制**：注意API调用频率，避免超出限制
4. **内容安全**：遵守内容使用政策

## 参考文档

- [完整API文档](./CHERRY-STUDIO-API-DOCUMENTATION.md)
- [Cherry Studio GitHub](https://github.com/CherryHQ/cherry-studio)
