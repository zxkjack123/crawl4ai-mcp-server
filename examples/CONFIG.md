# 配置文件说明# 配置文件说明



## 如何配置## 如何配置



1. **复制示例配置**1. **复制示例配置**

   ```bash   ```bash

   cp examples/config.example.json config.json   cp examples/config.example.json config.json

   ```   ```



2. **编辑配置文件**2. **编辑配置文件**

   ```bash   ```bash

   nano config.json   nano config.json

   # 或使用您喜欢的编辑器   # 或使用您喜欢的编辑器

   ```   ```



3. **填入您的配置**3. **填入您的 API 凭据**



---### Google Custom Search API 配置



## 支持的搜索引擎```json

{

### 1. DuckDuckGo (默认)  "google": {

✅ **完全免费，无需配置**    "api_key": "YOUR_GOOGLE_API_KEY_HERE",

    "cse_id": "YOUR_CUSTOM_SEARCH_ENGINE_ID_HERE"

DuckDuckGo 搜索引擎默认启用，无需任何配置即可使用。  }

}

---```



### 2. Google Custom Search API#### 参数说明



```json- **api_key**: Google API 密钥

{  - 格式: `AIzaSy...` (以 AIzaSy 开头)

  "google": {  - 获取方式: 参见 `docs/GOOGLE_API_SETUP_CN.md`

    "api_key": "YOUR_GOOGLE_API_KEY_HERE",  

    "cse_id": "YOUR_CUSTOM_SEARCH_ENGINE_ID_HERE"- **cse_id**: 自定义搜索引擎 ID

  }  - 格式: 类似 `e7250f42e66574df7`

}  - 获取方式: https://programmablesearchengine.google.com/

```

## 安全提示

#### 参数说明

⚠️ **重要**: 

- **api_key**: Google API 密钥- `config.json` 已添加到 `.gitignore`，不会被提交到 Git

  - 格式: `AIzaSy...` (以 AIzaSy 开头)- 请勿将包含真实 API Key 的配置文件分享给他人

  - 获取方式: 参见 `docs/GOOGLE_API_SETUP_CN.md`- 定期检查 GitHub 确保没有意外提交隐私信息

  - 免费额度: 100 次查询/天

  ## 获取 API 凭据

- **cse_id**: 自定义搜索引擎 ID

  - 格式: 类似 `e7250f42e66574df7`### Google API Key

  - 获取方式: https://programmablesearchengine.google.com/

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)

#### 获取 Google API Key2. 创建或选择项目

3. 启用 Custom Search API

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)4. 创建 API 密钥（不是 OAuth 客户端密钥！）

2. 创建或选择项目

3. 启用 Custom Search API详细步骤请参考：

4. 创建 API 密钥（不是 OAuth 客户端密钥！）- `docs/GOOGLE_API_SETUP_CN.md` - 中文详细指南

- `docs/GOOGLE_API_ENABLE_GUIDE.md` - API 启用指南

详细步骤请参考：- `docs/API_KEY_ERROR_GUIDE.md` - 常见错误解决

- `docs/GOOGLE_API_SETUP_CN.md` - 中文详细指南

- `docs/GOOGLE_API_ENABLE_GUIDE.md` - API 启用指南### 自定义搜索引擎 ID

- `docs/API_KEY_ERROR_GUIDE.md` - 常见错误解决

1. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)

#### 获取自定义搜索引擎 ID2. 创建新的搜索引擎

3. 在"概览"页面找到搜索引擎 ID

1. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)

2. 创建新的搜索引擎## 验证配置

3. 在"概览"页面找到搜索引擎 ID

配置完成后，运行测试脚本验证：

---

```bash

### 3. SearXNG (推荐自建)# 激活虚拟环境

source .venv/bin/activate

```json

{# 测试 Google API

  "searxng": {python tests/test_google_api_direct.py

    "base_url": "http://localhost:8080",

    "language": "zh-CN"# 测试双引擎

  }python tests/test_dual_engines.py

}```

```

## 故障排除

#### 参数说明

如果遇到问题，请查看：

- **base_url**: SearXNG 实例的地址- `docs/API_KEY_ERROR_GUIDE.md` - API Key 错误诊断

  - 本地部署: `http://localhost:8080`- `docs/GOOGLE_API_ENABLE_GUIDE.md` - API 启用问题

  - 远程实例: `https://searx.example.com`- `docs/TEST_RESULTS.md` - 测试结果参考

  - 公共实例: 参见 https://searx.space/

  ## 配置文件位置

- **language**: 搜索语言

  - 中文: `zh-CN` (默认)- ✅ **实际配置**: `config.json` (不提交到 Git)

  - 英文: `en-US`- 📝 **示例配置**: `examples/config.example.json` (提交到 Git)

  - 其他: `ja-JP`, `ko-KR` 等- 📖 **配置说明**: `examples/CONFIG.md` (本文件)


#### 快速部署 SearXNG

**方式 1: Docker 一键部署**
```bash
# 启动 SearXNG 实例
docker run -d -p 8080:8080 --name searxng searxng/searxng

# 验证运行状态
curl http://localhost:8080/search?q=test&format=json
```

**方式 2: Docker Compose 部署**
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

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f searxng
```

#### 使用公共 SearXNG 实例

你也可以使用公共 SearXNG 实例，无需自己部署：

```json
{
  "searxng": {
    "base_url": "https://searx.be",
    "language": "zh-CN"
  }
}
```

公共实例列表: https://searx.space/

⚠️ **注意**: 公共实例可能有速率限制或不稳定，建议生产环境自建。

---

## 完整配置示例

```json
{
  "google": {
    "api_key": "AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz",
    "cse_id": "e7250f42e66574df7"
  },
  "searxng": {
    "base_url": "http://localhost:8080",
    "language": "zh-CN"
  }
}
```

---

## 使用搜索引擎

在 MCP 客户端中调用搜索工具时，可以指定使用的搜索引擎：

```python
# 使用 DuckDuckGo (默认)
search(query="Python教程", engine="duckduckgo")

# 使用 Google
search(query="Python教程", engine="google")

# 使用 SearXNG
search(query="Python教程", engine="searxng")

# 使用所有引擎
search(query="Python教程", engine="all")
```

---

## 安全提示

⚠️ **重要**: 
- `config.json` 已添加到 `.gitignore`，不会被提交到 Git
- 请勿将包含真实 API Key 的配置文件分享给他人
- 定期检查 GitHub 确保没有意外提交隐私信息
- SearXNG 本地实例默认监听 `localhost`，如需外网访问请配置防火墙

---

## 验证配置

配置完成后，运行测试脚本验证：

```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 测试 Google API
python tests/test_google_api_direct.py

# 测试双引擎
python tests/test_dual_engines.py

# 测试 SearXNG
python tests/test_searxng.py
```

---

## 故障排除

### Google API 问题
- `docs/API_KEY_ERROR_GUIDE.md` - API Key 错误诊断
- `docs/GOOGLE_API_ENABLE_GUIDE.md` - API 启用问题
- `docs/TEST_RESULTS.md` - 测试结果参考

### SearXNG 问题

**问题**: 连接失败 `Connection refused`
- **原因**: SearXNG 未运行
- **解决**: `docker run -d -p 8080:8080 searxng/searxng`

**问题**: 搜索结果为空
- **原因**: 语言设置不匹配
- **解决**: 检查 `language` 配置是否正确

**问题**: 搜索速度慢
- **原因**: 公共实例负载高
- **解决**: 自建本地实例或更换实例

---

## 搜索引擎对比

| 引擎           | 免费额度         | 配置难度       | 搜索质量 | 推荐场景          |
| -------------- | ---------------- | -------------- | -------- | ----------------- |
| **DuckDuckGo** | 无限(有速率限制) | ⭐ 无需配置     | ⭐⭐⭐      | 日常使用          |
| **Google**     | 100次/天         | ⭐⭐ 需要API Key | ⭐⭐⭐⭐⭐    | 精确搜索          |
| **SearXNG**    | 无限             | ⭐⭐⭐ 需要部署   | ⭐⭐⭐⭐     | 高频使用/隐私保护 |

---

## 推荐配置策略

### 个人使用
```json
{
  "searxng": {
    "base_url": "http://localhost:8080",
    "language": "zh-CN"
  }
}
```
+ DuckDuckGo (默认) 作为备份

### 团队使用
```json
{
  "google": {
    "api_key": "...",
    "cse_id": "..."
  },
  "searxng": {
    "base_url": "http://your-server:8080",
    "language": "zh-CN"
  }
}
```
+ 多引擎备份策略

### 生产环境
- 自建 SearXNG 集群
- Google API 作为备份
- 配置监控和自动切换

---

## 配置文件位置

- ✅ **实际配置**: `config.json` (不提交到 Git)
- 📝 **示例配置**: `examples/config.example.json` (提交到 Git)
- 📖 **配置说明**: `examples/CONFIG.md` (本文件)
- 🔍 **搜索引擎汇总**: `docs/FREE_SEARCH_ENGINES.md`

---

## 相关文档

- [FREE_SEARCH_ENGINES.md](../docs/FREE_SEARCH_ENGINES.md) - 免费搜索引擎 API 汇总
- [GOOGLE_API_SETUP_CN.md](../docs/GOOGLE_API_SETUP_CN.md) - Google API 设置指南
- [VSCODE_INTEGRATION.md](../docs/VSCODE_INTEGRATION.md) - VS Code 集成说明
- [QUICK_START.md](../docs/QUICK_START.md) - 快速开始指南
