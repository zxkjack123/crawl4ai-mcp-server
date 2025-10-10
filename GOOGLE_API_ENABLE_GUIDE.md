# ✅ API Key 验证成功！现在需要启用 API

## 🎉 好消息

您的 API Key 现在是**有效的**！测试结果从 `400 Bad Request` 变成了 `403 Permission Denied`，这意味着：

✅ API Key 格式正确  
✅ API Key 已通过身份验证  
❌ Custom Search API 尚未在您的项目中启用

---

## 🔧 立即启用 Custom Search API

### 方法 1：通过浏览器（推荐，最快）

1. **点击下面的链接** 直接访问启用页面：
   ```
   https://console.developers.google.com/apis/api/customsearch.googleapis.com/overview?project=111944390041
   ```

2. **点击 "启用" 按钮**
   - 页面会显示 "Custom Search API"
   - 点击蓝色的 **"启用"** 按钮

3. **等待几秒钟**
   - API 启用后，页面会显示 "API 已启用"
   - 可能需要等待 1-2 分钟让配置生效

### 方法 2：手动导航

如果上面的链接无法访问，请按以下步骤操作：

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)

2. 确保选择了正确的项目（项目编号：111944390041）

3. 在左侧菜单中，点击 **"API 和服务"** > **"库"**

4. 在搜索框中输入 `Custom Search API`

5. 点击 **"Custom Search API"** 进入详情页

6. 点击 **"启用"** 按钮

---

## 🧪 启用后测试

启用 API 后，请等待 1-2 分钟，然后运行测试：

```bash
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
python test_google_api_direct.py
```

如果看到类似以下输出，说明成功：

```
✅ API 请求成功！

找到 3 个结果：

1. Python.org
   URL: https://www.python.org/
   摘要: The official home of the Python Programming Language...

2. Learn Python - Free Interactive Python Tutorial
   URL: https://www.learnpython.org/
   摘要: Learn Python online: Python tutorials...
```

---

## 🚀 测试双引擎搜索

Custom Search API 启用后，可以测试 DuckDuckGo 和 Google 双引擎协同工作：

```bash
python test_dual_engines.py
```

预期输出：

```
=== 测试 1: DuckDuckGo 搜索 ===
✅ 搜索成功！
找到 3 个结果

=== 测试 2: Google 搜索 ===
✅ 搜索成功！
找到 3 个结果

=== 测试 3: 双引擎并行搜索 ===
✅ DuckDuckGo: 成功
✅ Google: 成功
总共 6 个结果
```

---

## 📊 API 配额信息

Google Custom Search API 的免费配额：

- **每天**: 100 次搜索请求
- **超过后**: 需要付费（$5/1000 次请求）

您可以在 [API 控制台](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas?project=111944390041) 查看使用情况。

---

## ⚠️ 常见问题

### Q: 启用后立即测试失败？

A: 请等待 1-2 分钟。Google Cloud 的配置更改需要时间传播到所有服务器。

### Q: 如何查看 API 使用情况？

A: 访问 [API 指标](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/metrics?project=111944390041)

### Q: 超过免费配额怎么办？

A: 系统会自动切换到 DuckDuckGo 搜索引擎（无限制）。或者您可以在 Google Cloud Console 启用计费。

### Q: 可以提高配额吗？

A: 免费配额是固定的（100/天）。如果需要更多，需要启用计费账号。

---

## 📝 当前配置状态

✅ **API Key**: `AIzaSyD7upQYiTOjxxQXYeGAXzMk-61p-2PlyE8`  
✅ **CSE ID**: `e7250f42e66574df7`  
✅ **配置文件**: `config.json` 已更新  
⏳ **API 状态**: 等待您启用 Custom Search API

---

## 🎯 下一步

1. **点击启用链接**: https://console.developers.google.com/apis/api/customsearch.googleapis.com/overview?project=111944390041

2. **点击"启用"按钮**

3. **等待 1-2 分钟**

4. **运行测试**:
   ```bash
   source .venv/bin/activate
   python test_google_api_direct.py
   ```

5. **享受双引擎搜索** 🎉

---

## 📞 需要帮助？

如果启用后仍有问题，请告诉我：
- 错误信息
- 测试输出
- 是否等待了足够的时间

我会继续帮您排查！
