"""
基础分析器类
为所有分析器提供通用功能和接口
"""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import SessionFile, ScanResult


class BaseAnalyzer(ABC):
    """基础分析器抽象类"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.start_time = None
        self.end_time = None
        self.processed_files = 0
        self.processed_records = 0
        self.errors = []
        
    def start_analysis(self):
        """开始分析"""
        self.start_time = datetime.now()
        print(f"🚀 {self.name} 开始分析")
        print("=" * 50)
        
    def finish_analysis(self):
        """结束分析"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        print(f"\n✅ {self.name} 分析完成！")
        print(f"   处理文件: {self.processed_files}")
        print(f"   处理记录: {self.processed_records:,}")
        print(f"   处理时间: {duration:.2f}秒")
        if self.errors:
            print(f"   错误数量: {len(self.errors)}")
            
    def log_error(self, error: str, file_path: Optional[str] = None):
        """记录错误"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'file_path': file_path
        }
        self.errors.append(error_info)
        print(f"❌ 错误: {error}")
        
    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    # JSON Lines格式
                    return [json.loads(line.strip()) for line in f if line.strip()]
                else:
                    # 标准JSON格式
                    data = json.load(f)
                    return [data] if isinstance(data, dict) else data
        except Exception as e:
            self.log_error(f"读取文件失败: {e}", file_path)
            return []
            
    def save_json_result(self, data: Any, output_path: str, pretty: bool = True):
        """保存JSON结果"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(data, f, ensure_ascii=False)
                    
            print(f"📁 结果已保存到: {output_path}")
        except Exception as e:
            self.log_error(f"保存文件失败: {e}", output_path)
            
    def truncate_value(self, value: Any, max_length: int = 100) -> Any:
        """递归截断最深层的值，保持嵌套结构完整"""
        if isinstance(value, str) and len(value) > max_length:
            return value[:max_length] + "..."
        elif isinstance(value, dict):
            return {k: self.truncate_value(v, max_length) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.truncate_value(item, max_length) for item in value]
        else:
            return value
            
    def generate_summary(self) -> Dict[str, Any]:
        """生成分析摘要"""
        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            
        return {
            "分析器": self.name,
            "版本": self.version,
            "生成时间": datetime.now().isoformat(),
            "分析时长": f"{duration:.2f}秒",
            "处理统计": {
                "文件数": self.processed_files,
                "记录数": self.processed_records,
                "错误数": len(self.errors)
            }
        }
        
    @abstractmethod
    def analyze(self, scan_result: ScanResult) -> Dict[str, Any]:
        """执行分析 - 需要子类实现"""
        pass
        
    @abstractmethod
    def get_output_paths(self) -> Dict[str, str]:
        """获取输出路径 - 需要子类实现"""
        pass


class FileBasedAnalyzer(BaseAnalyzer):
    """基于文件的分析器基类"""
    
    def __init__(self, name: str, version: str = "1.0.0", output_dir: str = "outputs"):
        super().__init__(name, version)
        self.output_dir = Path(output_dir)
        
    def process_file(self, file_path: str, file_type: str = "jsonl") -> int:
        """处理单个文件"""
        try:
            records = self.load_json_file(file_path)
            self.processed_files += 1
            
            for record in records:
                self.process_record(record)
                self.processed_records += 1
                
            return len(records)
        except Exception as e:
            self.log_error(f"处理文件失败: {e}", file_path)
            return 0
            
    @abstractmethod
    def process_record(self, record: Dict[str, Any]) -> None:
        """处理单条记录 - 需要子类实现"""
        pass


class ProgressMixin:
    """进度显示混入类"""
    
    def show_progress(self, current: int, total: int, item_name: str = "项目"):
        """显示进度"""
        if current % 10 == 0 or current == total:
            percentage = (current / total) * 100 if total > 0 else 0
            print(f"  📊 进度: {current}/{total} {item_name} ({percentage:.1f}%)")