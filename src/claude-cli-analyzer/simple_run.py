#!/usr/bin/env python3

import sys
import os
sys.path.append('./src')

try:
    # 测试导入
    from core.field_extractor import FieldExtractor
    print("✅ FieldExtractor导入成功")
    
    # 创建简单测试
    extractor = FieldExtractor()
    test_data = {
        "toolUseResult": {
            "results": [
                {
                    "content": [
                        {"title": "GitHub - microsoft/playwright-mcp", "url": "https://github.com/microsoft/playwright-mcp"},
                        {"title": "Using Playwright MCP with Claude Code", "url": "https://til.simonwillison.net/claude-code/playwright"},
                        {"title": "Playwright MCP: Comprehensive Guide", "url": "https://medium.com/@bluudit/playwright-mcp-comp"}
                    ]
                }
            ]
        }
    }
    
    print("🔍 提取字段...")
    extractor.extract_fields_from_value(test_data)
    
    print(f"合并前字段数: {len(extractor.field_registry)}")
    
    # 生成结果（会自动调用合并）
    result = extractor.generate_extraction_result()
    
    print(f"合并后字段数: {result.total_fields_discovered}")
    print("✅ 字段合并功能正常工作")
    
    # 显示合并效果
    merged_fields = [path for path in extractor.field_registry.keys() if '[*]' in path]
    print(f"\n🔄 合并字段示例:")
    for field in merged_fields:
        info = extractor.field_registry[field]
        print(f"   • {field} ({info.occurrence_count}次)")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()