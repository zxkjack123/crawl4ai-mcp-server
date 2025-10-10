# 🚀 快速参考

**Crawl4AI MCP Server** - 项目快速参考指南

---

## 📂 目录结构

```
crawl4ai-mcp-server/
├── src/          # 源代码
├── tests/        # 测试脚本
├── docs/         # 完整文档
├── examples/     # 配置示例
├── output/       # 测试输出（不提交）
└── config.json   # 实际配置（不提交）
```

---

## ⚡ 快速开始

### 1. 克隆并安装
```bash
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

### 2. 配置
```bash
cp examples/config.example.json config.json
nano config.json  # 填入你的 API 凭据
```

### 3. 测试
```bash
python tests/test_google_api_direct.py
```

---

## 📖 常用文档

| 文档                                         | 说明     |
| -------------------------------------------- | -------- |
| [README.md](README.md)                       | 项目介绍 |
| [docs/QUICK_START.md](docs/QUICK_START.md)   | 快速开始 |
| [examples/CONFIG.md](examples/CONFIG.md)     | 配置说明 |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | 结构说明 |

---

## 🔑 获取 API Key

### Google API Key
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目 → 启用 Custom Search API
3. 创建凭据 → 选择"API 密钥"
4. 详见: [docs/GOOGLE_API_SETUP_CN.md](docs/GOOGLE_API_SETUP_CN.md)

### CSE ID
1. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 创建搜索引擎
3. 复制搜索引擎 ID

---

## 🧪 常用测试

```bash
# Google API 测试
python tests/test_google_api_direct.py

# 双引擎测试
python tests/test_dual_engines.py

# 完整功能测试
python tests/test_comprehensive.py
```

---

## 🔧 VS Code 集成

配置文件位置：`~/.config/Code/User/mcp.json`

详见：[docs/VSCODE_INTEGRATION.md](docs/VSCODE_INTEGRATION.md)

---

## 🛡️ 隐私保护

**不会提交到 Git 的文件：**
- `config.json` - 包含真实 API Key
- `output/` - 测试输出
- `.venv/` - 虚拟环境

**安全提示：** 永远不要将 `config.json` 提交到 Git！

---

## 📞 获取帮助

- 📖 查看 [docs/](docs/) 目录获取完整文档
- 🐛 遇到问题？查看 [docs/API_KEY_ERROR_GUIDE.md](docs/API_KEY_ERROR_GUIDE.md)
- 💡 需要示例？查看 [examples/](examples/) 目录

---

## 🎯 项目状态

- ✅ 双搜索引擎（Google + DuckDuckGo）
- ✅ MCP 协议支持
- ✅ VS Code / Cherry Studio 集成
- ✅ 完整测试覆盖
- ✅ 详尽文档

**状态**: 🟢 生产就绪

---

*最后更新: 2025-10-10*
