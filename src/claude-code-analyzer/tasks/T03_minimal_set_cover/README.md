# T03: 最小集合覆盖分析

## 问题描述

Claude CLI产生了208个Session文件，总计118MB数据。为了构建高效的分析和展示系统，需要：

1. **数据冗余问题**: 许多Session包含相似的数据类型模式
2. **存储优化**: 如何用最少的Session覆盖所有414种数据类型
3. **代表性选择**: 选出的Session要能代表完整的数据特征
4. **算法效率**: 这是一个NP-Hard的集合覆盖问题

## 技术挑战

- **集合覆盖问题**: 经典的NP-Hard优化问题
- **贪心算法**: 每次选择覆盖最多新类型的Session
- **类型去重**: 确保选中的Session集合覆盖所有414种类型
- **效率平衡**: 在覆盖完整性和Session数量之间找平衡

## 预期结果

### 输出文件
- `coverage_analysis.json` - 覆盖分析报告
- `selected_sessions/` - 选中的最小Session集合

### 关键指标
- **压缩比**: 从208个Session压缩到20-30个 (85%+压缩率)
- **类型覆盖**: 100%覆盖所有414种数据类型
- **数据量**: 选中Session的总数据量和分布
- **代表性**: 确保各个项目和时间段都有代表

### 实际成果
根据最新执行结果：
- ✅ 原始Session数: 208个
- ✅ 选中Session数: 27个 (87%压缩率)
- ✅ 类型覆盖率: 100% (414/414种类型)
- ✅ 数据量优化: 选中最具代表性的Session集合
- ✅ 项目分布: 覆盖所有主要项目类型

## 贪心算法逻辑

```python
# 伪代码
selected_sessions = []
covered_types = set()
remaining_types = all_types.copy()

while remaining_types:
    # 选择覆盖最多新类型的Session
    best_session = max(sessions, key=lambda s: len(s.types & remaining_types))
    selected_sessions.append(best_session)
    
    # 更新已覆盖类型
    new_types = best_session.types & remaining_types
    covered_types |= new_types
    remaining_types -= new_types
```

## 使用方式

```bash
# 单独执行
python tasks/T03_minimal_set_cover/set_cover_analyzer.py outputs/T03_set_cover

# 通过调度器执行  
python task_scheduler.py --tasks T06 T02 T03
```

## 依赖关系

- **输入依赖**: T02 消息结构类型分析结果
- **输出用途**: T08 前端展示策略、数据采样和示例展示

## 应用价值

- **开发测试**: 用27个Session代替208个进行快速测试
- **数据展示**: 前端展示时优先加载代表性Session
- **性能优化**: 减少85%的数据加载量
- **样本分析**: 为机器学习和统计分析提供高质量样本

## 技术实现

- **算法**: 贪心集合覆盖算法
- **数据结构**: 集合运算 + 类型映射 + Session元数据
- **性能**: 处理208个Session的覆盖分析 < 2秒