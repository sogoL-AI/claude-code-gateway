#!/usr/bin/env python3
"""
演示字段合并功能
"""

import sys
import os
import json
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def demo_field_merge():
    """演示字段合并功能"""
    
    print("🎯 Claude CLI 字段合并功能演示")
    print("=" * 50)
    
    try:
        from core.field_extractor import FieldExtractor
        
        # 创建测试数据 - 模拟Web搜索结果
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
        
        print("📊 提取字段...")
        extractor.extract_fields_from_value(test_data)
        
        print(f"✅ 字段提取完成，发现 {len(extractor.field_registry)} 个字段")
        
        # 显示合并前的字段
        print(f"\n🔍 合并前的字段示例:")
        content_fields = [path for path in extractor.field_registry.keys() if 'content[' in path]
        for i, field in enumerate(sorted(content_fields)[:10]):
            print(f"   {i+1}. {field}")
        
        print(f"\n⚙️  执行字段合并...")
        
        # 手动调用合并功能
        extractor.merge_array_index_fields()
        
        print(f"✅ 合并完成，现在有 {len(extractor.field_registry)} 个字段")
        
        # 显示合并后的字段
        print(f"\n🎯 合并后的字段:")
        merged_content_fields = [path for path in extractor.field_registry.keys() if 'content[' in path]
        for i, field in enumerate(sorted(merged_content_fields)):
            info = extractor.field_registry[field]
            print(f"   {i+1}. {field:<40} (出现{info.occurrence_count}次)")
        
        # 显示合并效果统计
        all_merged_fields = [path for path in extractor.field_registry.keys() if '[*]' in path]
        print(f"\n📈 合并效果统计:")
        print(f"   包含[*]的合并字段: {len(all_merged_fields)} 个")
        print(f"   总字段数减少: {content_fields.__len__() - merged_content_fields.__len__()} 个")
        
        # 创建输出目录并保存结果
        output_dir = current_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        (output_dir / "demo").mkdir(exist_ok=True)
        
        # 保存演示结果
        demo_result = {
            "演示说明": "字段合并功能演示",
            "合并前字段数": len(content_fields),
            "合并后字段数": len(merged_content_fields),
            "合并字段示例": {},
            "合并效果": f"减少了 {len(content_fields) - len(merged_content_fields)} 个重复字段"
        }
        
        for field_path, field_info in extractor.field_registry.items():
            if '[*]' in field_path:
                demo_result["合并字段示例"][field_path] = {
                    "出现次数": field_info.occurrence_count,
                    "数据类型": field_info.data_type,
                    "示例值": field_info.value_examples[:3]
                }
        
        with open(output_dir / "demo" / "field_merge_demo.json", 'w', encoding='utf-8') as f:
            json.dump(demo_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 演示结果已保存到: {output_dir}/demo/field_merge_demo.json")
        print(f"\n🎉 字段合并功能运行正常！")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_field_merge()
    if success:
        print("\n✅ 字段合并功能验证成功 - 准备处理真实数据!")
    else:
        print("\n❌ 字段合并功能验证失败")