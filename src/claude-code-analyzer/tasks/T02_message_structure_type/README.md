# T02: 消息结构类型分析

## 问题描述

Claude CLI数据包含复杂多样的对象结构，不同消息类型有不同的数据模式。为了深入理解数据特征，需要：

1. **类型识别问题**: 相同字段名但结构完全不同的对象
2. **结构复杂度**: 某些对象嵌套深度达到30+层
3. **类型分布**: 需要了解哪些数据类型最常见
4. **结构签名**: 生成唯一的类型指纹用于精确分类

## 技术挑战

- **完整结构签名**: 不仅看字段名，还要看完整的嵌套结构
- **递归类型生成**: 支持任意深度的嵌套对象和数组
- **性能优化**: 处理14万+对象的类型分析
- **统计排序**: 按出现频率和复杂度进行智能排序

## 预期结果

### 输出文件
- `object_types_detail.json` - 详细类型分析数据
- `object_types_compact.json` - 紧凑格式类型清单  
- `object_types_summary.json` - 类型分析摘要报告

### 关键指标
- **分析规模**: 处理468个文件，分析14万+个对象
- **类型发现**: 预期发现400+种不同的数据结构类型
- **复杂度分析**: 统计结构复杂度分布 (字段数量)
- **频率排序**: 识别最常见的数据类型模式

### 实际成果
根据最新执行结果：
- ✅ 处理文件数: 468
- ✅ 分析对象总数: 147,800
- ✅ 发现类型数: 414种
- ✅ 最高复杂度: 37层嵌套结构
- ✅ 热门类型: `object{content:string,id:string,priority:string,status:string}` (16.30%占比)

## 结构签名示例

```javascript
// 简单对象
object{content:string,id:string,status:string}

// 复杂嵌套
object{message:object{content:array[object{text:string,type:string}],role:string},usage:object{input_tokens:integer,output_tokens:integer}}

// 数组类型
array[object{content:string,tool_use_id:string,type:string}]
```

## 使用方式

```bash
# 单独执行  
python tasks/T02_message_structure_type/type_analyzer.py outputs/T02_structure_types

# 通过调度器执行
python task_scheduler.py --tasks T06 T02
```

## 依赖关系

- **输入依赖**: T06 数据源扫描结果
- **输出用途**: T03 最小集合覆盖算法、T08 前端展示策略

## 技术实现

- **算法**: 递归结构遍历 + 签名哈希生成
- **数据结构**: 类型字典 + 频率统计 + 复杂度计算
- **性能**: 支持10万+对象分析，执行时间 < 2秒