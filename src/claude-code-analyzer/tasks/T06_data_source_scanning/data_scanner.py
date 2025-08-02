#!/usr/bin/env python3
"""
T06: 数据源扫描分析任务
基础数据统计和文件扫描，为其他所有任务提供数据源
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from shared.models import SessionFile, ScanResult
from shared.utils import setup_logging


class DataSourceScanner:
    """数据源扫描器"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.expanduser("~/.claude")
        self.projects_dir = os.path.join(self.base_dir, "projects")
        self.todos_dir = os.path.join(self.base_dir, "todos")
        self.logger = setup_logging("T06_DataScanner")
    
    def scan_all(self) -> ScanResult:
        """扫描所有会话文件"""
        self.logger.info("开始扫描Claude CLI会话记录...")
        
        result = ScanResult()
        projects = set()
        dates = []
        
        # 扫描projects目录
        if os.path.exists(self.projects_dir):
            self.logger.info("扫描projects目录...")
            project_files = list(self._scan_projects())
            result.files.extend(project_files)
            self.logger.info(f"找到 {len(project_files)} 个项目会话文件")
        
        # 扫描todos目录  
        if os.path.exists(self.todos_dir):
            self.logger.info("扫描todos目录...")
            todo_files = list(self._scan_todos())
            result.files.extend(todo_files)
            self.logger.info(f"找到 {len(todo_files)} 个todo文件")
        
        # 统计结果
        for file in result.files:
            projects.add(file.project)
            dates.append(file.modified)
            result.total_files += 1
            result.total_records += file.records
            result.total_size += file.size
        
        result.projects = sorted(list(projects))
        if dates:
            result.date_range = (min(dates), max(dates))
        
        self.logger.info("扫描完成！")
        self.logger.info(f"总文件数: {result.total_files}")
        self.logger.info(f"总记录数: {result.total_records}")
        self.logger.info(f"总大小: {result.total_size / 1024 / 1024:.2f} MB")
        self.logger.info(f"项目数: {len(result.projects)}")
        
        if result.date_range:
            start, end = result.date_range
            self.logger.info(f"时间范围: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}")
        
        return result
    
    def _scan_projects(self):
        """扫描projects目录"""
        for project in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project)
            if not os.path.isdir(project_path):
                continue
                
            for filename in os.listdir(project_path):
                if filename.endswith('.jsonl'):
                    file_path = os.path.join(project_path, filename)
                    yield self._create_file_info(file_path, project, "jsonl")
    
    def _scan_todos(self):
        """扫描todos目录"""
        for filename in os.listdir(self.todos_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.todos_dir, filename)
                # 检查文件是否有效
                if self._is_valid_json(file_path):
                    yield self._create_file_info(file_path, "todos", "json")
    
    def _create_file_info(self, file_path: str, project: str, file_type: str) -> SessionFile:
        """创建文件信息"""
        stat = os.stat(file_path)
        session_id = os.path.splitext(os.path.basename(file_path))[0]
        
        # 提取会话ID（去除agent部分）
        if '-agent-' in session_id:
            session_id = session_id.split('-agent-')[0]
        
        # 计算记录数
        records = self._count_records(file_path, file_type)
        
        return SessionFile(
            path=file_path,
            size=stat.st_size,
            session_id=session_id,
            project=project,
            modified=datetime.fromtimestamp(stat.st_mtime),
            records=records,
            file_type=file_type
        )
    
    def _count_records(self, file_path: str, file_type: str) -> int:
        """计算记录数"""
        try:
            if file_type == "jsonl":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return sum(1 for line in f if line.strip())
            else:  # json
                return 1
        except (UnicodeDecodeError, FileNotFoundError):
            return 0
    
    def _is_valid_json(self, file_path: str) -> bool:
        """检查JSON文件是否有效"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python data_scanner.py <output_dir>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔍 T06: 数据源扫描分析任务")
    print("=" * 50)
    
    # 执行扫描
    scanner = DataSourceScanner()
    scan_result = scanner.scan_all()
    
    # 生成扫描报告
    report = {
        "task_id": "T06",
        "task_name": "数据源扫描分析",
        "execution_time": datetime.now().isoformat(),
        "scan_summary": {
            "total_files": scan_result.total_files,
            "total_records": scan_result.total_records,
            "total_size_mb": round(scan_result.total_size / 1024 / 1024, 2),
            "projects_count": len(scan_result.projects),
            "session_files": len([f for f in scan_result.files if f.file_type == "jsonl"]),
            "todos_files": len([f for f in scan_result.files if f.file_type == "json"])
        },
        "projects": scan_result.projects,
        "date_range": {
            "start": scan_result.date_range[0].isoformat() if scan_result.date_range else None,
            "end": scan_result.date_range[1].isoformat() if scan_result.date_range else None
        },
        "file_details": [
            {
                "path": f.path,
                "session_id": f.session_id,
                "project": f.project,
                "size": f.size,
                "records": f.records,
                "file_type": f.file_type,
                "modified": f.modified.isoformat()
            }
            for f in scan_result.files
        ]
    }
    
    # 保存扫描结果
    scan_file = output_dir / "scan_results.json"
    with open(scan_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ T06 任务完成")
    print(f"📊 扫描结果:")
    print(f"   文件总数: {scan_result.total_files}")
    print(f"   记录总数: {scan_result.total_records:,}")
    print(f"   数据大小: {scan_result.total_size / 1024 / 1024:.2f} MB")
    print(f"   项目数量: {len(scan_result.projects)}")
    print(f"💾 结果已保存: {scan_file}")


if __name__ == "__main__":
    main()