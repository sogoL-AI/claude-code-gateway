# Claude Code 本地目录结构分析

## 概览

Claude Code 在本地系统中使用了多个目录来存储配置、数据和缓存文件。了解这些目录结构对于构建管理工具和集成系统至关重要。

## 核心目录结构

### 1. 用户配置目录：`~/.claude/`

这是 Claude Code 的主要用户级配置和数据目录。

```
~/.claude/
├── settings.json              # 用户级配置文件
├── settings.json.backup       # 配置文件备份
├── projects/                  # 项目会话数据
│   ├── -Users-Zhuanz-Projects-Arche/
│   ├── -Users-Zhuanz-Projects-SylloOS/
│   ├── -Users-Zhuanz-Projects-claude-code-gateway/
│   └── ...                   # 其他项目目录（路径编码）
├── scripts/                  # 用户自定义脚本
│   ├── __pycache__/
│   ├── prompt_enhancer.py
│   ├── session_notifier.py
│   ├── uv_helper.py
│   └── uv_response_helper.py
├── ide/                      # IDE 集成相关文件
│   ├── 19285.lock
│   ├── 48973.lock
│   └── 60612.lock           # 进程锁文件
├── shell-snapshots/          # Shell 状态快照
│   ├── snapshot-zsh-1753691406990-ng2ajv.sh
│   ├── snapshot-zsh-1753692347561-0yavsg.sh
│   └── ...                  # 时间戳命名的快照文件
├── statsig/                 # 统计和分析数据
└── todos/                   # 待办事项存储
```

### 2. 项目级配置目录：`.claude/`

每个项目可以有自己的 Claude Code 配置目录。

```
PROJECT/.claude/
├── settings.json            # 项目级共享配置
├── settings.local.json      # 个人项目配置
├── scripts/                 # 项目专用脚本
├── commands/                # 自定义斜杠命令
├── CLAUDE.md               # 项目记忆文件
└── CLAUDE.local.md         # 个人项目记忆文件（已弃用）
```

### 3. 全局安装目录：`/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/`

Claude Code 的 npm 全局安装位置（macOS Homebrew）。

```
/opt/homebrew/lib/node_modules/@anthropic-ai/claude-code/
├── cli.js                  # 主要 CLI 脚本
├── sdk.mjs                 # SDK 模块
├── sdk.d.ts               # TypeScript 类型定义
├── sdk-tools.d.ts         # SDK 工具类型定义
├── package.json           # 包配置文件
├── README.md              # 文档
├── LICENSE.md             # 许可证
├── yoga.wasm              # WebAssembly 文件
├── node_modules/          # 依赖包
└── vendor/                # 第三方依赖
```

## 重要配置文件详解

### 用户级配置文件：`~/.claude/settings.json`

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "id": "prompt-enhancer",
            "name": "Prompt增强器",
            "description": "在用户prompt后添加ultra think、session ID和时间戳",
            "type": "command",
            "command": "/Users/Zhuanz/.claude/scripts/prompt_enhancer.py",
            "timeout": 5,
            "enabled": true,
            "category": "prompt-enhancement",
            "author": "Claude Code Expert",
            "version": "1.0.0"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "id": "session-notifier",
            "name": "Session Notifier 会话通知器",
            "description": "在Claude Code会话停止时发送macOS系统通知",
            "type": "command",
            "command": "python3 \"/Users/Zhuanz/.claude/scripts/session_notifier.py\"",
            "timeout": 5,
            "enabled": true,
            "category": "automation",
            "author": "VibeCoding-Kit",
            "version": "1.0.0"
          }
        ]
      }
    ]
  }
}
```

### 包配置文件：`package.json`

```json
{
  "name": "@anthropic-ai/claude-code",
  "version": "1.0.61",
  "main": "sdk.mjs",
  "types": "sdk.d.ts",
  "bin": {
    "claude": "cli.js"
  },
  "engines": {
    "node": ">=18.0.0"
  },
  "type": "module",
  "author": "Anthropic <support@anthropic.com>",
  "license": "SEE LICENSE IN README.md",
  "description": "Use Claude, Anthropic's AI assistant, right from your terminal.",
  "homepage": "https://github.com/anthropics/claude-code",
  "bugs": {
    "url": "https://github.com/anthropics/claude-code/issues"
  }
}
```

## 目录功能说明

### projects/ 目录
- **用途**: 存储每个项目的会话历史和上下文
- **命名规则**: 路径中的 `/` 被替换为 `-`
- **内容**: 对话历史、上下文信息、项目特定设置

### scripts/ 目录
- **用途**: 存储用户自定义的 hook 脚本
- **支持语言**: Python、Shell、Node.js 等
- **执行时机**: 在特定事件触发时运行

### shell-snapshots/ 目录
- **用途**: 保存 shell 环境的快照
- **格式**: `snapshot-{shell}-{timestamp}-{id}.sh`
- **作用**: 帮助 Claude 理解当前 shell 环境状态

### ide/ 目录
- **用途**: IDE 集成相关的锁文件和状态
- **内容**: 进程锁文件，防止多实例冲突

### statsig/ 目录
- **用途**: 存储统计和遥测数据
- **隐私**: 遵循用户隐私设置

### todos/ 目录
- **用途**: 存储任务和待办事项
- **持久化**: 跨会话保持任务状态

## 配置层级

Claude Code 使用分层配置系统：

1. **全局默认配置**: 内置在应用中
2. **用户级配置**: `~/.claude/settings.json`
3. **项目级共享配置**: `PROJECT/.claude/settings.json`
4. **项目级个人配置**: `PROJECT/.claude/settings.local.json`

配置优先级：个人配置 > 项目配置 > 用户配置 > 默认配置

## 内存管理文件

### CLAUDE.md 文件位置
1. **项目内存**: `./CLAUDE.md` (团队共享)
2. **用户内存**: `~/.claude/CLAUDE.md` (个人偏好)
3. **本地项目内存**: `./CLAUDE.local.md` (已弃用)

### 内存文件特性
- 自动加载和递归发现
- 支持 `@path/to/import` 语法
- 最大导入深度 5 跳
- 向上遍历目录树查找

## Hook 系统

### Hook 类型
- `PreToolUse`: 工具使用前
- `PostToolUse`: 工具使用后
- `UserPromptSubmit`: 用户提示提交时
- `Notification`: 系统通知时
- `Stop/SubagentStop`: 会话停止时
- `SessionStart`: 会话开始时

### Hook 配置
- 支持命令行脚本执行
- 可配置超时时间
- 支持启用/禁用状态
- 支持分类和版本管理

## 安全考虑

### 敏感文件
- `~/.claude/settings.json`: 可能包含 API 密钥和敏感配置
- `~/.config/claude-code/auth.json`: 认证信息 (如果存在)
- Hook 脚本: 可执行文件，需要审查

### 权限管理
- 脚本文件需要执行权限
- 配置文件应限制读写权限
- 项目目录权限继承项目设置

## 管理工具开发指导

### 目录监控
- 监控配置文件变化
- 追踪项目会话状态
- 管理 hook 脚本生命周期

### 数据备份
- 定期备份用户配置
- 导出项目会话历史
- 保存自定义脚本和命令

### 清理维护
- 清理过期的 shell 快照
- 管理项目目录存储大小
- 维护 hook 脚本依赖

### 集成接口
- 读取项目配置信息
- 监控会话状态
- 管理用户偏好设置
- 提供配置迁移工具

这个目录结构分析为构建 Claude Code 管理工具提供了完整的文件系统蓝图。