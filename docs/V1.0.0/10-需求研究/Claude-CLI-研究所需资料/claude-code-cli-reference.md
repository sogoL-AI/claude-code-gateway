# Claude Code CLI 完整参考文档

## 基础命令

### 启动和会话管理
```bash
# 启动交互式 REPL
claude

# 使用初始提示启动
claude "query"

# 非交互模式查询并退出
claude -p "explain this function"

# 管道输入处理
cat logs.txt | claude -p "explain"

# 继续最近的对话
claude -c

# 继续最近对话并添加新提示
claude -c -p "query"

# 恢复特定会话
claude -r "<session-id>" "query"

# 显示会话选择器
claude --resume
```

### 更新和维护
```bash
# 更新到最新版本
claude update

# 配置 MCP 服务器
claude mcp

# 检查安装健康状态
claude /doctor
```

## 主要 CLI 标志和选项

### 核心标志
- `--add-dir`: 添加工作目录
- `--allowedTools`: 指定允许的工具
- `--print/-p`: 打印响应而不进入交互模式
- `--output-format`: 指定响应格式 (text/json/stream-json)
- `--verbose`: 启用详细日志
- `--model`: 为会话设置特定模型
- `--permission-mode`: 设置权限模式
- `--continue`: 加载最近的对话

### 输出格式选项
- `text`: 默认纯文本输出
- `json`: 完整对话日志
- `stream-json`: 实时 JSON 输出

## 内置斜杠命令

### 会话管理
- `/clear`: 清除对话历史
- `/status`: 查看账户和系统状态
- `/cost`: 显示 token 使用统计
- `/help`: 获取使用帮助

### 配置和设置
- `/config`: 查看/修改配置
- `/permissions`: 查看/更新权限
- `/model`: 选择或更改AI模型
- `/terminal-setup`: 安装换行键绑定

### 项目和开发
- `/add-dir`: 添加额外的工作目录
- `/init`: 使用 CLAUDE.md 指南初始化项目
- `/memory`: 编辑 CLAUDE.md 内存文件
- `/review`: 请求代码审查
- `/pr_comments`: 查看拉取请求评论

### 账户管理
- `/login`: 切换 Anthropic 账户
- `/logout`: 登出 Anthropic 账户

### 扩展功能
- `/agents`: 管理自定义AI子代理
- `/mcp`: 管理 MCP 服务器连接
- `/vim`: 进入 vim 模式
- `/compact`: 压缩对话（可选择焦点）
- `/bug`: 向 Anthropic 报告错误

## 交互模式键盘快捷键

### 通用快捷键
- `Ctrl+C`: 取消当前输入或生成
- `Ctrl+D`: 退出 Claude Code 会话
- `Ctrl+L`: 清除终端屏幕
- `Up/Down 箭头`: 导航命令历史
- `Esc` + `Esc`: 编辑上一条消息
- `Ctrl+R`: 反向搜索历史记录

### 多行输入方法
- `\` + `Enter`: 快速转义（适用于所有终端）
- `Option+Enter`: macOS 默认
- `Shift+Enter`: 终端设置模式

### 快速命令
- `#` 开头: 内存快捷方式到 CLAUDE.md
- `/` 开头: 调用斜杠命令

### Vim 模式导航（NORMAL 模式）
- `h/j/k/l`: 左/下/上/右移动
- `w`: 下一个单词
- `e`: 单词结尾
- `b`: 上一个单词
- `0`: 行首
- `$`: 行尾
- `gg`: 输入开始
- `G`: 输入结束

### Vim 模式编辑
- `x`: 删除字符
- `dd`: 删除行
- `D`: 删除到行尾
- `cc`: 更改行
- `.`: 重复上次更改

## 配置系统

### 配置文件
- `~/.claude/settings.json`: 用户级设置
- `.claude/settings.json`: 项目级共享设置
- `.claude/settings.local.json`: 个人项目设置

### 配置命令
```bash
# 查看设置
claude config list

# 查看特定设置
claude config get <key>

# 更改设置
claude config set <key> <value>

# 修改列表设置
claude config add <key> <value>
claude config remove <key> <value>
```

### 关键配置选项

#### 权限设置
- `allow`: 允许特定工具使用
- `deny`: 阻止特定工具使用
- `additionalDirectories`: 扩展 Claude 的工作目录
- `defaultMode`: 设置默认权限模式

#### 全局设置
- `autoUpdates`: 启用/禁用自动更新
- `preferredNotifChannel`: 选择通知方法
- `theme`: 选择颜色主题
- `verbose`: 显示完整命令输出

#### 高级设置
- `apiKeyHelper`: 生成认证的自定义脚本
- `cleanupPeriodDays`: 保留聊天记录持续时间
- `hooks`: 配置自定义预/后工具执行命令
- `model`: 覆盖默认AI模型

### 环境变量
- `ANTHROPIC_API_KEY`: API 认证
- `ANTHROPIC_MODEL`: 指定使用的模型
- `CLAUDE_CODE_USE_BEDROCK`: 启用 Amazon Bedrock
- `CLAUDE_CODE_USE_VERTEX`: 启用 Google Vertex AI
- `DISABLE_TELEMETRY`: 退出使用跟踪

## 工作流模式

### 文件和目录引用
- `@src/utils/auth.js`: 引用特定文件
- `@src/components`: 引用目录
- `@github:repos/owner/repo/issues`: 引用 MCP 资源

### 自定义斜杠命令

#### 创建自定义命令
```bash
# 项目级命令
mkdir -p .claude/commands
echo "Analyze this code for performance issues" > .claude/commands/optimize.md

# 个人级命令
mkdir -p ~/.claude/commands
echo "Review this code for security vulnerabilities" > ~/.claude/commands/security.md
```

#### 命令参数支持
- 使用 `$ARGUMENTS` 占位符支持参数
- 可包含 bash 命令和文件引用
- 通过子目录支持命名空间组织

### 工作流示例

#### 代码审查工作流
```bash
# 启动代码审查
claude -p 'you are a linter...'

# 管道错误日志
cat build-error.txt | claude -p 'explain error'

# 继续会话并添加任务
claude --continue --print "Continue with my task"
```

#### Git 工作树并行会话
创建隔离的 Claude Code 环境，适用于多分支开发。
