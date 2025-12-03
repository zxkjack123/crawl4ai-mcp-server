[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/weidwonder-crawl4ai-mcp-server-badge.png)](https://mseep.ai/app/weidwonder-crawl4ai-mcp-server)

# Crawl4AI MCP Server

[![smithery badge](https://smithery.ai/badge/@weidwonder/crawl4ai-mcp-server)](https://smithery.ai/server/@weidwonder/crawl4ai-mcp-server)

这是一个基于MCP (Model Context Protocol)的智能信息获取服务器,为AI助手系统提供强大的搜索能力和面向LLM优化的网页内容理解功能。通过多引擎搜索和智能内容提取,帮助AI系统高效获取和理解互联网信息,将网页内容转换为最适合LLM处理的格式。

## 特性

### 🚀 v0.5.10 新亮点
- 🌐 **HTTP Bridge 定稿** *(承接 v0.5.9)* - `src/rest_server.py` + `tests/test_rest_server*.py` 组成完整的 REST 层，第三方服务可直接通过 `/health`、`/search`、`/read_url` 复用搜索/爬取能力。
- 🐳 **Compose + Makefile 一键联动** *(承接 v0.5.9)* - `make docker-up` 会自动启动 HTTP Bridge 与 SearXNG，映射到宿主机 `18080/28981`，并继承 `.env` 中的 API Key、代理和缓存配置。
- 🔁 **SearXNG 独立端口 28981** *(承接 v0.5.9)* - Docker Compose、`.env.example`、`examples/CONFIG.md`、`docs/SEARXNG_INTEGRATION.md` 等文件全部切换到 28981，避免与常见服务 (Dify 等) 冲突，并在文档中补充了排查步骤。
- 🧩 **VS Code + MCP 配置修正** - `docs/VSCODE_INTEGRATION.md` 新增示例: 宿主机直连 MCP 服务器时使用 `SERVER_MODE=mcp` 与 `SEARXNG_BASE_URL=http://localhost:28981`，而 Docker 内 HTTP Bridge 继续使用 `http://searxng:8080`，保证 `@crawl4ai search` 与 HTTP `/search` 返回一致结果。
- 🧪 **并发搜索测试更友好** - 当 CI / 本地环境完全离线或未启动 SearXNG 时, 并发搜索集成测试会自动跳过, 避免把网络/环境问题误判为功能回归; 在至少一个引擎可用时仍严格校验行为。

### 🎉 v0.5.0 新功能
- 💾 **缓存持久化** - SQLite持久化存储，双层缓存架构(内存+数据库)，75%性能提升
- 🔄 **跨会话缓存** - 重启后数据不丢失，支持导出/导入/预热
- 🧪 **单元测试覆盖** - 81%代码覆盖率，21个单元测试，100%通过率
- 📊 **缓存管理工具** - 统计、清理、导出、优化等5种MCP操作
- 🏥 **健康检查端点** - 服务状态、就绪检查、性能指标监控
- 📦 **JSON导出** - 搜索结果导出为JSON，包含完整元数据
- ⚡ **并发搜索优化** - asyncio并行查询，多引擎同时搜索

### 核心功能
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

> 💡 **无需在 config.json 中硬编码密钥**: 只需将 `BRAVE_API_KEY`、`GOOGLE_API_KEY`、`GOOGLE_CSE_ID` 等写入 `.env`，无论本地运行还是 Docker 容器都会自动读取这些环境变量。`make docker-up` 会自动加载根目录下的 `.env` 文件。

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
- 🌐 [Docker HTTP 服务接入](docs/HTTP_BRIDGE_USAGE.md) - 让第三方服务通过 Docker API 复用 Crawl4AI

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
        "base_url": "http://localhost:28981",
        "language": "zh-CN"
    }
}
```

    > 💡 推荐使用 `docker/searxng/settings.yml` + `docker/docker-compose.yml` 一键启动本地 SearXNG, HTTP Bridge 会通过 `http://searxng:8080` 自动访问该服务。若你仍在宿主机单独运行 SearXNG, 则继续在 `.env` 中设置 `SEARXNG_BASE_URL=http://host.docker.internal:28981`（Linux 需 `extra_hosts: host.docker.internal:host-gateway`）以确保容器可访问该实例。需要修改代理出口时，可直接编辑 `docker/searxng/settings.yml` 中的 `outgoing.proxies`。

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

## HTTP 服务桥接

如果希望在其他项目中通过 HTTP 而非 MCP 协议调用这些能力,可以启用内置的 FastAPI 网关 `src/rest_server.py`。它会在启动时复用同一套配置/缓存,因此无需额外改动即可被任意语言或框架调用。

> 💡 Docker 镜像默认设置 `SERVER_MODE=http` 并通过 `docker/entrypoint.sh` 自动运行 `uvicorn src.rest_server:app`。如需改回传统 MCP 运行模式,只需在 `.env` 或 compose 文件中设置 `SERVER_MODE=mcp`。

### 启动方式

先确保常规依赖已安装,然后运行:

```bash
uvicorn src.rest_server:app --host 0.0.0.0 --port 8000
```

默认会监听 `http://localhost:8000`, 你也可以调整主机/端口。服务启动后会预热搜索管理器以降低首个请求延迟。

### 可用端点

| 方法 | 路径        | 说明                   |
| ---- | ----------- | ---------------------- |
| GET  | `/health`   | 返回健康/就绪状态      |
| POST | `/search`   | 触发多引擎搜索         |
| POST | `/read_url` | 抓取网页并输出指定格式 |

所有端点的请求/响应结构与 MCP 工具保持一致,错误会以 `HTTP 400` 返回。

### 示例调用

```bash
# 触发一次搜索
curl -X POST http://localhost:8000/search \
    -H "Content-Type: application/json" \
    -d '{"query": "latest ai papers", "num_results": 5, "engine": "auto"}'

# 抓取网页内容
curl -X POST http://localhost:8000/read_url \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "format": "markdown_with_citations"}'
```

这样便可在任意支持 HTTP 的环境中复用 Crawl4AI 的搜索与内容提取能力,无需直接集成 MCP。

快速容器化体验:

```bash
make docker-build
make docker-up
make docker-health
```

上述命令会自动加载 `.env`、拉起内置 SearXNG + HTTP Bridge,运行完成后即可在 `http://localhost:18080` 访问 `/health`、`/search`、`/read_url`。

### 🐳 Docker 常驻服务

若需要长期对外暴露 HTTP 能力,推荐使用容器方式运行:

1. 准备环境变量 (API Key、代理、Clash 设置等)。复制示例文件并填写:
    ```bash
    cp .env.example .env
    nano .env  # BRAVE_API_KEY=xxx, GOOGLE_API_KEY=xxx, GOOGLE_CSE_ID=xxx
               # CRAWL4AI_HTTP_PROXY=http://host.docker.internal:7890
               # CRAWL4AI_HTTPS_PROXY=http://host.docker.internal:7890
               # CRAWL4AI_ALLOW_PROXY_REWRITE=true
               # HOST_PROXY_PORT_OVERRIDE=7890  (Clash 默认 7890/7891, 端口需在 1-65535)
    ```
    `make` 会自动把 `.env` 注入到 `docker compose`，这样镜像内就自带密钥，调用方无需再额外配置。
2. (可选) 如果还需要自定义其他搜索引擎或缓存策略，可以照旧挂载 `config.json`:
    ```bash
    cp examples/config.example.json config.json
    ```
    没有 `config.json` 也能运行，容器会直接使用 `.env` 中的密钥和代理。
3. 在项目根目录执行 Makefile 目标即可构建/运行(自动加载 `.env`):
    ```bash
    make docker-build
    make docker-up
    make docker-health
    ```
    默认会将容器内 `8080` 端口映射到宿主机 `18080`，可在 `docker/docker-compose.yml` 的 `ports` 中调整。
4. 需要停止或重新部署时:
    ```bash
    make docker-down
    make docker-restart  # 等同于 down + up
    ```

> ⚠️ `ERR_PROXY_CONNECTION_FAILED`：容器内的 127.0.0.1 指向自身而不是宿主机。若代理(如 Clash)已开启 LAN 并监听 `0.0.0.0:7890`，推荐直接把 `.env` 中的 `CRAWL4AI_HTTP_PROXY/HTTPS_PROXY` 设为 `http://host.docker.internal:7890`。若仍绑定在宿主机 `127.0.0.1`, 同时设置 `CRAWL4AI_ALLOW_PROXY_REWRITE=true`、`HOST_PROXY_PORT_OVERRIDE=7890`(或你的真实端口, 必须在 1-65535)，容器会自动把所有 `http://127.0.0.1:*` 重写为 `host.docker.internal:<端口>`。

快速连通性自检:

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec crawl4ai-http \
    curl -x http://host.docker.internal:7890 -I https://www.google.com
```

看到 `HTTP/2 200` 即表示容器已经可以通过 Clash 出网。

容器默认使用 `SERVER_MODE=http` 运行 FastAPI, 并通过 `HTTP_PORT` 控制端口(默认 8080)。若需要在容器中运行传统 MCP 服务,可启动时设置 `SERVER_MODE=mcp` 即可。

### 🤝 在其他程序中调用 Docker 服务

当容器启动并健康 (见上方 `curl` 检查) 后, 任意支持 HTTP 的语言/框架都可以通过以下端点复用搜索与网页提取能力:

| 方法 | 路径        | 描述                           |
| ---- | ----------- | ------------------------------ |
| GET  | `/health`   | 服务状态+指标,可用于探活/监控  |
| POST | `/search`   | 执行多引擎搜索,结构同 MCP 工具 |
| POST | `/read_url` | 抓取网页并输出指定格式         |

所有请求/返回都使用 JSON,字段与 MCP 工具完全一致。示例:

```bash
# 发起搜索
curl -X POST http://localhost:18080/search \
    -H "Content-Type: application/json" \
    -d '{"query":"latest ai papers","num_results":5,"engine":"auto"}'

# 抓取网页内容
curl -X POST http://localhost:18080/read_url \
    -H "Content-Type: application/json" \
    -d '{"url":"https://example.com","format":"markdown_with_citations"}'
```

主机语言示例:

```python
import requests

BASE = "http://localhost:18080"
payload = {"query": "rust memory model", "num_results": 3, "engine": "auto"}
resp = requests.post(f"{BASE}/search", json=payload, timeout=30)
resp.raise_for_status()
print(resp.json())
```

```javascript
const fetch = require("node-fetch");

async function run() {
    const res = await fetch("http://localhost:18080/read_url", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url: "https://example.com", format: "fit_markdown"})
    });
    if (!res.ok) throw new Error(await res.text());
    console.log(await res.json());
}

run();
```

接入提醒:

- **同配置/缓存**: Compose 会把宿主机 `config.json`、缓存与日志目录挂载进容器,因此 API Key、缓存策略等与 MCP 模式一致。
- **超时与重试**: 远程搜索可能耗时数秒,建议在客户端设置合适的超时和重试策略。
- **健康探测**: 在流量入口处定期探测 `/health`,可结合 `make docker-health` 做本地巡检。
- **安全/公开部署**: 需对外暴露时请配合反向代理(如 Nginx/Traefik)、VPN 或鉴权机制; 默认镜像不会自带认证。
- **宿主机代理**: 若 Clash 已开启 LAN, 直接把 `.env` 中的 `CRAWL4AI_HTTP_PROXY/HTTPS_PROXY` 指向 `http://host.docker.internal:<端口>` 即可; 若仍绑定 `127.0.0.1`, 结合 `CRAWL4AI_ALLOW_PROXY_REWRITE=true` + `HOST_PROXY_PORT_OVERRIDE=<端口>` 让容器自动重写。

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
├── examples/config.example.json  # 配置文件示例
├── pyproject.toml    # 项目配置
├── requirements.txt  # 依赖列表
└── README.md        # 项目文档
```

## 配置说明

1. 复制配置示例文件:
```bash
cp examples/config.example.json config.json
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

📋 **查看完整更新日志**: [CHANGELOG.md](CHANGELOG.md)

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