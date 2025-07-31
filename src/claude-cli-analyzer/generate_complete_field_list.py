#!/usr/bin/env python3
"""
生成包含所有字段的完整报告
"""

import sys
import os
from pathlib import Path
import ujson

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


def generate_complete_field_report():
    print("📋 生成包含所有字段的完整报告...")
    
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
    
    print(f"📊 处理 {len(field_registry)} 个字段...")
    
    # 整理所有字段信息
    all_fields = []
    
    for field_path, field_info in field_registry.items():
        field_entry = {
            'path': field_path,
            'type': field_info['data_type'],
            'occurrences': field_info['occurrence_count'],
            'null_count': field_info['null_count'],
            'is_enum': field_info['is_enum'],
            'enum_values': field_info['enum_values'] if field_info['is_enum'] else None,
            'examples': field_info['value_examples'][:3],  # 前3个示例
            'patterns': field_info['value_patterns'],
            'depth': field_path.count('.') + field_path.count('[')  # 估算嵌套深度
        }
        all_fields.append(field_entry)
    
    # 按嵌套深度和字母顺序排序
    all_fields.sort(key=lambda x: (x['depth'], x['path']))
    
    # 生成Markdown报告
    report_content = generate_markdown_report(all_fields, data)
    
    # 保存报告
    output_file = "outputs/reports/complete_field_inventory.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ 完整字段报告已生成: {output_file}")
    
    # 同时生成JSON格式的完整清单
    json_output_file = "outputs/reports/complete_field_inventory.json"
    with open(json_output_file, 'w', encoding='utf-8') as f:
        ujson.dump({
            'metadata': {
                'total_fields': len(all_fields),
                'total_enum_fields': len([f for f in all_fields if f['is_enum']]),
                'max_depth': max(f['depth'] for f in all_fields),
                'generation_time': data.get('generation_time', 'unknown')
            },
            'fields': all_fields
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON格式字段清单已生成: {json_output_file}")
    
    return all_fields


def generate_markdown_report(all_fields, data):
    """生成Markdown格式的完整报告"""
    
    content = f"""# Claude Code 完整字段清单 (All Fields Inventory)

> **Claude CLI会话记录中发现的所有字段路径完整清单**
> 
> 生成时间: 2025-08-01T01:22:48  
> 数据源: {data.get('total_records_processed', 0)}条记录深度分析  
> 字段总数: **{len(all_fields)}**个字段路径  
> 最大嵌套深度: **{max(f['depth'] for f in all_fields)}**层

## 📊 统计概览

- **字段总数**: {len(all_fields)}个
- **枚举字段**: {len([f for f in all_fields if f['is_enum']])}个
- **最大嵌套深度**: {max(f['depth'] for f in all_fields)}层
- **包含Subagent的记录**: {data.get('subagent_records_found', 0)}条
- **工具使用记录**: {data.get('tool_use_records_found', 0)}条

## 📋 完整字段清单

### 字段说明
- **路径**: 完整的字段路径，包含所有嵌套层级
- **类型**: 推断的数据类型
- **出现次数**: 在所有记录中的出现频率
- **枚举值**: 如果是枚举类型，列出所有可能的值
- **示例**: 典型的字段值示例

---

"""

    # 按深度分组显示字段
    fields_by_depth = {}
    for field in all_fields:
        depth = field['depth']
        if depth not in fields_by_depth:
            fields_by_depth[depth] = []
        fields_by_depth[depth].append(field)
    
    for depth in sorted(fields_by_depth.keys()):
        depth_fields = fields_by_depth[depth]
        content += f"\n### 嵌套深度 {depth} ({len(depth_fields)}个字段)\n\n"
        
        # 创建表格
        content += "| 字段路径 | 类型 | 出现次数 | 枚举值/示例 |\n"
        content += "|----------|------|----------|-------------|\n"
        
        for field in depth_fields:
            path = field['path']
            field_type = field['type']
            occurrences = field['occurrences']
            
            # 处理枚举值或示例
            if field['is_enum'] and field['enum_values']:
                if len(field['enum_values']) <= 5:
                    values_display = f"**枚举**: {field['enum_values']}"
                else:
                    values_display = f"**枚举**: {field['enum_values'][:3]}... ({len(field['enum_values'])}个值)"
            else:
                if field['examples']:
                    examples_str = ', '.join([f'`{ex}`' if isinstance(ex, str) and len(str(ex)) < 50 else f'`{str(ex)[:47]}...`' for ex in field['examples'][:2]])
                    values_display = f"示例: {examples_str}"
                else:
                    values_display = "-"
            
            # 转义Markdown特殊字符
            path_escaped = path.replace('|', '\\|')
            values_escaped = values_display.replace('|', '\\|')
            
            content += f"| `{path_escaped}` | {field_type} | {occurrences} | {values_escaped} |\n"
        
        content += "\n"
    
    # 添加枚举字段汇总
    enum_fields = [f for f in all_fields if f['is_enum']]
    if enum_fields:
        content += f"\n## 🔖 枚举字段汇总 ({len(enum_fields)}个)\n\n"
        
        content += "| 字段路径 | 枚举值 | 值数量 |\n"
        content += "|----------|--------|--------|\n"
        
        # 按出现次数排序
        enum_fields.sort(key=lambda x: x['occurrences'], reverse=True)
        
        for field in enum_fields:
            path = field['path'].replace('|', '\\|')
            enum_values = field['enum_values']
            
            if len(enum_values) <= 10:
                values_str = str(enum_values)
            else:
                values_str = f"{enum_values[:3]}... (+{len(enum_values)-3}个)"
            
            values_escaped = values_str.replace('|', '\\|')
            content += f"| `{path}` | {values_escaped} | {len(enum_values)} |\n"
    
    # 添加高频字段汇总
    high_freq_fields = [f for f in all_fields if f['occurrences'] >= 100]
    if high_freq_fields:
        content += f"\n## 🔥 高频字段 (出现≥100次，共{len(high_freq_fields)}个)\n\n"
        
        content += "| 字段路径 | 类型 | 出现次数 | 描述/枚举值 |\n"
        content += "|----------|------|----------|-------------|\n"
        
        # 按出现次数排序
        high_freq_fields.sort(key=lambda x: x['occurrences'], reverse=True)
        
        for field in high_freq_fields[:50]:  # 只显示前50个高频字段
            path = field['path'].replace('|', '\\|')
            field_type = field['type']
            occurrences = field['occurrences']
            
            if field['is_enum'] and field['enum_values']:
                desc = f"**枚举**: {field['enum_values'][:3]}..." if len(field['enum_values']) > 3 else f"**枚举**: {field['enum_values']}"
            else:
                desc = field['examples'][0] if field['examples'] else "-"
                if isinstance(desc, str) and len(desc) > 50:
                    desc = desc[:47] + "..."
                desc = f"`{desc}`"
            
            desc_escaped = desc.replace('|', '\\|')
            content += f"| `{path}` | {field_type} | {occurrences} | {desc_escaped} |\n"
    
    content += f"\n---\n\n*本报告包含Claude CLI会话记录中发现的全部{len(all_fields)}个字段路径，涵盖所有嵌套层级。*\n"
    
    return content


if __name__ == "__main__":
    generate_complete_field_report()