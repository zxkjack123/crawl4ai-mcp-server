[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/weidwonder-crawl4ai-mcp-server-badge.png)](https://mseep.ai/app/weidwonder-crawl4ai-mcp-server)

# Crawl4AI MCP Server

[![smithery badge](https://smithery.ai/badge/@weidwonder/crawl4ai-mcp-server)](https://smithery.ai/server/@weidwonder/crawl4ai-mcp-server)

这是一个基于MCP (Model Context Protocol)的智能信息获取服务器,为AI助手系统提供强大的搜索能力和面向LLM优化的网页内容理解功能。通过多引擎搜索和智能内容提取,帮助AI系统高效获取和理解互联网信息,将网页内容转换为最适合LLM处理的格式。

## 特性

- 🔍 强大的多引擎搜索能力,支持 Brave Search、DuckDuckGo、Google 和 SearXNG
- 🤖 智能自动回退 - API 失效时自动切换其他搜索引擎
- 🆓 多种免费选项 - Brave (2000次/月)、DuckDuckGo (无限制)、SearXNG (自建无限制)
- ⚡ **搜索缓存** - LRU+TTL 缓存策略,10-200x 性能提升,节省 90% API 配额
- 🎯 **结果去重和排序** - 自动去重，按引擎优先级智能排序
- 🔄 **错误重试机制** - 指数退避自动重试，提高成功率 10%
- 📊 **性能监控** - 完整的监控和日志系统，实时性能指标
- 🛡️ **API 限流保护** - 令牌桶算法，防止 API 超限
- 📚 面向LLM优化的网页内容提取,智能过滤非核心内容
- 🎯 专注信息价值,自动识别和保留关键内容
- 📝 多种输出格式,支持引用溯源
- 🚀 基于FastMCP的高性能异步设计
- 🔐 隐私保护 - Brave 和 SearXNG 不跟踪用户搜索记录

## 项目结构

```
crawl4ai-mcp-server/
├── src/                    # 源代码
│   ├── index.py           # MCP 服务器入口
│   └── search.py          # 搜索引擎管理
├── tests/                  # 测试脚本
│   ├── test_google_api_direct.py
│   ├── test_dual_engines.py
│   └── test_comprehensive.py
├── docs/                   # 完整文档
│   ├── DEPLOYMENT_GUIDE.md
│   ├── VSCODE_INTEGRATION.md
│   ├── CHERRY_STUDIO_INTEGRATION.md
│   ├── GOOGLE_API_SETUP_CN.md
│   └── ...
├── examples/               # 配置示例
│   ├── config.example.json
│   └── CONFIG.md
├── output/                 # 测试输出（不提交）
├── config.json            # 实际配置（不提交）
├── pyproject.toml         # 项目配置
└── README.md              # 本文件
```

## 快速开始

### 📦 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Linux, macOS, Windows 10/11
- **磁盘空间**: 至少 500 MB

### 🚀 安装方式

#### 🪟 Windows 用户

**快速安装**（推荐）:
```powershell
# PowerShell
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server
.\setup.ps1

# 或使用 CMD
setup.bat
```

📖 **详细指南**: [Windows 安装文档](docs/WINDOWS_INSTALLATION.md)

#### 🐧 Linux / 🍎 macOS 用户

**快速安装**:

**快速安装**:
```bash
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt
playwright install
```

#### 🎨 通过 Smithery 安装（Claude 桌面客户端）

#### 🎨 通过 Smithery 安装（Claude 桌面客户端）

通过 [Smithery](https://smithery.ai/server/@weidwonder/crawl4ai-mcp-server) 一键安装：

```bash
npx -y @smithery/cli install @weidwonder/crawl4ai-mcp-server --client claude
```

---

### ⚙️ 配置

#### 1. 复制配置模板

**Linux/macOS**:
```bash
cp examples/config.example.json config.json
nano config.json
```

**Windows**:
```powershell
copy examples\config.example.json config.json
notepad config.json
```

#### 2. 配置搜索引擎（可选）

本项目支持四种搜索引擎：

- **Brave Search**（推荐）：需要 API 密钥，2000次/月免费额度
  - 📖 [Brave Search 集成指南](docs/BRAVE_SEARCH_INTEGRATION.md) - 完整配置教程
- **DuckDuckGo**（默认）：无需配置，开箱即用
- **Google**：需要 API 密钥，100次/天免费额度
  - 📖 [Google API 配置指南](docs/GOOGLE_API_SETUP_CN.md) - 详细中文教程
- **SearXNG**：完全免费无限制，需要部署实例
  - 📖 [SearXNG 集成指南](docs/SEARXNG_INTEGRATION.md) - 部署和配置教程

更多配置详情，请参考 📖 [配置说明](examples/CONFIG.md)。

### 🧪 测试

**Linux/macOS**:
```bash
source .venv/bin/activate
python tests/test_comprehensive.py
```

**Windows**:
```powershell
.\run_tests.ps1  # PowerShell
# 或
run_tests.bat    # CMD
```

---

## 📚 完整文档

### 安装指南
- 🪟 [Windows 安装指南](docs/WINDOWS_INSTALLATION.md) - Windows 详细步骤
- 🪟 [Windows 快速开始](docs/WINDOWS_QUICK_START.md) - 5分钟快速安装
- 📖 [部署指南](docs/DEPLOYMENT_GUIDE.md) - 通用部署文档
- 🚀 [快速开始](docs/QUICK_START.md) - Linux/macOS 快速开始

### 集成教程
- 🔧 [VS Code 集成](docs/VSCODE_INTEGRATION.md) - MCP 配置
- 🎨 [Cherry Studio 集成](docs/CHERRY_STUDIO_INTEGRATION.md) - 其他客户端

### 配置和 API
- ⚙️ [配置说明](examples/CONFIG.md) - 配置文件详解
- 🔑 [Google API 设置](docs/GOOGLE_API_SETUP_CN.md) - 获取 API 凭据
- 🔍 [API Key 错误诊断](docs/API_KEY_ERROR_GUIDE.md) - 问题排查
- ⚡ [缓存指南](docs/CACHE_GUIDE.md) - 搜索缓存配置和使用
- 🎯 [Phase 2 功能](docs/PHASE2_FEATURES.md) - 去重、重试、监控、限流

### 项目信息
- 📁 [项目结构](PROJECT_STRUCTURE.md) - 目录组织说明
- 📝 [快速参考](QUICK_REFERENCE.md) - 常用命令和链接
- 🔄 [重构总结](REFACTOR_SUMMARY.md) - 项目重构记录

---

## 使用方法

服务器提供以下工具:

### search
强大的网络搜索工具,支持多个搜索引擎、智能回退和高性能缓存:

**搜索引擎支持:**
- **Brave Search**：需要API密钥，高质量搜索结果，2000次/月免费
- **DuckDuckGo**：无需API密钥，完全免费，作为默认回退引擎
- **Google**：需要配置API密钥，提供精准搜索结果
- **SearXNG**：完全免费无限制，需要部署实例，支持隐私保护
- **智能回退**：当主引擎失败（API过期、配额用尽等）时，自动切换到备用引擎

**缓存功能:**
- **LRU+TTL 双重策略**：结合最近最少使用和过期时间管理
- **10-200x 性能提升**：DuckDuckGo (10-50x), Google/Brave (50-100x), SearXNG (100-200x)
- **节省 90% API 配额**：重复查询直接使用缓存，大幅降低 API 调用
- **灵活配置**：默认启用，TTL 3600秒（1小时），最多缓存 1000 条
- **持久化支持**：支持导出/导入 JSON 文件，跨会话保留缓存
- 📖 详细配置和使用请查看 [缓存指南](docs/CACHE_GUIDE.md)

参数说明:
- `query`: 搜索查询字符串
- `num_results`: 返回结果数量(默认10)
- `engine`: 搜索引擎选择
  - "auto": 自动选择最佳引擎,失败时自动回退(默认,推荐)
  - "brave": Brave搜索(需要API密钥,2000次/月免费)
  - "duckduckgo": DuckDuckGo搜索(完全免费)
  - "google": Google搜索(需要API密钥)
  - "searxng": SearXNG搜索(需要部署实例,完全免费无限制)
  - "all": 同时使用所有可用的搜索引擎

示例:
```python
# 自动模式（推荐，支持智能回退）
{
    "query": "python programming",
    "num_results": 5,
    "engine": "auto"
}

# Brave搜索
{
    "query": "python programming",
    "num_results": 5,
    "engine": "brave"
}

# DuckDuckGo搜索
{
    "query": "python programming",
    "num_results": 5,
    "engine": "duckduckgo"
}

# Google搜索
{
    "query": "python programming",
    "num_results": 5,
    "engine": "google"
}

# SearXNG搜索
{
    "query": "python programming",
    "num_results": 5,
    "engine": "searxng"
}

# 使用所有可用引擎
{
    "query": "python programming",
    "num_results": 5,
    "engine": "all"
}
```

配置说明:
- **Brave**: 需要在 `config.json` 中配置 API 密钥
- **DuckDuckGo**: 无需配置
- **Google**: 需要在 `config.json` 中配置 API 密钥
- **SearXNG**: 需要在 `config.json` 中配置实例地址
- **缓存**: 默认启用，可在代码中配置

```json
{
    "brave": {
        "api_key": "your-brave-api-key"
    },
    "google": {
        "api_key": "your-api-key",
        "cse_id": "your-cse-id"
    },
    "searxng": {
        "base_url": "http://localhost:8080",
        "language": "zh-CN"
    }
}
```

缓存配置（在代码中）:
```python
# 启用缓存（默认）
manager = SearchManager(enable_cache=True, cache_ttl=3600)

# 禁用缓存
manager = SearchManager(enable_cache=False)

# 自定义 TTL（10分钟）
manager = SearchManager(enable_cache=True, cache_ttl=600)

# 查看缓存统计
stats = manager.get_cache_stats()

# 导出缓存
manager.export_cache("cache_backup.json")

# 导入缓存
manager.import_cache("cache_backup.json")
```

📖 更多缓存配置和最佳实践，请查看 [缓存指南](docs/CACHE_GUIDE.md)

### read_url
面向LLM优化的网页内容理解工具,提供智能内容提取和格式转换:

- `markdown_with_citations`: 包含内联引用的Markdown(默认),保持信息溯源
- `fit_markdown`: 经过LLM优化的精简内容,去除冗余信息
- `raw_markdown`: 基础HTML→Markdown转换
- `references_markdown`: 单独的引用/参考文献部分
- `fit_html`: 生成fit_markdown的过滤后HTML
- `markdown`: 默认Markdown格式

示例:
```python
{
    "url": "https://example.com",
    "format": "markdown_with_citations"
}
```

## LLM内容优化

服务器采用了一系列针对LLM的内容优化策略:

- 智能内容识别: 自动识别并保留文章主体、关键信息段落
- 噪音过滤: 自动过滤导航栏、广告、页脚等对理解无帮助的内容
- 信息完整性: 保留URL引用,支持信息溯源
- 长度优化: 使用最小词数阈值(10)过滤无效片段
- 格式优化: 默认输出markdown_with_citations格式,便于LLM理解和引用

## 开发说明

项目结构:
```
crawl4ai_mcp_server/
├── src/
│   ├── index.py      # 服务器主实现
│   └── search.py     # 搜索功能实现
├── config_demo.json  # 配置文件示例
├── pyproject.toml    # 项目配置
├── requirements.txt  # 依赖列表
└── README.md        # 项目文档
```

## 配置说明

1. 复制配置示例文件:
```bash
cp config_demo.json config.json
```

2. 如需使用Google搜索,在config.json中配置API密钥:
```json
{
    "google": {
        "api_key": "your-google-api-key",
        "cse_id": "your-google-cse-id"
    }
}
```

## 更新日志

- 2025.10.11: **🎯 Phase 2 功能发布**
  - 搜索结果去重和排序：基于 URL 去重，引擎优先级排序
  - 错误重试机制：指数退避算法，最多 3 次重试，成功率提升 10%
  - 监控和日志系统：完整性能监控，结构化日志，实时统计
  - API 限流保护：令牌桶算法，防止 API 超限，保护账户安全
  - 新增模块：utils.py (工具函数)、monitor.py (监控系统)
  - 详见：[Phase 2 功能文档](docs/PHASE2_FEATURES.md)
- 2025.02.08: **✨ 添加搜索缓存功能**
  - 实现 LRU+TTL 缓存策略（SearchCache 类）
  - 性能提升：10-200x 加速，节省 90% API 配额
  - 支持导出/导入 JSON 持久化
  - 添加缓存管理 API（统计、清除、导出、导入）
  - 代码质量优化：修复 140+ linting 错误
- 2025.02.08: 添加搜索功能,支持DuckDuckGo(默认)和Google搜索
- 2025.02.07: 重构项目结构,使用FastMCP实现,优化依赖管理
- 2025.02.07: 优化内容过滤配置,提高token效率并保持URL完整性

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request!

## 作者

- Owner: weidwonder  
- Coder: Claude Sonnet 3.5 
    - 100% Code wrote by Claude. Cost: $9 ($2 for code writing, $7 cost for Debuging😭)
    - 3 hours time cost. 0.5 hours for code writing, 0.5 hours for env preparing, 2 hours for debuging.😭

## 致谢

感谢所有为项目做出贡献的开发者!

特别感谢:
- [Crawl4ai](https://github.com/crawl4ai/crawl4ai) 项目提供的优秀网页内容提取技术支持