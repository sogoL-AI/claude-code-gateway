# 🔬 Claude Code 分析器

## 📋 概述

这是一个综合性的Claude CLI分析工具集，按照不同分析维度组织，用于深入理解Claude CLI的内部机制和行为模式。

## 🗂️ 目录结构

```
claude-code-analyzer/
├── README.md                                    # 总体项目说明
├── shared/                                      # 共享组件和工具
│   ├── models.py                               # 通用数据模型
│   ├── base_analyzer.py                        # 基础分析器类
│   ├── utils.py                                # 工具函数库
│   └── __init__.py                             # 包初始化
├── tasks/                                      # 任务执行目录
│   ├── T01_deep_field_extraction/              # 深度字段提取分析
│   │   ├── README.md                           # 任务说明
│   │   └── field_extractor.py                 # 字段提取器
│   ├── T02_message_structure_type/             # 消息结构类型分析
│   │   ├── README.md                           # 任务说明
│   │   └── type_analyzer.py                   # 类型分析器
│   ├── T03_minimal_set_cover/                  # 最小集合覆盖算法
│   │   ├── README.md                           # 任务说明
│   │   └── set_cover_analyzer.py              # 集合覆盖分析器
│   ├── T04_session_inheritance/                # Session ID继承机制分析
│   │   ├── README.md                           # 任务说明
│   │   └── inheritance_analyzer.py            # 继承分析器
│   ├── T05_session_todos_relationship/         # Session-Todos关系分析
│   │   ├── README.md                           # 任务说明
│   │   └── relationship_analyzer.py           # 关系分析器
│   ├── T06_data_source_scanning/               # 数据源全景扫描
│   │   ├── README.md                           # 任务说明
│   │   └── data_scanner.py                    # 数据扫描器
│   ├── T07_session_mechanism/                  # Session关联机制分析
│   │   └── README.md                           # 任务说明
│   └── T08_frontend_strategy/                  # 前端展示策略优化
│       ├── README.md                           # 任务说明
│       └── frontend_strategy_analyzer.py      # 策略分析器
├── outputs/                                    # 分析结果输出
│   ├── T01_field_extraction/                   # 字段提取结果
│   ├── T02_structure_types/                    # 结构类型结果
│   ├── T03_set_cover/                          # 集合覆盖结果
│   ├── T04_inheritance/                        # 继承分析结果
│   ├── T05_relationships/                      # 关系分析结果
│   ├── T06_data_scan/                          # 数据扫描结果
│   ├── T07_session_mechanism/                  # 会话机制结果
│   ├── T08_frontend/                           # 前端策略结果
│   └── execution_report.json                   # 执行报告
└── task_scheduler.py                           # 任务调度器
```

## 🎯 分析维度说明

### T01. deep-field-extraction
**分析目标**: 实现JSON数据的深度字段提取和去重  
**核心问题**: 如何递归到最深层并规范化字段路径？  
**关键发现**: 成功提取196个唯一字段路径，处理29,460条记录

### T02. message-structure-type
**分析目标**: 基于完整结构签名识别消息类型  
**核心问题**: 如何从142,377个对象中识别独特结构类型？  
**关键发现**: 识别出414种独特结构类型，实现智能分类

### T03. minimal-set-cover
**分析目标**: 用最少Session覆盖所有数据类型  
**核心问题**: 如何实现86.6%的数据压缩率？  
**关键发现**: 27个Session覆盖414种类型，贪心算法高效

### T04. session-inheritance
**分析目标**: 研究Session ID的继承和创建机制  
**核心问题**: `claude -c`如何选择和继承Session？  
**关键发现**: 71对快速连续Session，68.2%继续现有文件

### T05. session-todos-relationship
**分析目标**: 分析Session和Todos文件的复杂关系  
**核心问题**: 为什么一个Session对应多个Todos文件？  
**关键发现**: 220个Session对应252个Todos，Agent ID完全唯一

### T06. data-source-scanning
**分析目标**: 全景扫描~/.claude目录的所有数据源  
**核心问题**: Claude CLI存储了哪些类型的数据？  
**关键发现**: 发现7种数据类型，453个文件，115.46MB

### T07. session-mechanism
**分析目标**: 理解Claude CLI的完整会话机制  
**核心问题**: Claude CLI是否支持ChatGPT式的连续对话？  
**关键发现**: 完全支持，通过leafUuid实现跨Session关联

### T08. frontend-strategy
**分析目标**: 优化400+数据类型的前端展示策略  
**核心问题**: 如何智能展示和分组大量数据类型？  
**关键发现**: 帕累托原理应用，20%类型覆盖80%使用场景

## 🚀 使用方法

### 任务执行
通过任务调度器运行所有分析任务：
```bash
python task_scheduler.py
```

### 单独执行任务
每个分析维度都可以独立使用：

1. **查看任务说明**: 阅读`tasks/TXX_*/README.md`
2. **运行分析器**: 执行对应的Python分析器
3. **查看结果**: 在`outputs/TXX_*/`目录查看分析结果
4. **参考实现**: 查看`tasks/TXX_*/`目录下的分析器代码

## 📊 分析价值

- **技术可行性验证**: 证明Claude CLI完全支持连续对话界面开发
- **架构设计参考**: 提供完整的技术实现方案
- **数据格式理解**: 深入理解Session文件的存储机制
- **最佳实践指导**: 基于实际测试的开发建议

## 🔧 技术栈

- **分析工具**: Python 3.x
- **数据格式**: JSON Lines (.jsonl)
- **测试方法**: Claude CLI v1.0.61
- **文档格式**: Markdown

## 📈 更新记录

- **2025-08-01**: 初始版本，包含4个核心分析维度
- **2025-08-01**: 完成claude -c机制深度测试
- **2025-08-01**: 建立完整的目录结构和文档体系