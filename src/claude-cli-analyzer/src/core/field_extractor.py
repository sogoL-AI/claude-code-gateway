#!/usr/bin/env python3
"""
Claude CLI Field Extractor
递归提取和分析JSON字段，建立完整的字段清单
"""

import json
import ujson
from typing import Dict, List, Set, Any, Union, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import re
from pathlib import Path


@dataclass
class FieldInfo:
    """字段信息"""
    path: str  # 字段路径，如 "message.content.tool_use.name"
    data_type: str  # 推断的数据类型
    value_examples: List[Any] = field(default_factory=list)  # 值示例
    occurrence_count: int = 0  # 出现次数
    null_count: int = 0  # null值次数
    unique_values: Set[Any] = field(default_factory=set)  # 唯一值集合
    is_enum: bool = False  # 是否为枚举类型
    enum_values: List[Any] = field(default_factory=list)  # 枚举值列表
    value_patterns: List[str] = field(default_factory=list)  # 值的模式


@dataclass
class ExtractionResult:
    """提取结果"""
    total_records_processed: int = 0
    total_fields_discovered: int = 0
    field_registry: Dict[str, FieldInfo] = field(default_factory=dict)
    data_type_distribution: Dict[str, int] = field(default_factory=dict)
    enum_fields: Dict[str, List[Any]] = field(default_factory=dict)


class FieldExtractor:
    """字段提取器"""
    
    def __init__(self, max_unique_values: int = 50, max_examples: int = 10, max_value_length: int = 100):
        self.max_unique_values = max_unique_values  # 枚举判断阈值
        self.max_examples = max_examples
        self.max_value_length = max_value_length  # 值长度限制
        self.field_registry: Dict[str, FieldInfo] = {}
        
    def truncate_value(self, value: Any) -> Any:
        """截断过长的值"""
        if isinstance(value, str) and len(value) > self.max_value_length:
            return value[:self.max_value_length] + "..."
        elif isinstance(value, (dict, list)):
            # 对复杂对象转换为字符串后截断
            str_value = str(value)
            if len(str_value) > self.max_value_length:
                return str_value[:self.max_value_length] + "..."
            return str_value
        return value
        
    def extract_fields_from_value(self, value: Any, current_path: str = "", max_depth: int = 20) -> None:
        """从值中递归提取字段，增强递归深度"""
        
        if max_depth <= 0:  # 防止无限递归
            return
            
        if isinstance(value, dict):
            # 记录对象字段本身
            if current_path:
                self._record_field(current_path, value)
                
            for key, val in value.items():
                new_path = f"{current_path}.{key}" if current_path else key
                # 总是记录字段，即使是复杂类型
                self._record_field(new_path, val)
                # 递归处理嵌套对象，增加深度控制
                self.extract_fields_from_value(val, new_path, max_depth - 1)
                
        elif isinstance(value, list):
            # 记录数组字段本身
            if current_path:
                self._record_field(current_path, value)
            
            if value:  # 非空列表
                # 分析数组元素，增加分析数量
                for i, item in enumerate(value[:10]):  # 分析前10个元素而不是5个
                    if isinstance(item, (dict, list)):
                        # 使用通用的数组元素路径
                        array_item_path = f"{current_path}[{i}]"
                        self.extract_fields_from_value(item, array_item_path, max_depth - 1)
                        
                        # 同时使用通用的数组元素模式
                        if i == 0:  # 只对第一个元素使用通用模式
                            generic_array_path = f"{current_path}[]"
                            self.extract_fields_from_value(item, generic_array_path, max_depth - 1)
                    else:
                        # 数组中的基本类型元素
                        array_element_path = f"{current_path}[]"
                        self._record_field(array_element_path, item)
        else:
            # 基本数据类型已在上层记录
            pass
    
    def _record_field(self, field_path: str, value: Any) -> None:
        """记录字段信息"""
        
        if field_path not in self.field_registry:
            self.field_registry[field_path] = FieldInfo(
                path=field_path,
                data_type=self._infer_data_type(value),
                unique_values=set()
            )
        
        field_info = self.field_registry[field_path]
        field_info.occurrence_count += 1
        
        # 记录null值
        if value is None:
            field_info.null_count += 1
            return
        
        # 更新数据类型（可能需要泛化）
        current_type = self._infer_data_type(value)
        field_info.data_type = self._merge_data_types(field_info.data_type, current_type)
        
        # 收集值示例
        if len(field_info.value_examples) < self.max_examples:
            truncated_value = self.truncate_value(value)
            if truncated_value not in field_info.value_examples:  # 避免重复
                field_info.value_examples.append(truncated_value)
        
        # 收集唯一值（用于枚举判断）
        if len(field_info.unique_values) < self.max_unique_values:
            # 只对字符串和数字类型收集唯一值
            if isinstance(value, (str, int, float, bool)):
                field_info.unique_values.add(value)
        
        # 分析值的模式
        if isinstance(value, str):
            pattern = self._extract_string_pattern(value)
            if pattern and pattern not in field_info.value_patterns:
                field_info.value_patterns.append(pattern)
    
    def _infer_data_type(self, value: Any) -> str:
        """推断数据类型"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            # 进一步分析字符串类型
            if self._is_uuid(value):
                return "uuid"
            elif self._is_iso_datetime(value):
                return "datetime"
            elif self._is_url(value):
                return "url"
            elif value.startswith(("req_", "toolu_", "msg_")):
                return "id"
            else:
                return "string"
        elif isinstance(value, list):
            if not value:
                return "array[empty]"
            # 分析数组元素类型
            element_types = {self._infer_data_type(item) for item in value[:10]}
            if len(element_types) == 1:
                return f"array[{list(element_types)[0]}]"
            else:
                return f"array[mixed]"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    def _merge_data_types(self, type1: str, type2: str) -> str:
        """合并数据类型（处理类型冲突）"""
        if type1 == type2:
            return type1
        
        # 处理null类型
        if type1 == "null":
            return type2
        if type2 == "null":
            return type1
        
        # 数字类型的泛化
        if {type1, type2} <= {"integer", "number"}:
            return "number"
        
        # 字符串子类型的泛化
        string_types = {"string", "uuid", "datetime", "url", "id"}
        if {type1, type2} <= string_types:
            return "string"
        
        # 数组类型的处理
        if type1.startswith("array") and type2.startswith("array"):
            return "array[mixed]"
        
        # 其他情况返回更通用的类型
        return "mixed"
    
    def _is_uuid(self, value: str) -> bool:
        """判断是否为UUID格式"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value, re.IGNORECASE))
    
    def _is_iso_datetime(self, value: str) -> bool:
        """判断是否为ISO时间格式"""
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$'
        return bool(re.match(iso_pattern, value))
    
    def _is_url(self, value: str) -> bool:
        """判断是否为URL"""
        return value.startswith(('http://', 'https://', 'ftp://'))
    
    def _extract_string_pattern(self, value: str) -> str:
        """提取字符串模式"""
        if self._is_uuid(value):
            return "UUID"
        elif self._is_iso_datetime(value):
            return "ISO_DATETIME"
        elif self._is_url(value):
            return "URL"
        elif value.startswith("req_"):
            return "REQUEST_ID"
        elif value.startswith("toolu_"):
            return "TOOL_USE_ID"
        elif value.startswith("msg_"):
            return "MESSAGE_ID"
        elif re.match(r'^[A-Z_]+$', value):
            return "UPPER_CASE"
        elif re.match(r'^[a-z_]+$', value):
            return "LOWER_CASE"
        elif re.match(r'^\d+$', value):
            return "NUMERIC_STRING"
        else:
            return None
    
    def analyze_enums(self) -> None:
        """分析枚举字段"""
        for field_path, field_info in self.field_registry.items():
            # 判断是否为枚举类型
            unique_count = len(field_info.unique_values)
            total_count = field_info.occurrence_count - field_info.null_count
            
            # 枚举判断条件：
            # 1. 有足够的出现次数
            # 2. 唯一值数量相对较少
            # 3. 基本数据类型
            if (total_count >= 5 and 
                unique_count <= min(self.max_unique_values, total_count * 0.8) and
                field_info.data_type in ["string", "integer", "boolean"]):
                
                field_info.is_enum = True
                field_info.enum_values = sorted(list(field_info.unique_values))
    
    def process_jsonl_file(self, file_path: str, max_records: int = None) -> int:
        """处理JSONL文件"""
        processed_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    if max_records and processed_count >= max_records:
                        break
                        
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = ujson.loads(line)
                        self.extract_fields_from_value(record)
                        processed_count += 1
                        
                        if processed_count % 1000 == 0:
                            print(f"  已处理 {processed_count} 条记录...")
                            
                    except json.JSONDecodeError as e:
                        print(f"  JSON解析错误 (行 {line_no}): {e}")
                        continue
                        
        except Exception as e:
            print(f"文件读取错误 {file_path}: {e}")
            
        return processed_count
    
    def process_json_file(self, file_path: str) -> int:
        """处理JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = ujson.load(f)
                self.extract_fields_from_value(data)
                return 1
        except Exception as e:
            print(f"JSON文件处理错误 {file_path}: {e}")
            return 0
    
    def merge_array_index_fields(self) -> None:
        """合并相似的数组索引字段，如将 content[0].title, content[1].title 合并为 content[*].title"""
        import re
        from collections import defaultdict
        
        # 按基础模式分组字段
        pattern_groups = defaultdict(list)
        
        for field_path in list(self.field_registry.keys()):
            # 将数组索引替换为通配符以识别模式
            normalized_path = re.sub(r'\[\d+\]', '[*]', field_path)
            
            # 只处理包含数组索引的字段
            if '[*]' in normalized_path and normalized_path != field_path:
                pattern_groups[normalized_path].append(field_path)
        
        # 合并相似字段
        for normalized_path, similar_fields in pattern_groups.items():
            if len(similar_fields) <= 1:
                continue
                
            # 创建合并后的字段信息
            merged_field = FieldInfo(
                path=normalized_path,
                data_type="mixed",
                unique_values=set()
            )
            
            # 合并所有相似字段的信息
            all_examples = []
            all_patterns = []
            data_types = set()
            
            for field_path in similar_fields:
                field_info = self.field_registry[field_path]
                
                merged_field.occurrence_count += field_info.occurrence_count
                merged_field.null_count += field_info.null_count
                
                # 收集数据类型
                data_types.add(field_info.data_type)
                
                # 收集示例值
                all_examples.extend(field_info.value_examples)
                
                # 收集模式
                all_patterns.extend(field_info.value_patterns)
                
                # 收集唯一值
                merged_field.unique_values.update(field_info.unique_values)
                
                # 删除原始字段
                del self.field_registry[field_path]
            
            # 设置合并后字段的数据类型
            if len(data_types) == 1:
                merged_field.data_type = list(data_types)[0]
            else:
                merged_field.data_type = "mixed"
            
            # 去重并限制示例数量（处理不可哈希类型）
            unique_examples = []
            seen_examples_str = set()  # 使用字符串表示来去重
            for example in all_examples:
                if len(unique_examples) >= self.max_examples:
                    break
                truncated_example = self.truncate_value(example)
                example_str = str(truncated_example)
                if example_str not in seen_examples_str:
                    seen_examples_str.add(example_str)
                    unique_examples.append(truncated_example)
            merged_field.value_examples = unique_examples
            
            # 去重模式
            merged_field.value_patterns = list(set(all_patterns))
            
            # 添加合并后的字段
            self.field_registry[normalized_path] = merged_field

    def generate_extraction_result(self) -> ExtractionResult:
        """生成提取结果"""
        # 分析枚举
        self.analyze_enums()
        
        # 合并数组索引字段
        self.merge_array_index_fields()
        
        # 统计数据类型分布
        type_distribution = Counter()
        enum_fields = {}
        
        for field_path, field_info in self.field_registry.items():
            type_distribution[field_info.data_type] += 1
            
            if field_info.is_enum:
                enum_fields[field_path] = field_info.enum_values
        
        return ExtractionResult(
            total_records_processed=sum(info.occurrence_count for info in self.field_registry.values()),
            total_fields_discovered=len(self.field_registry),
            field_registry=self.field_registry,
            data_type_distribution=dict(type_distribution),
            enum_fields=enum_fields
        )
    
    def print_field_summary(self) -> None:
        """打印字段汇总信息"""
        result = self.generate_extraction_result()
        
        print(f"\n📊 字段提取汇总:")
        print(f"总共发现字段: {result.total_fields_discovered}")
        print(f"处理记录总数: {result.total_records_processed}")
        print(f"识别的枚举字段: {len(result.enum_fields)}")
        
        print(f"\n📈 数据类型分布:")
        for data_type, count in sorted(result.data_type_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"  {data_type}: {count}")
        
        print(f"\n🔖 枚举字段:")
        for field_path, enum_values in sorted(result.enum_fields.items()):
            print(f"  {field_path}: {enum_values}")


if __name__ == "__main__":
    # 测试字段提取器
    extractor = FieldExtractor()
    
    # 可以添加测试代码
    test_data = {
        "sessionId": "137e4b21-641f-4c6f-b288-ad127c871a24",
        "message": {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hello"},
                {"type": "tool_use", "name": "Read"}
            ]
        },
        "timestamp": "2025-07-31T17:02:24.244Z",
        "isSidechain": False
    }
    
    extractor.extract_fields_from_value(test_data)
    extractor.print_field_summary()