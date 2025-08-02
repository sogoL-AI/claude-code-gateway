#!/usr/bin/env python3
"""
T03: 最小集合覆盖分析任务
贪心算法实现最优Session选择
"""

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, Set, List, Tuple

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from shared.utils import setup_logging


class MinimalSessionCoverAnalyzer:
    """最小Session集合覆盖分析器"""
    
    def __init__(self):
        self.session_types: Dict[str, Set[str]] = {}  # session_id -> 包含的类型集合
        self.type_sessions: Dict[str, Set[str]] = defaultdict(set)  # 类型 -> 包含此类型的session集合
        self.all_types: Set[str] = set()
        self.session_info: Dict[str, dict] = {}
        self.logger = setup_logging("T03_SetCover")
        
    def analyze_session_types(self, scan_result_file: str, max_sessions: int = None) -> None:
        """分析每个session包含的数据类型"""
        
        self.logger.info("开始分析每个Session的数据类型...")
        
        # 加载扫描结果
        with open(scan_result_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        
        # 只分析JSONL文件（项目会话）
        session_files = [f for f in scan_data["file_details"] if f["file_type"] == "jsonl"]
        
        if max_sessions:
            session_files = session_files[:max_sessions]
            self.logger.info(f"限制分析前 {max_sessions} 个Session")
        
        self.logger.info(f"找到 {len(session_files)} 个Session文件")
        
        processed = 0
        for i, session_file in enumerate(session_files, 1):
            if i % 10 == 0:
                self.logger.info(f"进度: {i}/{len(session_files)} ({processed} 个已处理)")
            
            session_id = session_file["session_id"]
            
            # 为每个session创建独立的类型分析器
            session_type_set = self._analyze_session_file(session_file["path"])
            
            if session_type_set:  # 只记录有类型的session
                self.session_types[session_id] = session_type_set
                self.all_types.update(session_type_set)
                
                # 更新反向索引
                for type_sig in session_type_set:
                    self.type_sessions[type_sig].add(session_id)
                
                # 记录session基本信息
                self.session_info[session_id] = {
                    'file_path': session_file["path"],
                    'project': session_file["project"],
                    'records': session_file["records"],
                    'size': session_file["size"],
                    'modified': session_file["modified"],
                    'type_count': len(session_type_set)
                }
                processed += 1
        
        self.logger.info(f"分析完成!")
        self.logger.info(f"有效Session: {len(self.session_types)}")
        self.logger.info(f"发现类型总数: {len(self.all_types)}")
        self.logger.info(f"平均每Session类型数: {sum(len(types) for types in self.session_types.values()) / len(self.session_types):.1f}")
    
    def _analyze_session_file(self, file_path: str) -> Set[str]:
        """分析单个session文件的数据类型"""
        from tasks.T02_message_structure_type.type_analyzer import ObjectTypeAnalyzer
        
        analyzer = ObjectTypeAnalyzer()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        analyzer.analyze_record(record)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.warning(f"分析文件错误 {file_path}: {e}")
            return set()
        
        return set(analyzer.object_types.keys())
    
    def greedy_set_cover(self) -> List[str]:
        """贪心算法求解最小集合覆盖"""
        
        self.logger.info(f"开始贪心算法求解最小集合覆盖...")
        self.logger.info(f"目标: 用最少Session覆盖 {len(self.all_types)} 种数据类型")
        
        uncovered_types = self.all_types.copy()
        selected_sessions = []
        
        iteration = 0
        while uncovered_types:
            iteration += 1
            
            # 找到能覆盖最多未覆盖类型的session
            best_session = None
            best_coverage = 0
            best_new_types = set()
            
            for session_id, session_types in self.session_types.items():
                if session_id in selected_sessions:
                    continue
                
                # 计算这个session能新覆盖多少类型
                new_types = session_types & uncovered_types
                coverage = len(new_types)
                
                if coverage > best_coverage:
                    best_coverage = coverage
                    best_session = session_id
                    best_new_types = new_types
            
            if best_session is None:
                break
            
            # 选择最佳session
            selected_sessions.append(best_session)
            uncovered_types -= best_new_types
            
            coverage_percent = (len(self.all_types) - len(uncovered_types)) / len(self.all_types) * 100
            
            self.logger.info(f"第{iteration}轮: 选择 {best_session}")
            self.logger.info(f"  新覆盖类型: {best_coverage}")
            self.logger.info(f"  累计覆盖: {len(self.all_types) - len(uncovered_types)}/{len(self.all_types)} ({coverage_percent:.1f}%)")
            self.logger.info(f"  剩余类型: {len(uncovered_types)}")
        
        if uncovered_types:
            self.logger.warning(f"仍有 {len(uncovered_types)} 个类型未覆盖")
        
        self.logger.info(f"算法完成!")
        self.logger.info(f"选择Session数: {len(selected_sessions)}")
        self.logger.info(f"覆盖率: {(len(self.all_types) - len(uncovered_types)) / len(self.all_types) * 100:.2f}%")
        
        return selected_sessions
    
    def analyze_coverage_efficiency(self, selected_sessions: List[str]) -> Dict:
        """分析覆盖效率"""
        
        analysis = {
            "task_id": "T03",
            "task_name": "最小集合覆盖分析",
            "execution_time": datetime.now().isoformat(),
            "total_sessions_available": len(self.session_types),
            "selected_sessions": len(selected_sessions),
            "reduction_ratio": len(selected_sessions) / len(self.session_types),
            "total_types": len(self.all_types),
            "covered_types": 0,
            "coverage_details": [],
            "type_frequency_analysis": {},
            "session_details": []
        }
        
        covered_types = set()
        
        for i, session_id in enumerate(selected_sessions, 1):
            session_types = self.session_types[session_id]
            new_types = session_types - covered_types
            covered_types.update(session_types)
            
            session_detail = {
                "rank": i,
                "session_id": session_id,
                "project": self.session_info[session_id]['project'],
                "total_types_in_session": len(session_types),
                "new_types_contributed": len(new_types),
                "cumulative_coverage": len(covered_types),
                "coverage_percentage": len(covered_types) / len(self.all_types) * 100,
                "records": self.session_info[session_id]['records'],
                "size_mb": self.session_info[session_id]['size'] / 1024 / 1024
            }
            
            analysis["session_details"].append(session_detail)
        
        analysis["covered_types"] = len(covered_types)
        analysis["coverage_percentage"] = len(covered_types) / len(self.all_types) * 100
        
        # 分析类型频率
        type_frequencies = Counter()
        for session_types in self.session_types.values():
            for type_sig in session_types:
                type_frequencies[type_sig] += 1
        
        analysis["type_frequency_analysis"] = {
            "rare_types_1_session": sum(1 for count in type_frequencies.values() if count == 1),
            "common_types_5plus_sessions": sum(1 for count in type_frequencies.values() if count >= 5),
            "very_common_types_10plus_sessions": sum(1 for count in type_frequencies.values() if count >= 10),
        }
        
        return analysis
    
    def extract_selected_sessions(self, selected_sessions: List[str], output_dir: Path) -> None:
        """提取选中的session到指定目录"""
        
        self.logger.info(f"提取选中的Session到目录: {output_dir}")
        
        session_dir = output_dir / "selected_sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 提取每个选中的session
        for i, session_id in enumerate(selected_sessions, 1):
            self.logger.info(f"[{i}/{len(selected_sessions)}] 提取Session: {session_id}")
            
            session_info = self.session_info[session_id]
            source_path = Path(session_info['file_path'])
            
            # 创建目标文件名
            target_name = f"session_{i:02d}_{session_id}.jsonl"
            target_path = session_dir / target_name
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            self.logger.info(f"  项目: {session_info['project']}")
            self.logger.info(f"  类型数: {session_info['type_count']}")
            self.logger.info(f"  记录数: {session_info['records']}")
            self.logger.info(f"  → 已提取到: {target_name}")
        
        self.logger.info(f"所有Session已提取到: {session_dir}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python set_cover_analyzer.py <output_dir> [max_sessions]")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    max_sessions = None
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        max_sessions = int(sys.argv[2])
    
    print("🧮 T03: 最小集合覆盖分析任务")
    print("=" * 50)
    
    if max_sessions:
        print(f"限制分析Session数: {max_sessions}")
    
    # 查找T06的扫描结果
    scan_result_file = output_dir.parent / "T06_data_scan" / "scan_results.json"
    if not scan_result_file.exists():
        print(f"❌ 依赖文件不存在: {scan_result_file}")
        print("   请先执行 T06 数据源扫描任务")
        sys.exit(1)
    
    # 创建覆盖算法实例
    cover_algo = MinimalSessionCoverAnalyzer()
    
    # 分析每个session的类型
    cover_algo.analyze_session_types(str(scan_result_file), max_sessions)
    
    # 执行贪心算法
    selected_sessions = cover_algo.greedy_set_cover()
    
    # 分析覆盖效率
    analysis = cover_algo.analyze_coverage_efficiency(selected_sessions)
    
    # 保存分析结果
    analysis_file = output_dir / "coverage_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print(f"\\n📊 覆盖效率分析:")
    print(f"   原始Session数: {analysis['total_sessions_available']}")
    print(f"   选择Session数: {analysis['selected_sessions']}")
    print(f"   压缩比: {analysis['reduction_ratio']:.1%} (减少 {(1-analysis['reduction_ratio'])*100:.1f}%)")
    print(f"   类型覆盖率: {analysis['coverage_percentage']:.2f}%")
    print(f"   稀有类型(仅1个Session): {analysis['type_frequency_analysis']['rare_types_1_session']}")
    print(f"   常见类型(5+Session): {analysis['type_frequency_analysis']['common_types_5plus_sessions']}")
    
    print(f"\\n📋 前5个关键Session:")
    for session in analysis["session_details"][:5]:
        print(f"   {session['rank']}. {session['session_id']}")
        print(f"      项目: {session['project']}")
        print(f"      贡献新类型: {session['new_types_contributed']}")
        print(f"      累计覆盖: {session['coverage_percentage']:.1f}%")
    
    # 提取选中的session
    cover_algo.extract_selected_sessions(selected_sessions, output_dir)
    
    print(f"\\n🎉 T03任务完成! 分析报告已保存到: {analysis_file}")


if __name__ == "__main__":
    main()