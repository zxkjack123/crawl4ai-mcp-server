# 使用 Docker 暴露 Crawl4AI HTTP 服务

本指南说明如何使用本仓库自带的 Docker Compose 栈,将 Crawl4AI 的搜索 / 爬取能力以 HTTP API 的形式提供给其他服务调用。

## 1. 架构总览

```
┌────────────┐     28981/tcp      ┌──────────────┐
│  SearXNG   │◀──────────────────▶│  crawl4ai    │
│  (searxng) │                    │  HTTP Bridge │
└────────────┘                    └──────────────┘
       ▲                                 │
       │                                 │ 18080/tcp
       └─────────────────────────────────┘
                                    ↓
                         3rd-party services / clients
```

- **`searxng`**: 本地 SearXNG 元搜索引擎实例,默认映射到宿主机 `http://localhost:28981`。
- **`crawl4ai-http`**: FastAPI HTTP Bridge,依赖 `src/rest_server.py`,对外暴露 `/health`、`/search`、`/read_url` 等端点,默认映射到宿主机 `http://localhost:18080`。
- **第三方服务**: 可以在同一主机、内网或通过反向代理访问 `http://{host}:18080` 来复用 Crawl4AI 的搜索 / 爬取能力。

## 2. 准备工作

1. **安装依赖**
   - Docker 20+ / Docker Desktop
   - Docker Compose v2 (或内置 Compose 插件)

2. **复制配置文件**
   ```bash
   cp .env.example .env
   cp examples/config.example.json config.json
   ```
   - `.env` 中填写各类 API Key / 代理地址(Brave、Google、HTTP_PROXY 等)。
   - `config.json` 用于覆盖搜索引擎、爬虫、代理等默认配置,会被挂载进容器。

3. **目录权限**
   - `logs/`、`cache/`、`reports/` 会被挂载到容器,确保宿主机有写权限。

## 3. 启动 Docker 服务

```bash
# 一键启动 SearXNG + HTTP Bridge
cd /path/to/crawl4ai-mcp-server
docker compose -f docker/docker-compose.yml up -d

# 查看状态
docker compose -f docker/docker-compose.yml ps
```

默认端口映射:

| 服务          | 容器端口 | 宿主机端口 | 说明                              |
| ------------- | -------- | ---------- | --------------------------------- |
| crawl4ai-http | 8080     | 18080      | 对外 HTTP API                     |
| searxng       | 8080     | 28981      | HTTP Bridge 内部使用,亦可外部调试 |

> 如需修改端口,可编辑 `docker/docker-compose.yml` 的 `ports` 映射,或在 `.env` 中注入 `HTTP_PORT` 等变量并在 compose 文件中引用。

## 4. 健康检查

第三方服务可以在接入前调用 `GET /health`:

```bash
curl http://localhost:18080/health | jq
```

返回示例:

```json
{
  "status": "healthy",
  "version": "0.5.10",
  "components": {
    "crawler": {"status": "initialized", "ready": true},
    "search": {
      "status": "ready",
      "engines_count": 4,
      "engines": ["BraveSearch", "GoogleSearch", "SearXNGSearch", "DuckDuckGoSearch"]
    }
  },
  "checks": {...},
  "metrics": {...}
}
```

- `GET /health` 会聚合 `health/readiness/metrics` 三类信息,适合用作容器探针或上游依赖检查。

## 5. 搜索 API (`POST /search`)

### 请求体

```json
{
  "query": "US NRC technical basis LLW classification report",
  "num_results": 5,
  "engine": "all"
}
```

字段说明:

| 字段          | 类型       | 默认   | 说明                                                           |
| ------------- | ---------- | ------ | -------------------------------------------------------------- |
| `query`       | str        | 必填   | 搜索关键词                                                     |
| `num_results` | int (1-50) | 10     | 期望返回条数,超过可由内部限速调节                              |
| `engine`      | str        | `auto` | `auto` / `brave` / `google` / `duckduckgo` / `searxng` / `all` |

### 响应示例

```json
{
  "results": [
    {
      "title": "Technical Basis for NRC LLW Classification",
      "link": "https://www.nrc.gov/...",
      "snippet": "This report summarizes...",
      "source": "searxng",
      "engine": "searxng",
      "rank": 1
    }
  ],
  "count": 1
}
```

- 当内部出现错误时,HTTP 状态码为 `400`,`detail` 字段包含错误信息(例如: `No search engines available`).

### 客户端示例

```bash
curl -X POST http://localhost:18080/search \
  -H "Content-Type: application/json" \
  -d '{"query":"python crawl4ai","num_results":5,"engine":"auto"}'
```

```python
import requests

payload = {
    "query": "python crawl4ai",
    "num_results": 5,
    "engine": "auto"
}
resp = requests.post("http://localhost:18080/search", json=payload, timeout=30)
resp.raise_for_status()
print(resp.json()["results"])
```

## 6. 爬取 API (`POST /read_url`)

### 请求体

```json
{
  "url": "https://example.com",
  "format": "markdown_with_citations"
}
```

- `format` 支持 `raw_markdown` / `markdown_with_citations` / `references_markdown` / `fit_markdown` / `fit_html` / `markdown`。

### 响应示例

```json
{
  "url": "https://example.com",
  "format": "markdown_with_citations",
  "content": "# Example Domain...",
  "error": null
}
```

- 若抓取失败,`error` 字段会包含详细原因,HTTP 状态码仍为 `400`。

## 7. 与其他服务集成的建议

1. **超时与重试**
   - 建议客户端超时设为 ≥ 30s,尤其是 `engine="all"` 或抓取大型页面时。
   - 使用幂等重试,但需注意 `read_url` 会实时抓取,不宜无限重试。

2. **并发限制**
   - 可在上游入口加速率限制(例如 Nginx `limit_req`),或通过 `.env` 中的 `ENABLE_RATE_LIMIT`/`ENABLE_CACHE` 控制桥接层的缓存与限流。

3. **认证 / 网络隔离**
   - 默认未启用鉴权,推荐在生产环境通过以下方式保护:
     - 仅在内网暴露 `18080`
     - 通过 Nginx / Traefik 添加 Basic Auth / JWT / API Key 校验
     - 使用云防火墙或安全组限制访问源

4. **日志与监控**
   - 容器日志位于 `logs/` 挂载目录,可配合 ELK/ Loki 收集。
   - `docker compose logs -f crawl4ai-http` 可实时观察入口调用情况。

5. **SearXNG 可选暴露**
   - 如果第三方服务也想直接使用 SearXNG,可以访问 `http://{host}:28981/search?q=test&format=json`。
   - 记得在 `.env` 或 `docker/searxng/settings.yml` 中配置 `outgoing.proxies` 以匹配宿主网络。

## 8. 常见问题 (FAQ)

| 问题                  | 解决方案                                                                                                                              |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `/search` 返回空数组  | 确认 `.env` 中的代理 / API Key 配置正确; 如在宿主机直接运行 MCP,需将 `SEARXNG_BASE_URL` 设置为 `http://localhost:28981`。             |
| `/read_url` 报 SSL 错 | 在 `config.json` 中为 `crawler.proxy` 配置可信代理,或在 `.env` 添加 `CRAWL4AI_ALLOW_PROXY_REWRITE=true` + `HOST_PROXY_GATEWAY` 参数。 |
| 端口冲突              | 修改 `docker/docker-compose.yml` 中的 `ports`,并同步更新上游调用地址。                                                                |

---

现在,任何运行在内网或同一宿主机的第三方服务,都可以直接向 `http://localhost:18080` 发送 JSON 请求,即可复用 Crawl4AI 的多引擎搜索与网页抓取能力。"},