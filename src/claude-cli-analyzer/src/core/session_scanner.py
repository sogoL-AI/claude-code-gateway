#!/usr/bin/env python3
"""
Claude CLI Session Scanner
扫描和索引所有Claude CLI会话记录文件
"""

import os
import json
import ujson
from pathlib import Path
from typing import Dict, List, Generator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


@dataclass
class SessionFileInfo:
    """会话文件信息"""
    file_path: str
    file_size: int
    session_id: str
    project_path: str
    last_modified: datetime
    record_count: int = 0
    file_type: str = "jsonl"  # jsonl, json, shell


@dataclass
class ScanResult:
    """扫描结果汇总"""
    total_files: int = 0
    total_records: int = 0
    total_size_bytes: int = 0
    session_files: List[SessionFileInfo] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    date_range: Tuple[datetime, datetime] = field(default=None)


class SessionScanner:
    """Claude CLI会话扫描器"""
    
    def __init__(self, base_claude_dir: str = None):
        self.base_claude_dir = base_claude_dir or os.path.expanduser("~/.claude")
        self.projects_dir = os.path.join(self.base_claude_dir, "projects")
        self.todos_dir = os.path.join(self.base_claude_dir, "todos")
        self.shell_snapshots_dir = os.path.join(self.base_claude_dir, "shell-snapshots")
        
    def discover_all_claude_dirs(self) -> List[str]:
        """发现所有.claude目录"""
        claude_dirs = []
        home_dir = os.path.expanduser("~")
        
        # 使用find命令搜索所有.claude目录  
        import subprocess
        try:
            result = subprocess.run(
                ["find", home_dir, "-name", ".claude", "-type", "d"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                claude_dirs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        return claude_dirs
    
    def scan_jsonl_file(self, file_path: str) -> SessionFileInfo:
        """扫描单个JSONL文件"""
        path_obj = Path(file_path)
        file_stat = path_obj.stat()
        
        # 从文件路径推断session_id和project_path
        file_name = path_obj.stem
        project_dir = path_obj.parent.name
        
        session_id = file_name if file_name else "unknown"
        project_path = project_dir
        
        # 计算记录数量（快速方式）
        record_count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for _ in f:
                    record_count += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return SessionFileInfo(
            file_path=file_path,
            file_size=file_stat.st_size,
            session_id=session_id,
            project_path=project_path,
            last_modified=datetime.fromtimestamp(file_stat.st_mtime),
            record_count=record_count,
            file_type="jsonl"
        )
    
    def scan_json_file(self, file_path: str) -> SessionFileInfo:
        """扫描单个JSON文件"""
        path_obj = Path(file_path)
        file_stat = path_obj.stat()
        
        file_name = path_obj.stem
        session_id = file_name.split('-')[0] if '-' in file_name else file_name
        
        return SessionFileInfo(
            file_path=file_path,
            file_size=file_stat.st_size,
            session_id=session_id,
            project_path="todos",
            last_modified=datetime.fromtimestamp(file_stat.st_mtime),
            record_count=1,  # JSON文件通常是单个对象
            file_type="json"
        )
    
    def scan_projects_directory(self) -> List[SessionFileInfo]:
        """扫描projects目录"""
        session_files = []
        
        if not os.path.exists(self.projects_dir):
            return session_files
            
        for project_dir in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_dir)
            if not os.path.isdir(project_path):
                continue
                
            for file_name in os.listdir(project_path):
                if file_name.endswith('.jsonl'):
                    file_path = os.path.join(project_path, file_name)
                    try:
                        session_info = self.scan_jsonl_file(file_path)
                        session_files.append(session_info)
                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")
        
        return session_files
    
    def scan_todos_directory(self) -> List[SessionFileInfo]:
        """扫描todos目录"""
        session_files = []
        
        if not os.path.exists(self.todos_dir):
            return session_files
            
        for file_name in os.listdir(self.todos_dir):
            if file_name.endswith('.json'):
                file_path = os.path.join(self.todos_dir, file_name)
                try:
                    session_info = self.scan_json_file(file_path)
                    session_files.append(session_info)
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")
        
        return session_files
    
    def scan_all_sessions(self) -> ScanResult:
        """扫描所有会话记录"""
        print("🔍 开始扫描Claude CLI会话记录...")
        
        all_session_files = []
        
        # 扫描projects目录
        print("📁 扫描projects目录...")
        projects_files = self.scan_projects_directory()
        all_session_files.extend(projects_files)
        print(f"   找到 {len(projects_files)} 个项目会话文件")
        
        # 扫描todos目录
        print("📝 扫描todos目录...")
        todos_files = self.scan_todos_directory()
        all_session_files.extend(todos_files)
        print(f"   找到 {len(todos_files)} 个todo文件")
        
        # 计算统计信息
        total_records = sum(f.record_count for f in all_session_files)
        total_size = sum(f.file_size for f in all_session_files)
        projects = list(set(f.project_path for f in all_session_files))
        
        # 计算日期范围
        if all_session_files:
            dates = [f.last_modified for f in all_session_files]
            date_range = (min(dates), max(dates))
        else:
            date_range = None
        
        result = ScanResult(
            total_files=len(all_session_files),
            total_records=total_records,
            total_size_bytes=total_size,
            session_files=all_session_files,
            projects=projects,
            date_range=date_range
        )
        
        print(f"✅ 扫描完成！")
        print(f"   总文件数: {result.total_files}")
        print(f"   总记录数: {result.total_records}")
        print(f"   总大小: {result.total_size_bytes / 1024 / 1024:.2f} MB")
        print(f"   项目数: {len(result.projects)}")
        if result.date_range:
            print(f"   时间范围: {result.date_range[0].strftime('%Y-%m-%d')} ~ {result.date_range[1].strftime('%Y-%m-%d')}")
        
        return result


if __name__ == "__main__":
    scanner = SessionScanner()
    result = scanner.scan_all_sessions()
    
    # 输出详细统计
    print("\n📊 详细统计:")
    print(f"项目列表: {', '.join(result.projects)}")
    
    # 按项目分组统计
    project_stats = {}
    for session_file in result.session_files:
        project = session_file.project_path
        if project not in project_stats:
            project_stats[project] = {"files": 0, "records": 0, "size": 0}
        project_stats[project]["files"] += 1
        project_stats[project]["records"] += session_file.record_count
        project_stats[project]["size"] += session_file.file_size
    
    print("\n📁 按项目统计:")
    for project, stats in sorted(project_stats.items()):
        print(f"  {project}: {stats['files']} 文件, {stats['records']} 记录, {stats['size']/1024:.1f} KB")