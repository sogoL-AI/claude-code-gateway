#!/usr/bin/env python3
"""
运行深度Claude CLI字段分析，专门捕获深层嵌套字段
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from analyzers.main_analyzer import MainAnalyzer
from core.field_extractor import FieldExtractor


def run_deep_analysis():
    print("🔍 启动深度字段分析，专门查找subagent等深层字段...")
    
    # 设置输出目录
    output_dir = Path(__file__).parent / "outputs"
    
    # 创建增强的字段分析器
    analyzer = MainAnalyzer(output_dir=str(output_dir))
    
    # 重新运行字段提取，重点关注深层嵌套
    print("\n🚀 重新扫描和分析...")
    scan_result = analyzer.scanner.scan_all_sessions()
    
    # 创建新的字段提取器，专门处理深层嵌套
    deep_extractor = FieldExtractor(max_unique_values=100, max_examples=20)
    
    print(f"\n🔎 深度提取字段，重点关注工具input和subagent...")
    
    processed_records = 0
    subagent_records = 0
    tool_use_records = 0
    
    for i, session_file in enumerate(scan_result.session_files, 1):
        if session_file.file_type != "jsonl":
            continue
            
        print(f"[{i}/{scan_result.total_files}] 深度分析: {session_file.session_id}")
        
        try:
            with open(session_file.file_path, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        import ujson
                        record = ujson.loads(line)
                        
                        # 深度递归提取字段，增加递归深度
                        deep_extractor.extract_fields_from_value(record, max_depth=25)
                        processed_records += 1
                        
                        # 特别检查subagent相关记录
                        record_str = str(record).lower()
                        if 'subagent' in record_str:
                            subagent_records += 1
                            
                        if 'tool_use' in record_str:
                            tool_use_records += 1
                        
                        if processed_records % 5000 == 0:
                            print(f"    已处理 {processed_records} 条记录...")
                            
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"  文件处理错误: {e}")
            continue
    
    print(f"\n📊 深度分析统计:")
    print(f"   总处理记录: {processed_records}")
    print(f"   包含subagent的记录: {subagent_records}")
    print(f"   包含tool_use的记录: {tool_use_records}")
    
    # 生成深度分析结果
    deep_result = deep_extractor.generate_extraction_result()
    
    print(f"\n🎯 深度字段发现:")
    print(f"   总字段数: {deep_result.total_fields_discovered}")
    print(f"   枚举字段数: {len(deep_result.enum_fields)}")
    
    # 特别关注subagent相关字段
    subagent_fields = {}
    tool_input_fields = {}
    
    for field_path, field_info in deep_result.field_registry.items():
        if 'subagent' in field_path.lower():
            subagent_fields[field_path] = field_info
        if 'input.' in field_path and 'tool_use' in field_path:
            tool_input_fields[field_path] = field_info
    
    print(f"\n🤖 Subagent相关字段 ({len(subagent_fields)}个):")
    for field_path in sorted(subagent_fields.keys()):
        field_info = subagent_fields[field_path]
        if field_info.is_enum:
            print(f"   • {field_path} [{field_info.data_type}]: {field_info.enum_values}")
        else:
            print(f"   • {field_path} [{field_info.data_type}]: {field_info.occurrence_count}次")
    
    print(f"\n⚙️ 工具Input参数字段 (前20个):")
    tool_input_sorted = sorted(tool_input_fields.items(), key=lambda x: x[1].occurrence_count, reverse=True)
    for field_path, field_info in tool_input_sorted[:20]:
        if field_info.is_enum:
            print(f"   • {field_path} [{field_info.data_type}]: {field_info.enum_values}")
        else:
            print(f"   • {field_path} [{field_info.data_type}]: {field_info.occurrence_count}次")
    
    # 保存深度分析结果
    deep_output_file = output_dir / "fields" / "deep_extraction_result.json"
    import ujson
    
    serializable_fields = {}
    for field_path, field_info in deep_result.field_registry.items():
        serializable_fields[field_path] = {
            "path": field_info.path,
            "data_type": field_info.data_type,
            "value_examples": field_info.value_examples,
            "occurrence_count": field_info.occurrence_count,
            "null_count": field_info.null_count,
            "unique_values": list(field_info.unique_values),
            "is_enum": field_info.is_enum,
            "enum_values": field_info.enum_values,
            "value_patterns": field_info.value_patterns
        }
    
    deep_serializable_data = {
        "total_records_processed": processed_records,
        "total_fields_discovered": deep_result.total_fields_discovered,
        "subagent_records_found": subagent_records,
        "tool_use_records_found": tool_use_records,
        "data_type_distribution": deep_result.data_type_distribution,
        "enum_fields": deep_result.enum_fields,
        "field_registry": serializable_fields,
        "subagent_fields": {k: v.enum_values if v.is_enum else v.occurrence_count for k, v in subagent_fields.items()},
        "tool_input_fields": {k: v.enum_values if v.is_enum else v.occurrence_count for k, v in tool_input_fields.items()}
    }
    
    with open(deep_output_file, 'w', encoding='utf-8') as f:
        ujson.dump(deep_serializable_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 深度分析结果已保存: {deep_output_file}")
    
    return deep_serializable_data


if __name__ == "__main__":
    result = run_deep_analysis()