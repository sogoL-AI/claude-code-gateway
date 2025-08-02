"""
通用工具函数
提供各种分析器共用的工具函数
"""

import re
import json
import hashlib
import logging
from typing import Any, Dict, List, Set, Tuple, Optional
from pathlib import Path
from datetime import datetime


def normalize_array_indices(path: str) -> str:
    """
    规范化数组索引: [0], [1], [2] → [*]
    
    Args:
        path: 字段路径，如 "message.content[0].text"
        
    Returns:
        规范化后的路径，如 "message.content[*].text"
    """
    return re.sub(r'\[\d+\]', '[*]', path)


def generate_structure_signature(obj: Any) -> str:
    """
    递归生成完整结构描述 - 类型识别核心
    
    Args:
        obj: 要分析的对象
        
    Returns:
        结构签名字符串
    """
    if isinstance(obj, dict):
        # 按key排序确保签名一致性
        field_signatures = []
        for key in sorted(obj.keys()):
            value_sig = generate_structure_signature(obj[key])
            field_signatures.append(f"{key}:{value_sig}")
        return f"object{{{','.join(field_signatures)}}}"
    elif isinstance(obj, list):
        if obj:
            # 使用第一个元素的结构代表数组类型
            item_sig = generate_structure_signature(obj[0])
            return f"array<{item_sig}>"
        return "array<unknown>"
    else:
        # 基础类型识别
        return type(obj).__name__


def get_data_type(value: Any) -> str:
    """
    获取数据类型的友好名称
    
    Args:
        value: 要检查的值
        
    Returns:
        类型名称字符串
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return str(type(value).__name__)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_uuid(value: str) -> bool:
    """
    判断字符串是否为UUID格式
    
    Args:
        value: 要检查的字符串
        
    Returns:
        是否为UUID格式
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, value, re.IGNORECASE))


def is_timestamp(value: str) -> bool:
    """
    判断字符串是否为时间戳格式
    
    Args:
        value: 要检查的字符串
        
    Returns:
        是否为时间戳格式
    """
    # ISO 8601格式检查
    timestamp_patterns = [
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d{3})?$'
    ]
    
    for pattern in timestamp_patterns:
        if re.match(pattern, value):
            return True
    return False


def calculate_file_hash(file_path: str) -> str:
    """
    计算文件的MD5哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件的MD5哈希值
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return ""


def format_bytes(bytes_size: int) -> str:
    """
    格式化字节大小为人类可读格式
    
    Args:
        bytes_size: 字节大小
        
    Returns:
        格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def safe_get(obj: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    安全地获取嵌套字典中的值
    
    Args:
        obj: 字典对象
        path: 点分隔的路径，如 "message.content.text"
        default: 默认值
        
    Returns:
        获取到的值或默认值
    """
    try:
        keys = path.split('.')
        current = obj
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except Exception:
        return default


def create_output_structure(base_dir: str, analysis_name: str) -> Dict[str, str]:
    """
    创建标准输出目录结构
    
    Args:
        base_dir: 基础输出目录
        analysis_name: 分析名称
        
    Returns:
        输出路径字典
    """
    base_path = Path(base_dir)
    paths = {
        'base': str(base_path),
        'analysis': str(base_path / analysis_name),
        'detail': str(base_path / analysis_name / f"{analysis_name}_detail.json"),
        'summary': str(base_path / analysis_name / f"{analysis_name}_summary.json"),
        'compact': str(base_path / analysis_name / f"{analysis_name}_compact.json"),
        'metadata': str(base_path / analysis_name / 'metadata.json')
    }
    
    # 创建目录
    for key, path in paths.items():
        if key in ['analysis']:
            Path(path).mkdir(parents=True, exist_ok=True)
    
    return paths


def find_common_patterns(values: List[str], min_count: int = 3) -> List[Tuple[str, int]]:
    """
    在字符串列表中查找常见模式
    
    Args:
        values: 字符串值列表
        min_count: 最小出现次数
        
    Returns:
        模式和出现次数的列表
    """
    from collections import Counter
    
    patterns = []
    
    # UUID模式
    uuid_count = sum(1 for v in values if is_uuid(v))
    if uuid_count >= min_count:
        patterns.append(("UUID", uuid_count))
    
    # 时间戳模式
    timestamp_count = sum(1 for v in values if is_timestamp(v))
    if timestamp_count >= min_count:
        patterns.append(("Timestamp", timestamp_count))
    
    # 长度模式
    length_counter = Counter(len(v) for v in values)
    for length, count in length_counter.most_common(3):
        if count >= min_count:
            patterns.append((f"Length-{length}", count))
    
    return patterns


def merge_analysis_results(*results: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个分析结果
    
    Args:
        *results: 多个分析结果字典
        
    Returns:
        合并后的结果
    """
    merged = {
        "合并时间": datetime.now().isoformat(),
        "来源数量": len(results),
        "合并结果": {}
    }
    
    for i, result in enumerate(results):
        merged["合并结果"][f"结果_{i+1}"] = result
    
    return merged


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    设置标准化的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    
    return logger