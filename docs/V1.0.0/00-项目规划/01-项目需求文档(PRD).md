# 📋 Claude Code Gateway - 项目需求文档

## 🎯 项目概述

Claude Code Gateway 是一个**性能优先**的 Go 服务，提供三大核心能力：

1. **LiteLLM Provider** - 作为 LiteLLM 的 Claude Code 提供者，接入 100+ AI 框架和工具
2. **Claude Code 原生 API** - 完整复刻 CLI 所有功能，支持会话管理、Agent 切换、工具调用等
3. **管理 + 可视化** - Web 界面管理 Claude Code 功能，实时展示 AI 决策过程和代码生成

**核心设计原则：性能第一，功能第二**

## 👥 目标用户群体

**主要用户：开发者**
- 想要构建更好的 Claude Code 产品的开发者
- 需要集成 Claude Code 能力到现有系统的工程师
- 希望可视化和管理 Claude Code 行为的高级用户
- 想要利用 OpenAI 生态但使用 Claude Code 后端的开发者

## 💡 核心价值主张

- **性能极致优化** - 毫秒级 API 响应，支持大规模并发
- **功能完全一致** - CLI 能做的一切，API 都能做，零功能损失
- **零额外配置** - CLI 可用即 API 可用，无需额外认证或设置
- **双模式设计** - 既支持 LiteLLM 生态集成，也提供 Claude Code 原生 API
- **功能零损失** - CLI 的所有功能通过原生 API 完整保留
- **透明可控管理** - 完整的 Claude Code 功能可视化和管理能力
- **开发者友好** - 专为开发者设计的功能和体验

## 📊 功能需求

### 🚀 F1: 高性能 LiteLLM Provider API

#### F1.1 OpenAI 兼容端点（LiteLLM 规范）
- `/v1/chat/completions` - 严格 OpenAI 格式，LiteLLM 兼容
- `/v1/models` - 模型列表接口
- `/v1/health` - 健康检查接口

#### F1.2 协议兼容性
- 100% OpenAI Chat Completions API 规范兼容
- 完整的流式响应（Server-Sent Events）支持
- 支持多种输入格式（文本、图片、文件）
- 支持会话上下文管理
- 标准 HTTP 状态码和错误格式

#### F1.3 Claude 特有功能支持
- 通过 `extra_body` 参数传递 Claude 特性
- Thinking blocks 透传和可视化
- Web search、Code execution 等功能
- Tool use 工具调用支持
- Citations 引用功能

#### F1.4 LiteLLM 生态完整集成
- **自定义 Provider** - 完美适配 LiteLLM 的 custom provider 机制
- **负载均衡** - 支持多实例部署和智能路由
- **故障转移** - 自动健康检查和切换
- **使用统计** - 详细的调用量和性能数据
- **成本控制** - 集成 LiteLLM 的成本管理功能
- **缓存支持** - 兼容 LiteLLM 缓存机制

#### F1.5 生态覆盖（通过 LiteLLM）
- **100+ 框架支持** - LangChain、AutoGPT、Streamlit 等所有 LiteLLM 生态
- **多语言 SDK** - 通过 OpenAI SDK 支持所有编程语言
- **企业工具** - CI/CD、Jupyter、VSCode 插件等开发工具
- **BI 平台** - 数据分析和可视化工具集成

### 💻 F2: Claude Code 原生 API

#### F2.1 会话管理 API
- **POST** `/api/sessions` - 创建新会话
- **GET** `/api/sessions` - 获取会话列表
- **GET** `/api/sessions/{id}` - 获取会话详情
- **POST** `/api/sessions/{id}/messages` - 发送消息到会话
- **DELETE** `/api/sessions/{id}` - 删除会话
- **PUT** `/api/sessions/{id}/context` - 更新会话上下文

#### F2.2 Agent 管理 API
- **GET** `/api/agents` - 获取可用 Agent 列表
- **POST** `/api/agents` - 创建自定义 Agent
- **PUT** `/api/sessions/{id}/agent` - 切换会话的 Agent
- **GET** `/api/agents/{name}/config` - 获取 Agent 配置
- **PUT** `/api/agents/{name}/config` - 更新 Agent 配置

#### F2.3 CLI 命令完整支持

**确保 CLI 能用的所有功能，原生 API 都能完整支持**
- 支持所有 Claude CLI 斜杠命令（`/init`, `/config`, `/clear`, `/reset`, `/help` 等）
- 提供与 CLI 完全一致的功能体验和参数支持
- 命令执行结果和错误处理与 CLI 保持一致
- 支持交互式和非交互式两种执行模式

#### F2.4 工具调用 API

**智能工具调用（Claude 主动决策）**
- **POST** `/api/sessions/{id}/messages` - 发送消息，Claude 自动选择并调用工具
- **GET** `/api/sessions/{id}/tool-calls` - 获取会话中的工具调用历史
- **PUT** `/api/sessions/{id}/tool-permissions` - 设置允许的工具列表

**直接工具调用（用户显式控制）**
- **POST** `/api/sessions/{id}/tools/search` - 直接执行搜索工具
- **POST** `/api/sessions/{id}/tools/bash` - 直接执行 Bash 命令
- **POST** `/api/sessions/{id}/tools/edit` - 直接调用文件编辑工具
- **POST** `/api/sessions/{id}/tools/read` - 直接调用文件读取工具
- **POST** `/api/sessions/{id}/tools/glob` - 直接调用文件模式匹配工具
- **GET** `/api/tools` - 获取可用工具列表和文档

#### F2.5 文件和项目管理 API
- **POST** `/api/sessions/{id}/files/upload` - 上传文件到会话
- **GET** `/api/sessions/{id}/files` - 获取会话文件列表
- **POST** `/api/sessions/{id}/project/init` - 初始化项目上下文
- **PUT** `/api/sessions/{id}/project/workspace` - 设置工作空间路径

#### F2.6 高级功能 API
- **POST** `/api/sessions/{id}/thinking` - 启用/配置 thinking 模式
- **POST** `/api/sessions/{id}/memory` - 管理长期记忆
- **GET** `/api/sessions/{id}/history` - 获取完整对话历史
- **POST** `/api/sessions/{id}/export` - 导出会话数据
- **POST** `/api/sessions/{id}/resume` - 恢复中断的会话

#### F2.7 实时功能
- **WebSocket** `/api/sessions/{id}/stream` - 实时消息流
- **WebSocket** `/api/sessions/{id}/tools/stream` - 实时工具调用状态
- **SSE** `/api/sessions/{id}/events` - 服务器推送事件

### 🎛️ F3: Web 管理 + 可视化界面

#### F3.1 实时决策过程展示
- 完整的思考步骤（thinking blocks）可视化
- 工具调用链和参数详细展示
- 关键决策点高亮标注
- 思考过程搜索和过滤功能

#### F3.2 代码生成追踪
- 实时显示所有生成的代码片段
- 记录文件创建、修改、删除操作
- 代码语法高亮和格式化
- 代码版本对比功能

#### F3.3 会话可视化管理
- 会话列表和详情的图形化界面
- 实时会话状态监控
- 会话上下文和记忆可视化
- 交互式会话操作（暂停、恢复、分支）

#### F3.4 Agent 和工具管理界面
- Agent 列表查看和配置管理
- 工具调用历史和状态监控
- 自定义 Agent 创建和编辑
- Agent 性能分析和优化建议

#### F3.5 系统监控仪表板
- API 响应时间实时监控
- 并发连接数和资源使用统计
- 成功率和错误率趋势分析
- 性能瓶颈识别和告警

### 🔧 F4: 系统功能

#### F4.1 认证与安全
- 完全依赖 Claude CLI 的认证机制
- 前置条件：本地 CLI 可用即 API 可用
- 无额外认证层，保持极简设计

#### F4.2 配置管理
- YAML/JSON 配置文件支持
- 环境变量配置覆盖
- 运行时配置热重载
- 多环境配置支持

#### F4.3 监控与日志
- 详细的请求响应日志
- 结构化日志输出
- 错误追踪和告警
- Prometheus 指标导出

#### F4.4 部署支持
- Docker 容器化支持
- Kubernetes 部署配置
- 一键部署脚本
- 健康检查和优雅关闭

## ⚡ 非功能需求（性能核心）

### 🎯 P1: 性能要求（最高优先级）

#### P1.1 响应时间
- API Gateway 延迟 < 10ms（P99）
- Web 界面响应 < 100ms（P99）
- 实时数据更新延迟 < 50ms

#### P1.2 并发能力
- 支持 10,000+ 并发连接
- API 吞吐量 > 50,000 QPS
- 单实例支持 1000+ 活跃 Session

#### P1.3 资源效率
- 内存占用 < 50MB（空载）
- CPU 使用率 < 10%（空闲时）
- 启动时间 < 2 秒

### 🛡️ P2: 可靠性要求

#### P2.1 高可用性
- 服务可用性 > 99.99%
- 平均故障恢复时间 < 30s
- 零停机配置更新

#### P2.2 错误处理
- 优雅的错误降级
- CLI 调用失败自动重试
- 资源泄漏防护

### 🔄 P3: 可扩展性要求

#### P3.1 水平扩展
- 支持负载均衡部署
- 无状态服务设计
- 数据持久化分离

#### P3.2 功能扩展
- 插件式架构设计
- API 版本向后兼容
- 模块化组件设计

## 📈 成功指标

### 🚀 性能指标（核心）
- **API 延迟**: P99 < 10ms, P95 < 5ms
- **并发处理**: > 10,000 并发连接稳定运行
- **吞吐量**: > 50,000 QPS 持续处理
- **资源效率**: 单核心支持 1000+ QPS
- **启动速度**: < 2s 完全就绪

### 📊 功能指标
- **双模式支持**: 100% 同时支持 LiteLLM 兼容和原生API两种模式
- **功能完备性**: 100% 复制 Claude Code CLI 的所有能力（通过原生API）
- **LiteLLM 兼容**: 100% 通过 LiteLLM 官方兼容性测试
- **OpenAI 规范**: 100% 符合 OpenAI API 规范，支持所有 OpenAI SDK
- **生态覆盖**: 通过 LiteLLM 支持 100+ AI 框架和工具
- **原生API功能**: 100% 支持会话管理、Agent切换、工具调用等CLI特性
- **可视化覆盖**: 100% 的 Claude 操作可追踪和管理

### 👥 用户指标
- **开发者采用率**: 目标用户群体 50% 采用
- **集成成功率**: 95% 的集成尝试成功
- **用户满意度**: NPS > 9.0
- **活跃使用**: 80% 用户日活使用

### 💰 业务指标
- **性能提升**: 相比直接 CLI 调用提升 100x 并发能力
- **开发效率**: 降低 80% 的 Claude Code 集成开发时间
- **功能覆盖**: 原生API提供CLI 100%功能，LiteLLM提供生态兼容
- **维护成本**: 降低 90% 的运维工作量
- **生态价值**: 双模式设计，既支持简单集成也支持复杂应用
- **用户选择**: 开发者可根据需求选择最适合的使用模式
- **企业价值**: 统一管理多种AI模型源，支持复杂会话和工作流

## 🏗️ 技术约束

### 必须满足
- 基于 Go 语言开发（性能和并发优势）
- 单二进制文件部署
- 零外部依赖启动
- 内存安全和并发安全

### 建议采用
- Fiber 框架（高性能 HTTP 服务）
- 结构化日志（zerolog）
- 配置管理（viper）
- 容器化部署（Docker）

## 🔗 API 架构设计

### 🎯 **三模块 API 设计**

```
Claude Code Gateway
├── LiteLLM 兼容层
│   ├── GET  /v1/models
│   ├── POST /v1/chat/completions  (OpenAI 格式)
│   └── GET  /v1/health
│
├── Claude Code 原生 API
│   ├── 会话管理: /api/sessions/*
│   ├── Agent 管理: /api/agents/*
│   ├── 斜杠命令: /api/sessions/{id}/commands/*, /api/commands
│   ├── 工具调用: /api/sessions/{id}/tools/*
│   ├── 文件管理: /api/sessions/{id}/files/*
│   ├── 高级功能: /api/sessions/{id}/thinking, /memory, /export
│   └── 实时通信: WebSocket, SSE
│
└── Web 管理界面
    ├── 静态文件: /admin/*
    ├── 管理 API: /admin/api/*
    └── WebSocket: /admin/ws/*
```

### 📡 **使用模式对比**

#### 模式1: 通过 LiteLLM 使用（生态集成）
```python
import openai
client = openai.OpenAI(base_url="http://litellm:4000/v1")
response = client.chat.completions.create(
    model="claude-code-sonnet",
    messages=[{"role": "user", "content": "Hello"}]
)
```

#### 模式2: 直接使用原生 API（完整功能）  
```python
import requests

# 创建会话
session = requests.post("http://gateway:8080/api/sessions", json={
    "agent": "general-purpose",
    "workspace": "/path/to/project"
}).json()

# 执行斜杠命令（如初始化项目）
requests.post(f"http://gateway:8080/api/sessions/{session['id']}/commands/init", json={
    "args": ["--project-type", "go"]
})

# 发送消息
response = requests.post(f"http://gateway:8080/api/sessions/{session['id']}/messages", json={
    "content": "分析这个项目的架构",
    "tools_enabled": ["search", "read", "bash"]
})
```

## 🎯 三阶段开发计划

### 第一阶段（2周）- LiteLLM Provider + 基础架构
- **F1.1-F1.2**: OpenAI 兼容端点完整实现
- **F1.4**: LiteLLM 集成验证和优化
- **基础设施**: CLI 调用封装、错误处理、日志系统
- **性能基准**: 达到基础性能要求

### 第二阶段（2.5周）- Claude Code 原生 API
- **F2.1**: 会话管理 API（创建、获取、删除、上下文）
- **F2.2**: Agent 管理 API（列表、切换、配置）
- **F2.3**: 斜杠命令 API（/init, /config, /clear, /reset等所有CLI命令）
- **F2.4**: 工具调用 API（search、bash、edit、read）
- **F2.5**: 文件和项目管理 API
- **F2.6**: 高级功能 API（thinking、记忆、导出、恢复）
- **F2.7**: 实时功能（WebSocket、SSE）

### 第三阶段（1.5周）- Web 管理界面 + 优化
- **F3.1-F3.2**: 实时决策可视化和代码生成追踪
- **F3.3**: 会话可视化管理界面
- **F3.4**: Agent 和工具管理界面
- **F3.5**: 系统监控仪表板
- **性能优化**: 达到 10ms P99 延迟目标
- **压力测试**: 验证并发能力

**总开发周期：6周**

## 🏆 验证标准

### 模块验收标准
- **F1 模块**: ✅ 通过 LiteLLM 官方兼容性测试，支持所有主流框架
- **F2 模块**: ✅ CLI 功能 100% API 化，所有操作可通过 API 完成
- **F3 模块**: ✅ 完整的可视化界面，实时监控和管理功能

### 性能验收标准  
- **API 延迟**: LiteLLM 模式 < 10ms, 原生 API < 5ms
- **并发能力**: > 10,000 并发连接稳定运行
- **资源效率**: 内存 < 100MB, CPU < 20% (空闲)

----

**核心理念：双模式设计，兼顾生态兼容和功能完整性**