#!/usr/bin/env python3
"""
T02: 消息结构类型分析任务
基于完整结构签名分类414种数据类型
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any, Tuple, Union
from collections import defaultdict, Counter
from dataclasses import dataclass, field

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils import setup_logging


@dataclass
class ObjectType:
    """对象类型信息"""
    structure_signature: str  # 完整结构签名
    count: int = 0  # 出现次数
    examples: List[Dict[str, Any]] = field(default_factory=list)  # 示例对象
    
    def add_example(self, obj: Dict[str, Any], max_examples: int = 5):
        """添加示例对象"""
        self.count += 1
        if len(self.examples) < max_examples:
            self.examples.append(obj)


class ObjectTypeAnalyzer:
    """深度对象类型分析器"""
    
    def __init__(self, max_examples: int = 5):
        self.max_examples = max_examples
        self.object_types: Dict[str, ObjectType] = {}
        self.total_objects = 0
        self.total_files = 0
        self.logger = setup_logging("T02_TypeAnalyzer")
        
    def truncate_value(self, value: Any, max_length: int = 100) -> Any:
        """递归截断最深层的值，保持嵌套结构完整"""
        if isinstance(value, str) and len(value) > max_length:
            return value[:max_length] + "..."
        elif isinstance(value, dict):
            # 递归处理字典中的每个值，保持结构
            return {k: self.truncate_value(v, max_length) for k, v in value.items()}
        elif isinstance(value, list):
            # 递归处理列表中的每个元素，保持结构
            return [self.truncate_value(item, max_length) for item in value]
        else:
            # 其他类型（int, float, bool, None等）直接返回
            return value
    
    def truncate_example_object(self, obj: Dict[str, Any], max_length: int = 100) -> Dict[str, Any]:
        """截断示例对象中的长值"""
        return {k: self.truncate_value(v, max_length) for k, v in obj.items()}

    def generate_structure_signature(self, obj: Any) -> str:
        """递归生成完整结构签名"""
        if obj is None:
            return "null"
        elif isinstance(obj, bool):
            return "boolean"
        elif isinstance(obj, int):
            return "integer"
        elif isinstance(obj, float):
            return "number"
        elif isinstance(obj, str):
            return "string"
        elif isinstance(obj, list):
            if not obj:
                return "array[]"
            # 分析数组中元素的结构类型
            element_signatures = set()
            for item in obj[:10]:  # 只分析前10个元素避免性能问题
                element_signatures.add(self.generate_structure_signature(item))
            # 如果数组中所有元素结构相同，用单一类型表示
            if len(element_signatures) == 1:
                return f"array[{list(element_signatures)[0]}]"
            else:
                # 如果元素类型不同，列出所有类型
                sorted_sigs = sorted(list(element_signatures))
                return f"array[{','.join(sorted_sigs)}]"
        elif isinstance(obj, dict):
            if not obj:
                return "object{}"
            # 递归生成所有字段的结构签名
            field_signatures = []
            for key in sorted(obj.keys()):  # 排序确保签名一致性
                value_sig = self.generate_structure_signature(obj[key])
                field_signatures.append(f"{key}:{value_sig}")
            return f"object{{{','.join(field_signatures)}}}"
        else:
            return f"unknown({type(obj).__name__})"
            
    def analyze_object(self, obj: Dict[str, Any]) -> None:
        """分析单个对象"""
        if not isinstance(obj, dict):
            return
            
        self.total_objects += 1
        
        # 生成完整结构签名
        structure_signature = self.generate_structure_signature(obj)
        
        # 如果是新的类型，创建ObjectType
        if structure_signature not in self.object_types:
            self.object_types[structure_signature] = ObjectType(
                structure_signature=structure_signature
            )
            
        # 添加到对应类型
        self.object_types[structure_signature].add_example(obj, self.max_examples)
        
    def analyze_record(self, record: Dict[str, Any]) -> None:
        """递归分析记录中的所有对象"""
        self._analyze_recursive(record)
        
    def _analyze_recursive(self, value: Any, depth: int = 20) -> None:
        """递归分析对象"""
        if depth <= 0:
            return
            
        if isinstance(value, dict):
            # 分析当前对象
            self.analyze_object(value)
            
            # 递归分析子对象
            for v in value.values():
                self._analyze_recursive(v, depth - 1)
                
        elif isinstance(value, list):
            # 递归分析数组中的元素
            for item in value:
                self._analyze_recursive(item, depth - 1)
                
    def process_scan_result(self, scan_result_file: str) -> int:
        """基于T06扫描结果处理文件"""
        self.logger.info(f"加载扫描结果: {scan_result_file}")
        
        with open(scan_result_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        
        processed = 0
        file_details = scan_data.get("file_details", [])
        
        self.logger.info(f"开始分析 {len(file_details)} 个文件...")
        
        for file_info in file_details:
            file_path = file_info["path"]
            file_type = file_info["file_type"]
            
            count = self._process_file(file_path, file_type)
            processed += count
            self.total_files += 1
            
            if self.total_files % 50 == 0:
                self.logger.info(f"已分析 {self.total_files} 个文件, {processed:,} 条记录")
        
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
                            self.analyze_record(record)
                            processed += 1
                            
                            if processed % 1000 == 0:
                                self.logger.info(f"    已分析 {processed} 条记录...")
                                
                        except json.JSONDecodeError:
                            continue
                            
            else:  # json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.analyze_record(data)
                    processed = 1
                    
        except Exception as e:
            self.logger.warning(f"文件处理错误 {file_path}: {e}")
            
        return processed
        
    def get_results(self) -> Dict[str, Any]:
        """获取分析结果（带值截断）"""
        # 按出现次数排序
        sorted_types = sorted(
            self.object_types.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        results = {
            "生成时间": datetime.now().isoformat(),
            "任务信息": {
                "task_id": "T02",
                "task_name": "消息结构类型分析"
            },
            "说明": "Claude CLI深度对象类型分析结果 - 按完整嵌套结构分类（示例值已截断）",
            "统计信息": {
                "处理文件数": self.total_files,
                "分析对象总数": self.total_objects,
                "发现类型数": len(self.object_types)
            },
            "类型详情": []
        }
        
        for i, (signature, obj_type) in enumerate(sorted_types, 1):
            # 计算结构复杂度（大致）
            complexity = signature.count(':') + signature.count('[') + signature.count('{')
            
            # 截断示例对象中的长值
            truncated_examples = [
                self.truncate_example_object(example) 
                for example in obj_type.examples
            ]
            
            type_info = {
                "类型ID": f"type_{i:03d}",
                "结构签名": signature,
                "结构复杂度": complexity,
                "出现次数": obj_type.count,
                "占比": f"{obj_type.count/self.total_objects*100:.2f}%",
                "示例对象": truncated_examples
            }
            results["类型详情"].append(type_info)
            
        return results
        
    def get_compact_results(self) -> Dict[str, Any]:
        """获取紧凑分析结果（每种类型只保留一个示例）"""
        # 按出现次数排序
        sorted_types = sorted(
            self.object_types.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        results = {
            "生成时间": datetime.now().isoformat(),
            "任务信息": {
                "task_id": "T02",
                "task_name": "消息结构类型分析"
            },
            "说明": "Claude CLI深度对象类型分析结果 - 紧凑版（每种类型只保留一个示例）",
            "统计信息": {
                "处理文件数": self.total_files,
                "分析对象总数": self.total_objects,
                "发现类型数": len(self.object_types)
            },
            "类型详情": []
        }
        
        for i, (signature, obj_type) in enumerate(sorted_types, 1):
            # 计算结构复杂度（大致）
            complexity = signature.count(':') + signature.count('[') + signature.count('{')
            
            # 只保留第一个示例，并截断长值
            single_example = None
            if obj_type.examples:
                single_example = self.truncate_example_object(obj_type.examples[0])
            
            type_info = {
                "类型ID": f"type_{i:03d}",
                "结构签名": signature,
                "结构复杂度": complexity,
                "出现次数": obj_type.count,
                "占比": f"{obj_type.count/self.total_objects*100:.2f}%",
                "示例对象": single_example
            }
            results["类型详情"].append(type_info)
            
        return results
        
    def get_type_summary(self) -> Dict[str, Any]:
        """获取类型摘要信息"""
        # 按结构复杂度分组统计
        complexity_dist = Counter()
        occurrence_dist = Counter()
        
        for obj_type in self.object_types.values():
            # 计算结构复杂度
            complexity = obj_type.structure_signature.count(':') + obj_type.structure_signature.count('[') + obj_type.structure_signature.count('{')
            complexity_dist[complexity] += 1
            
            # 按出现次数分组（1, 2-5, 6-10, 11-50, 50+）
            if obj_type.count == 1:
                occurrence_dist["单次出现"] += 1
            elif obj_type.count <= 5:
                occurrence_dist["2-5次"] += 1
            elif obj_type.count <= 10:
                occurrence_dist["6-10次"] += 1
            elif obj_type.count <= 50:
                occurrence_dist["11-50次"] += 1
            else:
                occurrence_dist["50次以上"] += 1
                
        summary = {
            "生成时间": datetime.now().isoformat(),
            "任务信息": {
                "task_id": "T02",
                "task_name": "消息结构类型分析"
            },
            "说明": "深度对象类型分析摘要",
            "统计信息": {
                "处理文件数": self.total_files,
                "分析对象总数": self.total_objects,
                "发现类型数": len(self.object_types)
            },
            "结构复杂度分布": dict(complexity_dist),
            "出现次数分布": dict(occurrence_dist),
            "热门类型": []
        }
        
        # 添加最常见的10种类型
        sorted_types = sorted(
            self.object_types.items(),
            key=lambda x: x[1].count,
            reverse=True
        )
        
        for i, (signature, obj_type) in enumerate(sorted_types[:20], 1):
            complexity = signature.count(':') + signature.count('[') + signature.count('{')
            # 截断过长的签名用于显示
            display_signature = signature[:200] + "..." if len(signature) > 200 else signature
            
            hot_type = {
                "排名": i,
                "结构签名": display_signature,
                "结构复杂度": complexity,
                "出现次数": obj_type.count,
                "占比": f"{obj_type.count/self.total_objects*100:.2f}%"
            }
            summary["热门类型"].append(hot_type)
            
        return summary


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python type_analyzer.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🏗️ T02: 消息结构类型分析任务")
    print("=" * 50)
    
    # 查找T06的扫描结果
    scan_result_file = output_dir.parent / "T06_data_scan" / "scan_results.json"
    if not scan_result_file.exists():
        print(f"❌ 依赖文件不存在: {scan_result_file}")
        print("   请先执行 T06 数据源扫描任务")
        sys.exit(1)
    
    # 执行类型分析
    analyzer = ObjectTypeAnalyzer()
    processed_records = analyzer.process_scan_result(str(scan_result_file))
    
    print(f"\\n✅ 类型分析完成！")
    print(f"   处理文件: {analyzer.total_files}")
    print(f"   处理记录: {processed_records:,}")
    print(f"   分析对象: {analyzer.total_objects:,}")
    print(f"   发现类型: {len(analyzer.object_types)}")
    
    # 生成详细结果（带值截断）
    print(f"\\n📋 生成详细类型分析（值已截断）...")
    results = analyzer.get_results()
    
    detail_file = output_dir / "object_types_detail.json"
    with open(detail_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"   详细结果: {detail_file}")
    
    # 生成紧凑结果（每种类型只保留一个示例）
    print(f"\\n📋 生成紧凑版类型分析...")
    compact_results = analyzer.get_compact_results()
    
    compact_file = output_dir / "object_types_compact.json"
    with open(compact_file, 'w', encoding='utf-8') as f:
        json.dump(compact_results, f, ensure_ascii=False, indent=2)
    print(f"   紧凑结果: {compact_file}")
    
    # 生成摘要结果
    print(f"\\n📊 生成类型摘要...")
    summary = analyzer.get_type_summary()
    
    summary_file = output_dir / "object_types_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"   摘要结果: {summary_file}")
    
    # 显示热门类型
    print(f"\\n🔥 热门对象类型 (Top 10):")
    for i, hot_type in enumerate(summary["热门类型"][:10], 1):
        signature = hot_type["结构签名"]
        complexity = hot_type["结构复杂度"]
        signature_preview = signature[:80] + "..." if len(signature) > 80 else signature
        print(f"   {i:2d}. {hot_type['出现次数']:6,}次 ({hot_type['占比']:>6s}) - 复杂度{complexity:2d}")
        print(f"       {signature_preview}")
    
    # 显示结构复杂度分布
    print(f"\\n📈 结构复杂度分布 (Top 10):")
    complexity_items = sorted(summary["结构复杂度分布"].items(), key=lambda x: x[1], reverse=True)
    for complexity, type_count in complexity_items[:10]:
        print(f"   复杂度{complexity:2d}: {type_count:4d}种类型")
    
    print(f"\\n🎉 T02任务完成！结果文件保存在 {output_dir} 目录")


if __name__ == "__main__":
    main()