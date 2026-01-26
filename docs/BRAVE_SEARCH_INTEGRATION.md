# Brave Search 集成指南

## 📖 目录

- [简介](#简介)
- [快速开始](#快速开始)
- [获取 API 密钥](#获取-api-密钥)
- [配置方法](#配置方法)
- [自动回退机制](#自动回退机制)
- [使用示例](#使用示例)
- [API 限制](#api-限制)
- [常见问题](#常见问题)

## 简介

Brave Search API 是由 Brave 浏览器提供的独立搜索 API，具有以下优势：

- **🆓 免费额度**: 每月 2,000 次免费查询
- **🔐 隐私保护**: 不跟踪用户，保护隐私
- **🌍 全球覆盖**: 基于 Brave 自己的搜索索引
- **⚡ 高性能**: 快速响应，低延迟
- **🎯 高质量**: 搜索结果质量优秀

## 快速开始

### 1. 获取 API 密钥

访问 [Brave Search API](https://brave.com/search/api/) 注册并获取免费 API 密钥。

### 2. 配置 API 密钥

编辑 `config.json` 文件：

```json
{
    "brave": {
        "api_key": "YOUR_BRAVE_API_KEY"
    }
}
```

### 3. 开始使用

使用 Brave Search 进行搜索：

```python
# 使用 Brave Search
results = await search_manager.search("Python programming", engine="brave")

# 使用自动模式（推荐，支持回退）
results = await search_manager.search("Python programming", engine="auto")
```

## 获取 API 密钥

### 注册步骤

1. **访问官网**: 打开 https://brave.com/search/api/
2. **创建账户**: 点击 "Sign Up" 注册账户
3. **选择计划**: 选择 Free 计划（每月 2,000 次免费查询）
4. **获取密钥**: 在控制台中获取 API 密钥

### 免费计划详情

- **每月配额**: 2,000 次查询
- **速率限制**: 1 次/秒
- **功能完整**: 支持所有 API 功能
- **无需信用卡**: 注册时不需要信用卡

## 配置方法

### 完整配置示例

`config.json`:

```json
{
    "brave": {
        "api_key": "YOUR_BRAVE_API_KEY"
    },
    "google": {
        "api_key": "YOUR_GOOGLE_API_KEY",
        "cse_id": "YOUR_CSE_ID"
    },
    "searxng": {
        "base_url": "http://localhost:28981",
        "language": "zh-CN"
    }
}
```

### 配置优先级

当配置多个搜索引擎时，系统会按以下优先级初始化：

1. **Brave Search** - 优先级最高（如果配置）
2. **Google Search** - 次优先级（如果配置）
3. **SearXNG** - 第三优先级（如果配置）
4. **DuckDuckGo** - 始终作为默认回退引擎

## 自动回退机制

### 回退工作原理

本项目实现了智能回退机制，确保搜索服务的高可用性：

#### 1. Auto 模式（推荐）

```python
# 自动选择最佳引擎，失败时自动回退
results = await search_manager.search(query, engine="auto")
```

**工作流程**：
- 优先使用配置的引擎（Brave → Google → SearXNG）
- 如果主引擎失败（API 过期、配额用尽等），自动切换到回退引擎
- 回退顺序：DuckDuckGo → Google → SearXNG
- 获得足够结果后立即返回，无需尝试所有引擎

#### 2. 指定引擎模式

```python
# 指定使用 Brave Search
results = await search_manager.search(query, engine="brave")
```

**工作流程**：
- 尝试使用指定的引擎
- 如果指定引擎不可用或失败，自动回退到 DuckDuckGo

#### 3. 回退触发条件

系统在以下情况下会触发自动回退：

- ✗ API 密钥无效或过期（401 错误）
- ✗ API 配额用尽（429 错误）
- ✗ 网络连接失败
- ✗ 搜索引擎返回空结果
- ✗ 未配置指定的搜索引擎

### 回退引擎列表

| 引擎       | 用途         | 特点               |
| ---------- | ------------ | ------------------ |
| DuckDuckGo | 主要回退引擎 | 始终可用，无需配置 |
| Google     | 次要回退引擎 | 需要配置，100次/天 |
| SearXNG    | 第三回退引擎 | 需要部署，无限制   |

### 日志输出示例

```
INFO: Brave Search engine initialized
INFO: Starting search with query: Python, engine: auto, num_results: 10
INFO: Got 10 results from BraveSearch
INFO: Got enough results from BraveSearch, stopping
INFO: Returning 10 total results
```

失败回退示例：

```
ERROR: Brave Search API key is invalid or expired
WARNING: No results from BraveSearch, trying next engine
INFO: Trying fallback engines due to BraveSearch failure
INFO: Got 10 results from DuckDuckGoSearch
INFO: Returning 10 total results
```

## 使用示例

### Python 代码示例

```python
import asyncio
from search import SearchManager

async def main():
    manager = SearchManager()
    
    # 1. 自动模式（推荐）
    results = await manager.search(
        query="人工智能",
        num_results=10,
        engine="auto"
    )
    
    # 2. 指定使用 Brave
    results = await manager.search(
        query="machine learning",
        num_results=5,
        engine="brave"
    )
    
    # 3. 聚合所有引擎
    results = await manager.search(
        query="deep learning",
        num_results=20,
        engine="all"
    )
    
    for result in results:
        print(f"{result['title']}")
        print(f"URL: {result['link']}")
        print(f"来源: {result['source']}")
        print()

asyncio.run(main())
```

### MCP 工具调用

```json
{
    "query": "Python programming",
    "num_results": 10,
    "engine": "auto"
}
```

### 运行测试

```bash
# 测试 Brave Search
python tests/test_brave.py

# 查看测试输出
# ✓ 测试基本搜索
# ✓ 测试自动回退
# ✓ 测试所有引擎
# ✓ 测试无效引擎回退
```

## API 限制

### 免费计划限制

| 项目           | 限制       |
| -------------- | ---------- |
| 每月查询数     | 2,000 次   |
| 速率限制       | 1 次/秒    |
| 每次查询结果数 | 最多 20 个 |
| 功能限制       | 无         |

### 付费计划

如果需要更多查询配额，可以升级到付费计划：

- **Starter**: $5/月，10,000 次查询
- **Pro**: $50/月，100,000 次查询
- **Enterprise**: 定制，按需定价

## 常见问题

### 1. API 密钥无效

**错误信息**：
```
ERROR: Brave Search API key is invalid or expired
```

**解决方法**：
- 检查 `config.json` 中的 API 密钥是否正确
- 访问 Brave Search API 控制台确认密钥状态
- 重新生成新的 API 密钥

### 2. 配额用尽

**错误信息**：
```
ERROR: Brave Search API rate limit exceeded
```

**解决方法**：
- 等待下个月配额重置
- 升级到付费计划
- 使用 `engine="auto"` 模式自动回退到其他引擎

### 3. 搜索结果为空

**可能原因**：
- API 配额用尽
- API 密钥过期
- 网络连接问题
- 查询关键词问题

**解决方法**：
- 系统会自动回退到 DuckDuckGo
- 检查日志确认回退是否成功
- 如果所有引擎都失败，检查网络连接

### 4. 如何查看配额使用情况

访问 [Brave Search API 控制台](https://brave.com/search/api/dashboard/) 查看：

- 当月已使用查询数
- 剩余配额
- API 密钥状态
- 使用统计图表

### 5. 如何优化查询配额

**建议**：

1. **使用 Auto 模式**: 失败时自动回退，节省配额
2. **缓存结果**: 对相同查询缓存结果
3. **合理控制 num_results**: 不要请求过多结果
4. **组合使用多引擎**: 分散查询压力

```python
# 好的做法：使用 auto 模式
results = await manager.search(query, engine="auto")

# 不推荐：总是指定 brave，配额用尽后无法回退
results = await manager.search(query, engine="brave")
```

## 性能对比

### 搜索引擎对比

| 引擎       | 免费配额 | 响应速度 | 结果质量 | 隐私保护 |
| ---------- | -------- | -------- | -------- | -------- |
| Brave      | 2000/月  | ⚡⚡⚡⚡     | ⭐⭐⭐⭐     | ✓✓✓✓     |
| Google     | 100/天   | ⚡⚡⚡⚡⚡    | ⭐⭐⭐⭐⭐    | ✓✓       |
| DuckDuckGo | 无限制   | ⚡⚡⚡      | ⭐⭐⭐      | ✓✓✓✓✓    |
| SearXNG    | 无限制*  | ⚡⚡⚡      | ⭐⭐⭐⭐     | ✓✓✓✓✓    |

*需要自己部署

### 推荐使用策略

1. **日常使用**: `engine="auto"`（自动选择 + 回退）
2. **高质量需求**: `engine="google"` 或 `engine="brave"`
3. **大量查询**: `engine="searxng"` 或 `engine="duckduckgo"`
4. **隐私优先**: `engine="duckduckgo"` 或 `engine="searxng"`

## 相关资源

- 📖 [Brave Search API 官方文档](https://brave.com/search/api/docs/)
- 📖 [免费搜索引擎对比](FREE_SEARCH_ENGINES.md)
- 📖 [配置指南](../examples/CONFIG.md)
- 📖 [项目 README](../README.md)

## 技术支持

如果遇到问题：

1. 查看日志输出确认错误信息
2. 运行测试脚本 `python tests/test_brave.py`
3. 检查 [常见问题](#常见问题) 部分
4. 提交 Issue 到 GitHub 仓库

---

**最后更新**: 2025-10-11
**版本**: v0.2.0
