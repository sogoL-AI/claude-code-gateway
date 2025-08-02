# Claude Code API 响应格式规范

## 🎯 设计原则

1. **一致性** - 所有 API 响应使用统一的格式结构
2. **可预测性** - 开发者可以可靠地解析所有响应
3. **完整性** - 包含足够的元数据用于调试和监控
4. **向后兼容** - 支持格式版本化和平滑升级
5. **类型安全** - 明确的字段类型定义

---

## 📋 标准响应格式

### 基础响应结构

```typescript
interface BaseResponse {
  // 响应元数据
  meta: {
    request_id: string;           // 唯一请求标识
    timestamp: string;            // ISO 8601 时间戳
    version: string;              // API 版本
    session_id?: string;          // 会话 ID（如适用）
    execution_time_ms: number;    // 执行时间（毫秒）
  };
  
  // 响应状态
  status: 'success' | 'error' | 'pending' | 'partial';
  
  // 主要数据载荷
  data?: any;
  
  // 错误信息（仅当 status = 'error'）
  error?: ErrorDetail;
  
  // 警告信息（可选）
  warnings?: Warning[];
  
  // 额外的上下文信息
  context?: ResponseContext;
}
```

### 错误详情结构

```typescript
interface ErrorDetail {
  code: string;                 // 错误代码
  message: string;              // 用户友好的错误消息
  details?: string;             // 详细错误信息
  suggestion?: string;          // 解决建议
  cli_error?: {                 // 原始 CLI 错误（如果适用）
    exit_code: number;
    stderr: string;
    stdout: string;
  };
}
```

### 警告结构

```typescript
interface Warning {
  code: string;                 // 警告代码
  message: string;              // 警告消息
  severity: 'low' | 'medium' | 'high';
}
```

### 响应上下文

```typescript
interface ResponseContext {
  permission_mode?: string;     // 当前权限模式
  tools_used?: string[];        // 使用的工具列表
  files_accessed?: string[];    // 访问的文件列表
  execution_plan_id?: string;   // 执行计划 ID（如果适用）
  thinking_blocks?: ThinkingBlock[]; // 思考过程（如果适用）
}
```

---

## 🎭 响应类型分类

### 1. 简单查询响应

**场景**: 普通的对话查询，无工具调用

```json
{
  "meta": {
    "request_id": "req_1234567890",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "execution_time_ms": 1500
  },
  "status": "success",
  "data": {
    "type": "completion",
    "content": "这是一个简单的回答...",
    "content_type": "text/plain",
    "model": "claude-3-5-sonnet",
    "usage": {
      "input_tokens": 50,
      "output_tokens": 120,
      "total_tokens": 170
    }
  },
  "context": {
    "permission_mode": "auto"
  }
}
```

### 2. 工具调用响应

**场景**: 涉及工具使用的复杂查询

```json
{
  "meta": {
    "request_id": "req_1234567891",
    "timestamp": "2024-01-15T10:31:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "execution_time_ms": 3200
  },
  "status": "success",
  "data": {
    "type": "tool_completion",
    "content": "我已经分析了你的项目结构...",
    "content_type": "text/markdown",
    "tool_calls": [
      {
        "tool": "read",
        "parameters": {
          "file_path": "package.json"
        },
        "result": {
          "success": true,
          "content": "{\n  \"name\": \"my-project\"...",
          "execution_time_ms": 150
        }
      },
      {
        "tool": "bash",
        "parameters": {
          "command": "find . -name '*.js' | wc -l"
        },
        "result": {
          "success": true,
          "stdout": "23\n",
          "stderr": "",
          "exit_code": 0,
          "execution_time_ms": 200
        }
      }
    ],
    "model": "claude-3-5-sonnet",
    "usage": {
      "input_tokens": 200,
      "output_tokens": 350,
      "total_tokens": 550
    }
  },
  "context": {
    "permission_mode": "auto",
    "tools_used": ["read", "bash"],
    "files_accessed": ["package.json"]
  }
}
```

### 3. 权限请求响应

**场景**: Ask 模式下需要权限确认

```json
{
  "meta": {
    "request_id": "req_1234567892",
    "timestamp": "2024-01-15T10:32:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "execution_time_ms": 800
  },
  "status": "pending",
  "data": {
    "type": "permission_request",
    "message": "我需要执行以下操作，请确认：",
    "pending_actions": [
      {
        "id": "action_001",
        "tool": "edit",
        "parameters": {
          "file_path": "src/main.js",
          "operation": "modify"
        },
        "description": "修改 main.js 文件中的配置",
        "risk_level": "medium",
        "estimated_changes": 5
      }
    ],
    "approval_endpoint": "/api/sessions/sess_abc123/approve",
    "expires_at": "2024-01-15T10:37:00Z"
  },
  "context": {
    "permission_mode": "ask"
  }
}
```

### 4. 执行计划响应

**场景**: Plan 模式下生成的执行计划

```json
{
  "meta": {
    "request_id": "req_1234567893",
    "timestamp": "2024-01-15T10:33:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "execution_time_ms": 2100
  },
  "status": "success",
  "data": {
    "type": "execution_plan",
    "plan_id": "plan_xyz789",
    "title": "重构用户认证模块",
    "description": "基于当前代码结构，我建议按以下步骤重构...",
    "steps": [
      {
        "order": 1,
        "title": "分析现有代码结构",
        "actions": [
          {
            "tool": "read",
            "target": "src/auth.js",
            "reasoning": "了解当前认证实现"
          },
          {
            "tool": "grep",
            "pattern": "function.*auth",
            "target": "src/",
            "reasoning": "查找所有认证相关函数"
          }
        ]
      },
      {
        "order": 2,
        "title": "创建新的认证模块",
        "actions": [
          {
            "tool": "write",
            "target": "src/auth/index.js",
            "reasoning": "创建模块化的认证入口"
          }
        ]
      }
    ],
    "estimated_impact": {
      "files_modified": 5,
      "files_created": 3,
      "risk_level": "medium",
      "estimated_time": "30-45 minutes"
    },
    "execution_endpoint": "/api/sessions/sess_abc123/execute-plan/plan_xyz789"
  },
  "context": {
    "permission_mode": "plan"
  }
}
```

### 5. 思考过程响应

**场景**: 扩展思考模式的响应

```json
{
  "meta": {
    "request_id": "req_1234567894",
    "timestamp": "2024-01-15T10:34:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "execution_time_ms": 4500
  },
  "status": "success",
  "data": {
    "type": "thinking_completion",
    "content": "基于深入分析，我推荐以下架构方案...",
    "content_type": "text/markdown",
    "thinking_process": {
      "enabled": true,
      "blocks": [
        {
          "step": "analysis",
          "title": "问题分析",
          "content": "让我仔细分析这个架构需求...",
          "reasoning": "需要考虑可扩展性、性能和维护性",
          "duration_ms": 1200
        },
        {
          "step": "evaluation",
          "title": "方案评估", 
          "content": "比较几种可能的架构方案...",
          "reasoning": "权衡各种架构的优缺点",
          "duration_ms": 1800
        },
        {
          "step": "recommendation",
          "title": "最终建议",
          "content": "综合考虑，我建议采用微服务架构...",
          "reasoning": "最符合项目的长期发展需求",
          "duration_ms": 900
        }
      ]
    },
    "confidence": 0.85
  },
  "context": {
    "thinking_level": "extended"
  }
}
```

### 6. 错误响应

**场景**: 各种错误情况

```json
{
  "meta": {
    "request_id": "req_1234567895",
    "timestamp": "2024-01-15T10:35:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "execution_time_ms": 500
  },
  "status": "error",
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "无法找到指定的文件",
    "details": "文件 'config.json' 在当前工作目录中不存在",
    "suggestion": "请检查文件路径是否正确，或使用 'ls' 命令查看可用文件",
    "cli_error": {
      "exit_code": 1,
      "stderr": "Error: ENOENT: no such file or directory, open 'config.json'",
      "stdout": ""
    }
  },
  "context": {
    "permission_mode": "auto",
    "tools_used": ["read"]
  }
}
```

### 7. 流式响应

**场景**: 长时间运行的操作，需要实时反馈

```json
{
  "meta": {
    "request_id": "req_1234567896",
    "timestamp": "2024-01-15T10:36:00Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "stream": true
  },
  "status": "partial",
  "data": {
    "type": "stream_chunk",
    "chunk_id": 1,
    "content": "正在分析项目结构...",
    "is_final": false
  }
}

// 最后一个流式响应
{
  "meta": {
    "request_id": "req_1234567896",
    "timestamp": "2024-01-15T10:36:30Z",
    "version": "1.0.0",
    "session_id": "sess_abc123",
    "stream": true,
    "execution_time_ms": 30000
  },
  "status": "success",
  "data": {
    "type": "stream_final",
    "chunk_id": 15,
    "content": "分析完成！项目包含...",
    "is_final": true,
    "summary": {
      "total_chunks": 15,
      "tools_used": ["read", "bash", "grep"],
      "files_analyzed": 42
    }
  }
}
```

---

## 📊 错误代码规范

### CLI 相关错误 (1000-1999)
- `1001 CLI_NOT_FOUND` - Claude CLI 未安装或不可用
- `1002 CLI_EXECUTION_FAILED` - CLI 命令执行失败  
- `1003 CLI_TIMEOUT` - CLI 命令执行超时
- `1004 CLI_PERMISSION_DENIED` - CLI 权限不足

### 文件系统错误 (2000-2999)
- `2001 FILE_NOT_FOUND` - 文件不存在
- `2002 DIRECTORY_NOT_FOUND` - 目录不存在
- `2003 PERMISSION_DENIED` - 文件权限不足
- `2004 FILE_TOO_LARGE` - 文件过大

### 权限和安全错误 (3000-3999)
- `3001 PERMISSION_REQUIRED` - 需要用户权限确认
- `3002 PERMISSION_DENIED` - 权限被拒绝
- `3003 PERMISSION_EXPIRED` - 权限请求过期
- `3004 UNSAFE_OPERATION` - 不安全的操作

### 会话管理错误 (4000-4999)
- `4001 SESSION_NOT_FOUND` - 会话不存在
- `4002 SESSION_EXPIRED` - 会话已过期
- `4003 SESSION_LIMIT_EXCEEDED` - 会话数量超限
- `4004 INVALID_SESSION_STATE` - 会话状态无效

### API 相关错误 (5000-5999)  
- `5001 INVALID_REQUEST` - 无效的请求格式
- `5002 MISSING_PARAMETER` - 缺少必需参数
- `5003 INVALID_PARAMETER` - 参数值无效
- `5004 RATE_LIMIT_EXCEEDED` - 请求频率超限

---

## 🔧 解析和转换规则

### CLI Text 格式解析

```typescript
interface TextParser {
  parseSimpleResponse(text: string): SimpleResponse;
  parseToolOutput(text: string): ToolCallResponse;
  parseError(text: string, exitCode: number): ErrorResponse;
  parseThinking(text: string): ThinkingResponse;
}
```

### CLI JSON 格式解析

```typescript
interface JsonParser {
  validateSchema(json: any): boolean;
  transformToStandard(json: any): BaseResponse;
  extractMetadata(json: any): ResponseMeta;
  handleMalformed(json: string): ErrorResponse;
}
```

### 流式格式处理

```typescript
interface StreamParser {
  processChunk(chunk: string): StreamChunk;
  assembleComplete(chunks: StreamChunk[]): CompleteResponse;
  handleStreamError(error: any): ErrorResponse;
}
```

---

## 📋 实现检查清单

### 基础实现
- [ ] 定义 TypeScript 接口
- [ ] 实现响应构建器
- [ ] 创建错误处理器
- [ ] 建立格式验证器

### 解析器实现
- [ ] CLI Text 输出解析器
- [ ] CLI JSON 输出解析器  
- [ ] CLI Stream 输出解析器
- [ ] 错误输出解析器

### 转换器实现
- [ ] 标准格式转换器
- [ ] 元数据提取器
- [ ] 上下文信息构建器
- [ ] 类型安全验证器

### 测试覆盖
- [ ] 单元测试覆盖所有响应类型
- [ ] 集成测试覆盖解析流程
- [ ] 错误场景测试
- [ ] 性能基准测试

---

这个规范将确保 Claude Code Gateway 提供一致、可预测和开发者友好的 API 响应格式！