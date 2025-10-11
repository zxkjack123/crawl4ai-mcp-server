# 免费/有免费额度的搜索引擎 API 汇总

本文档整理了除 DuckDuckGo 和 Google Custom Search 之外,其他可用的免费或有免费额度的搜索引擎 API,供 Crawl4AI MCP Server 集成参考。

---

## 📋 目录
- [完全免费的搜索引擎](#完全免费的搜索引擎)
- [有免费额度的搜索 API 服务](#有免费额度的搜索-api-服务)
- [开源自建方案](#开源自建方案)
- [集成建议](#集成建议)

---

## 🆓 完全免费的搜索引擎

### 1. **DuckDuckGo** (当前已集成)
- **状态**: ✅ 已集成
- **特点**: 完全免费,无需 API Key
- **限制**: 有速率限制,不适合大规模爬取
- **文档**: https://duckduckgo.com/api

### 2. **Brave Search API**
- **免费额度**: 2,000 次查询/月
- **特点**: 
  - 注重隐私
  - 独立索引(不依赖 Google/Bing)
  - 响应速度快
- **定价**: 
  - Free tier: 2,000 queries/月
  - Paid: $3/千次查询
- **文档**: https://brave.com/search/api/
- **Python 库**: `brave-search-python`

### 3. **Yandex Search API**
- **免费额度**: 10,000 次请求/天 (需申请)
- **特点**: 
  - 俄罗斯最大搜索引擎
  - 对俄语和东欧语言支持好
  - 提供 XML API
- **限制**: 需要企业账户
- **文档**: https://yandex.com/dev/xml/

### 4. **Baidu Search API**
- **免费额度**: 有免费试用额度
- **特点**: 
  - 中文搜索最优
  - 需要国内账号
  - API 调用相对稳定
- **文档**: https://ai.baidu.com/tech/websearch

---

## 💰 有免费额度的搜索 API 服务

### 1. **SerpApi**
- **免费额度**: 100 次搜索/月
- **特点**:
  - 支持多个搜索引擎 (Google, Bing, Yahoo, DuckDuckGo, Baidu, Yandex 等)
  - 结构化 JSON 数据
  - 自动处理 CAPTCHA
  - 地理位置精确定位
- **定价**:
  - Free: 100 searches/月
  - Developer: $75/月 (5,000 searches)
  - Production: $150/月 (15,000 searches)
- **文档**: https://serpapi.com/
- **Python 库**: `pip install serpapi`

```python
# SerpApi 示例代码
from serpapi import GoogleSearch

params = {
    "q": "query",
    "api_key": "your_api_key"
}
search = GoogleSearch(params)
results = search.get_dict()
```

### 2. **ScraperAPI**
- **免费额度**: 5,000 API 调用/月
- **特点**:
  - 通用爬虫 API (不限搜索引擎)
  - 自动处理代理和 CAPTCHA
  - 支持 JavaScript 渲染
- **定价**: $49/月起 (100K requests)
- **文档**: https://www.scraperapi.com/

### 3. **ValueSERP**
- **免费额度**: 100 次搜索/月
- **特点**:
  - 支持 Google, Bing, Baidu
  - 价格相对便宜
  - 响应速度快
- **定价**: $50/月起 (5,000 searches)
- **文档**: https://www.valueserp.com/

### 4. **Zenserp**
- **免费额度**: 50 次搜索/月
- **特点**:
  - 支持 Google 搜索
  - 提供地理位置定位
  - 结构化数据
- **定价**: $29.99/月起 (5,000 searches)
- **文档**: https://zenserp.com/

### 5. **SearchAPI**
- **免费额度**: 100 次搜索/月
- **特点**:
  - 支持 Google, Bing, Baidu, YouTube 等
  - 实时搜索结果
  - 简单易用
- **定价**: $49/月起 (2,500 searches)
- **文档**: https://www.searchapi.io/

### 6. **RapidAPI - Multiple Search APIs**
RapidAPI 平台上有多个免费/低价搜索 API:
- **Real-Time Google Search**: 100 requests/月免费
- **Bing Search**: 基础版免费
- **Web Search API**: 500 requests/月免费
- **文档**: https://rapidapi.com/

---

## 🛠️ 开源自建方案

### 1. **SearXNG**
- **特点**:
  - 完全开源,可自建
  - 元搜索引擎 (聚合多个搜索引擎)
  - 无跟踪,注重隐私
  - 提供 JSON API
- **部署**: Docker 一键部署
- **GitHub**: https://github.com/searxng/searxng
- **实例**: https://searx.space/ (公共实例列表)

```bash
# Docker 部署 SearXNG
docker run -d -p 8080:8080 searxng/searxng
```

### 2. **Whoogle Search**
- **特点**:
  - Google 搜索的隐私代理
  - 无广告,无跟踪
  - 可自建
  - 提供 API 接口
- **GitHub**: https://github.com/benbusby/whoogle-search

### 3. **search-engine-tool (GitHub)**
- **特点**:
  - Python 实现
  - 支持多个搜索引擎
  - 开源免费
- **GitHub**: https://github.com/freewu/search-engine-tool

### 4. **search-node-api (GitHub)**
- **特点**:
  - Node.js + Puppeteer
  - 代理 Bing 搜索
  - 提供免费搜索 API
- **GitHub**: https://github.com/RobbieXie/search-node-api

---

## 🎯 集成建议

### 推荐优先级

#### 1️⃣ 短期快速集成 (1-2天)
```
Brave Search API > SerpApi Free Tier > ValueSERP
```
- **理由**: 
  - Brave 有 2000 次/月免费额度
  - 官方 API,稳定可靠
  - 集成简单,代码示例丰富

#### 2️⃣ 中期自建方案 (1周)
```
SearXNG 自建 > Whoogle 自建
```
- **理由**:
  - 完全免费,无限制
  - 聚合多个搜索引擎
  - Docker 部署简单

#### 3️⃣ 长期生产方案
```
SerpApi (付费) > 自建 + 备用 API
```
- **理由**:
  - 商业支持,SLA 保证
  - 自动处理 CAPTCHA 和代理
  - 多搜索引擎支持

---

## 📊 对比表格

| 搜索引擎/服务 | 免费额度 | 优点 | 缺点 | 推荐度 |
|------------|---------|------|------|--------|
| **DuckDuckGo** | 无限(有速率限制) | 完全免费,隐私友好 | 速率限制严格 | ⭐⭐⭐⭐ |
| **Brave Search** | 2,000/月 | 独立索引,快速 | 月度限制 | ⭐⭐⭐⭐⭐ |
| **SerpApi** | 100/月 | 多引擎,结构化数据 | 免费额度少 | ⭐⭐⭐⭐ |
| **Yandex** | 10,000/天 | 高额度,俄语强 | 需企业账户 | ⭐⭐⭐ |
| **Baidu** | 有限试用 | 中文最佳 | 需国内账户 | ⭐⭐⭐ |
| **SearXNG** | 无限 | 完全免费,可自建 | 需自己维护 | ⭐⭐⭐⭐⭐ |
| **ValueSERP** | 100/月 | 价格便宜 | 免费额度少 | ⭐⭐⭐ |
| **SearchAPI** | 100/月 | 简单易用 | 功能基础 | ⭐⭐⭐ |

---

## 🚀 快速开始 - Brave Search API

### 1. 注册获取 API Key
访问: https://brave.com/search/api/

### 2. Python 集成示例
```python
import requests

def brave_search(query, api_key, count=10):
    """
    Brave Search API 调用示例
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key
    }
    params = {
        "q": query,
        "count": count,
        "search_lang": "zh",  # 中文搜索
        "country": "CN"       # 中国地区
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# 使用示例
results = brave_search("Python教程", "your_api_key")
for result in results.get("web", {}).get("results", []):
    print(f"标题: {result['title']}")
    print(f"链接: {result['url']}")
    print(f"摘要: {result['description']}")
    print("---")
```

### 3. 集成到 Crawl4AI MCP Server
```python
# src/search.py 新增 Brave Search 支持
class SearchManager:
    def __init__(self):
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
    
    def search_brave(self, query: str, num_results: int = 10) -> List[Dict]:
        """Brave Search API 搜索"""
        if not self.brave_api_key:
            raise ValueError("BRAVE_API_KEY not set")
        
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }
        params = {
            "q": query,
            "count": num_results
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        results = []
        for item in response.json().get("web", {}).get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("description")
            })
        return results
```

---

## 🔧 SearXNG 自建方案

### Docker Compose 部署
```yaml
# docker-compose.yml
version: '3.7'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped
```

### 一键部署
```bash
# 创建配置目录
mkdir -p searxng

# 启动 SearXNG
docker-compose up -d

# 访问 API
curl "http://localhost:8080/search?q=test&format=json"
```

### API 调用示例
```python
import requests

def searxng_search(query, base_url="http://localhost:8080"):
    """SearXNG 搜索"""
    url = f"{base_url}/search"
    params = {
        "q": query,
        "format": "json",
        "language": "zh-CN"
    }
    
    response = requests.get(url, params=params)
    results = response.json()
    
    return [{
        "title": r["title"],
        "url": r["url"],
        "snippet": r.get("content", "")
    } for r in results.get("results", [])]
```

---

## 📝 总结

### 最佳实践建议

1. **多引擎备份策略**
   ```
   Primary: Brave Search (2000/月)
   Backup 1: DuckDuckGo (已集成)
   Backup 2: Google CSE (100/天)
   Backup 3: SearXNG 自建 (无限)
   ```

2. **成本优化**
   - 优先使用免费额度
   - 超出后自动切换到备用引擎
   - 对于高频用户推荐自建 SearXNG

3. **用户体验**
   - 允许用户在配置中选择搜索引擎
   - 提供搜索引擎健康检查
   - 自动失败转移

4. **下一步行动**
   - [ ] 集成 Brave Search API
   - [ ] 部署 SearXNG 实例
   - [ ] 实现多引擎轮换策略
   - [ ] 添加搜索引擎性能监控

---

## 📚 参考资源

- [Brave Search API 文档](https://brave.com/search/api/)
- [SerpApi 文档](https://serpapi.com/search-api)
- [SearXNG GitHub](https://github.com/searxng/searxng)
- [免费 API 汇总](https://github.com/public-apis/public-apis#search)

---

**文档版本**: v1.0  
**更新日期**: 2025-10-11  
**作者**: Crawl4AI MCP Server Team
