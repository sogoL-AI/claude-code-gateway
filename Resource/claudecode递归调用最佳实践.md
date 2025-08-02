
<claude_cli_best_practices>

## Claude CLI递归调用最佳实践

在Claude Code内部调用Claude CLI的实用指南 - 基于实际测试验证。

### 🎯 核心调用模式

#### 1. 基础Session获取 ✅
```bash
# 获取session ID
SESSION=$(echo "你的问题" | claude --output-format json | jq -r .session_id)
echo "Session ID: $SESSION"

# 完整JSON信息
echo "分析项目结构" | claude --output-format json | jq .
```

**实测结果示例：**
```json
{
  "session_id": "a2b71185-b90a-4311-b868-5b58b8ab4b9e",
  "result": "项目分析结果...",
  "total_cost_usd": 0.0279034,
  "duration_ms": 25015
}
```

#### 2. Session传递模式 ⚠️
```bash
# 第一轮调用
SESSION=$(echo "分析CC-Toolkit项目结构" | claude --output-format json | jq -r .session_id)

# 基于session继续对话
echo "基于刚才的分析，请具体说明..." | claude --resume $SESSION
```

**注意：** Resume功能有时不稳定，建议在prompt中包含必要上下文。

#### 3. Debug模式调用 ✅
```bash
# 获取详细调试信息
echo "检查项目优化点" | claude --debug 2>&1 | head -20

# 调试输出包含：
# [DEBUG] Session创建信息
# [DEBUG] Hook执行状态
# [DEBUG] 文件操作记录
```

### 📋 实用调用规范

#### 基本原则
1. **优先使用JSON输出** - 获取结构化数据和session ID
2. **Debug模式仅调试时用** - 输出冗长，仅必要时启用
3. **Session传递需验证** - 检查resume是否成功
4. **设置超时保护** - 防止长时间等待

#### 标准工作流
```bash
#!/bin/bash
# claude_workflow.sh

# 1. 主任务调用
echo "分析当前项目" | claude --output-format json > analysis.json
SESSION=$(jq -r .session_id analysis.json)
RESULT=$(jq -r .result analysis.json)

# 2. 验证结果
if [[ -n "$SESSION" && "$SESSION" != "null" ]]; then
    echo "✅ Session获取成功: $SESSION"
    
    # 3. 后续调用
    echo "基于分析结果，提供优化建议" | claude --resume $SESSION
else
    echo "❌ Session获取失败，使用独立调用"
    echo "请提供优化建议" | claude --output-format json
fi
```

#### 错误处理
```bash
# 安全调用函数
safe_claude_call() {
    local prompt="$1"
    local max_retries=3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if result=$(echo "$prompt" | claude --output-format json 2>/dev/null); then
            echo "$result"
            return 0
        else
            ((retry++))
            echo "重试 $retry/$max_retries..." >&2
            sleep 2
        fi
    done
    
    echo "调用失败，回退到debug模式" >&2
    echo "$prompt" | claude --debug
}
```

### 🧪 实测案例

#### 案例1：项目分析
```bash
# 实际测试命令
SESSION=$(echo "分析CC-Toolkit项目的prompts目录结构" | claude --output-format json | jq -r .session_id)
# 结果：a2b71185-b90a-4311-b868-5b58b8ab4b9e

# 继续分析
echo "基于刚才的分析，请具体说明每个XML文件的作用" | claude --resume $SESSION
# 成功获得基于上下文的详细回复
```

#### 案例2：Debug调试
```bash
# Debug模式输出关键信息
echo "检查优化建议" | claude --debug 2>&1 | grep -E "(session|Hook|DEBUG.*File)"

# 输出示例：
# [DEBUG] session_id: 43064195-fa6a-40ae-ac77-4294981a4d09
# [DEBUG] Hook command completed with status 0
# [DEBUG] File written atomically
```

#### 案例3：JSON数据处理
```bash
# 获取项目目录信息
echo "CC-Toolkit项目有哪些目录？" | claude --output-format json | jq '{
  session: .session_id,
  result: .result,
  cost: .total_cost_usd,
  tokens: .usage.output_tokens
}'

# 输出结构化数据便于后续处理
```

### ⚡ 性能优化建议

#### 调用频率控制
- 避免过于频繁的递归调用
- 设置合理的重试间隔
- 监控API成本和token使用

#### Session生命周期
- Session有效期约为会话期间
- 长时间间隔后session可能失效
- 建议每次调用都获取新session作为备份
- **配置隔离**: 测试时使用`.claude/settings.local.json`，避免污染团队共享配置

#### 输出格式选择
| 场景 | 推荐格式 | 原因 |
|-----|---------|------|
| 数据处理 | `--output-format json` | 结构化，便于解析 |
| 调试分析 | `--debug` | 详细信息，便于排错 |
| 快速测试 | 默认输出 | 简洁直接 |

### 🛠️ 实用脚本模板

#### Session管理器
```bash
#!/bin/bash
# session_manager.sh
SESSION_FILE="/tmp/claude_session.txt"

get_session() {
    local prompt="$1"
    local session=$(echo "$prompt" | claude --output-format json | jq -r .session_id)
    echo "$session" > $SESSION_FILE
    echo "$session"
}

use_session() {
    local prompt="$1"
    local session=$(cat $SESSION_FILE 2>/dev/null)
    
    if [[ -n "$session" && "$session" != "null" ]]; then
        claude --resume "$session" "$prompt"
    else
        get_session "$prompt"
    fi
}
```

#### 批量处理
```bash
#!/bin/bash
# batch_claude.sh

process_files() {
    local files=("$@")
    local main_session=""
    
    for file in "${files[@]}"; do
        echo "处理文件: $file"
        if [[ -z "$main_session" ]]; then
            # 第一个文件建立主session
            main_session=$(echo "分析文件 $file" | claude --output-format json | jq -r .session_id)
        else
            # 后续文件使用同一session
            echo "继续分析文件 $file，与之前的文件对比" | claude --resume $main_session
        fi
    done
}
```

</claude_cli_best_practices>
