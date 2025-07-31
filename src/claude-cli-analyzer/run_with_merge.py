#!/usr/bin/env python3
"""
使用字段合并功能运行完整分析
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def truncate_value_for_output(value, max_length=100):
    """为输出截断值"""
    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "..."
    elif isinstance(value, (dict, list)):
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length] + "..."
        return str_value
    return value

def truncate_examples_list(examples, max_length=100):
    """截断示例值列表"""
    return [truncate_value_for_output(example, max_length) for example in examples]

def main():
    print("🚀 启动Claude CLI字段分析 (包含字段合并功能)")
    print("=" * 60)
    
    try:
        from core.field_extractor import FieldExtractor
        from core.session_scanner import SessionScanner
        
        # 1. 扫描会话文件
        print("\n📁 第1步：扫描Claude CLI会话文件...")
        scanner = SessionScanner()
        scan_result = scanner.scan_all_sessions()
        
        print(f"✅ 扫描完成！")
        print(f"   📂 总文件数: {scan_result.total_files}")
        print(f"   📝 总记录数: {scan_result.total_records}")
        print(f"   💾 总大小: {scan_result.total_size_bytes / (1024*1024):.1f} MB")
        
        # 创建输出目录
        output_dir = current_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        for subdir in ["sessions", "fields", "reports"]:
            (output_dir / subdir).mkdir(exist_ok=True)
        
        # 保存扫描结果
        scan_result_dict = {
            "total_files": scan_result.total_files,
            "total_records": scan_result.total_records,
            "total_size_bytes": scan_result.total_size_bytes,
            "projects": scan_result.projects,
            "files": [{"path": f.file_path, "size": f.file_size, "records": f.record_count} for f in scan_result.session_files]
        }
        with open(output_dir / "sessions" / "scan_result.json", 'w', encoding='utf-8') as f:
            json.dump(scan_result_dict, f, ensure_ascii=False, indent=2)
        
        # 2. 提取字段信息
        print(f"\n🔍 第2步：提取字段信息...")
        extractor = FieldExtractor()
        
        # 处理前100个文件以加快速度
        files_to_process = scan_result.session_files[:100]
        processed_count = 0
        
        for i, file_info in enumerate(files_to_process):
            file_path = file_info.file_path
            print(f"[{i+1:3}/{len(files_to_process)}] {Path(file_path).name}")
            
            try:
                count = extractor.process_jsonl_file(file_path, max_records=1000)
                processed_count += count
                
                if processed_count % 5000 == 0:
                    print(f"  已累计处理 {processed_count} 条记录...")
                    
            except Exception as e:
                print(f"  ⚠️  处理文件出错: {e}")
                continue
        
        print(f"✅ 字段提取完成，累计处理 {processed_count} 条记录")
        
        # 3. 生成分析结果（自动包含字段合并）
        print(f"\n⚙️  第3步：生成分析结果 (包含字段合并)")
        
        # 显示合并前的字段数
        print(f"合并前发现字段: {len(extractor.field_registry)} 个")
        
        # 显示一些典型的重复字段示例
        array_fields = [path for path in extractor.field_registry.keys() if '[' in path and ']' in path]
        if array_fields:
            print(f"数组索引字段示例:")
            for field in sorted(array_fields)[:5]:
                print(f"   • {field}")
        
        # 生成结果（会自动调用字段合并）
        result = extractor.generate_extraction_result()
        
        print(f"✅ 分析完成！")
        print(f"   🔍 合并后字段数: {result.total_fields_discovered}")
        print(f"   📊 处理记录总数: {result.total_records_processed}")
        print(f"   🏷️  枚举字段数: {len(result.enum_fields)}")
        
        # 4. 保存结果
        print(f"\n💾 第4步：保存分析结果...")
        
        # 保存字段提取结果
        result_dict = {
            "生成时间": datetime.now().isoformat(),
            "总结": {
                "处理文件数": len(files_to_process),
                "处理记录数": result.total_records_processed,
                "发现字段数": result.total_fields_discovered,
                "枚举字段数": len(result.enum_fields)
            },
            "数据类型分布": result.data_type_distribution,
            "枚举字段": {path: truncate_examples_list(values) for path, values in result.enum_fields.items()},
            "字段详情": {}
        }
        
        # 转换字段信息
        for path, info in result.field_registry.items():
            result_dict["字段详情"][path] = {
                "数据类型": info.data_type,
                "出现次数": info.occurrence_count,
                "空值次数": info.null_count,
                "示例值": truncate_examples_list(info.value_examples[:3]),
                "是否枚举": info.is_enum
            }
        
        # 保存结果
        with open(output_dir / "fields" / "extraction_result.json", 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        
        # 生成报告
        report = {
            "分析报告": "Claude CLI 字段分析报告 (含字段合并)",
            "生成时间": datetime.now().isoformat(),
            "扫描统计": {
                "总文件数": scan_result.total_files,
                "处理文件数": len(files_to_process),
                "总记录数": scan_result.total_records,
                "处理记录数": result.total_records_processed
            },
            "字段统计": {
                "发现字段总数": result.total_fields_discovered,
                "枚举字段数": len(result.enum_fields),
                "数据类型分布": result.data_type_distribution
            },
            "字段合并效果": {
                "合并字段数量": len([p for p in result.field_registry.keys() if '[*]' in p]),
                "合并字段示例": [p for p in result.field_registry.keys() if '[*]' in p][:10]
            }
        }
        
        with open(output_dir / "reports" / "analysis_report.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 5. 显示结果摘要
        print(f"\n🎉 分析完成！主要发现:")
        print(f"   📁 处理文件: {len(files_to_process)} / {scan_result.total_files} 个")
        print(f"   📝 处理记录: {result.total_records_processed:,} 条")
        print(f"   🔍 发现字段: {result.total_fields_discovered} 个")
        print(f"   🏷️  枚举字段: {len(result.enum_fields)} 个")
        
        # 显示最常用字段
        sorted_fields = sorted(result.field_registry.items(), 
                             key=lambda x: x[1].occurrence_count, reverse=True)
        
        print(f"\n📊 最常用的10个字段:")
        for i, (path, info) in enumerate(sorted_fields[:10], 1):
            print(f"   {i:2d}. {path:<35} {info.data_type:<12} ({info.occurrence_count:,}次)")
        
        # 显示字段合并效果
        merged_fields = [path for path in result.field_registry.keys() if '[*]' in path]
        if merged_fields:
            print(f"\n🔄 字段合并效果 (共{len(merged_fields)}个合并字段):")
            for field in merged_fields[:5]:
                info = result.field_registry[field]
                print(f"   • {field} ({info.occurrence_count:,}次)")
        
        print(f"\n📂 详细结果已保存到: {output_dir}")
        print(f"   - sessions/scan_result.json")
        print(f"   - fields/extraction_result.json")  
        print(f"   - reports/analysis_report.json")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)