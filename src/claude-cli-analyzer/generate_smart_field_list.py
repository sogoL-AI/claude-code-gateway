#!/usr/bin/env python3
"""
生成智能字段清单，将相似的数组索引字段归并为模式
"""

import sys
import os
from pathlib import Path
import ujson
import re
from collections import defaultdict

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


def normalize_field_pattern(field_path):
    """将字段路径标准化为模式"""
    # 将数组索引 [0], [1], [2] 等替换为 [*]
    pattern = re.sub(r'\[\d+\]', '[*]', field_path)
    return pattern


def extract_array_indices(field_path):
    """提取字段路径中的数组索引"""
    indices = re.findall(r'\[(\d+)\]', field_path)
    return [int(idx) for idx in indices]


def generate_smart_field_report():
    print("🧠 生成智能字段清单，归并相似的数组索引字段...")
    
    # 读取深度分析结果
    deep_result_file = "outputs/fields/deep_extraction_result.json"
    
    try:
        with open(deep_result_file, 'r', encoding='utf-8') as f:
            data = ujson.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到深度分析结果文件: {deep_result_file}")
        return None
    
    field_registry = data.get('field_registry', {})
    enum_fields = data.get('enum_fields', {})
    
    print(f"📊 处理 {len(field_registry)} 个原始字段...")
    
    # 按模式分组字段
    pattern_groups = defaultdict(list)
    
    for field_path, field_info in field_registry.items():
        pattern = normalize_field_pattern(field_path)
        pattern_groups[pattern].append({
            'original_path': field_path,
            'field_info': field_info,
            'indices': extract_array_indices(field_path)
        })
    
    # 生成合并后的字段清单
    merged_fields = []
    
    for pattern, fields in pattern_groups.items():
        if len(fields) == 1:
            # 单个字段，直接使用
            field = fields[0]
            merged_field = {
                'pattern': pattern,
                'original_paths': [field['original_path']],
                'type': field['field_info']['data_type'],
                'total_occurrences': field['field_info']['occurrence_count'],
                'null_count': field['field_info']['null_count'],
                'is_enum': field['field_info']['is_enum'],
                'enum_values': field['field_info']['enum_values'] if field['field_info']['is_enum'] else None,
                'examples': field['field_info']['value_examples'][:3],
                'patterns': field['field_info']['value_patterns'],
                'depth': pattern.count('.') + pattern.count('['),
                'array_indices': sorted(set().union(*[f['indices'] for f in fields])) if any(f['indices'] for f in fields) else [],
                'instance_count': 1
            }
        else:
            # 多个相似字段，需要合并
            all_occurrences = sum(f['field_info']['occurrence_count'] for f in fields)
            all_null_count = sum(f['field_info']['null_count'] for f in fields)
            
            # 合并类型（通常应该相同）
            types = set(f['field_info']['data_type'] for f in fields)
            merged_type = list(types)[0] if len(types) == 1 else f"mixed({','.join(types)})"
            
            # 合并枚举值
            all_enum_values = set()
            is_enum = False
            for f in fields:
                if f['field_info']['is_enum'] and f['field_info']['enum_values']:
                    is_enum = True
                    all_enum_values.update(f['field_info']['enum_values'])
            
            # 合并示例（需要处理可能的复杂数据类型）
            all_examples = []
            seen_examples = set()
            for f in fields:
                for example in f['field_info']['value_examples'][:2]:
                    # 转换为字符串用于去重
                    example_str = str(example)
                    if example_str not in seen_examples and len(all_examples) < 5:
                        all_examples.append(example)
                        seen_examples.add(example_str)
            
            # 合并模式
            all_patterns = set()
            for f in fields:
                all_patterns.update(f['field_info']['value_patterns'])
            
            merged_field = {
                'pattern': pattern,
                'original_paths': [f['original_path'] for f in fields],
                'type': merged_type,
                'total_occurrences': all_occurrences,
                'null_count': all_null_count,
                'is_enum': is_enum,
                'enum_values': sorted(list(all_enum_values)) if is_enum else None,
                'examples': all_examples[:3],  # 限制到前3个
                'patterns': sorted(list(all_patterns)),
                'depth': pattern.count('.') + pattern.count('['),
                'array_indices': sorted(set().union(*[f['indices'] for f in fields])) if any(f['indices'] for f in fields) else [],
                'instance_count': len(fields)
            }
        
        merged_fields.append(merged_field)
    
    # 按深度和出现次数排序
    merged_fields.sort(key=lambda x: (x['depth'], -x['total_occurrences']))
    
    print(f"🎯 原始字段: {len(field_registry)} 个")
    print(f"✨ 合并后模式: {len(merged_fields)} 个")
    print(f"📉 减少了: {len(field_registry) - len(merged_fields)} 个重复字段")
    
    # 生成Markdown报告
    report_content = generate_smart_markdown_report(merged_fields, data, len(field_registry))
    
    # 保存报告
    output_file = "outputs/reports/smart_field_inventory.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ 智能字段报告已生成: {output_file}")
    
    # 同时生成JSON格式
    json_output_file = "outputs/reports/smart_field_inventory.json"
    with open(json_output_file, 'w', encoding='utf-8') as f:
        ujson.dump({
            'metadata': {
                'original_field_count': len(field_registry),
                'merged_pattern_count': len(merged_fields),
                'reduction_count': len(field_registry) - len(merged_fields),
                'generation_time': '2025-08-01T01:27:37'
            },
            'patterns': merged_fields
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON格式智能清单已生成: {json_output_file}")
    
    return merged_fields


def generate_smart_markdown_report(merged_fields, data, original_count):
    """生成智能Markdown报告"""
    
    content = f"""# Claude Code 智能字段清单 (Smart Field Inventory)

> **Claude CLI会话记录字段模式分析 - 归并相似数组索引字段**
> 
> 生成时间: 2025-08-01T01:27:37  
> 原始字段数: **{original_count}**个  
> 智能模式数: **{len(merged_fields)}**个  
> 优化减少: **{original_count - len(merged_fields)}**个重复字段  
> 最大嵌套深度: **{max(f['depth'] for f in merged_fields)}**层

## 📊 智能优化统计

- **原始字段总数**: {original_count}个
- **智能模式数**: {len(merged_fields)}个  
- **减少重复字段**: {original_count - len(merged_fields)}个
- **数组模式字段**: {len([f for f in merged_fields if f['instance_count'] > 1])}个
- **单独字段**: {len([f for f in merged_fields if f['instance_count'] == 1])}个
- **枚举模式**: {len([f for f in merged_fields if f['is_enum']])}个

## 💡 模式说明

- **字段模式**: 使用 `[*]` 表示数组索引模式，如 `content[*].title` 表示 `content[0].title`, `content[1].title` 等
- **实例数**: 该模式包含的具体字段实例数量
- **索引范围**: 数组字段的索引范围，如 `[0-5]` 表示索引从0到5
- **总出现次数**: 所有实例的出现次数总和

---

"""

    # 按深度分组显示
    fields_by_depth = defaultdict(list)
    for field in merged_fields:
        fields_by_depth[field['depth']].append(field)
    
    for depth in sorted(fields_by_depth.keys()):
        depth_fields = fields_by_depth[depth]
        single_fields = [f for f in depth_fields if f['instance_count'] == 1]
        pattern_fields = [f for f in depth_fields if f['instance_count'] > 1]
        
        content += f"\n### 嵌套深度 {depth} ({len(depth_fields)}个模式)\n\n"
        
        if single_fields:
            content += f"#### 单独字段 ({len(single_fields)}个)\n\n"
            content += "| 字段路径 | 类型 | 出现次数 | 枚举值/示例 |\n"
            content += "|----------|------|----------|-------------|\n"
            
            for field in sorted(single_fields, key=lambda x: -x['total_occurrences']):
                pattern = field['pattern'].replace('|', '\\|')
                field_type = field['type']
                occurrences = field['total_occurrences']
                
                # 处理枚举值或示例
                if field['is_enum'] and field['enum_values']:
                    if len(field['enum_values']) <= 5:
                        values_display = f"**枚举**: {field['enum_values']}"
                    else:
                        values_display = f"**枚举**: {field['enum_values'][:3]}... ({len(field['enum_values'])}个值)"
                else:
                    if field['examples']:
                        examples_str = ', '.join([f'`{ex}`' if isinstance(ex, str) and len(str(ex)) < 30 else f'`{str(ex)[:27]}...`' for ex in field['examples'][:2]])
                        values_display = f"示例: {examples_str}"
                    else:
                        values_display = "-"
                
                values_escaped = values_display.replace('|', '\\|')
                content += f"| `{pattern}` | {field_type} | {occurrences} | {values_escaped} |\n"
            
            content += "\n"
        
        if pattern_fields:
            content += f"#### 数组模式字段 ({len(pattern_fields)}个)\n\n"
            content += "| 字段模式 | 类型 | 实例数 | 索引范围 | 总出现次数 | 枚举值/示例 |\n"
            content += "|----------|------|--------|----------|------------|-------------|\n"
            
            for field in sorted(pattern_fields, key=lambda x: -x['total_occurrences']):
                pattern = field['pattern'].replace('|', '\\|')
                field_type = field['type']
                instance_count = field['instance_count']
                total_occurrences = field['total_occurrences']
                
                # 处理索引范围
                if field['array_indices']:
                    min_idx = min(field['array_indices'])
                    max_idx = max(field['array_indices'])
                    if min_idx == max_idx:
                        idx_range = f"[{min_idx}]"
                    else:
                        idx_range = f"[{min_idx}-{max_idx}]"
                else:
                    idx_range = "-"
                
                # 处理枚举值或示例
                if field['is_enum'] and field['enum_values']:
                    if len(field['enum_values']) <= 3:
                        values_display = f"**枚举**: {field['enum_values']}"
                    else:
                        values_display = f"**枚举**: {field['enum_values'][:2]}... (+{len(field['enum_values'])-2})"
                else:
                    if field['examples']:
                        examples_str = ', '.join([f'`{ex}`' if isinstance(ex, str) and len(str(ex)) < 25 else f'`{str(ex)[:22]}...`' for ex in field['examples'][:2]])
                        values_display = f"示例: {examples_str}"
                    else:
                        values_display = "-"
                
                values_escaped = values_display.replace('|', '\\|')
                content += f"| `{pattern}` | {field_type} | {instance_count} | {idx_range} | {total_occurrences} | {values_escaped} |\n"
            
            content += "\n"
    
    # 添加高频模式汇总
    high_freq_patterns = [f for f in merged_fields if f['total_occurrences'] >= 100]
    if high_freq_patterns:
        content += f"\n## 🔥 高频字段模式 (总出现≥100次，共{len(high_freq_patterns)}个)\n\n"
        
        content += "| 字段模式 | 类型 | 实例数 | 总出现次数 | 描述 |\n"
        content += "|----------|------|--------|------------|------|\n"
        
        for field in sorted(high_freq_patterns, key=lambda x: -x['total_occurrences'])[:30]:
            pattern = field['pattern'].replace('|', '\\|')
            field_type = field['type']
            instance_count = field['instance_count']
            total_occurrences = field['total_occurrences']
            
            # 生成描述
            if field['instance_count'] > 1:
                desc = f"数组模式，包含{field['instance_count']}个实例"
                if field['array_indices']:
                    desc += f"，索引{min(field['array_indices'])}-{max(field['array_indices'])}"
            else:
                desc = "单独字段"
                
            if field['is_enum']:
                desc += f"，枚举({len(field['enum_values'])}个值)"
            
            content += f"| `{pattern}` | {field_type} | {instance_count} | {total_occurrences} | {desc} |\n"
    
    # 添加数组模式统计
    array_patterns = [f for f in merged_fields if f['instance_count'] > 1]
    if array_patterns:
        content += f"\n## 📊 数组模式统计\n\n"
        content += f"发现 **{len(array_patterns)}** 个数组模式，共包含 **{sum(f['instance_count'] for f in array_patterns)}** 个字段实例。\n\n"
        
        # 按实例数排序，显示最复杂的模式
        content += "### 最复杂的数组模式 (实例数最多)\n\n"
        content += "| 字段模式 | 实例数 | 索引范围 | 示例字段 |\n"
        content += "|----------|--------|----------|----------|\n"
        
        for field in sorted(array_patterns, key=lambda x: -x['instance_count'])[:15]:
            pattern = field['pattern'].replace('|', '\\|')
            instance_count = field['instance_count']
            
            if field['array_indices']:
                min_idx = min(field['array_indices'])
                max_idx = max(field['array_indices'])
                idx_range = f"[{min_idx}-{max_idx}]" if min_idx != max_idx else f"[{min_idx}]"
            else:
                idx_range = "-"
            
            example_field = field['original_paths'][0].replace('|', '\\|')
            content += f"| `{pattern}` | {instance_count} | {idx_range} | `{example_field}` |\n"
    
    content += f"\n---\n\n*本报告将{original_count}个原始字段智能归并为{len(merged_fields)}个模式，优化了{original_count - len(merged_fields)}个重复的数组索引字段。*\n"
    
    return content


if __name__ == "__main__":
    generate_smart_field_report()