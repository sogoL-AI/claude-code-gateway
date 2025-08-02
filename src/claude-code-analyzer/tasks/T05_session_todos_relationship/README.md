# T05: Session-Todos关系分析

## 问题描述

Claude CLI会为某些Session创建对应的Todos文件，但关系复杂且不明确。需要深入分析：

1. **一对多关系**: 一个Session可能对应多个Todos文件
2. **命名规律**: Todos文件名 `{session_id}-agent-{agent_id}.json` 的含义
3. **Agent复用**: 同一个Agent是否会服务多个Session
4. **Self-Agent**: Session ID作为Agent ID的特殊情况

## 技术挑战

- **复杂映射**: Session与Todos的多对多关系分析
- **模式识别**: 从文件名解析Session-Agent关联规律
- **统计分析**: Agent复用频率和Session分布特征  
- **异常检测**: 识别异常的关系模式和边界情况

## 预期结果

### 输出文件
- `session_todos_relationship_analysis.json` - Session-Todos关系分析报告

### 关键指标
- **映射统计**: 208个Session中有多少个有对应的Todos文件
- **关系分布**: 1:1, 1:2-5, 1:6-10, 1:10+ 的关系类型分布
- **Agent分析**: 唯一Agent数量和复用模式
- **复杂关系**: 识别最复杂的Session-Todos关系实例

### 实际成果
根据最新执行结果：
- ✅ 总Session数: 208个
- ✅ 有Todos的Session数: 识别具有Todos文件的Session
- ✅ 总Todos文件数: 260个文件
- ✅ 唯一Agent数: 统计不同的Agent ID数量
- ✅ 复杂关系Session: 识别一对多关系的典型案例

## 分析维度

### 关系类型分类
- **1:1关系**: 一个Session对应一个Todos文件
- **1:2-5关系**: 一个Session对应2-5个Todos文件  
- **1:6-10关系**: 一个Session对应6-10个Todos文件
- **1:10+关系**: 一个Session对应10个以上Todos文件

### Agent模式分析
- **Self-Agent**: Session ID == Agent ID的情况
- **Unique-Agent**: 每个Todos文件都有不同的Agent ID
- **Mixed-Agent**: 部分Agent ID重复的混合模式

### 时间关联分析
- **时间跨度**: 同一Session的多个Todos文件的创建时间分布
- **活跃期**: 分析Session-Todos关系的活跃时间段
- **延续性**: Todos文件创建是否与Session活动同步

## 文件命名解析

```
{session_id}-agent-{agent_id}.json
```

- **session_id**: 关联的Claude CLI Session ID
- **agent_id**: 可能是执行特定任务的Agent标识符
- **特殊情况**: 当 `session_id == agent_id` 时为Self-Agent模式

## 使用方式

```bash
# 单独执行
python tasks/T05_session_todos_relationship/relationship_analyzer.py outputs/T05_relationships

# 通过调度器执行
python task_scheduler.py --tasks T06 T05
```

## 依赖关系

- **输入依赖**: T06 数据源扫描结果 (需要文件列表和元数据)
- **输出用途**: T07 会话机制分析 (理解Claude CLI的完整工作流程)

## 应用价值

- **系统理解**: 理解Claude CLI的内部Agent机制
- **关系映射**: 为数据可视化提供关系图谱数据
- **异常检测**: 识别不正常的Session-Todos关系
- **优化建议**: 为Agent管理系统设计提供参考

## 技术实现

- **算法**: 正则表达式解析 + 关系映射 + 统计分析
- **数据结构**: 多重映射 + 关系图 + 分布统计
- **性能**: 处理260个Todos文件的关系分析 < 1秒