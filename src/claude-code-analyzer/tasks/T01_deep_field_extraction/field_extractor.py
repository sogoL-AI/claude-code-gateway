#!/usr/bin/env python3
"""
T01: 深度字段提取分析任务
递归提取JSON字段到最深层，实现204字段去重
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
from collections import defaultdict, Counter

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from shared.models import FieldInfo, AnalysisResult
from shared.utils import setup_logging


class FieldExtractor:
    """深度字段提取器"""
    
    def __init__(self, max_examples: int = 10, max_value_length: int = 100):
        self.max_examples = max_examples
        self.max_value_length = max_value_length
        self.fields: Dict[str, FieldInfo] = {}
        self.total_records = 0
        self.total_files = 0
        self.logger = setup_logging("T01_FieldExtractor")
        
    def extract_from_record(self, record: Dict[str, Any]) -> None:
        """从单条记录中提取字段"""
        self.total_records += 1
        self._extract_recursive(record, "")
        
    def _extract_recursive(self, value: Any, path: str, depth: int = 20) -> None:
        """递归提取字段"""
        if depth <= 0:
            return
            
        if isinstance(value, dict):
            if path:  # 记录对象本身
                self._add_field(path, value)
                
            for key, val in value.items():
                new_path = f"{path}.{key}" if path else key
                self._add_field(new_path, val)
                self._extract_recursive(val, new_path, depth - 1)
                
        elif isinstance(value, list):
            if path:  # 记录数组本身
                self._add_field(path, value)
                
            if value:
                # 处理数组元素
                for i, item in enumerate(value[:10]):  # 分析前10个元素
                    if isinstance(item, (dict, list)):
                        # 使用索引路径
                        indexed_path = f"{path}[{i}]"
                        self._extract_recursive(item, indexed_path, depth - 1)
                        
                        # 同时使用通用路径（仅第一个元素）
                        if i == 0:
                            generic_path = f"{path}[*]"
                            self._extract_recursive(item, generic_path, depth - 1)
                    else:
                        # 基本类型数组元素
                        element_path = f"{path}[*]"
                        self._add_field(element_path, item)
                        
    def _add_field(self, path: str, value: Any) -> None:
        """添加字段信息"""
        if path not in self.fields:
            self.fields[path] = FieldInfo(
                path=path,
                data_type=self._get_type(value),
                examples=[],
                unique_values=set()
            )
            
        field = self.fields[path]
        field.count += 1
        
        if value is None:
            field.null_count += 1
            return
            
        # 更新数据类型
        current_type = self._get_type(value)
        field.data_type = self._merge_types(field.data_type, current_type)
        
        # 添加示例值
        if len(field.examples) < self.max_examples:
            truncated = self._truncate_value(value)
            if truncated not in field.examples:
                field.examples.append(truncated)
                
        # 收集唯一值（仅基本类型）
        if isinstance(value, (str, int, float, bool)) and len(field.unique_values) < 50:
            field.unique_values.add(value)
            
        # 检查是否为枚举
        if (field.count >= 5 and 
            len(field.unique_values) <= min(50, field.count * 0.8) and
            field.data_type in ["string", "integer", "boolean"]):
            field.is_enum = True
            field.enum_values = sorted(list(field.unique_values))
            
    def _get_type(self, value: Any) -> str:
        """获取数据类型"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"  
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return self._get_string_type(value)
        elif isinstance(value, list):
            return "array" if value else "array[empty]"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
            
    def _get_string_type(self, value: str) -> str:
        """获取字符串子类型"""
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', value, re.I):
            return "uuid"
        elif re.match(r'^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z?$', value):
            return "datetime"
        elif value.startswith(('http://', 'https://')):
            return "url"
        elif value.startswith(('req_', 'toolu_', 'msg_')):
            return "id"
        else:
            return "string"
            
    def _merge_types(self, type1: str, type2: str) -> str:
        """合并数据类型"""
        if type1 == type2:
            return type1
        if type1 == "null":
            return type2
        if type2 == "null":
            return type1
        if {type1, type2} <= {"integer", "number"}:
            return "number"
        if {type1, type2} <= {"string", "uuid", "datetime", "url", "id"}:
            return "string"
        return "mixed"
        
    def _truncate_value(self, value: Any) -> Any:
        """截断过长值"""
        if isinstance(value, str) and len(value) > self.max_value_length:
            return value[:self.max_value_length] + "..."
        elif isinstance(value, (dict, list)):
            str_value = str(value)
            if len(str_value) > self.max_value_length:
                return str_value[:self.max_value_length] + "..."
            return str_value
        return value
        
    def merge_array_fields(self) -> None:
        """合并数组索引字段，如 content[0].title + content[1].title -> content[*].title"""
        self.logger.info("合并数组索引字段...")
        
        # 按模式分组字段
        pattern_groups = defaultdict(list)
        for field_path in list(self.fields.keys()):
            # 将 [数字] 和 [] 都替换为 [*]
            normalized = re.sub(r'\\[\\d*\\]', '[*]', field_path)
            if '[*]' in normalized and normalized != field_path:
                pattern_groups[normalized].append(field_path)
                
        merged_count = 0
        for normalized_path, similar_fields in pattern_groups.items():
            if len(similar_fields) <= 1:
                continue
                
            # 创建合并字段
            merged_field = FieldInfo(
                path=normalized_path,
                data_type="mixed",
                examples=[],
                unique_values=set()
            )
            
            # 合并信息
            all_examples = []
            data_types = set()
            
            for field_path in similar_fields:
                field = self.fields[field_path]
                merged_field.count += field.count
                merged_field.null_count += field.null_count
                data_types.add(field.data_type)
                all_examples.extend(field.examples)
                merged_field.unique_values.update(field.unique_values)
                del self.fields[field_path]
                
            # 设置合并后的类型
            merged_field.data_type = list(data_types)[0] if len(data_types) == 1 else "mixed"
            
            # 去重示例
            seen = set()
            for example in all_examples:
                if len(merged_field.examples) >= self.max_examples:
                    break
                example_str = str(example)
                if example_str not in seen:
                    seen.add(example_str)
                    merged_field.examples.append(example)
                    
            self.fields[normalized_path] = merged_field
            merged_count += len(similar_fields)
            
        self.logger.info(f"合并了 {merged_count} 个重复字段")
        
    def process_scan_result(self, scan_result_file: str) -> int:
        """基于T06扫描结果处理文件"""
        self.logger.info(f"加载扫描结果: {scan_result_file}")
        
        with open(scan_result_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        
        processed = 0
        file_details = scan_data.get("file_details", [])
        
        self.logger.info(f"开始处理 {len(file_details)} 个文件...")
        
        for file_info in file_details:
            file_path = file_info["path"]
            file_type = file_info["file_type"]
            
            count = self._process_file(file_path, file_type)
            processed += count
            self.total_files += 1
            
            if self.total_files % 50 == 0:
                self.logger.info(f"已处理 {self.total_files} 个文件, {processed:,} 条记录")
        
        return processed
        
    def _process_file(self, file_path: str, file_type: str) -> int:
        """处理单个文件"""
        processed = 0
        
        try:
            if file_type == "jsonl":
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_no, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                            
                        try:
                            record = json.loads(line)
                            self.extract_from_record(record)
                            processed += 1
                        except json.JSONDecodeError:
                            continue
                            
            else:  # json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.extract_from_record(data)
                    processed = 1
                    
        except Exception as e:
            self.logger.warning(f"文件处理错误 {file_path}: {e}")
            
        return processed
        
    def get_result(self) -> AnalysisResult:
        """获取分析结果"""
        # 合并数组字段
        self.merge_array_fields()
        
        # 统计数据类型分布
        type_dist = Counter(field.data_type for field in self.fields.values())
        
        return AnalysisResult(
            fields=self.fields,
            total_records=self.total_records,
            total_fields=len(self.fields),
            total_files=self.total_files,
            data_types=dict(type_dist)
        )


def generate_field_outputs(result: AnalysisResult, output_dir: Path):
    """生成字段分析输出"""
    
    # 1. 生成去重字段清单
    merged_count = sum(1 for field in result.fields.values() if '[*]' in field.path)
    
    deduplicated_output = {
        "生成时间": datetime.now().isoformat(),
        "任务信息": {
            "task_id": "T01",
            "task_name": "深度字段提取分析"
        },
        "统计信息": {
            "处理文件数": result.total_files,
            "处理记录数": result.total_records,
            "去重字段总数": result.total_fields,
            "合并字段数": merged_count
        },
        "字段清单": {}
    }
    
    # 按字段路径排序，生成字段清单 (字段路径作为键，示例值作为值)
    for field_path, field_info in sorted(result.fields.items()):
        # 取第一个示例值作为代表
        if field_info.examples:
            example_value = field_info.examples[0]
        else:
            # 如果没有示例，根据类型提供默认值
            type_defaults = {
                "string": "",
                "integer": 0,
                "boolean": False,
                "array": [],
                "object": {},
                "null": None
            }
            example_value = type_defaults.get(field_info.data_type, "")
            
        deduplicated_output["字段清单"][field_path] = example_value
        
    # 保存去重字段清单
    dedupe_file = output_dir / "deduplicated_fields.json"
    with open(dedupe_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_output, f, indent=2, ensure_ascii=False)
    
    # 2. 生成详细字段分析
    detailed_output = {
        "生成时间": datetime.now().isoformat(),
        "任务信息": {
            "task_id": "T01", 
            "task_name": "深度字段提取分析"
        },
        "统计信息": deduplicated_output["统计信息"],
        "数据类型分布": result.data_types,
        "字段详情": []
    }
    
    for field_path, field_info in sorted(result.fields.items()):
        field_detail = {
            "字段路径": field_path,
            "数据类型": field_info.data_type,
            "出现次数": field_info.count,
            "空值次数": field_info.null_count,
            "空值率": f"{field_info.null_count/field_info.count*100:.1f}%" if field_info.count > 0 else "0%",
            "示例值": field_info.examples,
            "是否枚举": field_info.is_enum,
            "枚举值": field_info.enum_values if field_info.is_enum else None
        }
        detailed_output["字段详情"].append(field_detail)
    
    # 保存详细分析
    detailed_file = output_dir / "field_analysis_detailed.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_output, f, indent=2, ensure_ascii=False)
    
    return [dedupe_file, detailed_file]


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python field_extractor.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔍 T01: 深度字段提取分析任务")
    print("=" * 50)
    
    # 查找T06的扫描结果
    scan_result_file = output_dir.parent / "T06_data_scan" / "scan_results.json"
    if not scan_result_file.exists():
        print(f"❌ 依赖文件不存在: {scan_result_file}")
        print("   请先执行 T06 数据源扫描任务")
        sys.exit(1)
    
    # 执行字段提取
    extractor = FieldExtractor()
    processed_records = extractor.process_scan_result(str(scan_result_file))
    
    # 获取分析结果
    result = extractor.get_result()
    
    # 生成输出文件
    output_files = generate_field_outputs(result, output_dir)
    
    print(f"\\n✅ T01 任务完成")
    print(f"📊 提取结果:")
    print(f"   处理文件: {result.total_files}")
    print(f"   处理记录: {result.total_records:,}")
    print(f"   提取字段: {result.total_fields}")
    print(f"   数组合并: {sum(1 for f in result.fields.values() if '[*]' in f.path)}")
    
    print(f"\\n📁 输出文件:")
    for output_file in output_files:
        print(f"   {output_file}")


if __name__ == "__main__":
    main()