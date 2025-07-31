#!/usr/bin/env python3
"""
运行Claude CLI完整分析
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from analyzers.main_analyzer import MainAnalyzer


def main():
    print("🚀 启动Claude CLI字段分析...")
    
    # 设置输出目录
    output_dir = Path(__file__).parent / "outputs"
    
    # 创建主分析器
    analyzer = MainAnalyzer(output_dir=str(output_dir))
    
    # 运行完整分析（限制记录数以提高速度）
    try:
        report = analyzer.run_complete_analysis(max_records_per_file=2000)
        
        print("\n🎉 分析完成！主要发现:")
        print(f"   📁 扫描文件: {report['扫描统计']['总文件数']} 个")
        print(f"   📝 处理记录: {report['扫描统计']['总记录数']} 条")
        print(f"   🔍 发现字段: {report['字段分析']['发现字段总数']} 个")
        print(f"   🏷️  枚举字段: {report['字段分析']['枚举字段数']} 个")
        
        # 显示前10个最常用字段
        print(f"\n📊 最常用的10个字段:")
        for i, field_spec in enumerate(report["字段规范"][:10], 1):
            print(f"   {i:2d}. {field_spec['字段名']:<25} {field_spec['类型']:<15} ({field_spec['出现频率']})")
        
        # 显示枚举字段
        if report["枚举字段完整列表"]:
            print(f"\n🔖 发现的枚举字段:")
            for field_name, enum_values in list(report["枚举字段完整列表"].items())[:10]:
                print(f"   • {field_name}: {enum_values}")
        
        print(f"\n📂 详细结果请查看: {output_dir}")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())