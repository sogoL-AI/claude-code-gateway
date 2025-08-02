# Claude 官方 API 接口规范

## API 基础信息

### 基础URL
```
https://api.anthropic.com
```

### 认证方式
- 请求头：`x-api-key: YOUR_API_KEY`
- API Key 可在 Anthropic Console 中生成
- 支持组织和工作空间级别的密钥管理

### 通用请求头
```http
Content-Type: application/json
x-api-key: YOUR_API_KEY
anthropic-version: 2023-06-01
```

### 请求大小限制
- 标准端点：32 MB
- 批处理 API：256 MB
- 文件 API：500 MB

## 核心 API 端点

### 1. Messages API
**端点**: `POST /v1/messages`

**必需参数**:
- `model`: 指定 Claude 模型 (如 "claude-sonnet-4-20250514")
- `messages`: 对话历史消息数组
- `max_tokens`: 最大生成 token 数

**请求示例**:
```json
{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "Hello, Claude"}
    ]
}
```

**可选参数**:
- `temperature`: 控制输出随机性 (0.0-1.0)
- `system`: 系统提示
- `tools`: 工具使用配置
- `stream`: 启用流式响应
- `stop_sequences`: 停止序列
- `top_p`: 核采样参数
- `top_k`: Top-K 采样参数

**响应格式**:
```json
{
    "id": "msg_123",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "Hello! How can I help you today?"
        }
    ],
    "model": "claude-sonnet-4-20250514",
    "stop_reason": "end_turn",
    "stop_sequence": null,
    "usage": {
        "input_tokens": 10,
        "output_tokens": 25
    }
}
```

### 2. Models API
**端点**: `GET /v1/models/{model_id}`

**请求示例**:
```bash
curl https://api.anthropic.com/v1/models/claude-sonnet-4-20250514 \
     --header "x-api-key: $ANTHROPIC_API_KEY" \
     --header "anthropic-version: 2023-06-01"
```

**响应示例**:
```json
{
    "created_at": "2025-02-19T00:00:00Z",
    "display_name": "Claude Sonnet 4",
    "id": "claude-sonnet-4-20250514",
    "type": "model"
}
```

### 3. Message Batches API
**端点**: `POST /v1/messages/batches`

用于批量处理多个消息请求，适用于非实时处理场景。

### 4. Files API
**端点**: `POST /v1/files`

用于上传文件以供 Claude 分析和处理。

## 可用模型

### Claude 4 系列
- `claude-opus-4-20250514`: 最强大模型，适用于复杂推理
- `claude-sonnet-4-20250514`: 平衡性能和速度
- `claude-haiku-4-20250514`: 快速响应模型

### 模型特性对比
| 模型 | 上下文长度 | 适用场景 | 性能特点 |
|------|------------|----------|----------|
| Opus 4 | 200K tokens | 复杂推理、代码生成 | 最高质量 |
| Sonnet 4 | 200K tokens | 通用对话、分析 | 平衡性能 |
| Haiku 4 | 200K tokens | 快速响应、简单任务 | 最快速度 |

## 流式响应

### 启用流式响应
```json
{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [
        {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true
}
```

### 流式响应格式
```
data: {"type": "message_start", "message": {...}}

data: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}

data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

data: {"type": "content_block_stop", "index": 0}

data: {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": null}}

data: {"type": "message_stop"}
```

## 工具使用 (Tool Use)

### 工具定义
```json
{
    "tools": [
        {
            "name": "calculator",
            "description": "计算数学表达式",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式"
                    }
                },
                "required": ["expression"]
            }
        }
    ]
}
```

### 工具使用响应
```json
{
    "content": [
        {
            "type": "tool_use",
            "id": "toolu_123",
            "name": "calculator",
            "input": {"expression": "2 + 2"}
        }
    ]
}
```

## 错误处理

### 错误响应格式
```json
{
    "type": "error",
    "error": {
        "type": "invalid_request_error",
        "message": "messages: Field required"
    }
}
```

### 常见错误类型
- `invalid_request_error`: 请求参数错误
- `authentication_error`: 认证失败
- `rate_limit_error`: 速率限制
- `api_error`: API 内部错误
- `overloaded_error`: 服务过载

## 速率限制

### 限制维度
- 每分钟请求数 (RPM)
- 每分钟输入 Token 数 (ITPM)
- 每分钟输出 Token 数 (OTPM)

### Tier 4 限制 (最高等级)
- Claude Opus 4 和 Sonnet 4:
  - 4,000 RPM
  - 2,000,000 ITPM
  - 400,000 OTPM

### 超限处理
```json
{
    "type": "error",
    "error": {
        "type": "rate_limit_error",
        "message": "Rate limit exceeded"
    }
}
```
- 响应包含 `retry-after` 头指示等待时间

## 响应头

### 标准响应头
- `request-id`: 唯一请求标识符
- `anthropic-organization-id`: 关联的组织ID
- `retry-after`: 速率限制时的等待时间 (秒)

## SDK 支持

### 官方 SDK
- **Python**: `pip install anthropic`
- **TypeScript/JavaScript**: `npm install @anthropic-ai/sdk`
- **OpenAI 兼容模式**: 支持 OpenAI SDK

### Python SDK 示例
```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude"}
    ]
)
```

### TypeScript SDK 示例
```typescript
import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
    apiKey: 'your-api-key',
});

const message = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 1024,
    messages: [
        { role: 'user', content: 'Hello, Claude' }
    ],
});
```

## 最佳实践

### 性能优化
1. **合理设置 max_tokens**: 避免不必要的长响应
2. **使用流式响应**: 提供更好的用户体验
3. **批量处理**: 对于大量请求使用 Batch API
4. **缓存策略**: 缓存常用响应避免重复请求

### 错误处理
1. **实现重试机制**: 使用指数退避算法
2. **监控速率限制**: 主动监控使用量
3. **优雅降级**: 服务不可用时的降级策略

### 安全建议
1. **密钥管理**: 使用环境变量存储 API 密钥
2. **输入验证**: 验证用户输入防止注入攻击
3. **日志记录**: 记录请求但避免记录敏感信息

## OpenAI 兼容性

### 兼容的端点
- `/v1/chat/completions` (映射到 Messages API)
- `/v1/models` (映射到 Models API)

### 使用 OpenAI SDK
```python
from openai import OpenAI

# 配置为使用 Claude
client = OpenAI(
    api_key="your-anthropic-api-key",
    base_url="https://api.anthropic.com"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-20250514",
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)
```

这个规范为构建 Claude API 兼容的代理服务提供了完整的参考，支持与现有 OpenAI 生态系统的无缝集成。