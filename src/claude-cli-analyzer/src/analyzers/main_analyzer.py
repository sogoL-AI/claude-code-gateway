#!/usr/bin/env python3
"""
Claude CLI Main Analyzer
主分析器，协调扫描和字段提取工作
"""

import os
import json
import ujson
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

from core.session_scanner import SessionScanner, ScanResult
from core.field_extractor import FieldExtractor, ExtractionResult, FieldInfo


class MainAnalyzer:
    """主分析器"""
    
    def __init__(self, output_dir: str = None):
        self.scanner = SessionScanner()
        self.field_extractor = FieldExtractor()
        self.output_dir = output_dir or "./outputs"
        self.ensure_output_directories()
        
    def ensure_output_directories(self):
        """确保输出目录存在"""
        for subdir in ["sessions", "analysis", "fields", "reports"]:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
    
    def run_complete_analysis(self, max_records_per_file: int = None) -> Dict[str, Any]:
        """运行完整分析"""
        print("🚀 开始Claude CLI完整分析...")
        
        # 第1步：扫描所有会话文件
        print("\n=== 第1步：扫描会话文件 ===")
        scan_result = self.scanner.scan_all_sessions()
        self.save_scan_result(scan_result)
        
        # 第2步：提取字段信息
        print("\n=== 第2步：提取字段信息 ===")
        extraction_result = self.extract_all_fields(scan_result, max_records_per_file)
        self.save_extraction_result(extraction_result)
        
        # 第3步：生成分析报告
        print("\n=== 第3步：生成分析报告 ===")
        analysis_report = self.generate_analysis_report(scan_result, extraction_result)
        self.save_analysis_report(analysis_report)
        
        print("\n✅ 完整分析完成!")
        return analysis_report
    
    def extract_all_fields(self, scan_result: ScanResult, max_records_per_file: int = None) -> ExtractionResult:
        """从所有会话文件中提取字段"""
        print(f"📊 开始字段提取，共 {scan_result.total_files} 个文件...")
        
        total_processed = 0
        
        for i, session_file in enumerate(scan_result.session_files, 1):
            print(f"[{i}/{scan_result.total_files}] 处理: {session_file.file_path}")
            
            if session_file.file_type == "jsonl":
                processed = self.field_extractor.process_jsonl_file(
                    session_file.file_path, 
                    max_records_per_file
                )
            elif session_file.file_type == "json":
                processed = self.field_extractor.process_json_file(session_file.file_path)
            else:
                print(f"  跳过未知文件类型: {session_file.file_type}")
                continue
            
            total_processed += processed
            print(f"  ✓ 已处理 {processed} 条记录")
        
        print(f"\n📈 字段提取完成，总共处理 {total_processed} 条记录")
        self.field_extractor.print_field_summary()
        
        return self.field_extractor.generate_extraction_result()
    
    def generate_analysis_report(self, scan_result: ScanResult, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """生成分析报告"""
        print("📋 生成分析报告...")
        
        # 构建字段规范表
        field_specifications = []
        for field_path, field_info in extraction_result.field_registry.items():
            # 计算出现频率
            frequency = (field_info.occurrence_count / extraction_result.total_records_processed * 100) if extraction_result.total_records_processed > 0 else 0
            
            # 准备示例值
            examples = field_info.value_examples[:3] if field_info.value_examples else []
            examples_str = ", ".join([f'"{ex}"' if isinstance(ex, str) else str(ex) for ex in examples])
            
            field_specifications.append({
                "字段名": field_path,
                "类型": field_info.data_type,
                "描述": self.generate_field_description(field_path, field_info),
                "示例": examples_str,
                "出现频率": f"{frequency:.1f}%",
                "出现次数": field_info.occurrence_count,
                "是否枚举": "是" if field_info.is_enum else "否",
                "枚举值": field_info.enum_values if field_info.is_enum else None,
                "空值次数": field_info.null_count,
                "值模式": ", ".join(field_info.value_patterns) if field_info.value_patterns else ""
            })
        
        # 按出现频率排序
        field_specifications.sort(key=lambda x: x["出现次数"], reverse=True)
        
        # 构建报告
        report = {
            "生成时间": datetime.now().isoformat(),
            "扫描统计": {
                "总文件数": scan_result.total_files,
                "总记录数": scan_result.total_records,
                "总大小MB": round(scan_result.total_size_bytes / 1024 / 1024, 2),
                "项目数": len(scan_result.projects),
                "时间范围": {
                    "开始": scan_result.date_range[0].isoformat() if scan_result.date_range else None,
                    "结束": scan_result.date_range[1].isoformat() if scan_result.date_range else None
                }
            },
            "字段分析": {
                "发现字段总数": extraction_result.total_fields_discovered,
                "处理记录总数": extraction_result.total_records_processed,
                "枚举字段数": len(extraction_result.enum_fields),
                "数据类型分布": extraction_result.data_type_distribution
            },
            "字段规范": field_specifications,
            "枚举字段完整列表": extraction_result.enum_fields,
            "项目分布": scan_result.projects
        }
        
        return report
    
    def generate_field_description(self, field_path: str, field_info: FieldInfo) -> str:
        """生成字段描述"""
        descriptions = {
            "sessionId": "会话唯一标识符",
            "uuid": "记录唯一标识符", 
            "parentUuid": "父级记录UUID",
            "timestamp": "记录时间戳",
            "type": "记录类型",
            "message.role": "消息角色",
            "message.content": "消息内容",
            "message.id": "消息ID",
            "message.model": "使用的模型",
            "message.type": "消息类型",
            "cwd": "当前工作目录",
            "version": "Claude Code版本",
            "gitBranch": "Git分支",
            "userType": "用户类型",
            "isSidechain": "是否为侧链记录",
            "isMeta": "是否为元数据",
            "requestId": "API请求ID",
            "isVisibleInTranscriptOnly": "是否仅在转录中可见"
        }
        
        # 尝试匹配已知描述
        for pattern, desc in descriptions.items():
            if pattern in field_path:
                return desc
        
        # 基于字段路径推断描述
        if "tool_use" in field_path:
            return "工具使用相关"
        elif "content" in field_path:
            return "内容相关"
        elif "usage" in field_path:
            return "使用统计相关"
        elif field_info.is_enum:
            return f"枚举值，可选: {', '.join(map(str, field_info.enum_values))}"
        else:
            return f"{field_info.data_type}类型字段"
    
    def save_scan_result(self, scan_result: ScanResult):
        """保存扫描结果"""
        output_file = os.path.join(self.output_dir, "sessions", "scan_result.json")
        
        # 转换为可序列化的格式
        serializable_data = {
            "total_files": scan_result.total_files,
            "total_records": scan_result.total_records,
            "total_size_bytes": scan_result.total_size_bytes,
            "projects": scan_result.projects,
            "date_range": [
                scan_result.date_range[0].isoformat(),
                scan_result.date_range[1].isoformat()
            ] if scan_result.date_range else None,
            "session_files": [
                {
                    "file_path": sf.file_path,
                    "file_size": sf.file_size,
                    "session_id": sf.session_id,
                    "project_path": sf.project_path,
                    "last_modified": sf.last_modified.isoformat(),
                    "record_count": sf.record_count,
                    "file_type": sf.file_type
                }
                for sf in scan_result.session_files
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            ujson.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 扫描结果已保存: {output_file}")
    
    def save_extraction_result(self, extraction_result: ExtractionResult):
        """保存字段提取结果"""
        output_file = os.path.join(self.output_dir, "fields", "extraction_result.json")
        
        # 转换字段信息为可序列化格式
        serializable_fields = {}
        for field_path, field_info in extraction_result.field_registry.items():
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
        
        serializable_data = {
            "total_records_processed": extraction_result.total_records_processed,
            "total_fields_discovered": extraction_result.total_fields_discovered,
            "data_type_distribution": extraction_result.data_type_distribution,
            "enum_fields": extraction_result.enum_fields,
            "field_registry": serializable_fields
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            ujson.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 字段提取结果已保存: {output_file}")
    
    def save_analysis_report(self, report: Dict[str, Any]):
        """保存分析报告"""
        # 保存完整JSON报告
        json_file = os.path.join(self.output_dir, "reports", "analysis_report.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            ujson.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存字段规范表为CSV
        csv_file = os.path.join(self.output_dir, "reports", "field_specifications.csv")
        df = pd.DataFrame(report["字段规范"])
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        # 保存枚举字段列表
        enum_file = os.path.join(self.output_dir, "reports", "enum_fields.json")
        with open(enum_file, 'w', encoding='utf-8') as f:
            ujson.dump(report["枚举字段完整列表"], f, indent=2, ensure_ascii=False)
        
        print(f"💾 分析报告已保存:")
        print(f"   JSON报告: {json_file}")
        print(f"   字段规范表: {csv_file}")
        print(f"   枚举字段: {enum_file}")


if __name__ == "__main__":
    analyzer = MainAnalyzer()
    report = analyzer.run_complete_analysis(max_records_per_file=1000)  # 限制每个文件处理1000条记录以提高速度