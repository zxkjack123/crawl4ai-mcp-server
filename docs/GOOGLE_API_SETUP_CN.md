# 获取 Google API Key 和 CSE ID 完整指南

## 📋 概述

本指南将帮助您获取 Google Custom Search API Key 和 Search Engine ID (CSE ID)，用于配置 Crawl4AI MCP Server 的 Google 搜索功能。

---

## 🎯 第一步：获取 Google API Key

### 1. 访问 Google Cloud Console

打开浏览器，访问：[https://console.cloud.google.com/](https://console.cloud.google.com/)

### 2. 创建或选择项目

- 如果还没有项目，点击顶部的项目下拉菜单
- 点击 **"新建项目"** (New Project)
- 输入项目名称（例如：`crawl4ai-search`）
- 点击 **"创建"**

### 3. 启用 Custom Search API

- 在左侧菜单中，找到 **"APIs & Services"** > **"启用的 API 和服务"**
- 点击顶部的 **"+ 启用 API 和服务"**
- 在搜索框中输入：`Custom Search API`
- 点击搜索结果中的 **"Custom Search API"**
- 点击 **"启用"** 按钮

### 4. 创建 API 凭据

- 返回 **"APIs & Services"** > **"凭据"** (Credentials)
- 点击顶部的 **"+ 创建凭据"**
- 选择 **"API 密钥"** (API Key)
- 系统会生成一个 API Key，类似：`AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **重要**：点击 **"复制"** 按钮保存这个 API Key

### 5. （可选）限制 API Key

为了安全起见，建议限制 API Key 的使用：

- 在 API Key 创建后，点击 **"编辑 API 密钥"**
- 在 **"API 限制"** 部分，选择 **"限制密钥"**
- 在列表中勾选 **"Custom Search API"**
- 点击 **"保存"**

---

## 🔍 第二步：获取 CSE ID (Custom Search Engine ID)

### 1. 访问 Programmable Search Engine

打开新标签页，访问：[https://programmablesearchengine.google.com/](https://programmablesearchengine.google.com/)

### 2. 创建新搜索引擎

- 点击 **"Get Started"** 或 **"Add"** 按钮
- 如果提示登录，使用与 Google Cloud 相同的账号登录

### 3. 配置搜索引擎

填写以下信息：

**搜索引擎名称：**
- 例如：`Crawl4AI Search Engine`

**要搜索的网站：**
- 选项 1：输入特定网站（例如：`wikipedia.org`）
- 选项 2：选择 **"搜索整个网络"** (Search the entire web)
  - **推荐选择此选项**，这样可以搜索所有网站

**语言：**
- 选择您需要的语言（例如：中文、英文）

**搜索引擎位置：**
- 根据需要选择地区

### 4. 创建搜索引擎

- 点击 **"创建"** (Create) 按钮

### 5. 获取 Search Engine ID

创建完成后：

- 在左侧菜单中，点击您刚创建的搜索引擎名称
- 点击 **"Setup"** 或 **"Overview"** 标签
- 在 **"Basic"** 部分，找到 **"搜索引擎 ID"** (Search engine ID)
- 这个 ID 类似：`a1b2c3d4e5f6g7h8i`
- **重要**：复制这个 ID

### 6. （可选）启用整个网络搜索

如果之前没有选择搜索整个网络：

- 在 **"Setup"** 页面
- 找到 **"搜索整个网络"** (Search the entire web) 选项
- 打开开关
- 点击 **"更新"** (Update)

---

## ⚙️ 第三步：配置 Crawl4AI MCP Server

### 1. 打开配置文件

在 Crawl4AI MCP Server 目录中，编辑 `config.json` 文件：

```bash
cd /home/gw/opt/crawl4ai-mcp-server
nano config.json
```

### 2. 添加您的凭据

将文件内容修改为：

```json
{
  "google": {
    "api_key": "AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "cse_id": "a1b2c3d4e5f6g7h8i"
  }
}
```

**注意**：将上面的示例值替换为您实际获取的 API Key 和 CSE ID。

### 3. 保存文件

- 按 `Ctrl + O` 保存
- 按 `Enter` 确认
- 按 `Ctrl + X` 退出

### 4. 重启 MCP Server

如果 MCP Server 正在运行，需要重启以加载新配置。

---

## ✅ 第四步：测试配置

### 测试 Google 搜索

创建测试脚本 `test_google_search.py`：

```python
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search import SearchManager

async def test():
    sm = SearchManager()
    results = await sm.search("Python programming", num_results=3, engine="google")
    
    print(f"找到 {len(results)} 个结果：")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['link']}")
        print()

asyncio.run(test())
```

运行测试：

```bash
source .venv/bin/activate
python test_google_search.py
```

如果配置正确，应该能看到 Google 搜索结果。

---

## 📊 配额和限制

### 免费配额

- **每天**: 100 次查询
- **每秒**: 10 次查询

### 超出配额

如果需要更多查询次数：

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 进入 **"APIs & Services"** > **"配额"**
3. 找到 **"Custom Search API"**
4. 请求增加配额或启用计费

### 计费

- 前 100 次查询/天：免费
- 超出部分：约 $5 / 1000 次查询

---

## ⚠️ 重要注意事项

### 安全性

1. **不要公开 API Key**
   - 不要将 `config.json` 提交到 Git
   - 不要在公开代码中包含 API Key
   - 添加 `config.json` 到 `.gitignore`

2. **限制 API Key 使用**
   - 在 Google Cloud Console 中设置 API 限制
   - 只允许访问 Custom Search API
   - 考虑添加 IP 地址限制

### 使用建议

1. **DuckDuckGo vs Google**
   - DuckDuckGo：无需 API Key，无限制，免费
   - Google：需要 API Key，有配额，但结果可能更精准

2. **何时使用 Google 搜索**
   - 需要特定的搜索排序
   - 需要更精确的结果
   - 在配额范围内使用

3. **默认使用 DuckDuckGo**
   - 对于大多数搜索任务已经足够
   - 节省 Google API 配额

---

## 🔗 相关链接

- [Google Cloud Console](https://console.cloud.google.com/)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [Custom Search API 文档](https://developers.google.com/custom-search/v1/overview)
- [API Key 管理](https://cloud.google.com/docs/authentication/api-keys)
- [配额管理](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas)

---

## 🆘 常见问题

### Q1: API Key 无法工作？

**检查清单：**
- ✅ API Key 已创建
- ✅ Custom Search API 已启用
- ✅ API Key 没有过度限制
- ✅ `config.json` 格式正确
- ✅ 已重启 MCP Server

### Q2: CSE ID 找不到？

**解决方法：**
1. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 点击您的搜索引擎
3. 在 **Setup** > **Basic** 部分查找
4. Search Engine ID 通常是一串字母数字混合的字符串

### Q3: 超过配额怎么办？

**选项：**
1. 等待配额在第二天重置
2. 在 Google Cloud Console 中启用计费
3. 使用 DuckDuckGo 搜索（无限制）

### Q4: 搜索结果质量不好？

**优化建议：**
1. 在 Programmable Search Engine 控制台中调整设置
2. 确保启用了 "搜索整个网络"
3. 调整语言和地区设置
4. 使用更具体的搜索关键词

---

## ✅ 完成！

现在您已经成功配置了 Google Custom Search API！

Crawl4AI MCP Server 现在可以同时使用：
- 🔷 **DuckDuckGo**：默认引擎，免费无限制
- 🔶 **Google**：备选引擎，更精准但有配额

您可以在搜索时指定使用哪个引擎：

```python
# 使用 DuckDuckGo（默认）
results = await search_manager.search("query", engine="duckduckgo")

# 使用 Google
results = await search_manager.search("query", engine="google")
```

祝您使用愉快！🎉
