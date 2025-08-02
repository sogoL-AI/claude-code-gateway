#!/usr/bin/env python3
"""
Claude CLI 数据分析任务调度器
统一管理和执行8个核心分析任务
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import argparse
import subprocess


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    output_files: List[str] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        if self.metrics is None:
            self.metrics = {}


class TaskScheduler:
    """Claude CLI 分析任务调度器"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.tasks_dir = self.base_dir / "tasks"
        self.outputs_dir = self.base_dir / "outputs"
        self.shared_dir = self.base_dir / "shared"
        
        # 确保目录存在
        self.outputs_dir.mkdir(exist_ok=True)
        
        # 任务定义
        self.tasks = self._define_tasks()
        self.task_results: Dict[str, TaskResult] = {}
        
    def _define_tasks(self) -> Dict[str, Dict[str, Any]]:
        """定义所有分析任务"""
        return {
            "T01": {
                "name": "深度字段提取分析",
                "description": "递归提取JSON字段到最深层，实现204字段去重",
                "module": "T01_deep_field_extraction",
                "script": "field_extractor.py",
                "dependencies": ["T06"],  # 依赖数据源扫描
                "output_dir": "T01_field_extraction",
                "expected_outputs": ["deduplicated_fields.json", "field_examples.json"],
                "timeout": 300  # 5分钟
            },
            
            "T02": {
                "name": "消息结构类型分析", 
                "description": "基于完整结构签名分类414种数据类型",
                "module": "T02_message_structure_type",
                "script": "type_analyzer.py",
                "dependencies": ["T06"],
                "output_dir": "T02_structure_types",
                "expected_outputs": ["object_types_detail.json", "object_types_compact.json", "object_types_summary.json"],
                "timeout": 600  # 10分钟
            },
            
            "T03": {
                "name": "最小集合覆盖分析",
                "description": "贪心算法实现最优Session选择",
                "module": "T03_minimal_set_cover", 
                "script": "set_cover_analyzer.py",
                "dependencies": ["T02"],  # 依赖类型分析结果
                "output_dir": "T03_set_cover",
                "expected_outputs": ["coverage_analysis.json", "selected_sessions/"],
                "timeout": 300
            },
            
            "T04": {
                "name": "Session ID继承机制分析",
                "description": "分析claude -c命令的继承行为",
                "module": "T04_session_inheritance",
                "script": "inheritance_analyzer.py", 
                "dependencies": ["T06"],
                "output_dir": "T04_inheritance",
                "expected_outputs": ["session_inheritance_analysis.json"],
                "timeout": 180
            },
            
            "T05": {
                "name": "Session-Todos关系分析", 
                "description": "深入分析一对多复杂关系",
                "module": "T05_session_todos_relationship",
                "script": "relationship_analyzer.py",
                "dependencies": ["T06"],
                "output_dir": "T05_relationships", 
                "expected_outputs": ["session_todos_relationship_analysis.json"],
                "timeout": 120
            },
            
            "T06": {
                "name": "数据源扫描分析",
                "description": "基础数据统计和文件扫描",
                "module": "T06_data_source_scanning",
                "script": "data_scanner.py",
                "dependencies": [],  # 基础任务，无依赖
                "output_dir": "T06_data_scan",
                "expected_outputs": ["scan_results.json"],
                "timeout": 60
            },
            
            "T07": {
                "name": "会话机制分析",
                "description": "ChatGPT式对话可行性分析",
                "module": "T07_session_mechanism",
                "script": "session_mechanism_analyzer.py",
                "dependencies": ["T04", "T05"],  # 依赖继承和关系分析
                "output_dir": "T07_session_mechanism",
                "expected_outputs": ["chatgpt_feasibility_analysis.json"],
                "timeout": 180
            },
            
            "T08": {
                "name": "前端展示策略分析",
                "description": "UI/UX设计和技术架构方案",
                "module": "T08_frontend_strategy", 
                "script": "frontend_strategy_analyzer.py",
                "dependencies": ["T01", "T02", "T03"],  # 依赖主要分析结果
                "output_dir": "T08_frontend",
                "expected_outputs": ["frontend_design_spec.json", "technical_architecture.json"],
                "timeout": 120
            }
        }
    
    def get_task_dependency_order(self) -> List[str]:
        """获取任务的依赖执行顺序"""
        # 拓扑排序确定执行顺序
        in_degree = {task_id: 0 for task_id in self.tasks}
        
        # 计算入度
        for task_id, task_info in self.tasks.items():
            for dep in task_info.get("dependencies", []):
                if dep in in_degree:
                    in_degree[task_id] += 1
        
        # 拓扑排序
        result = []
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # 更新依赖当前任务的其他任务
            for task_id, task_info in self.tasks.items():
                if current in task_info.get("dependencies", []):
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return result
    
    def run_task(self, task_id: str) -> TaskResult:
        """执行单个任务"""
        if task_id not in self.tasks:
            return TaskResult(task_id, TaskStatus.FAILED, error_message=f"Unknown task: {task_id}")
        
        task_info = self.tasks[task_id]
        print(f"\n🚀 开始执行任务 {task_id}: {task_info['name']}")
        print(f"   描述: {task_info['description']}")
        
        result = TaskResult(task_id, TaskStatus.RUNNING, start_time=datetime.now())
        
        try:
            # 检查依赖
            for dep_id in task_info.get("dependencies", []):
                if dep_id not in self.task_results or self.task_results[dep_id].status != TaskStatus.COMPLETED:
                    result.status = TaskStatus.FAILED
                    result.error_message = f"Dependency {dep_id} not completed"
                    return result
            
            # 创建输出目录
            output_dir = self.outputs_dir / task_info["output_dir"]
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建执行命令
            task_script = self.tasks_dir / task_info["module"] / task_info["script"]
            
            if not task_script.exists():
                result.status = TaskStatus.FAILED
                result.error_message = f"Task script not found: {task_script}"
                return result
            
            # 执行任务
            cmd = [sys.executable, str(task_script), str(output_dir)]
            
            print(f"   执行命令: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                cwd=str(self.base_dir),
                timeout=task_info.get("timeout", 300),
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                result.status = TaskStatus.COMPLETED
                result.end_time = datetime.now()
                result.duration = (result.end_time - result.start_time).total_seconds()
                
                # 验证输出文件
                result.output_files = self._verify_outputs(output_dir, task_info.get("expected_outputs", []))
                
                print(f"   ✅ 任务完成 ({result.duration:.1f}s)")
                for output_file in result.output_files:
                    print(f"      输出: {output_file}")
                
            else:
                result.status = TaskStatus.FAILED
                result.error_message = f"Process failed with code {process.returncode}\nSTDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
                print(f"   ❌ 任务失败: {process.stderr}")
        
        except subprocess.TimeoutExpired:
            result.status = TaskStatus.FAILED
            result.error_message = f"Task timeout after {task_info.get('timeout', 300)} seconds"
            print(f"   ⏱️ 任务超时")
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error_message = str(e)
            print(f"   💥 任务异常: {e}")
        
        return result
    
    def _verify_outputs(self, output_dir: Path, expected_outputs: List[str]) -> List[str]:
        """验证输出文件是否存在"""
        actual_outputs = []
        
        for expected in expected_outputs:
            output_path = output_dir / expected
            if output_path.exists():
                actual_outputs.append(str(output_path))
            elif expected.endswith("/"):  # 目录
                if output_path.is_dir():
                    actual_outputs.append(str(output_path))
        
        return actual_outputs
    
    def run_all_tasks(self, task_filter: List[str] = None) -> Dict[str, TaskResult]:
        """执行所有任务或指定任务"""
        print("🎯 Claude CLI 数据分析任务调度器")
        print("=" * 60)
        
        # 确定要执行的任务
        if task_filter:
            tasks_to_run = [t for t in self.get_task_dependency_order() if t in task_filter]
        else:
            tasks_to_run = self.get_task_dependency_order()
        
        print(f"📋 计划执行 {len(tasks_to_run)} 个任务: {', '.join(tasks_to_run)}")
        
        # 执行任务
        start_time = datetime.now()
        
        for task_id in tasks_to_run:
            result = self.run_task(task_id)
            self.task_results[task_id] = result
            
            if result.status == TaskStatus.FAILED:
                print(f"❌ 任务 {task_id} 失败，停止执行后续任务")
                break
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # 生成执行报告
        self._generate_execution_report(total_duration)
        
        return self.task_results
    
    def _generate_execution_report(self, total_duration: float):
        """生成执行报告"""
        print(f"\n📊 执行报告")
        print("=" * 60)
        
        completed = sum(1 for r in self.task_results.values() if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in self.task_results.values() if r.status == TaskStatus.FAILED)
        
        print(f"总执行时间: {total_duration:.1f} 秒")
        print(f"任务完成: {completed}")
        print(f"任务失败: {failed}")
        print(f"成功率: {completed/(completed+failed)*100:.1f}%" if (completed+failed) > 0 else "成功率: 0%")
        
        print(f"\n📋 任务详情:")
        for task_id, result in self.task_results.items():
            task_info = self.tasks[task_id]
            status_emoji = {"completed": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}
            
            print(f"  {status_emoji.get(result.status.value, '❓')} {task_id}: {task_info['name']}")
            if result.duration:
                print(f"     执行时间: {result.duration:.1f}s")
            if result.output_files:
                print(f"     输出文件: {len(result.output_files)}个")
            if result.error_message:
                print(f"     错误: {result.error_message[:100]}...")
        
        # 保存报告到文件
        report_file = self.outputs_dir / "execution_report.json"
        report_data = {
            "execution_time": datetime.now().isoformat(),
            "total_duration": total_duration,
            "task_results": {
                task_id: {
                    "status": result.status.value,
                    "start_time": result.start_time.isoformat() if result.start_time else None,
                    "end_time": result.end_time.isoformat() if result.end_time else None,
                    "duration": result.duration,
                    "output_files": result.output_files,
                    "error_message": result.error_message,
                    "metrics": result.metrics
                }
                for task_id, result in self.task_results.items()
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 执行报告已保存: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Claude CLI 数据分析任务调度器")
    parser.add_argument("--tasks", "-t", nargs="+", 
                       choices=["T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08"],
                       help="指定要执行的任务ID")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用任务")
    parser.add_argument("--base-dir", "-b", help="指定基础目录")
    
    args = parser.parse_args()
    
    scheduler = TaskScheduler(args.base_dir)
    
    if args.list:
        print("📋 可用任务列表:")
        for task_id, task_info in scheduler.tasks.items():
            deps = ", ".join(task_info.get("dependencies", [])) or "无"
            print(f"  {task_id}: {task_info['name']}")
            print(f"      描述: {task_info['description']}")
            print(f"      依赖: {deps}")
            print()
        return
    
    # 执行任务
    results = scheduler.run_all_tasks(args.tasks)
    
    # 返回执行状态码
    failed_count = sum(1 for r in results.values() if r.status == TaskStatus.FAILED)
    sys.exit(failed_count)


if __name__ == "__main__":
    main()