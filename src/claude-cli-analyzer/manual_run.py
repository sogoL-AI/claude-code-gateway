#!/usr/bin/env python3
"""
手动运行Claude CLI分析
"""

import sys
import os
import json
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 直接导入需要的模块
from core.field_extractor import FieldExtractor
from core.session_scanner import SessionScanner

def main():
    print("🚀 手动启动Claude CLI字段分析...")
    
    try:
        # 1. 扫描会话文件
        print("\n=== 第1步：扫描会话文件 ===")
        scanner = SessionScanner()
        scan_result = scanner.scan_sessions()
        
        print(f"✅ 扫描完成！")
        print(f"   总文件数: {scan_result['total_files']}")
        print(f"   总记录数: {scan_result['total_records']}")
        
        # 创建输出目录
        output_dir = current_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        (output_dir / "sessions").mkdir(exist_ok=True)
        
        # 保存扫描结果
        with open(output_dir / "sessions" / "scan_result.json", 'w', encoding='utf-8') as f:
            json.dump(scan_result, f, ensure_ascii=False, indent=2)
            
        # 2. 提取字段
        print(f"\n=== 第2步：提取字段信息 ===")
        extractor = FieldExtractor()
        
        processed_files = 0
        for file_info in scan_result['files'][:50]:  # 限制处理前50个文件
            file_path = file_info['path']
            print(f"[{processed_files+1}] 处理: {file_path}")
            
            count = extractor.process_jsonl_file(file_path, max_records=2000)
            print(f"  ✓ 已处理 {count} 条记录")
            processed_files += 1
            
        # 3. 生成结果
        print(f"\n=== 第3步：生成分析结果 ===")
        result = extractor.generate_extraction_result()
        
        print(f"✅ 字段提取完成！")
        print(f"   发现字段: {result.total_fields_discovered}")
        print(f"   处理记录: {result.total_records_processed}")
        print(f"   枚举字段: {len(result.enum_fields)}")
        
        # 保存结果
        (output_dir / "fields").mkdir(exist_ok=True)
        
        # 转换结果为可序列化格式
        result_dict = {
            "total_records_processed": result.total_records_processed,
            "total_fields_discovered": result.total_fields_discovered,
            "data_type_distribution": result.data_type_distribution,
            "enum_fields": result.enum_fields,
            "field_registry": {}
        }
        
        for path, info in result.field_registry.items():
            result_dict["field_registry"][path] = {
                "path": info.path,
                "data_type": info.data_type,
                "occurrence_count": info.occurrence_count,
                "null_count": info.null_count,
                "value_examples": info.value_examples[:5],  # 只保存前5个示例
                "is_enum": info.is_enum,
                "enum_values": info.enum_values if info.is_enum else []
            }
        
        with open(output_dir / "fields" / "extraction_result.json", 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        
        print(f"\n📂 结果已保存到: {output_dir}")
        print(f"   - sessions/scan_result.json")
        print(f"   - fields/extraction_result.json")
        
        # 显示前10个最常用字段
        print(f"\n📊 最常用的10个字段:")
        sorted_fields = sorted(result.field_registry.items(), 
                             key=lambda x: x[1].occurrence_count, reverse=True)
        
        for i, (path, info) in enumerate(sorted_fields[:10], 1):
            print(f"   {i:2d}. {path:<40} {info.data_type:<15} ({info.occurrence_count}次)")
        
        # 显示合并效果
        merged_fields = [path for path in result.field_registry.keys() if '[*]' in path]
        print(f"\n🔄 字段合并效果:")
        print(f"   合并后的字段数量: {len(merged_fields)}")
        if merged_fields:
            print(f"   合并字段示例:")
            for field in merged_fields[:5]:
                info = result.field_registry[field]
                print(f"     • {field} ({info.occurrence_count}次)")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())