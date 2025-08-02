"""
数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Tuple, Optional
from datetime import datetime


@dataclass
class SessionFile:
    """会话文件信息"""
    path: str
    size: int
    session_id: str
    project: str
    modified: datetime
    records: int = 0
    file_type: str = "jsonl"


@dataclass
class ScanResult:
    """扫描结果"""
    files: List[SessionFile] = field(default_factory=list)
    total_files: int = 0
    total_records: int = 0
    total_size: int = 0
    projects: List[str] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    
    @property
    def session_files(self) -> List[SessionFile]:
        """兼容性属性"""
        return self.files


@dataclass  
class FieldInfo:
    """字段信息"""
    path: str
    data_type: str
    examples: List[Any] = field(default_factory=list)
    count: int = 0
    null_count: int = 0
    unique_values: Set[Any] = field(default_factory=set)
    is_enum: bool = False
    enum_values: List[Any] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """分析结果"""
    fields: Dict[str, FieldInfo] = field(default_factory=dict)
    total_records: int = 0
    total_fields: int = 0
    total_files: int = 0
    data_types: Dict[str, int] = field(default_factory=dict)