"""
Claude CLI 分析器 - 共享组件
包含用于分析Claude CLI会话数据的各种共享工具和类
"""

from .models import SessionFile, ScanResult, FieldInfo, AnalysisResult
from .base_analyzer import BaseAnalyzer, FileBasedAnalyzer, ProgressMixin
from .utils import (
    normalize_array_indices,
    generate_structure_signature,
    get_data_type,
    truncate_string,
    is_uuid,
    is_timestamp,
    calculate_file_hash,
    format_bytes,
    safe_get,
    create_output_structure,
    find_common_patterns,
    merge_analysis_results
)

__version__ = "3.0.0"
__all__ = [
    # 数据模型
    "SessionFile",
    "ScanResult", 
    "FieldInfo",
    "AnalysisResult",
    
    # 基础分析器
    "BaseAnalyzer",
    "FileBasedAnalyzer", 
    "ProgressMixin",
    
    # 工具函数
    "normalize_array_indices",
    "generate_structure_signature",
    "get_data_type",
    "truncate_string",
    "is_uuid",
    "is_timestamp",
    "calculate_file_hash",
    "format_bytes",
    "safe_get",
    "create_output_structure",
    "find_common_patterns",
    "merge_analysis_results"
]