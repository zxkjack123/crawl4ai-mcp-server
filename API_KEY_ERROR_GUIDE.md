# ⚠️ 重要：API Key 类型错误

## 问题说明

您提供的凭据：
```
API Key: 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
```

这个**不是** Google Custom Search API 所需的 API Key！

`GOCSPX-` 开头的是 **OAuth 客户端密钥**，不能用于 Custom Search API。

## 正确的 API Key 格式

Google Custom Search API Key 应该类似于：
```
AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

以 `AIzaSy` 开头，长度约 39 个字符。

---

## 如何获取正确的 API Key

### 方法 1：在 Google Cloud Console 中创建 API Key

1. **访问 Google Cloud Console**
   ```
   https://console.cloud.google.com/
   ```

2. **选择或创建项目**
   - 点击顶部的项目下拉菜单
   - 选择现有项目或点击"新建项目"

3. **启用 Custom Search API**
   - 在左侧菜单中，选择 **"API和服务"** > **"库"**
   - 搜索 `Custom Search API`
   - 点击进入，然后点击 **"启用"**

4. **创建 API 密钥**
   - 转到 **"API和服务"** > **"凭据"**
   - 点击顶部的 **"+ 创建凭据"**
   - 选择 **"API 密钥"** （注意：不是 OAuth 客户端 ID！）
   - 系统会生成一个新的 API 密钥，类似：`AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **重要**：立即复制这个密钥！

5. **（推荐）限制 API 密钥**
   - 点击刚创建的 API 密钥进行编辑
   - 在 **"API 限制"** 部分：
     - 选择 **"限制密钥"**
     - 勾选 **"Custom Search API"**
   - 点击 **"保存"**

### 方法 2：使用命令行工具

如果您安装了 Google Cloud SDK：

```bash
# 列出现有的 API 密钥
gcloud alpha services api-keys list

# 创建新的 API 密钥
gcloud alpha services api-keys create \
  --display-name="Crawl4AI Custom Search" \
  --api-target=service=customsearch.googleapis.com
```

---

## 您的 CSE ID 是正确的

您的 Search Engine ID 是正确的：
```
CSE ID: e7250f42e66574df7
```

这个 ID 来自 Programmable Search Engine 控制台，格式正确。

---

## 配置步骤

一旦您获得了正确的 API Key（以 `AIzaSy` 开头），请更新配置文件：

### 编辑 config.json

```bash
cd /home/gw/opt/crawl4ai-mcp-server
nano config.json
```

### 更新内容

```json
{
  "google": {
    "api_key": "AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "cse_id": "e7250f42e66574df7"
  }
}
```

**注意**：将 `AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxx` 替换为您新创建的 API Key。

---

## 测试配置

更新配置后，运行测试：

```bash
source .venv/bin/activate
python test_dual_engines.py
```

如果 API Key 正确，您应该看到 Google 搜索成功返回结果。

---

## 常见问题

### Q: 为什么我的 OAuth 客户端密钥不能用？

A: OAuth 客户端密钥（GOCSPX-...）用于需要用户授权的应用程序。Custom Search API 使用的是 API Key（AIzaSy...），这是一种更简单的认证方式，不需要用户交互。

### Q: 如何区分不同类型的凭据？

A: 
- **API Key**: `AIzaSy...` - 用于公开 API，无需用户授权
- **OAuth 客户端 ID**: `xxx.apps.googleusercontent.com` - 用于需要用户登录
- **OAuth 客户端密钥**: `GOCSPX-...` - 配合 OAuth 客户端 ID 使用
- **服务账号密钥**: JSON 文件 - 用于服务器到服务器的认证

### Q: 创建 API Key 后立即就能用吗？

A: 通常是的，但有时可能需要等待几分钟让配置生效。

### Q: API Key 安全吗？

A: API Key 应该保密。建议：
1. 不要将其提交到 Git
2. 在 Cloud Console 中设置 API 限制
3. 定期轮换密钥
4. 监控使用情况

---

## 下一步

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建正确的 API Key (AIzaSy...)
3. 更新 `config.json`
4. 运行测试验证配置

祝您配置成功！🎉

---

## 参考链接

- [Google Cloud Console](https://console.cloud.google.com/)
- [Custom Search API 文档](https://developers.google.com/custom-search/v1/overview)
- [API Key 管理](https://cloud.google.com/docs/authentication/api-keys)
- [创建 API Key 指南](https://support.google.com/googleapi/answer/6158862)
