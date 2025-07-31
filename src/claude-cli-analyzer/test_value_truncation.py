#!/usr/bin/env python3
"""
测试值截断功能
"""

import sys
import os
import json
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_value_truncation():
    """测试值截断功能"""
    
    print("🧪 测试值截断功能")
    print("=" * 50)
    
    try:
        from core.field_extractor import FieldExtractor
        
        # 创建包含长值的测试数据
        long_text = "这是一个非常长的文本，用来测试截断功能。" * 10  # 约400字符
        long_url = "https://example.com/very/long/path/with/many/segments/" + "x" * 200
        
        test_data = {
            "短文本": "正常长度的文本",
            "长文本": long_text,
            "长URL": long_url,
            "长数组": [f"元素{i}_" + "x" * 50 for i in range(10)],  # 包含长字符串的数组
            "长对象": {
                "description": "一个包含超长描述的对象：" + "详细信息 " * 50,
                "data": {"nested": "嵌套的长数据：" + "y" * 100}
            },
            "短枚举": ["A", "B", "C"],
            "长枚举": [long_text, long_url]
        }
        
        print(f"📊 测试数据长度:")
        print(f"   长文本: {len(long_text)} 字符")
        print(f"   长URL: {len(long_url)} 字符")
        
        # 创建字段提取器，设置截断长度为100
        extractor = FieldExtractor(max_value_length=100)
        
        print(f"\n🔍 提取字段...")
        extractor.extract_fields_from_value(test_data)
        
        # 生成结果
        result = extractor.generate_extraction_result()
        
        print(f"✅ 字段提取完成，发现 {result.total_fields_discovered} 个字段")
        
        # 检查截断效果
        print(f"\n📋 检查截断效果:")
        
        truncated_count = 0
        for field_path, field_info in result.field_registry.items():
            for example in field_info.value_examples:
                if isinstance(example, str) and example.endswith("..."):
                    truncated_count += 1
                    if truncated_count <= 5:  # 只显示前5个截断的例子
                        print(f"   ✂️  {field_path}: {example}")
        
        print(f"\n📈 截断统计:")
        print(f"   发现被截断的值: {truncated_count} 个")
        
        # 测试枚举字段的截断
        enum_truncated_count = 0
        for field_path, enum_values in result.enum_fields.items():
            for value in enum_values:
                if isinstance(value, str) and value.endswith("..."):
                    enum_truncated_count += 1
        
        print(f"   枚举字段被截断的值: {enum_truncated_count} 个")
        
        # 创建输出目录并保存测试结果
        output_dir = current_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        (output_dir / "test").mkdir(exist_ok=True)
        
        # 保存测试结果
        test_result = {
            "测试说明": "值截断功能测试",
            "截断设置": {
                "最大长度": 100,
                "截断后缀": "..."
            },
            "测试结果": {
                "总字段数": result.total_fields_discovered,
                "被截断的值数量": truncated_count,
                "枚举字段被截断值数量": enum_truncated_count
            },
            "截断示例": {}
        }
        
        # 收集截断示例
        for field_path, field_info in result.field_registry.items():
            for example in field_info.value_examples:
                if isinstance(example, str) and example.endswith("..."):
                    if len(test_result["截断示例"]) < 10:  # 最多记录10个示例
                        test_result["截断示例"][field_path] = example
        
        with open(output_dir / "test" / "value_truncation_test.json", 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存到: {output_dir}/test/value_truncation_test.json")
        
        # 验证结果
        success = truncated_count > 0
        if success:
            print(f"\n✅ 值截断功能测试通过！")
        else:
            print(f"\n❌ 值截断功能测试失败！")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_value_truncation()
    if success:
        print("\n🎉 值截断功能工作正常，现在可以运行完整分析了！")
    else:
        print("\n⚠️  值截断功能需要修复")