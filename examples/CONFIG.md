# 配置文件说明

## 如何配置

1. **复制示例配置**
   ```bash
   cp examples/config.example.json config.json
   ```

2. **编辑配置文件**
   ```bash
   nano config.json
   # 或使用您喜欢的编辑器
   ```

3. **填入您的 API 凭据**

### Google Custom Search API 配置

```json
{
  "google": {
    "api_key": "YOUR_GOOGLE_API_KEY_HERE",
    "cse_id": "YOUR_CUSTOM_SEARCH_ENGINE_ID_HERE"
  }
}
```

#### 参数说明

- **api_key**: Google API 密钥
  - 格式: `AIzaSy...` (以 AIzaSy 开头)
  - 获取方式: 参见 `docs/GOOGLE_API_SETUP_CN.md`
  
- **cse_id**: 自定义搜索引擎 ID
  - 格式: 类似 `e7250f42e66574df7`
  - 获取方式: https://programmablesearchengine.google.com/

## 安全提示

⚠️ **重要**: 
- `config.json` 已添加到 `.gitignore`，不会被提交到 Git
- 请勿将包含真实 API Key 的配置文件分享给他人
- 定期检查 GitHub 确保没有意外提交隐私信息

## 获取 API 凭据

### Google API Key

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建或选择项目
3. 启用 Custom Search API
4. 创建 API 密钥（不是 OAuth 客户端密钥！）

详细步骤请参考：
- `docs/GOOGLE_API_SETUP_CN.md` - 中文详细指南
- `docs/GOOGLE_API_ENABLE_GUIDE.md` - API 启用指南
- `docs/API_KEY_ERROR_GUIDE.md` - 常见错误解决

### 自定义搜索引擎 ID

1. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 创建新的搜索引擎
3. 在"概览"页面找到搜索引擎 ID

## 验证配置

配置完成后，运行测试脚本验证：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 测试 Google API
python tests/test_google_api_direct.py

# 测试双引擎
python tests/test_dual_engines.py
```

## 故障排除

如果遇到问题，请查看：
- `docs/API_KEY_ERROR_GUIDE.md` - API Key 错误诊断
- `docs/GOOGLE_API_ENABLE_GUIDE.md` - API 启用问题
- `docs/TEST_RESULTS.md` - 测试结果参考

## 配置文件位置

- ✅ **实际配置**: `config.json` (不提交到 Git)
- 📝 **示例配置**: `examples/config.example.json` (提交到 Git)
- 📖 **配置说明**: `examples/CONFIG.md` (本文件)
