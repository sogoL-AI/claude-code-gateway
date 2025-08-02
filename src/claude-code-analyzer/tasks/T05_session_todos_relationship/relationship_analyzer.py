#!/usr/bin/env python3
"""
T05: Session-Todos关系分析任务
深入分析一对多复杂关系
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils import setup_logging


class SessionTodosRelationshipAnalyzer:
    """Session-Todos关系分析器"""
    
    def __init__(self):
        self.session_todos_map: Dict[str, List[dict]] = defaultdict(list)  # session_id -> todos files
        self.agent_session_map: Dict[str, Set[str]] = defaultdict(set)     # agent_id -> session_ids
        self.todos_pattern = re.compile(r'([a-f0-9-]+)-agent-([a-f0-9-]+)\.json$')
        self.session_files: Dict[str, dict] = {}  # session_id -> session file info
        self.todos_files: List[dict] = []
        self.logger = setup_logging("T05_Relationship")
        
    def analyze_relationship_patterns(self, scan_result_file: str) -> Dict:
        """分析Session-Todos关系模式"""
        
        self.logger.info("开始分析Session-Todos复杂关系...")
        
        # 加载扫描结果
        with open(scan_result_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        
        file_details = scan_data.get("file_details", [])
        
        # 分离Session和Todos文件
        session_files = [f for f in file_details if f["file_type"] == "jsonl"]
        self.todos_files = [f for f in file_details if f["file_type"] == "json"]
        
        self.logger.info(f"文件统计:")
        self.logger.info(f"Session文件 (.jsonl): {len(session_files)}")
        self.logger.info(f"Todos文件 (.json): {len(self.todos_files)}")
        
        # 构建Session文件索引
        for session_file in session_files:
            session_id = session_file["session_id"]
            self.session_files[session_id] = session_file
        
        # 分析Todos文件命名模式
        self.logger.info("分析Todos文件命名模式...")
        
        for todos_file in self.todos_files:
            filename = Path(todos_file["path"]).name
            match = self.todos_pattern.match(filename)
            if match:
                session_id, agent_id = match.groups()
                
                # 建立Session-Todos映射
                self.session_todos_map[session_id].append({
                    'file_path': todos_file["path"],
                    'agent_id': agent_id,
                    'modified': todos_file["modified"],
                    'size': todos_file["size"]
                })
                
                # 建立Agent-Session映射
                self.agent_session_map[agent_id].add(session_id)
        
        # 生成分析报告
        return self._generate_relationship_analysis()
    
    def _generate_relationship_analysis(self) -> Dict:
        """生成关系分析报告"""
        
        self.logger.info("生成分析报告...")
        
        analysis = {
            "task_id": "T05",
            "task_name": "Session-Todos关系分析",
            "generation_time": datetime.now().isoformat(),
            "summary": {
                "total_sessions": len(self.session_files),
                "sessions_with_todos": len(self.session_todos_map),
                "total_todos_files": len(self.todos_files),
                "unique_agents": len(self.agent_session_map)
            },
            "relationship_distribution": self._analyze_relationship_distribution(),
            "agent_reuse_analysis": self._analyze_agent_reuse(),
            "complex_relationships": self._find_complex_relationships(),
            "session_details": []
        }
        
        # 详细Session信息
        for session_id, todos_list in self.session_todos_map.items():
            if session_id in self.session_files:
                session_info = self.session_files[session_id]
                agent_ids = [todo['agent_id'] for todo in todos_list]
                time_span = self._calculate_time_span(todos_list)
                
                session_detail = {
                    "session_id": session_id,
                    "project": session_info["project"],
                    "todos_count": len(todos_list),
                    "unique_agents": len(set(agent_ids)),
                    "has_self_agent": session_id in agent_ids,
                    "session_records": session_info["records"],
                    "time_span_hours": time_span,
                    "agent_pattern": self._analyze_agent_pattern(agent_ids)
                }
                analysis["session_details"].append(session_detail)
        
        # 按todos数量排序
        analysis["session_details"].sort(key=lambda x: x["todos_count"], reverse=True)
        
        return analysis
    
    def _analyze_relationship_distribution(self) -> Dict:
        """分析关系分布"""
        distribution = {
            "sessions_with_no_todos": len(self.session_files) - len(self.session_todos_map),
            "average_todos_per_session": 0,
            "max_todos_in_single_session": 0,
            "relationship_types": Counter()
        }
        
        if self.session_todos_map:
            todos_counts = [len(todos_list) for todos_list in self.session_todos_map.values()]
            distribution["average_todos_per_session"] = sum(todos_counts) / len(todos_counts)
            distribution["max_todos_in_single_session"] = max(todos_counts)
            
            # 分类关系类型
            for todos_count in todos_counts:
                if todos_count == 1:
                    distribution["relationship_types"]["1:1"] += 1
                elif todos_count <= 5:
                    distribution["relationship_types"]["1:2-5"] += 1
                elif todos_count <= 10:
                    distribution["relationship_types"]["1:6-10"] += 1
                else:
                    distribution["relationship_types"]["1:10+"] += 1
        
        distribution["relationship_types"] = dict(distribution["relationship_types"])
        return distribution
    
    def _analyze_agent_reuse(self) -> Dict:
        """分析Agent复用模式"""
        reuse_analysis = {
            "unique_agents": len(self.agent_session_map),
            "reused_agents": 0,
            "max_sessions_per_agent": 0,
            "agent_distribution": Counter()
        }
        
        for agent_id, session_set in self.agent_session_map.items():
            session_count = len(session_set)
            reuse_analysis["agent_distribution"][session_count] += 1
            
            if session_count > 1:
                reuse_analysis["reused_agents"] += 1
            
            if session_count > reuse_analysis["max_sessions_per_agent"]:
                reuse_analysis["max_sessions_per_agent"] = session_count
        
        reuse_analysis["agent_distribution"] = dict(reuse_analysis["agent_distribution"])
        return reuse_analysis
    
    def _find_complex_relationships(self) -> List[Dict]:
        """识别复杂的Session-Todos关系"""
        complex_sessions = []
        
        for session_id, todos_list in self.session_todos_map.items():
            if len(todos_list) > 1:  # 一对多关系
                if session_id in self.session_files:
                    session_info = self.session_files[session_id]
                    agent_ids = [todo['agent_id'] for todo in todos_list]
                    time_span = self._calculate_time_span(todos_list)
                    
                    complex_sessions.append({
                        'session_id': session_id,
                        'project': session_info["project"],
                        'todos_count': len(todos_list),
                        'unique_agents': len(set(agent_ids)),
                        'has_self_agent': session_id in agent_ids,
                        'session_records': session_info["records"],
                        'time_span_hours': time_span,
                        'agent_pattern': self._analyze_agent_pattern(agent_ids)
                    })
        
        return sorted(complex_sessions, key=lambda x: x['todos_count'], reverse=True)[:10]
    
    def _calculate_time_span(self, todos_list: List[dict]) -> float:
        """计算时间跨度"""
        if len(todos_list) < 2:
            return 0.0
        
        try:
            times = [datetime.fromisoformat(todo['modified']) for todo in todos_list]
            time_span = (max(times) - min(times)).total_seconds() / 3600
            return round(time_span, 2)
        except:
            return 0.0
    
    def _analyze_agent_pattern(self, agent_ids: List[str]) -> str:
        """分析Agent模式"""
        if len(set(agent_ids)) == 1:
            return "single_agent"
        elif len(agent_ids) == len(set(agent_ids)):
            return "unique_agents"
        else:
            return "mixed_agents"


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python relationship_analyzer.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🕸️ T05: Session-Todos关系分析任务")
    print("=" * 50)
    
    # 查找T06的扫描结果
    scan_result_file = output_dir.parent / "T06_data_scan" / "scan_results.json"
    if not scan_result_file.exists():
        print(f"❌ 依赖文件不存在: {scan_result_file}")
        print("   请先执行 T06 数据源扫描任务")
        sys.exit(1)
    
    # 创建分析器
    analyzer = SessionTodosRelationshipAnalyzer()
    
    # 执行分析
    analysis = analyzer.analyze_relationship_patterns(str(scan_result_file))
    
    # 保存分析报告
    analysis_file = output_dir / "session_todos_relationship_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    summary = analysis["summary"]
    distribution = analysis["relationship_distribution"]
    agent_reuse = analysis["agent_reuse_analysis"]
    complex_relations = analysis["complex_relationships"]
    
    print(f"\\n📊 Session-Todos关系分析摘要")
    print(f"📁 基本统计:")
    print(f"   总Session数: {summary['total_sessions']}")
    print(f"   有Todos的Session数: {summary['sessions_with_todos']}")
    print(f"   总Todos文件数: {summary['total_todos_files']}")
    print(f"   唯一Agent数: {summary['unique_agents']}")
    
    print(f"\\n🔗 Session-Todos分布:")
    print(f"   平均每Session的Todos数: {distribution['average_todos_per_session']:.1f}")
    print(f"   最多Todos的Session: {distribution['max_todos_in_single_session']}个文件")
    
    print(f"\\n👥 Agent复用分析:")
    print(f"   被多个Session使用的Agent数: {agent_reuse['reused_agents']}")
    print(f"   单个Agent最多服务Session数: {agent_reuse['max_sessions_per_agent']}")
    
    if complex_relations:
        print(f"\\n🎯 复杂关系Session (Top 5):")
        for i, rel in enumerate(complex_relations[:5], 1):
            print(f"   {i}. {rel['session_id']}")
            print(f"      项目: {rel['project']}")
            print(f"      Todos文件: {rel['todos_count']}个")
            print(f"      唯一Agent: {rel['unique_agents']}个")
            print(f"      Self-Agent: {'是' if rel['has_self_agent'] else '否'}")
            print(f"      Session记录: {rel['session_records']}")
            print(f"      时间跨度: {rel['time_span_hours']}小时")
    
    print(f"\\n🎉 T05任务完成! 详细报告已保存到: {analysis_file}")


if __name__ == "__main__":
    main()