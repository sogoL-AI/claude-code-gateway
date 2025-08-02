# Claude Code + LiteLLM 集成完整指南

## 概述

LiteLLM 是一个开源库，提供统一的OpenAI兼容接口来访问100+种大语言模型。通过集成LiteLLM，Claude Code可以：

1. **多模型支持**: 接入OpenAI、Anthropic、Google、Azure等多个提供商
2. **负载均衡**: 自动在多个API密钥间分配请求
3. **成本追踪**: 统一的使用监控和计费
4. **故障转移**: 自动切换到备用模型
5. **统一接口**: 保持OpenAI兼容的API格式

## 核心集成方案

### 方案1: 作为代理服务器 (推荐)

#### 架构图
```
Claude Code → LiteLLM Proxy Server → 多个LLM提供商
                     ↓
            [OpenAI, Anthropic, Google, Azure, ...]
```

#### 优势
- **零代码修改**: Claude Code无需代码变更
- **统一管理**: 集中式配置和监控
- **高性能**: 独立进程优化
- **多租户**: 支持多用户和项目隔离

## 详细部署步骤

### 第一步: 安装和配置LiteLLM

#### 1.1 安装LiteLLM
```bash
# 安装核心包
pip install litellm

# 安装代理服务器
pip install 'litellm[proxy]'
```

#### 1.2 创建配置文件 `config.yaml`
```yaml
model_list:
  # Anthropic Claude 模型
  - model_name: claude-4-sonnet
    litellm_params:
      model: anthropic/claude-4-sonnet-20250219
      api_key: os.environ/ANTHROPIC_API_KEY
      
  - model_name: claude-4-opus  
    litellm_params:
      model: anthropic/claude-4-opus-20250514
      api_key: os.environ/ANTHROPIC_API_KEY

  # OpenAI 模型作为备用
  - model_name: gpt-4-turbo
    litellm_params:
      model: openai/gpt-4-turbo
      api_key: os.environ/OPENAI_API_KEY

  # 其他提供商
  - model_name: gemini-pro
    litellm_params:
      model: vertex_ai/gemini-pro
      vertex_project: os.environ/GOOGLE_PROJECT_ID
      vertex_location: us-central1

# 代理服务器设置
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: "postgresql://user:password@localhost:5432/litellm"

# 路由和故障转移设置
router_settings:
  routing_strategy: "usage-based-routing"
  fallbacks:
    - claude-4-sonnet: ["claude-4-opus", "gpt-4-turbo"]
    - claude-4-opus: ["claude-4-sonnet", "gpt-4-turbo"]

# 速率限制
model_list[0].litellm_params.rpm: 1000
model_list[0].litellm_params.tpm: 100000
```

#### 1.3 设置环境变量
```bash
# LiteLLM 配置
export LITELLM_MASTER_KEY="sk-litellm-your-secret-key"

# API 密钥
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_PROJECT_ID="your-google-project"

# 数据库（可选，用于持久化）
export DATABASE_URL="postgresql://user:password@localhost:5432/litellm"
```

### 第二步: 启动LiteLLM代理服务器

#### 2.1 启动服务器
```bash
# 基础启动
litellm --config config.yaml

# 指定端口和host
litellm --config config.yaml --port 4000 --host 0.0.0.0

# 生产环境启动（使用Gunicorn）
litellm --config config.yaml --port 4000 --num_workers 4
```

#### 2.2 验证服务器状态
```bash
# 健康检查
curl http://localhost:4000/health

# 获取可用模型列表
curl -X GET http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-your-secret-key"

# 测试API调用
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-your-secret-key" \
  -d '{
    "model": "claude-4-sonnet",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### 第三步: 配置Claude Code使用LiteLLM代理

#### 3.1 设置环境变量
```bash
# 将Claude Code重定向到LiteLLM代理
export ANTHROPIC_BASE_URL="http://localhost:4000"
export ANTHROPIC_AUTH_TOKEN="sk-litellm-your-secret-key"

# 可选：指定默认模型
export ANTHROPIC_MODEL="claude-4-sonnet"
```

#### 3.2 更新Claude Code配置文件
编辑 `~/.claude/settings.json`:
```json
{
  "apiBaseUrl": "http://localhost:4000",
  "defaultModel": "claude-4-sonnet",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Using LiteLLM proxy with model: claude-4-sonnet'"
          }
        ]
      }
    ]
  }
}
```

#### 3.3 验证集成
```bash
# 启动Claude Code验证
claude --model claude-4-sonnet -p "Hello, this is a test"

# 检查是否使用了LiteLLM代理
claude --model gpt-4-turbo -p "Hello from GPT-4"
```

## 高级配置选项

### 负载均衡配置
```yaml
router_settings:
  routing_strategy: "usage-based-routing"  # 基于使用量
  # routing_strategy: "latency-based-routing"  # 基于延迟
  # routing_strategy: "cost-based-routing"    # 基于成本
  
  allowed_fails: 3
  cooldown_time: 30
  retry_after: 60
  
  # 模型组配置
  model_group_alias:
    "claude-family": ["claude-4-sonnet", "claude-4-opus"]
    "gpt-family": ["gpt-4-turbo", "gpt-4"]
```

### 成本和预算控制
```yaml
general_settings:
  max_budget: 100.0  # 每月最大预算（美元）
  budget_duration: "1mo"
  
  # 按用户限制
  max_user_budget: 50.0
  
  # 按API密钥限制
  max_api_key_budget: 10.0
  
  # 速率限制
  rpm_limit: 1000
  tpm_limit: 100000
```

### 缓存配置
```yaml
cache:
  type: "redis"
  host: "localhost"
  port: 6379
  ttl: 3600  # 缓存1小时
  
  # 或使用内存缓存
  # type: "local"
  # ttl: 600
```

### 监控和日志
```yaml
general_settings:
  # 启用详细日志
  set_verbose: true
  
  # 集成监控服务
  success_callback: ["langfuse", "prometheus"]
  failure_callback: ["langfuse"]
  
  # Langfuse配置
  langfuse_public_key: os.environ/LANGFUSE_PUBLIC_KEY
  langfuse_secret_key: os.environ/LANGFUSE_SECRET_KEY
  
  # Prometheus配置
  prometheus_port: 9090
```

## Docker部署方案

### Dockerfile
```dockerfile
FROM python:3.11-slim

# 安装LiteLLM
RUN pip install 'litellm[proxy]'

# 复制配置文件
COPY config.yaml /app/config.yaml
WORKDIR /app

# 暴露端口
EXPOSE 4000

# 启动命令
CMD ["litellm", "--config", "config.yaml", "--port", "4000", "--host", "0.0.0.0"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  litellm-proxy:
    build: .
    ports:
      - "4000:4000"
    environment:
      - LITELLM_MASTER_KEY=sk-litellm-your-secret-key
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/litellm
    depends_on:
      - db
    volumes:
      - ./config.yaml:/app/config.yaml

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=litellm
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 启动服务
```bash
# 启动完整服务栈
docker-compose up -d

# 查看日志
docker-compose logs -f litellm-proxy

# 扩展代理实例
docker-compose up -d --scale litellm-proxy=3
```

## 生产环境最佳实践

### 1. 高可用部署
```bash
# 使用多个实例
litellm --config config.yaml --port 4000 &
litellm --config config.yaml --port 4001 &
litellm --config config.yaml --port 4002 &

# 配置负载均衡器（Nginx）
upstream litellm_backend {
    server localhost:4000;
    server localhost:4001;
    server localhost:4002;
}

server {
    listen 80;
    location / {
        proxy_pass http://litellm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 监控和告警
```yaml
general_settings:
  # 健康检查端点
  health_check: true
  
  # 指标收集
  collect_metrics: true
  
  # 告警配置
  alert_webhooks:
    - url: "https://hooks.slack.com/your-webhook"
      events: ["budget_exceeded", "model_failure", "high_latency"]
```

### 3. 安全配置
```yaml
general_settings:
  # API密钥加密
  encrypt_keys_in_db: true
  
  # IP白名单
  allowed_ips: ["192.168.1.0/24", "10.0.0.0/8"]
  
  # HTTPS配置
  ssl_keyfile: "/path/to/keyfile"
  ssl_certfile: "/path/to/certfile"
  
  # 认证插件
  auth_strategy: "jwt"
  jwt_secret: os.environ/JWT_SECRET
```

## 故障排除

### 常见问题

#### 1. 连接错误
```bash
# 检查代理服务器状态
curl http://localhost:4000/health

# 检查Claude Code配置
echo $ANTHROPIC_BASE_URL
echo $ANTHROPIC_AUTH_TOKEN
```

#### 2. 模型不可用
```bash
# 检查模型列表
curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
     http://localhost:4000/v1/models

# 检查模型配置
litellm --config config.yaml --test
```

#### 3. 性能问题
```bash
# 启用详细日志
export LITELLM_LOG=DEBUG
litellm --config config.yaml

# 监控资源使用
docker stats litellm-proxy
```

### 调试工具
```python
# Python调试脚本
import requests
import json

def test_litellm_proxy():
    url = "http://localhost:4000/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-litellm-your-secret-key",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-4-sonnet",
        "messages": [{"role": "user", "content": "Test message"}],
        "max_tokens": 100
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_litellm_proxy()
```

## 集成收益总结

### 1. 多模型能力
- **无缝切换**: 在不同LLM间自由切换
- **成本优化**: 选择最经济的模型
- **性能优化**: 根据任务选择最适合的模型

### 2. 企业级功能
- **统一计费**: 跨模型的使用统计
- **访问控制**: 细粒度的权限管理
- **监控告警**: 实时性能和成本监控

### 3. 开发效率
- **一致接口**: 统一的API调用方式
- **故障转移**: 自动处理服务中断
- **负载均衡**: 自动分配请求负载

这个集成方案让Claude Code获得了企业级的多模型支持能力，同时保持了原有的使用体验。