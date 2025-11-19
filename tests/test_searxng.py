#!/usr/bin/env python3
"""
SearXNG 搜索引擎测试脚本

测试 SearXNG 搜索功能是否正常工作。
建议使用 `docker compose -f docker/docker-compose.yml up -d searxng`
启动本地实例（已包含 format=json + GET 配置）。
"""

import asyncio
import json
import os
import sys

# 添加项目根目录到路径, 便于单独运行脚本
try:
    from src.search import SearchManager
except ImportError:  # pragma: no cover - fallback when executed directly
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.search import SearchManager


async def test_searxng_search():
    """测试 SearXNG 搜索"""
    print("=" * 60)
    print("SearXNG 搜索引擎测试")
    print("=" * 60)
    print()
    
    # 检查 config.json 是否存在
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'config.json'
    )
    
    if not os.path.exists(config_path):
        print("⚠️  警告: config.json 不存在")
        print("📝 创建默认配置以使用本地 SearXNG...")
        
        # 创建默认配置
        default_config = {
            "searxng": {
                "base_url": "http://localhost:28981",
                "language": "zh-CN"
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print("✅ 已创建 config.json")
        print()
    else:
        # 读取并显示配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'searxng' in config:
            print("✅ SearXNG 配置已找到:")
            print(f"   Base URL: {config['searxng'].get('base_url')}")
            print(f"   Language: {config['searxng'].get('language')}")
        else:
            print("⚠️  警告: config.json 中未找到 SearXNG 配置")
            print("📝 请参考 examples/config.example.json 添加配置")
            return
        print()
    
    # 初始化搜索管理器
    print("🔧 初始化搜索管理器...")
    search_manager = SearchManager()
    
    # 显示可用的搜索引擎
    print(f"✅ 搜索引擎已加载: {[type(e).__name__ for e in search_manager.engines]}")
    print()
    
    # 检查 SearXNG 是否可用
    searxng_available = any(
        'SearXNG' in type(e).__name__ for e in search_manager.engines
    )
    
    if not searxng_available:
        print("❌ SearXNG 搜索引擎未加载")
        print("📝 请检查:")
        print("   1. config.json 中是否配置了 searxng")
        print("   2. SearXNG 是否正在运行")
        print("   3. base_url 是否正确")
        return
    
    print("=" * 60)
    print("测试 1: 使用 SearXNG 搜索 'Python教程'")
    print("=" * 60)
    
    try:
        results = await search_manager.search(
            query="Python教程",
            num_results=5,
            engine="searxng"
        )
        
        if results:
            print(f"✅ 搜索成功！找到 {len(results)} 个结果\n")
            
            for i, result in enumerate(results, 1):
                print(f"结果 {i}:")
                print(f"  标题: {result['title']}")
                print(f"  链接: {result['link']}")
                print(f"  摘要: {result['snippet'][:100]}...")
                print(f"  来源: {result['source']}")
                print()
        else:
            print("⚠️  搜索成功但没有返回结果")
            print("这可能是因为:")
            print("  1. SearXNG 实例未正确配置")
            print("  2. 网络连接问题")
            print("  3. 搜索查询没有匹配结果")
    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")
        print()
        print("故障排除:")
        print("  1. 确保 SearXNG 正在运行:")
        print("     docker ps | grep searxng")
        print("  2. 启动 SearXNG (推荐使用仓库内 docker-compose):")
        print("     docker compose -f docker/docker-compose.yml up -d searxng")
        print("     # 或手动运行镜像, 但务必挂载 docker/searxng/settings.yml 以允许 format=json")
        print("  3. 测试 SearXNG API:")
        print("     curl http://localhost:28981/search?q=test&format=json")
        return
    
    print("=" * 60)
    print("测试 2: 使用 SearXNG 搜索英文查询 'machine learning'")
    print("=" * 60)
    
    try:
        results = await search_manager.search(
            query="machine learning",
            num_results=3,
            engine="searxng"
        )
        
        if results:
            print(f"✅ 搜索成功！找到 {len(results)} 个结果\n")
            
            for i, result in enumerate(results, 1):
                print(f"结果 {i}:")
                print(f"  标题: {result['title']}")
                print(f"  链接: {result['link']}")
                print(f"  来源: {result['source']}")
                print()
        else:
            print("⚠️  没有返回结果")
    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")
    
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)
    print()
    print("💡 提示:")
    print("  - SearXNG 是一个元搜索引擎，聚合多个搜索引擎结果")
    print("  - 完全免费，无限制使用")
    print("  - 注重隐私保护")
    print("  - 可以自建部署，也可以使用公共实例")
    print()
    print("📚 相关文档:")
    print("  - docs/FREE_SEARCH_ENGINES.md - 搜索引擎汇总")
    print("  - examples/CONFIG.md - 配置说明")


if __name__ == "__main__":
    asyncio.run(test_searxng_search())
