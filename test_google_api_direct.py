#!/usr/bin/env python
"""
详细测试 Google 搜索 API
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_google_api():
    """直接测试 Google Custom Search API"""
    
    # 从 config.json 读取配置
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = config['google']['api_key']
    cse_id = config['google']['cse_id']
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    print("=" * 80)
    print("Google Custom Search API 直接测试")
    print("=" * 80)
    print(f"API Key: {api_key[:20]}...")
    print(f"CSE ID: {cse_id}")
    print()
    
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': 'Python programming',
        'num': 3
    }
    
    print("发送请求到 Google API...")
    print(f"URL: {base_url}")
    print(f"参数: {json.dumps(params, indent=2)}")
    print()
    
    # 使用 HTTP 代理
    import os
    proxies = None
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    if http_proxy and http_proxy.startswith('http'):
        proxies = {
            "http://": http_proxy,
            "https://": https_proxy or http_proxy
        }
        print(f"使用代理: {proxies}")
        print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0, proxies=proxies) as client:
            response = await client.get(base_url, params=params)
            
            print(f"响应状态码: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API 请求成功！")
                print()
                
                if 'items' in data:
                    print(f"找到 {len(data['items'])} 个结果：")
                    print()
                    for i, item in enumerate(data['items'], 1):
                        print(f"{i}. {item.get('title', 'No title')}")
                        print(f"   URL: {item.get('link', 'No link')}")
                        print(f"   摘要: {item.get('snippet', 'No snippet')[:100]}...")
                        print()
                else:
                    print("⚠️  响应中没有 'items' 字段")
                    print(f"响应内容: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ API 请求失败")
                print(f"响应内容: {response.text}")
                
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_google_api())
