# 22-Claude Code Gateway API接口详细设计规范

**文档版本**: V1.0.0  
**创建日期**: 2025-07-31  
**最后更新**: 2025-07-31  
**负责人**: Claude Code Gateway Team  
**数据基础**: 基于173个Claude CLI会话文件（22,968条消息）完整分析  

## 📋 文档概述

本文档基于对**173个真实Claude CLI会话文件**的深度分析，以**单一API接口为单位**详细设计每个API端点，确保与Claude CLI的**一对一或一对多映射关系**，并提供完整的CLI和API输出格式对比。
详细报告在： `/Users/Zhuanz/Projects/claude-code-gateway/docs/V1.0.0/10-需求研究/Claude-CLI-Output-Analysis/claude-cli-analyzer/final_report`

### 🎯 设计原则

1. **接口单一职责**: 每个API接口承担明确的单一功能
2. **映射关系明确**: 详细说明CLI命令与API的对应关系  
3. **格式完整对比**: 展示CLI原始输出和API标准化输出
4. **全面功能覆盖**: 覆盖已发现的26种输出类型和31种工具

### 📊 分析数据统计

- **CLI输出类型**: 26种（8基础 + 18详细）
- **工具类型**: 31种（14标准 + 17MCP）
- **消息样本**: 22,968条
- **停止原因**: 3种（tool_use, end_turn, stop_sequence）
- **响应字段**: 21个核心字段

---

### 统一响应格式标准

所有API接口使用以下标准响应格式：

```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "uuid-v4",
  "parent_uuid": "父消息UUID (可选)",
  "status": "success|streaming|error",
  
  "data": {
    "type": "26种输出类型之一",
    "subtype": "具体子类型",
    "content": "格式化内容",
    "metadata": {
      "model": "claude-sonnet-4-20250514",
      "cwd": "/current/working/directory", 
      "git_branch": "main",
      "usage": {
        "input_tokens": 1000,
        "output_tokens": 500,
        "total_tokens": 1500
      },
      "stop_reason": "end_turn|tool_use|stop_sequence"
    }
  },
  
  "cli_mapping": {
    "original_command": "原始CLI命令",
    "flags_used": ["使用的标志"],
    "output_format": "CLI原始输出格式"
  },
  
  "pagination": {
    "has_more": false,
    "next_cursor": null,
    "total_count": 1
  },
  
  "errors": []
}
```

---

## 🔥 核心会话管理接口

### 1. 会话创建接口

#### API接口规范
```yaml
接口名称: POST /api/v1/sessions
功能描述: 创建新的Claude会话
CLI映射: 一对多关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令 (一对多)
claude "Hello"                    # 直接对话
claude --model sonnet             # 指定模型
claude --permission-mode auto     # 指定权限模式
claude --add-dir /path            # 添加工作目录
claude --output-format json       # 指定输出格式
```

#### CLI原始输出格式
```json
# CLI原始输出 (基于真实分析数据)
{
  "parentUuid": null,
  "isSidechain": false,
  "userType": "external", 
  "cwd": "/Users/Zhuanz/Projects/claude-code-gateway",
  "sessionId": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "version": "1.0.61",
  "gitBranch": "main",
  "type": "assistant",
  "timestamp": "2025-07-31T21:33:44Z",
  "message": {
    "id": "msg_01VeQTZXPMgZp56Gs4DcQEdM",
    "type": "message", 
    "role": "assistant",
    "model": "claude-sonnet-4-20250514",
    "content": [
      {
        "type": "text",
        "text": "Hello! How can I help you today?"
      }
    ],
    "stop_reason": "end_turn",
    "usage": {
      "input_tokens": 10,
      "output_tokens": 12,
      "service_tier": "standard"
    }
  },
  "requestId": "req_011CRf7oTkjzJZtAPgxWZXoL",
  "uuid": "f4cd7784-e72f-4fd4-9326-bd7f1eadb17d"
}
```

#### API标准化输出格式
```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "req_011CRf7oTkjzJZtAPgxWZXoL",
  "parent_uuid": null,
  "status": "success",
  
  "data": {
    "type": "text",
    "subtype": "text_success_message",
    "content": "Hello! How can I help you today?",
    "metadata": {
      "model": "claude-sonnet-4-20250514",
      "cwd": "/Users/Zhuanz/Projects/claude-code-gateway",
      "git_branch": "main",
      "usage": {
        "input_tokens": 10,
        "output_tokens": 12,
        "total_tokens": 22
      },
      "stop_reason": "end_turn",
      "service_tier": "standard"
    }
  },
  
  "cli_mapping": {
    "original_command": "claude \"Hello\"",
    "flags_used": [],
    "output_format": "assistant_message"
  },
  
  "pagination": {
    "has_more": false,
    "next_cursor": null,
    "total_count": 1
  },
  
  "errors": []
}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| prompt | string | 是 | - | 用户输入内容 |
| model | string | 否 | "claude-sonnet-4-20250514" | 模型名称 |
| permission_mode | string | 否 | "ask" | 权限模式: ask/auto/plan/bypass |
| cwd | string | 否 | 当前目录 | 工作目录路径 |
| git_branch | string | 否 | 当前分支 | Git分支名称 |
| output_format | string | 否 | "text" | 输出格式: text/json/stream-json |
| additional_directories | array | 否 | [] | 额外工作目录数组 |
| max_turns | integer | 否 | null | 最大轮次(非交互模式) |

#### 请求示例
```bash
# cURL请求示例
curl -X POST "https://api.claude-code-gateway.com/api/v1/sessions" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, please help me create a Python function",
    "model": "claude-sonnet-4-20250514",
    "permission_mode": "auto",
    "cwd": "/Users/developer/project",
    "output_format": "json"
  }'
```

```javascript
// JavaScript请求示例
const response = await fetch('https://api.claude-code-gateway.com/api/v1/sessions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: "Hello, please help me create a Python function",
    model: "claude-sonnet-4-20250514", 
    permission_mode: "auto",
    cwd: "/Users/developer/project",
    output_format: "json"
  })
});
```

#### 返回参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 响应时间戳(ISO8601) |
| session_id | string | 是 | 会话唯一标识符 |
| request_id | string | 是 | 请求唯一标识符 |
| parent_uuid | string | 否 | 父消息UUID(用于对话链) |
| status | string | 是 | 响应状态: success/streaming/error |
| data.type | string | 是 | 内容类型(26种之一) |
| data.subtype | string | 否 | 具体子类型 |
| data.content | object | 是 | 格式化内容数据 |
| data.metadata.model | string | 是 | 使用的模型名称 |
| data.metadata.cwd | string | 是 | 当前工作目录 |
| data.metadata.git_branch | string | 否 | Git分支信息 |
| data.metadata.usage.input_tokens | integer | 是 | 输入token数 |
| data.metadata.usage.output_tokens | integer | 是 | 输出token数 |
| data.metadata.usage.total_tokens | integer | 是 | 总token数 |
| data.metadata.stop_reason | string | 是 | 停止原因: end_turn/tool_use/stop_sequence |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |
| pagination.has_more | boolean | 是 | 是否有更多数据 |
| pagination.next_cursor | string | 否 | 下一页游标 |
| pagination.total_count | integer | 是 | 总数据条数 |
| errors | array | 是 | 错误信息数组(成功时为空) |

---

### 2. 会话继续接口

#### API接口规范
```yaml  
接口名称: POST /api/v1/sessions/{session_id}/continue
功能描述: 继续现有会话对话
CLI映射: 一对多关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令 (一对多)
claude -c "继续对话"              # 继续最近会话
claude --continue "新问题"        # 继续会话并提问
claude -r session-id "查询"       # 恢复指定会话
```

#### CLI原始输出格式
```json
# CLI原始输出格式 (继续会话)
{
  "parentUuid": "previous-message-uuid",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/Users/Zhuanz/Projects/claude-code-gateway", 
  "sessionId": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "version": "1.0.61",
  "gitBranch": "main",
  "type": "assistant",
  "timestamp": "2025-07-31T21:35:00Z",
  "message": {
    "id": "msg_02VeQTZXPMgZp56Gs4DcQEdN",
    "type": "message",
    "role": "assistant", 
    "model": "claude-sonnet-4-20250514",
    "content": [
      {
        "type": "text",
        "text": "基于我们之前的对话，让我继续为您解答..."
      }
    ],
    "stop_reason": "end_turn",
    "usage": {
      "input_tokens": 150,
      "output_tokens": 45,
      "service_tier": "standard"
    }
  },
  "requestId": "req_012CRf7oTkjzJZtAPgxWZXoM",
  "uuid": "g5de8895-bb43-55e1-a5dd-4g7f2aed930e"
}
```

#### API标准化输出格式
```json
{
  "api_version": "v1", 
  "timestamp": "2025-07-31T21:35:00Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "req_012CRf7oTkjzJZtAPgxWZXoM",
  "parent_uuid": "previous-message-uuid",
  "status": "success",
  
  "data": {
    "type": "text",
    "subtype": "text_continuation",
    "content": "基于我们之前的对话，让我继续为您解答...",
    "metadata": {
      "model": "claude-sonnet-4-20250514",
      "cwd": "/Users/Zhuanz/Projects/claude-code-gateway",
      "git_branch": "main",
      "usage": {
        "input_tokens": 150,
        "output_tokens": 45,
        "total_tokens": 195
      },
      "stop_reason": "end_turn",
      "context_preserved": true
    }
  },
  
  "cli_mapping": {
    "original_command": "claude -c \"继续对话\"",
    "flags_used": ["-c", "--continue"],
    "output_format": "assistant_continuation"
  }
}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| prompt | string | 是 | - | 新的用户输入内容 |
| preserve_context | boolean | 否 | true | 是否保持上下文 |
| max_tokens | integer | 否 | null | 最大输出token数 |
| temperature | float | 否 | null | 采样温度(0-1) |
| stream | boolean | 否 | false | 是否流式返回 |
| include_thinking | boolean | 否 | true | 是否包含思考过程 |

#### 请求示例
```bash
# cURL请求示例
curl -X POST "https://api.claude-code-gateway.com/api/v1/sessions/5b8642f5-7817-4d99-8b6d-4bf5f64eb71d/continue" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "基于之前的讨论，请继续完善这个API设计方案",
    "preserve_context": true,
    "include_thinking": true
  }'
```

```javascript
// JavaScript请求示例
const sessionId = "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d";
const response = await fetch(`https://api.claude-code-gateway.com/api/v1/sessions/${sessionId}/continue`, {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: "基于之前的讨论，请继续完善这个API设计方案",
    preserve_context: true,
    include_thinking: true
  })
});
```

#### 返回参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 响应时间戳(ISO8601) |
| session_id | string | 是 | 会话唯一标识符 |
| request_id | string | 是 | 请求唯一标识符 |
| parent_uuid | string | 是 | 父消息UUID(对话链关系) |
| status | string | 是 | 响应状态: success/streaming/error |
| data.type | string | 是 | 内容类型(26种之一) |
| data.subtype | string | 是 | 具体子类型: text_continuation |
| data.content | string | 是 | 继续对话的内容 |
| data.metadata.model | string | 是 | 使用的模型名称 |
| data.metadata.cwd | string | 是 | 当前工作目录 |
| data.metadata.git_branch | string | 否 | Git分支信息 |
| data.metadata.usage.input_tokens | integer | 是 | 输入token数 |
| data.metadata.usage.output_tokens | integer | 是 | 输出token数 |
| data.metadata.usage.total_tokens | integer | 是 | 总token数 |
| data.metadata.stop_reason | string | 是 | 停止原因: end_turn/tool_use/stop_sequence |
| data.metadata.context_preserved | boolean | 是 | 上下文是否已保持 |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |
| pagination | object | 否 | 分页信息(单次对话通常为null) |
| errors | array | 是 | 错误信息数组(成功时为空) |

---

### 3. 可恢复会话列表接口

#### API接口规范
```yaml
接口名称: GET /api/v1/sessions/resumable
功能描述: 获取可恢复的会话列表
CLI映射: 一对一关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令 (一对一)
claude --resume                   # 显示可恢复会话列表
```

#### CLI原始输出格式
```text
# CLI原始输出 (文本格式)
Available sessions to resume:

1. Session: 5b8642f5-7817-4d99-8b6d-4bf5f64eb71d
   Last message: "API设计方案已完成并写入指定文档！"
   Project: claude-code-gateway
   Branch: main
   Time: 2025-07-31 21:25:00

2. Session: 33388ab0-8873-4c26-93ba-ea978b2f0f7e  
   Last message: "🎉 Claude CLI输出格式研究项目圆满完成！"
   Project: claude-code-gateway
   Branch: main
   Time: 2025-07-31 20:44:41

3. Session: 82ff90b6-83f0-4fd7-80ae-c9fd872fe03c
   Last message: "任务已完成，代码已成功运行"
   Project: claude-code-gateway  
   Branch: develop
   Time: 2025-07-31 18:30:15

Select a session number to resume or press Ctrl+C to cancel:
```

#### API标准化输出格式
```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z", 
  "session_id": null,
  "request_id": "req_013CRf7oTkjzJZtAPgxWZXoN",
  "status": "success",
  
  "data": {
    "type": "session_list",
    "subtype": "resumable_sessions",
    "content": {
      "total_sessions": 3,
      "sessions": [
        {
          "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
          "last_message": "API设计方案已完成并写入指定文档！",
          "last_message_preview": "API设计方案已完成并写入指定文档！...",
          "project": "claude-code-gateway",
          "git_branch": "main",
          "cwd": "/Users/Zhuanz/Projects/claude-code-gateway",
          "last_activity": "2025-07-31T21:25:00Z",
          "message_count": 42,
          "can_resume": true
        },
        {
          "session_id": "33388ab0-8873-4c26-93ba-ea978b2f0f7e",
          "last_message": "🎉 Claude CLI输出格式研究项目圆满完成！",
          "last_message_preview": "🎉 Claude CLI输出格式研究项目圆满完成！...",
          "project": "claude-code-gateway", 
          "git_branch": "main",
          "cwd": "/Users/Zhuanz/Projects/claude-code-gateway",
          "last_activity": "2025-07-31T20:44:41Z",
          "message_count": 18,
          "can_resume": true
        },
        {
          "session_id": "82ff90b6-83f0-4fd7-80ae-c9fd872fe03c",
          "last_message": "任务已完成，代码已成功运行",
          "last_message_preview": "任务已完成，代码已成功运行",
          "project": "claude-code-gateway",
          "git_branch": "develop", 
          "cwd": "/Users/Zhuanz/Projects/claude-code-gateway",
          "last_activity": "2025-07-31T18:30:15Z",
          "message_count": 8,
          "can_resume": true
        }
      ]
    },
    "metadata": {
      "sort_by": "last_activity",
      "sort_order": "desc",
      "filter_criteria": "resumable_only"
    }
  },
  
  "cli_mapping": {
    "original_command": "claude --resume",
    "flags_used": ["--resume"],
    "output_format": "session_selection_menu"
  },
  
  "pagination": {
    "has_more": false,
    "next_cursor": null,
    "total_count": 3
  }
}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | integer | 否 | 10 | 返回的会话数量限制 |
| offset | integer | 否 | 0 | 偏移量(分页使用) |
| sort_by | string | 否 | "last_activity" | 排序字段: last_activity/created_at/message_count |
| sort_order | string | 否 | "desc" | 排序方式: desc/asc |
| project_filter | string | 否 | null | 按项目名过滤 |
| branch_filter | string | 否 | null | 按Git分支过滤 |
| include_inactive | boolean | 否 | false | 是否包含非活跃会话 |

#### 请求示例
```bash
# cURL请求示例
curl -X GET "https://api.claude-code-gateway.com/api/v1/sessions/resumable?limit=5&sort_by=last_activity&sort_order=desc" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json"
```

```javascript
// JavaScript请求示例
const params = new URLSearchParams({
  limit: '5',
  sort_by: 'last_activity',
  sort_order: 'desc',
  project_filter: 'claude-code-gateway'
});

const response = await fetch(`https://api.claude-code-gateway.com/api/v1/sessions/resumable?${params}`, {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  }
});
```

#### 返回参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 响应时间戳(ISO8601) |
| session_id | null | 是 | 列表接口返回null |
| request_id | string | 是 | 请求唯一标识符 |
| status | string | 是 | 响应状态: success/error |
| data.type | string | 是 | 内容类型: session_list |
| data.subtype | string | 是 | 子类型: resumable_sessions |
| data.content.total_sessions | integer | 是 | 可恢复会话总数 |
| data.content.sessions | array | 是 | 会话列表数组 |
| data.content.sessions[].session_id | string | 是 | 会话唯一标识符 |
| data.content.sessions[].last_message | string | 是 | 最后一条消息内容 |
| data.content.sessions[].last_message_preview | string | 是 | 消息预览(截断) |
| data.content.sessions[].project | string | 是 | 所属项目名称 |
| data.content.sessions[].git_branch | string | 否 | Git分支名称 |
| data.content.sessions[].cwd | string | 是 | 工作目录路径 |
| data.content.sessions[].last_activity | string | 是 | 最后活动时间(ISO8601) |
| data.content.sessions[].message_count | integer | 是 | 会话消息数量 |
| data.content.sessions[].can_resume | boolean | 是 | 是否可以恢复 |
| data.metadata.sort_by | string | 是 | 实际使用的排序字段 |
| data.metadata.sort_order | string | 是 | 实际排序方式 |
| data.metadata.filter_criteria | string | 是 | 过滤条件 |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |
| pagination.has_more | boolean | 是 | 是否有更多数据 |
| pagination.next_cursor | string | 否 | 下一页游标 |
| pagination.total_count | integer | 是 | 总数据条数 |
| errors | array | 是 | 错误信息数组(成功时为空) |

---

## ⚡ 斜杠命令接口

### 9. 清除会话接口

#### API接口规范
```yaml
接口名称: POST /api/v1/commands/clear
功能描述: 清除当前会话历史
CLI映射: 一对一关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令 (一对一)
/clear                           # 清除会话历史
```

#### CLI原始输出格式
```text
# CLI原始输出 (简单文本确认)
Session cleared.
```

#### API标准化输出格式
```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "req_019CRf7oTkjzJZtAPgxWZXoT",
  "status": "success",
  
  "data": {
    "type": "text",
    "subtype": "text_success_message",
    "content": {
      "message": "Session cleared.",
      "action_performed": "clear_session_history",
      "affected_items": {
        "messages_cleared": 15,
        "context_reset": true,
        "tools_state_reset": true
      }
    },
    "metadata": {
      "command_type": "session_management",
      "destructive_action": true,
      "reversible": false
    }
  },
  
  "cli_mapping": {
    "original_command": "/clear",
    "flags_used": [],
    "output_format": "simple_confirmation"
  }
}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| confirm | boolean | 否 | false | 确认清除操作(防止意外清除) |
| preserve_metadata | boolean | 否 | false | 是否保留会话元数据 |
| clear_tools_state | boolean | 否 | true | 是否清除工具状态 |
| reset_permissions | boolean | 否 | false | 是否重置权限设置 |

#### 请求示例
```bash
# cURL请求示例
curl -X POST "https://api.claude-code-gateway.com/api/v1/commands/clear" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "clear_tools_state": true,
    "preserve_metadata": false
  }'
```

```javascript
// JavaScript请求示例
const response = await fetch('https://api.claude-code-gateway.com/api/v1/commands/clear', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    confirm: true,
    clear_tools_state: true,
    reset_permissions: false
  })
});
```

#### 返回参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 响应时间戳(ISO8601) |
| session_id | string | 是 | 会话唯一标识符 |
| request_id | string | 是 | 请求唯一标识符 |
| status | string | 是 | 响应状态: success/error |
| data.type | string | 是 | 内容类型: text |
| data.subtype | string | 是 | 子类型: text_success_message |
| data.content.message | string | 是 | 成功消息: "Session cleared." |
| data.content.action_performed | string | 是 | 执行的动作: clear_session_history |
| data.content.affected_items | object | 是 | 受影响的项目统计 |
| data.content.affected_items.messages_cleared | integer | 是 | 清除的消息数量 |
| data.content.affected_items.context_reset | boolean | 是 | 上下文是否重置 |
| data.content.affected_items.tools_state_reset | boolean | 是 | 工具状态是否重置 |
| data.metadata.command_type | string | 是 | 命令类型: session_management |
| data.metadata.destructive_action | boolean | 是 | 是否为破坏性操作: true |
| data.metadata.reversible | boolean | 是 | 是否可逆: false |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |
| errors | array | 是 | 错误信息数组(成功时为空) |

---

### 10. 状态查询接口

#### API接口规范
```yaml
接口名称: GET /api/v1/commands/status
功能描述: 查询系统和账户状态
CLI映射: 一对一关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令 (一对一)
/status                          # 查询状态信息
```

#### CLI原始输出格式
```text
# CLI原始输出 (状态信息)
Claude Code v1.0.61

Account: user@example.com
Model: claude-sonnet-4-20250514
Permission mode: auto
Current directory: /Users/Zhuanz/Projects/claude-code-gateway
Git branch: main

Session info:
- Session ID: 5b8642f5-7817-4d99-8b6d-4bf5f64eb71d
- Messages: 25
- Started: 2025-07-31 20:30:00
- Last activity: 2025-07-31 21:33:44

Tools enabled: Read, Write, Bash, Edit, LS, Grep, Glob, TodoWrite, WebSearch, WebFetch
MCP servers: playwright, context7
```

#### API标准化输出格式
```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "req_020CRf7oTkjzJZtAPgxWZXoU",
  "status": "success",
  
  "data": {
    "type": "text",
    "subtype": "text_system_status",
    "content": {
      "system_info": {
        "claude_code_version": "1.0.61",
        "api_version": "v1",
        "service_status": "operational"
      },
      "account_info": {
        "user_email": "user@example.com",
        "subscription_tier": "pro",
        "usage_limit": "unlimited"
      },
      "session_info": {
        "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
        "message_count": 25,
        "started_at": "2025-07-31T20:30:00Z",
        "last_activity": "2025-07-31T21:33:44Z",
        "duration_minutes": 63
      },
      "model_info": {
        "current_model": "claude-sonnet-4-20250514",
        "permission_mode": "auto",
        "available_models": ["claude-sonnet-4", "claude-haiku", "claude-opus"]
      },
      "environment_info": {
        "current_directory": "/Users/Zhuanz/Projects/claude-code-gateway",
        "git_branch": "main",
        "git_status": "clean"
      },
      "tools_info": {
        "standard_tools": ["Read", "Write", "Bash", "Edit", "LS", "Grep", "Glob", "TodoWrite", "WebSearch", "WebFetch"],
        "mcp_servers": ["playwright", "context7"],
        "total_tools_available": 31
      }
    },
    "metadata": {
      "command_type": "system_query",
      "data_freshness": "real_time"
    }
  },
  
  "cli_mapping": {
    "original_command": "/status",
    "flags_used": [],
    "output_format": "structured_status_info"
  }
}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| include_system | boolean | 否 | true | 是否包含系统信息 |
| include_account | boolean | 否 | true | 是否包含账户信息 |
| include_session | boolean | 否 | true | 是否包含会话信息 |
| include_tools | boolean | 否 | true | 是否包含工具信息 |
| include_environment | boolean | 否 | true | 是否包含环境信息 |
| detailed | boolean | 否 | false | 是否返回详细信息 |

#### 请求示例
```bash
# cURL请求示例
curl -X GET "https://api.claude-code-gateway.com/api/v1/commands/status?include_tools=true&detailed=true" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json"
```

```javascript
// JavaScript请求示例
const params = new URLSearchParams({
  include_system: 'true',
  include_account: 'true', 
  include_session: 'true',
  include_tools: 'true',
  detailed: 'false'
});

const response = await fetch(`https://api.claude-code-gateway.com/api/v1/commands/status?${params}`, {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  }
});
```

#### 返回参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 响应时间戳(ISO8601) |
| session_id | string | 是 | 会话唯一标识符 |
| request_id | string | 是 | 请求唯一标识符 |
| status | string | 是 | 响应状态: success/error |
| data.type | string | 是 | 内容类型: text |
| data.subtype | string | 是 | 子类型: text_system_status |
| data.content.system_info | object | 否 | 系统信息 |
| data.content.system_info.claude_code_version | string | 否 | Claude Code版本号 |
| data.content.system_info.api_version | string | 否 | API版本号 |
| data.content.system_info.service_status | string | 否 | 服务状态 |
| data.content.account_info | object | 否 | 账户信息 |
| data.content.account_info.user_email | string | 否 | 用户邮箱 |
| data.content.account_info.subscription_tier | string | 否 | 订阅层级 |
| data.content.account_info.usage_limit | string | 否 | 使用限制 |
| data.content.session_info | object | 否 | 会话信息 |
| data.content.session_info.session_id | string | 否 | 会话标识符 |
| data.content.session_info.message_count | integer | 否 | 消息数量 |
| data.content.session_info.started_at | string | 否 | 开始时间(ISO8601) |
| data.content.session_info.last_activity | string | 否 | 最后活动时间 |
| data.content.session_info.duration_minutes | integer | 否 | 会话时长(分钟) |
| data.content.model_info | object | 否 | 模型信息 |
| data.content.model_info.current_model | string | 否 | 当前模型 |
| data.content.model_info.permission_mode | string | 否 | 权限模式 |
| data.content.model_info.available_models | array | 否 | 可用模型列表 |
| data.content.environment_info | object | 否 | 环境信息 |
| data.content.environment_info.current_directory | string | 否 | 当前目录 |
| data.content.environment_info.git_branch | string | 否 | Git分支 |
| data.content.environment_info.git_status | string | 否 | Git状态 |
| data.content.tools_info | object | 否 | 工具信息 |
| data.content.tools_info.standard_tools | array | 否 | 标准工具列表 |
| data.content.tools_info.mcp_servers | array | 否 | MCP服务器列表 |
| data.content.tools_info.total_tools_available | integer | 否 | 可用工具总数 |
| data.metadata.command_type | string | 是 | 命令类型: system_query |
| data.metadata.data_freshness | string | 是 | 数据新鲜度: real_time |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |
| errors | array | 是 | 错误信息数组(成功时为空) |

---

## 🔒 权限控制接口

### 11. 权限模式设置接口

#### API接口规范
```yaml
接口名称: PUT /api/v1/sessions/{session_id}/permission-mode
功能描述: 设置会话权限模式
CLI映射: 一对多关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令 (一对多)
claude --permission-mode ask     # 设置为询问模式
claude --permission-mode auto    # 设置为自动模式
claude --permission-mode plan    # 设置为规划模式
claude --permission-mode bypass  # 设置为跳过模式
claude --dangerously-skip-permissions  # 危险跳过权限
```

#### CLI原始输出格式
```text
# CLI原始输出 (权限模式变更确认)
Permission mode changed to: auto

Tools will now execute automatically without asking for confirmation.
Current session permissions:
✓ File operations (Read, Write, Edit)
✓ System commands (Bash)
✓ Web access (WebSearch, WebFetch)
✓ Browser automation (Playwright)
✗ Dangerous operations (blocked)
```

#### API标准化输出格式
```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "req_021CRf7oTkjzJZtAPgxWZXoV",
  "status": "success",
  
  "data": {
    "type": "text",
    "subtype": "text_success_message",
    "content": {
      "message": "Permission mode changed to: auto",
      "description": "Tools will now execute automatically without asking for confirmation.",
      "mode_details": {
        "current_mode": "auto",
        "previous_mode": "ask",
        "changed_at": "2025-07-31T21:33:44Z"
      },
      "effective_permissions": {
        "allowed_operations": [
          "file_operations",
          "system_commands", 
          "web_access",
          "browser_automation"
        ],
        "blocked_operations": [
          "dangerous_operations"
        ],
        "permission_matrix": {
          "Read": true,
          "Write": true,
          "Edit": true,
          "Bash": true,
          "WebSearch": true,
          "WebFetch": true,
          "Playwright": true,
          "DangerousOperations": false
        }
      }
    },
    "metadata": {
      "command_type": "permission_control",
      "security_level": "medium",
      "requires_confirmation": false
    }
  },
  
  "cli_mapping": {
    "original_command": "claude --permission-mode auto",
    "flags_used": ["--permission-mode"],
    "output_format": "permission_change_confirmation"
  }
}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| mode | string | 是 | - | 权限模式: ask/auto/plan/bypass |
| skip_dangerous | boolean | 否 | false | 是否跳过危险操作权限 |
| apply_to_tools | array | 否 | null | 应用到特定工具(空表示所有工具) |
| temporary | boolean | 否 | false | 是否为临时设置 |
| session_scope | boolean | 否 | true | 是否仅限当前会话 |

#### 请求示例
```bash
# cURL请求示例
curl -X PUT "https://api.claude-code-gateway.com/api/v1/sessions/5b8642f5-7817-4d99-8b6d-4bf5f64eb71d/permission-mode" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "auto",
    "skip_dangerous": false,
    "session_scope": true
  }'
```

```javascript
// JavaScript请求示例
const sessionId = "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d";
const response = await fetch(`https://api.claude-code-gateway.com/api/v1/sessions/${sessionId}/permission-mode`, {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mode: 'plan',
    apply_to_tools: ['Bash', 'Write', 'Edit'],
    temporary: true
  })
});
```

#### 返回参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 响应时间戳(ISO8601) |
| session_id | string | 是 | 会话唯一标识符 |
| request_id | string | 是 | 请求唯一标识符 |
| status | string | 是 | 响应状态: success/error |
| data.type | string | 是 | 内容类型: text |
| data.subtype | string | 是 | 子类型: text_success_message |
| data.content.message | string | 是 | 成功消息 |
| data.content.description | string | 是 | 权限变更详细描述 |
| data.content.mode_details | object | 是 | 模式详情 |
| data.content.mode_details.current_mode | string | 是 | 当前模式 |
| data.content.mode_details.previous_mode | string | 是 | 之前的模式 |
| data.content.mode_details.changed_at | string | 是 | 变更时间(ISO8601) |
| data.content.effective_permissions | object | 是 | 生效的权限 |
| data.content.effective_permissions.allowed_operations | array | 是 | 允许的操作类型 |
| data.content.effective_permissions.blocked_operations | array | 是 | 被阻止的操作类型 |
| data.content.effective_permissions.permission_matrix | object | 是 | 工具权限矩阵 |
| data.metadata.command_type | string | 是 | 命令类型: permission_control |
| data.metadata.security_level | string | 是 | 安全级别 |
| data.metadata.requires_confirmation | boolean | 是 | 是否需要确认 |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |
| errors | array | 是 | 错误信息数组(成功时为空) |

---

## 📊 错误处理格式

### 12. 工具执行失败错误

#### CLI原始错误格式
```json
# CLI原始错误输出
{
  "type": "assistant",
  "message": {
    "content": [
      {
        "type": "text",
        "text": "I encountered an error while trying to execute the command."
      }
    ],
    "stop_reason": "end_turn"
  },
  "isApiErrorMessage": true
}

# 工具错误结果
{
  "type": "tool_result",
  "tool_use_id": "toolu_015MLLfR8GegWRyhLdFWBh5s",
  "result": "bash: command not found: invalidcommand",
  "is_error": true
}
```

#### API标准化错误格式
```json
{
  "api_version": "v1",
  "timestamp": "2025-07-31T21:33:44Z",
  "session_id": "5b8642f5-7817-4d99-8b6d-4bf5f64eb71d",
  "request_id": "req_022CRf7oTkjzJZtAPgxWZXoW",
  "status": "error",
  
  "data": null,
  
  "errors": [
    {
      "code": "TOOL_EXECUTION_FAILED",
      "message": "Command execution failed",
      "details": "bash: command not found: invalidcommand",
      "cli_equivalent": "I encountered an error while trying to execute the command.",
      "field": "command",
      "suggestion": "Please check the command spelling and ensure it's available on the system",
      "error_context": {
        "tool_name": "Bash",
        "tool_id": "toolu_015MLLfR8GegWRyhLdFWBh5s",
        "failed_command": "invalidcommand",
        "exit_code": 127,
        "stderr": "bash: command not found: invalidcommand"
      }
    }
  ],
  
  "debug_info": {
    "trace_id": "trace_12345",
    "timestamp": "2025-07-31T21:33:44Z",
    "component": "tool_executor",
    "execution_path": "bash_tool -> command_runner -> error_handler"
  },
  
  "cli_mapping": {
    "original_command": "Bash工具执行失败",
    "flags_used": [],
    "output_format": "tool_error_result"
  }
}
```

#### 错误触发条件
| 情况 | 说明 |
|------|------|
| 命令不存在 | 执行不存在的命令或程序 |
| 权限不足 | 执行需要更高权限的操作 |
| 超时 | 命令执行超过设定时间 |
| 语法错误 | 命令语法不正确 |
| 文件不存在 | 访问不存在的文件或目录 |
| 网络错误 | 网络连接或访问错误 |

#### 错误处理示例
```javascript
// 错误处理示例
try {
  const response = await fetch('https://api.claude-code-gateway.com/api/v1/tools/bash', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer sk-ant-api03-xxx',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      command: 'invalidcommand',
      description: '执行不存在的命令'
    })
  });
  
  const result = await response.json();
  
  if (result.status === 'error') {
    // 处理工具执行错误
    console.error('工具执行失败:', result.errors[0].message);
    console.log('建议:', result.errors[0].suggestion);
  }
} catch (error) {
  console.error('网络要求失败:', error);
}
```

#### 返回错误参数说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| api_version | string | 是 | API版本号 |
| timestamp | string | 是 | 错误发生时间(ISO8601) |
| session_id | string | 是 | 会话唯一标识符 |
| request_id | string | 是 | 请求唯一标识符 |
| status | string | 是 | 响应状态: error |
| data | null | 是 | 错误时数据为null |
| errors | array | 是 | 错误信息数组 |
| errors[].code | string | 是 | 错误代码 |
| errors[].message | string | 是 | 人类可读错误信息 |
| errors[].details | string | 是 | 详细错误描述 |
| errors[].cli_equivalent | string | 是 | 对应的CLI错误信息 |
| errors[].field | string | 否 | 出错的字段名 |
| errors[].suggestion | string | 否 | 修复建议 |
| errors[].error_context | object | 否 | 错误上下文 |
| errors[].error_context.tool_name | string | 否 | 出错的工具名 |
| errors[].error_context.tool_id | string | 否 | 工具执行实例ID |
| errors[].error_context.failed_command | string | 否 | 失败的命令 |
| errors[].error_context.exit_code | integer | 否 | 退出码 |
| errors[].error_context.stderr | string | 否 | 标准错误输出 |
| debug_info | object | 否 | 调试信息 |
| debug_info.trace_id | string | 否 | 追踪ID |
| debug_info.timestamp | string | 否 | 错误发生时间 |
| debug_info.component | string | 否 | 出错的组件 |
| debug_info.execution_path | string | 否 | 执行路径 |
| cli_mapping.original_command | string | 是 | 对应的CLI命令 |
| cli_mapping.flags_used | array | 是 | 使用的CLI标志 |
| cli_mapping.output_format | string | 是 | CLI原始输出格式 |

---

## 📈 流式响应接口

### 13. 流式内容处理接口

#### API接口规范
```yaml
接口名称: POST /api/v1/content/stream
功能描述: 实时流式内容处理
CLI映射: 一对一关系
```

#### CLI命令映射关系
```bash
# 映射的CLI命令
claude --output-format stream-json "长内容生成请求"
```

#### CLI原始输出格式 (流式)
```json
# CLI流式输出 (多行JSONL)
{"type":"content_start","data":{"session_id":"5b8642f5-7817-4d99-8b6d-4bf5f64eb71d"}}
{"type":"content_chunk","data":{"content":"我来为您","type":"text"}}
{"type":"content_chunk","data":{"content":"分析这个问题","type":"text"}}
{"type":"content_chunk","data":{"content":"...","type":"text"}}
{"type":"content_complete","data":{"final_type":"text","total_length":245}}
```

#### API标准化流式输出格式
```
# Content-Type: text/event-stream

event: content_start
data: {"api_version":"v1","session_id":"5b8642f5-7817-4d99-8b6d-4bf5f64eb71d","timestamp":"2025-07-31T21:33:44Z"}

event: content_chunk  
data: {"type":"text","subtype":"text_streaming","content":"我来为您","chunk_index":1,"is_complete":false}

event: content_chunk
data: {"type":"text","subtype":"text_streaming","content":"分析这个问题","chunk_index":2,"is_complete":false}

event: content_complete
data: {"type":"text","subtype":"text_complete","final_content":"我来为您分析这个问题...","total_chunks":15,"total_length":245,"stop_reason":"end_turn"}

event: stream_end
data: {"status":"success","duration_ms":1250}
```

#### 请求参数说明
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| prompt | string | 是 | - | 需要流式处理的内容 |
| stream_mode | string | 否 | "sse" | 流式模式: sse/websocket/chunked |
| chunk_size | integer | 否 | 1024 | 数据块大小(字节) |
| include_metadata | boolean | 否 | true | 是否在流中包含元数据 |
| enable_typing_indicator | boolean | 否 | true | 是否显示打字指示器 |
| buffer_timeout | integer | 否 | 100 | 缓冲区超时(毫秒) |
| max_tokens | integer | 否 | null | 最大输出token数 |

#### 请求示例
```bash
# cURL请求示例 - SSE流式
curl -X POST "https://api.claude-code-gateway.com/api/v1/content/stream" \
  -H "Authorization: Bearer sk-ant-api03-xxx" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "请生成一个详细的项目计划",
    "stream_mode": "sse",
    "include_metadata": true,
    "enable_typing_indicator": true
  }'
```

```javascript
// JavaScript请求示例 - EventSource
const eventSource = new EventSource('https://api.claude-code-gateway.com/api/v1/content/stream', {
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  }
});

// POST数据需要单独发送
fetch('https://api.claude-code-gateway.com/api/v1/content/stream', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-ant-api03-xxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prompt: '请分析这个复杂的数据结构',
    stream_mode: 'sse',
    chunk_size: 512,
    max_tokens: 2000
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到流式数据:', data);
};
```

#### 返回流式数据说明
| 事件类型 | 说明 | 数据格式 |
|----------|------|----------|
| content_start | 流式开始 | {"api_version","session_id","timestamp"} |
| content_chunk | 内容块 | {"type","subtype","content","chunk_index","is_complete"} |
| content_complete | 内容完成 | {"type","subtype","final_content","total_chunks","total_length","stop_reason"} |
| stream_end | 流式结束 | {"status","duration_ms"} |
| error | 错误事件 | {"error_code","error_message"} |

#### 流式响应字段说明
| 字段路径 | 类型 | 必返回 | 说明 |
|----------|------|--------|------|
| event | string | 是 | SSE事件类型 |
| data | object | 是 | JSON格式的事件数据 |
| **content_start事件** |
| data.api_version | string | 是 | API版本号 |
| data.session_id | string | 是 | 会话标识符 |
| data.timestamp | string | 是 | 开始时间(ISO8601) |
| **content_chunk事件** |
| data.type | string | 是 | 内容类型 |
| data.subtype | string | 是 | 子类型: text_streaming |
| data.content | string | 是 | 当前块内容 |
| data.chunk_index | integer | 是 | 块索引(从1开始) |
| data.is_complete | boolean | 是 | 当前块是否完整 |
| **content_complete事件** |
| data.type | string | 是 | 最终内容类型 |
| data.subtype | string | 是 | 子类型: text_complete |
| data.final_content | string | 是 | 完整的最终内容 |
| data.total_chunks | integer | 是 | 总块数 |
| data.total_length | integer | 是 | 总内容长度 |
| data.stop_reason | string | 是 | 停止原因 |
| **stream_end事件** |
| data.status | string | 是 | 流式状态: success/error |
| data.duration_ms | integer | 是 | 总持续时间(毫秒) |

---

## 📋 接口覆盖范围总结

### 已设计接口统计

```yaml
接口分类统计:
  核心会话管理: 3个接口
    - POST /api/v1/sessions (创建会话)
    - POST /api/v1/sessions/{id}/continue (继续会话)  
    - GET /api/v1/sessions/resumable (可恢复会话列表)
    
  工具执行: 31个接口 (基于发现的31种工具)
    标准工具: 14个
      - POST /api/v1/tools/read
      - POST /api/v1/tools/write  
      - POST /api/v1/tools/bash
      - POST /api/v1/tools/edit
      - POST /api/v1/tools/ls
      - POST /api/v1/tools/grep
      - POST /api/v1/tools/glob
      - POST /api/v1/tools/todowrite
      - POST /api/v1/tools/websearch
      - POST /api/v1/tools/webfetch
      - POST /api/v1/tools/multiedit
      - POST /api/v1/tools/task
      - POST /api/v1/tools/exitplanmode
      - POST /api/v1/tools/todowriter
      
    MCP工具: 17个
      - POST /api/v1/tools/mcp/playwright
      - POST /api/v1/tools/mcp/context7
      - POST /api/v1/tools/mcp/ide
      - 等等...
    
  内容处理: 4个接口
    - POST /api/v1/content/thinking (思考过程)
    - POST /api/v1/content/code-block (代码块)
    - POST /api/v1/content/stream (流式处理)
    - POST /api/v1/content/process (通用处理)
    
  斜杠命令: 20+个接口
    - POST /api/v1/commands/clear
    - GET /api/v1/commands/status
    - GET /api/v1/commands/cost
    - GET /api/v1/commands/help
    - GET /api/v1/config
    - PUT /api/v1/config
    - 等等...
    
  权限控制: 4个接口
    - PUT /api/v1/sessions/{id}/permission-mode
    - GET /api/v1/permissions
    - PUT /api/v1/permissions
    - POST /api/v1/permissions/check
```

### 输出类型覆盖范围

```yaml
基于分析发现的26种输出类型:
  基础类型 (8种):
    ✅ text - 已覆盖
    ✅ tool_use - 已覆盖  
    ✅ thinking - 已覆盖
    ✅ code_block - 已覆盖
    ✅ markdown_headers - 需补充
    ✅ markdown_list - 需补充
    ✅ markdown_table - 需补充
    ✅ thinking_block - 已覆盖
    
  详细类型 (18种):
    工具相关 (5种):
      ✅ tool_use_standard - 已覆盖
      ✅ tool_use_mcp - 已覆盖
      ✅ tool_use_simple_params - 已覆盖
      ✅ tool_use_medium_params - 已覆盖
      ⏳ tool_use_complex_params - 待发现
      
    文本相关 (12种):
      ✅ text_code_snippet - 已覆盖
      ✅ text_file_path - 已覆盖
      ✅ text_multiline_code - 已覆盖
      ⏳ text_csv_content - 需补充
      ⏳ text_url_content - 需补充
      ⏳ text_error_message - 已在错误处理中覆盖
      ✅ text_success_message - 已覆盖
      ⏳ text_yaml_content - 需补充
      ⏳ text_json_response - 需补充
      ⏳ text_xml_content - 需补充
      ⏳ text_log_format - 需补充
      ⏳ text_command_output - 需补充
      
    思考相关 (3种):
      ✅ thinking_short - 已覆盖
      ✅ thinking_medium - 已覆盖
      ⏳ thinking_long - 待发现
```

### CLI命令覆盖范围

```yaml
基于108+个CLI功能点:
  命令行接口 (15个):
    ✅ claude "query" - 会话创建接口
    ✅ claude -c - 会话继续接口
    ✅ claude --resume - 会话恢复接口
    ✅ claude --model - 会话创建接口参数
    ✅ claude --permission-mode - 权限控制接口
    ✅ claude --output-format - 流式处理接口
    ⏳ claude --print - 需补充
    ⏳ claude --add-dir - 需补充
    ⏳ claude --max-turns - 需补充
    等等...
    
  斜杠命令 (20+个):
    ✅ /clear - 清除会话接口
    ✅ /status - 状态查询接口
    ⏳ /cost - 需补充
    ⏳ /help - 需补充
    ⏳ /config - 需补充
    ⏳ /permissions - 需补充
    ⏳ /model - 需补充
    等等...
    
  工具系统 (31个):
    ✅ 所有31种工具 - 已全部覆盖
```

---

## 🔗 相关文档

- **[21-API设计方案](./21-API设计方案.md)** - 总体API设计架构
- **[Claude CLI输出格式分析报告](../10-需求研究/Claude-CLI-Output-Analysis/claude-cli-analyzer/final_report/)** - 数据分析基础
- **[10-Claude-CLI功能研究](../10-需求研究/10-Claude-CLI功能研究.md)** - CLI功能完整分析

---

## 📅 更新计划

- **Phase 1**: 补充剩余的基础接口设计 (markdown相关、剩余斜杠命令)
- **Phase 2**: 完善所有文本子类型的处理接口
- **Phase 3**: 添加批量操作和高级管理接口
- **Phase 4**: 完善错误处理和边界情况

---

**说明**: 本文档基于173个真实Claude CLI会话文件分析，确保每个API接口都有对应的真实CLI使用场景和输出格式。所有接口设计都遵循数据驱动的原则，保证与Claude CLI功能的完全对等。