#!/usr/bin/env python3
"""
测试字段合并功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.field_extractor import FieldExtractor

def test_field_merger():
    """测试字段合并功能"""
    
    # 创建测试数据
    test_data = {
        "toolUseResult": {
            "results": [
                {
                    "content": [
                        {"title": "GitHub - microsoft/playwright-mcp", "url": "https://github.com/microsoft/playwright-mcp"},
                        {"title": "Using Playwright MCP with Claude Code", "url": "https://til.simonwillison.net/claude-code/playwright"},
                        {"title": "Playwright MCP: Comprehensive Guide", "url": "https://medium.com/@bluudit/playwright-mcp-comp"},
                        {"title": "A Detailed Guide To Playwright MCP Server", "url": "https://www.qatouch.com/blog/playwright-mcp-ser"},
                        {"title": "GitHub - executeautomation/mcp-playwright", "url": "https://github.com/executeautomation/mcp-playwr"}
                    ]
                }
            ]
        }
    }
    
    # 创建字段提取器
    extractor = FieldExtractor()
    
    print("🔍 提取字段前...")
    extractor.extract_fields_from_value(test_data)
    
    # 显示合并前的字段
    print(f"\n📊 合并前发现的字段数量: {len(extractor.field_registry)}")
    
    content_fields_before = [path for path in extractor.field_registry.keys() 
                           if 'content[' in path and '].title' in path]
    print(f"内容标题字段 (合并前): {len(content_fields_before)}")
    for field in sorted(content_fields_before):
        print(f"  - {field}")
    
    content_url_fields_before = [path for path in extractor.field_registry.keys() 
                               if 'content[' in path and '].url' in path]
    print(f"内容URL字段 (合并前): {len(content_url_fields_before)}")
    for field in sorted(content_url_fields_before):
        print(f"  - {field}")
    
    # 执行合并
    print(f"\n🔄 执行字段合并...")
    extractor.merge_array_index_fields()
    
    # 显示合并后的字段
    print(f"\n📊 合并后发现的字段数量: {len(extractor.field_registry)}")
    
    content_fields_after = [path for path in extractor.field_registry.keys() 
                          if 'content[' in path and '].title' in path]
    print(f"内容标题字段 (合并后): {len(content_fields_after)}")
    for field in sorted(content_fields_after):
        field_info = extractor.field_registry[field]
        print(f"  - {field} (出现次数: {field_info.occurrence_count}, 示例: {field_info.value_examples[:2]})")
    
    content_url_fields_after = [path for path in extractor.field_registry.keys() 
                              if 'content[' in path and '].url' in path]
    print(f"内容URL字段 (合并后): {len(content_url_fields_after)}")
    for field in sorted(content_url_fields_after):
        field_info = extractor.field_registry[field]
        print(f"  - {field} (出现次数: {field_info.occurrence_count}, 示例: {field_info.value_examples[:2]})")
    
    # 验证结果
    print(f"\n✅ 测试结果:")
    title_merged = any('[*]' in field and 'title' in field for field in extractor.field_registry.keys())
    url_merged = any('[*]' in field and 'url' in field for field in extractor.field_registry.keys())
    
    print(f"标题字段已合并: {'✅' if title_merged else '❌'}")
    print(f"URL字段已合并: {'✅' if url_merged else '❌'}")
    
    # 检查合并后的字段统计
    merged_title_field = None
    merged_url_field = None
    
    for field_path, field_info in extractor.field_registry.items():
        if 'content[*].title' in field_path:
            merged_title_field = field_info
        elif 'content[*].url' in field_path:
            merged_url_field = field_info
    
    if merged_title_field:
        print(f"合并后的标题字段统计: 出现{merged_title_field.occurrence_count}次, {len(merged_title_field.value_examples)}个示例")
    
    if merged_url_field:
        print(f"合并后的URL字段统计: 出现{merged_url_field.occurrence_count}次, {len(merged_url_field.value_examples)}个示例")

if __name__ == "__main__":
    test_field_merger()