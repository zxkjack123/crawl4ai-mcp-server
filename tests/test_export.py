#!/usr/bin/env python3
"""
测试搜索结果导出功能
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.index import (
    export_search_results,
    initialize_search_manager
)


async def test_export_basic():
    """测试基本的导出功能"""
    print("=" * 60)
    print("测试基本的搜索结果导出")
    print("=" * 60)
    
    # 初始化搜索管理器
    await initialize_search_manager()
    
    # 导出搜索结果
    result = await export_search_results(
        query="Python programming",
        num_results=5,
        engine="duckduckgo",
        output_file="test_basic_export.json",
        include_metadata=True
    )
    
    data = json.loads(result)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 验证导出成功
    assert data["success"] is True, "导出失败"
    assert "output_file" in data, "缺少输出文件路径"
    assert "file_size_bytes" in data, "缺少文件大小"
    assert "total_results" in data, "缺少结果数量"
    
    # 检查文件是否存在
    output_path = Path(data["output_file"])
    assert output_path.exists(), f"输出文件不存在: {output_path}"
    
    # 检查文件内容
    with open(output_path, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
    
    assert "results" in exported_data, "导出数据缺少 results"
    assert "metadata" in exported_data, "导出数据缺少 metadata"
    
    print(f"\n✅ 基本导出测试通过")
    print(f"   文件位置: {output_path}")
    print(f"   文件大小: {data['file_size_bytes']} 字节")
    print(f"   结果数量: {data['total_results']}")


async def test_export_without_metadata():
    """测试不包含元数据的导出"""
    print("\n" + "=" * 60)
    print("测试不包含元数据的导出")
    print("=" * 60)
    
    # 导出搜索结果（不包含元数据）
    result = await export_search_results(
        query="Machine Learning",
        num_results=3,
        engine="auto",
        output_file="test_no_metadata_export.json",
        include_metadata=False
    )
    
    data = json.loads(result)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 验证导出成功
    assert data["success"] is True, "导出失败"
    
    # 检查文件内容
    output_path = Path(data["output_file"])
    with open(output_path, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
    
    assert "results" in exported_data, "导出数据缺少 results"
    assert "metadata" not in exported_data, "不应包含 metadata"
    
    print(f"\n✅ 无元数据导出测试通过")


async def test_export_custom_path():
    """测试自定义输出路径"""
    print("\n" + "=" * 60)
    print("测试自定义输出路径")
    print("=" * 60)
    
    # 导出到子目录
    result = await export_search_results(
        query="AI test",
        num_results=2,
        engine="duckduckgo",
        output_file="custom/path/test_export.json",
        include_metadata=True
    )
    
    data = json.loads(result)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 验证导出成功
    assert data["success"] is True, "导出失败"
    
    # 检查文件路径
    output_path = Path(data["output_file"])
    assert "custom/path" in str(output_path), "输出路径不正确"
    assert output_path.exists(), f"输出文件不存在: {output_path}"
    
    print(f"\n✅ 自定义路径导出测试通过")
    print(f"   文件位置: {output_path}")


async def test_metadata_content():
    """测试元数据内容的完整性"""
    print("\n" + "=" * 60)
    print("测试元数据内容")
    print("=" * 60)
    
    # 导出搜索结果
    result = await export_search_results(
        query="Test metadata",
        num_results=5,
        engine="duckduckgo",
        output_file="test_metadata_content.json",
        include_metadata=True
    )
    
    data = json.loads(result)
    output_path = Path(data["output_file"])
    
    # 读取导出的文件
    with open(output_path, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
    
    metadata = exported_data["metadata"]
    
    # 验证元数据字段
    required_fields = [
        "query", "num_results", "requested_engine",
        "actual_engine", "search_duration_seconds",
        "timestamp", "total_results", "version"
    ]
    
    for field in required_fields:
        assert field in metadata, f"元数据缺少字段: {field}"
    
    print("元数据内容:")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    
    print(f"\n✅ 元数据内容测试通过")


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试搜索结果导出功能...\n")
    
    try:
        await test_export_basic()
        await test_export_without_metadata()
        await test_export_custom_path()
        await test_metadata_content()
        
        print("\n" + "=" * 60)
        print("✅ 所有导出测试通过！")
        print("=" * 60)
        
        # 清理测试文件
        print("\n清理测试文件...")
        output_dir = Path("output")
        if output_dir.exists():
            import shutil
            test_files = [
                "test_basic_export.json",
                "test_no_metadata_export.json",
                "test_metadata_content.json",
                "custom"  # 目录
            ]
            for item in test_files:
                path = output_dir / item
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    print(f"   删除: {path}")
        
        print("✅ 清理完成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
