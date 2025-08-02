#!/usr/bin/env python3
"""
T04: Session ID继承机制分析任务
分析claude -c命令的继承行为
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils import setup_logging


class SessionInheritanceAnalyzer:
    """Session ID继承机制分析器"""
    
    def __init__(self):
        self.session_files: Dict[str, dict] = {}  # session_id -> file info
        self.session_records: Dict[str, List[dict]] = defaultdict(list)  # session_id -> records
        self.session_temporal_data: List[dict] = []  # 时间序列数据
        self.logger = setup_logging("T04_Inheritance")
        
    def analyze_session_inheritance(self, scan_result_file: str) -> Dict:
        """分析Session ID继承机制"""
        
        self.logger.info("开始分析Session ID继承和更新机制...")
        
        # 加载扫描结果
        with open(scan_result_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        
        # 收集session文件信息
        session_files = [f for f in scan_data["file_details"] if f["file_type"] == "jsonl"]
        
        self.logger.info(f"发现 {len(session_files)} 个Session文件")
        
        # 分析每个session文件
        for session_file in session_files:
            session_id = session_file["session_id"]
            self.session_files[session_id] = {
                'path': session_file["path"],
                'size': session_file["size"],
                'records': session_file["records"],
                'modified': datetime.fromisoformat(session_file["modified"]),
                'project': session_file["project"]
            }
            
            # 读取session记录来分析时间模式
            self._load_session_records(session_file)
        
        # 生成分析报告
        return self._generate_inheritance_analysis()
    
    def _load_session_records(self, session_file) -> None:
        """加载session记录"""
        try:
            with open(session_file["path"], 'r', encoding='utf-8') as f:
                records = []
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            record = json.loads(line)
                            # 添加记录时间信息
                            if 'timestamp' in record:
                                # 统一处理为naive datetime
                                timestamp_str = record['timestamp'].replace('Z', '').replace('+00:00', '')
                                if '.' not in timestamp_str:
                                    timestamp_str += '.000000'
                                record['_parsed_timestamp'] = datetime.fromisoformat(timestamp_str)
                            records.append(record)
                        except (json.JSONDecodeError, ValueError):
                            continue
                
                self.session_records[session_file["session_id"]] = records
                
                # 分析文件创建时间 vs 首条记录时间
                if records:
                    first_record_time = records[0].get('_parsed_timestamp')
                    last_record_time = records[-1].get('_parsed_timestamp') if len(records) > 1 else first_record_time
                    
                    self.session_temporal_data.append({
                        'session_id': session_file["session_id"],
                        'project': session_file["project"],
                        'file_modified': datetime.fromisoformat(session_file["modified"]),
                        'first_record_time': first_record_time,
                        'last_record_time': last_record_time,
                        'record_count': len(records),
                        'file_size': session_file["size"],
                        'time_span_hours': (last_record_time - first_record_time).total_seconds() / 3600 if first_record_time and last_record_time else 0
                    })
                    
        except Exception as e:
            self.logger.warning(f"无法读取session文件 {session_file['path']}: {e}")
    
    def _generate_inheritance_analysis(self) -> Dict:
        """生成继承机制分析报告"""
        
        self.logger.info(f"生成Session ID继承分析报告...")
        
        analysis = {
            "task_id": "T04",
            "task_name": "Session ID继承机制分析",
            "generation_time": datetime.now().isoformat(),
            "summary": {
                "total_sessions": len(self.session_files),
                "sessions_with_records": len([s for s in self.session_temporal_data if s['record_count'] > 0]),
                "total_records": sum(len(records) for records in self.session_records.values())
            },
            "file_creation_patterns": self._analyze_file_creation_patterns(),
            "session_timing_analysis": self._analyze_session_timing(),
            "inheritance_indicators": self._find_inheritance_indicators(),
            "storage_behavior_analysis": self._analyze_storage_behavior(),
            "potential_continuations": self._find_potential_continuations(),
            "session_details": []
        }
        
        # 详细session信息
        for session_data in self.session_temporal_data:
            session_id = session_data['session_id']
            session_detail = {
                **session_data,
                "file_vs_record_timing": self._analyze_file_record_timing(session_data),
                "session_pattern": self._classify_session_pattern(session_data)
            }
            # 转换datetime为字符串
            session_detail['file_modified'] = session_detail['file_modified'].isoformat()
            if session_detail['first_record_time']:
                session_detail['first_record_time'] = session_detail['first_record_time'].isoformat()
            if session_detail['last_record_time']:
                session_detail['last_record_time'] = session_detail['last_record_time'].isoformat()
            
            analysis["session_details"].append(session_detail)
        
        # 按记录数排序
        analysis["session_details"].sort(key=lambda x: x["record_count"], reverse=True)
        
        return analysis
    
    def _analyze_file_creation_patterns(self) -> Dict:
        """分析文件创建模式"""
        
        patterns = {
            "immediate_creation": 0,  # 文件创建时间 ≈ 首条记录时间
            "delayed_creation": 0,    # 文件创建时间 > 首条记录时间
            "pre_creation": 0,        # 文件创建时间 < 首条记录时间
            "timing_differences": []
        }
        
        for session_data in self.session_temporal_data:
            if session_data['first_record_time']:
                file_time = session_data['file_modified']
                record_time = session_data['first_record_time']
                
                # 计算时间差（秒）
                time_diff = (file_time - record_time).total_seconds()
                patterns["timing_differences"].append({
                    "session_id": session_data['session_id'],
                    "time_diff_seconds": time_diff,
                    "pattern": "immediate" if abs(time_diff) < 60 else ("delayed" if time_diff > 0 else "pre")
                })
                
                if abs(time_diff) < 60:  # 1分钟内认为是即时创建
                    patterns["immediate_creation"] += 1
                elif time_diff > 0:
                    patterns["delayed_creation"] += 1
                else:
                    patterns["pre_creation"] += 1
        
        return patterns
    
    def _analyze_session_timing(self) -> Dict:
        """分析session时间模式"""
        
        # 按时间排序
        sorted_sessions = sorted(self.session_temporal_data, 
                                key=lambda x: x['first_record_time'] or datetime.min)
        
        timing_analysis = {
            "sessions_by_hour": defaultdict(int),
            "session_duration_distribution": Counter(),
            "rapid_succession_sessions": [],  # 快速连续创建的session
        }
        
        # 分析创建时间分布
        for session_data in sorted_sessions:
            if session_data['first_record_time']:
                hour = session_data['first_record_time'].hour
                timing_analysis["sessions_by_hour"][hour] += 1
                
                # 持续时间分类
                duration_hours = session_data['time_span_hours']
                if duration_hours < 0.1:
                    timing_analysis["session_duration_distribution"]["<6min"] += 1
                elif duration_hours < 1:
                    timing_analysis["session_duration_distribution"]["<1hour"] += 1
                elif duration_hours < 6:
                    timing_analysis["session_duration_distribution"]["1-6hours"] += 1
                else:
                    timing_analysis["session_duration_distribution"][">6hours"] += 1
        
        # 寻找快速连续创建的session（可能的-c行为）
        for i in range(1, len(sorted_sessions)):
            current = sorted_sessions[i]
            previous = sorted_sessions[i-1]
            
            if (current['first_record_time'] and previous['first_record_time'] and
                (current['first_record_time'] - previous['first_record_time']).total_seconds() < 300):  # 5分钟内
                
                timing_analysis["rapid_succession_sessions"].append({
                    "previous_session": previous['session_id'],
                    "current_session": current['session_id'],
                    "time_gap_seconds": (current['first_record_time'] - previous['first_record_time']).total_seconds(),
                    "same_project": current['project'] == previous['project']
                })
        
        # 转换为可序列化格式
        timing_analysis["sessions_by_hour"] = dict(timing_analysis["sessions_by_hour"])
        timing_analysis["session_duration_distribution"] = dict(timing_analysis["session_duration_distribution"])
        
        return timing_analysis
    
    def _find_inheritance_indicators(self) -> List[Dict]:
        """寻找可能的继承指示器"""
        # 简化实现
        return []
    
    def _analyze_storage_behavior(self) -> Dict:
        """分析存储行为"""
        behavior = {
            "new_file_creation": 0,     # 明确新建文件
            "file_continuation": 0,     # 可能的文件继续写入
        }
        
        for session_data in self.session_temporal_data:
            file_record_analysis = self._analyze_file_record_timing(session_data)
            
            if file_record_analysis["likely_new_file"]:
                behavior["new_file_creation"] += 1
            else:
                behavior["file_continuation"] += 1
        
        return behavior
    
    def _find_potential_continuations(self) -> List[Dict]:
        """寻找可能的session延续"""
        continuations = []
        
        # 按项目分组分析
        by_project = defaultdict(list)
        for session_data in self.session_temporal_data:
            by_project[session_data['project']].append(session_data)
        
        for project, sessions in by_project.items():
            # 按时间排序
            sessions.sort(key=lambda x: x['first_record_time'] or datetime.min)
            
            for i in range(1, len(sessions)):
                current = sessions[i]
                previous = sessions[i-1]
                
                # 检查是否可能是延续session
                if (current['first_record_time'] and previous['last_record_time'] and
                    (current['first_record_time'] - previous['last_record_time']).total_seconds() < 3600):  # 1小时内
                    
                    continuations.append({
                        "project": project,
                        "previous_session": previous['session_id'],
                        "current_session": current['session_id'],
                        "gap_minutes": (current['first_record_time'] - previous['last_record_time']).total_seconds() / 60,
                        "context_preservation_score": self._calculate_context_score(previous, current)
                    })
        
        return continuations[:10]  # 返回前10个
    
    def _analyze_file_record_timing(self, session_data: Dict) -> Dict:
        """分析文件和记录的时间关系"""
        
        if not session_data['first_record_time']:
            return {"likely_new_file": True, "confidence": 0.5, "reason": "no_record_timestamp"}
        
        time_diff = (session_data['file_modified'] - session_data['first_record_time']).total_seconds()
        
        if abs(time_diff) < 10:  # 10秒内
            return {"likely_new_file": True, "confidence": 0.9, "reason": "immediate_creation"}
        elif time_diff > 0:  # 文件修改时间晚于首条记录
            return {"likely_new_file": False, "confidence": 0.7, "reason": "delayed_file_update"}
        else:  # 文件修改时间早于首条记录
            return {"likely_new_file": False, "confidence": 0.8, "reason": "pre_existing_file"}
    
    def _classify_session_pattern(self, session_data: Dict) -> str:
        """分类session模式"""
        
        records = session_data['record_count']
        duration = session_data['time_span_hours']
        
        if records == 0:
            return "empty"
        elif records == 1:
            return "single_interaction"
        elif duration < 0.1:
            return "burst_interaction"
        elif duration < 1:
            return "short_session"
        elif duration < 6:
            return "medium_session"
        else:
            return "long_session"
    
    def _calculate_context_score(self, previous: Dict, current: Dict) -> float:
        """计算上下文保持得分"""
        score = 0.0
        
        # 同一项目 +0.3
        if previous['project'] == current['project']:
            score += 0.3
        
        # 时间间隔越短得分越高 +0.4
        if previous['last_record_time'] and current['first_record_time']:
            gap_hours = (current['first_record_time'] - previous['last_record_time']).total_seconds() / 3600
            if gap_hours < 0.1:  # 6分钟内
                score += 0.4
            elif gap_hours < 1:  # 1小时内
                score += 0.3
            elif gap_hours < 6:  # 6小时内
                score += 0.2
        
        # 相似的持续时间模式 +0.3
        if abs(previous['time_span_hours'] - current['time_span_hours']) < 1:
            score += 0.3
        
        return min(score, 1.0)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python inheritance_analyzer.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🆔 T04: Session ID继承机制分析任务")
    print("=" * 50)
    
    # 查找T06的扫描结果
    scan_result_file = output_dir.parent / "T06_data_scan" / "scan_results.json"
    if not scan_result_file.exists():
        print(f"❌ 依赖文件不存在: {scan_result_file}")
        print("   请先执行 T06 数据源扫描任务")
        sys.exit(1)
    
    # 创建分析器
    analyzer = SessionInheritanceAnalyzer()
    
    # 执行分析
    analysis = analyzer.analyze_session_inheritance(str(scan_result_file))
    
    # 保存分析报告
    analysis_file = output_dir / "session_inheritance_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    summary = analysis["summary"]
    file_patterns = analysis["file_creation_patterns"]
    timing = analysis["session_timing_analysis"]
    storage = analysis["storage_behavior_analysis"]
    
    print(f"\\n📊 Session ID继承机制分析摘要")
    print(f"📁 基本统计:")
    print(f"   总Session数: {summary['total_sessions']}")
    print(f"   有记录的Session数: {summary['sessions_with_records']}")
    print(f"   总记录数: {summary['total_records']}")
    
    print(f"\\n🗂️ 文件创建模式:")
    print(f"   即时创建: {file_patterns['immediate_creation']}个 (可能新session)")
    print(f"   延迟创建: {file_patterns['delayed_creation']}个 (可能继续写入)")
    print(f"   预创建: {file_patterns['pre_creation']}个 (可能复用文件)")
    
    print(f"\\n⏰ 时间模式:")
    print(f"   快速连续session: {len(timing['rapid_succession_sessions'])}对")
    duration_dist = timing['session_duration_distribution']
    print(f"   持续时间分布: <6min: {duration_dist.get('<6min', 0)}, <1h: {duration_dist.get('<1hour', 0)}, 1-6h: {duration_dist.get('1-6hours', 0)}, >6h: {duration_dist.get('>6hours', 0)}")
    
    print(f"\\n💾 存储行为:")
    print(f"   新文件创建: {storage['new_file_creation']}个")
    print(f"   文件继续写入: {storage['file_continuation']}个")
    
    print(f"\\n🎉 T04任务完成! 详细报告已保存到: {analysis_file}")


if __name__ == "__main__":
    main()