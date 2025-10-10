# 项目结构说明

本文档说明项目的目录结构和文件组织。

## 目录结构

```
crawl4ai-mcp-server/
│
├── src/                        # 📦 源代码目录
│   ├── index.py               # MCP 服务器主入口
│   ├── search.py              # 搜索引擎管理器
│   └── __pycache__/           # Python 缓存（自动生成）
│
├── tests/                      # 🧪 测试脚本目录
│   ├── test_utils.py          # 测试辅助工具
│   ├── test_google_api_direct.py      # Google API 直接测试
│   ├── test_dual_engines.py           # 双引擎对比测试
│   ├── test_comprehensive.py          # 综合功能测试
│   ├── test_search.py                 # 基础搜索测试
│   ├── test_search_llm.py             # LLM 搜索测试
│   ├── test_search_manager.py         # 搜索管理器测试
│   ├── test_llm_programming.py        # LLM 编程测试
│   ├── search_google_api_detailed.py  # Google API 详细测试
│   └── search_google_api_guide.py     # Google API 指南测试
│
├── docs/                       # 📚 文档目录
│   ├── README.md              # 项目介绍（原始版本）
│   ├── DEPLOYMENT_GUIDE.md    # 部署指南
│   ├── VSCODE_INTEGRATION.md  # VS Code 集成教程
│   ├── CHERRY_STUDIO_INTEGRATION.md   # Cherry Studio 集成
│   ├── QUICK_START.md         # 快速开始指南
│   ├── SETUP_COMPLETE.md      # 配置完成总结
│   ├── TEST_RESULTS.md        # 测试结果记录
│   │
│   ├── GOOGLE_API_SETUP_CN.md         # Google API 设置（中文）
│   ├── GOOGLE_API_ENABLE_GUIDE.md     # API 启用指南
│   ├── GOOGLE_API_SEARCH_SUMMARY.md   # 搜索配置总结
│   ├── API_KEY_ERROR_GUIDE.md         # API Key 错误诊断
│   ├── google_api_setup_guide.md      # Google API 设置向导
│   │
│   ├── FINAL_SUMMARY.md       # 最终配置总结
│   ├── PROJ_INFO_4AI.md       # 项目信息（AI用）
│   └── LICENSE                # 开源许可证
│
├── examples/                   # 📋 配置示例目录
│   ├── config.example.json    # 配置文件示例
│   └── CONFIG.md              # 配置说明文档
│
├── output/                     # 📊 测试输出目录（不提交到 Git）
│   ├── test_results.json      # 测试结果
│   ├── dual_engine_test_results.json  # 双引擎测试结果
│   ├── test_search_output.json        # 搜索输出
│   ├── test_content_output.md         # 内容提取输出
│   ├── google_api_search_results.json # Google 搜索结果
│   └── llm_search_results.json        # LLM 搜索结果
│
├── .venv/                      # 🐍 Python 虚拟环境（不提交）
├── .mypy_cache/               # 类型检查缓存（不提交）
│
├── config.json                 # ⚙️ 实际配置文件（不提交，包含隐私）
├── .gitignore                 # Git 忽略规则
├── pyproject.toml             # 项目元数据和依赖
├── requirements.txt           # Python 依赖列表
├── smithery.yaml              # Smithery 配置
├── Dockerfile                 # Docker 镜像配置
├── README.md                  # 项目主文档（带结构说明）
└── PROJECT_STRUCTURE.md       # 本文件
```

## 目录说明

### 📦 src/ - 源代码

包含所有核心功能代码：
- `index.py`: MCP 服务器入口，定义工具接口
- `search.py`: 搜索引擎实现（DuckDuckGo, Google）

### 🧪 tests/ - 测试脚本

所有测试和验证脚本：
- 单元测试脚本
- 集成测试脚本
- API 验证脚本
- 性能测试脚本

### 📚 docs/ - 文档

完整的项目文档：
- **部署指南**: 如何安装和部署
- **集成教程**: VS Code、Cherry Studio 集成
- **API 配置**: Google API 详细设置
- **故障排除**: 常见问题和解决方案

### 📋 examples/ - 配置示例

配置文件模板和说明：
- `config.example.json`: 配置文件模板
- `CONFIG.md`: 详细配置说明

### 📊 output/ - 测试输出

**重要**: 此目录不提交到 Git（包含在 .gitignore 中）

存放测试运行时生成的输出文件：
- JSON 格式的测试结果
- 提取的网页内容
- 搜索结果数据

## 隐私和安全

### 不提交到 Git 的文件

以下文件包含隐私信息，已添加到 `.gitignore`：

1. **config.json** - 包含真实的 API Key 和凭据
2. **output/** - 可能包含敏感的测试数据
3. **.venv/** - 虚拟环境文件
4. **__pycache__/** - Python 缓存

### 如何配置

1. 复制示例配置：
   ```bash
   cp examples/config.example.json config.json
   ```

2. 编辑 `config.json` 填入真实凭据

3. 不要将 `config.json` 提交到 Git！

详细配置步骤请参考 `examples/CONFIG.md`。

## 快速导航

### 新用户

1. 📖 阅读 [README.md](../README.md) - 项目概述
2. 🚀 参考 [docs/QUICK_START.md](docs/QUICK_START.md) - 快速开始
3. ⚙️ 查看 [examples/CONFIG.md](examples/CONFIG.md) - 配置说明

### 部署

1. 📦 [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - 完整部署步骤
2. 🔧 [docs/VSCODE_INTEGRATION.md](docs/VSCODE_INTEGRATION.md) - VS Code 集成
3. 🎨 [docs/CHERRY_STUDIO_INTEGRATION.md](docs/CHERRY_STUDIO_INTEGRATION.md) - Cherry Studio

### 配置 Google API

1. 📝 [docs/GOOGLE_API_SETUP_CN.md](docs/GOOGLE_API_SETUP_CN.md) - 中文详细教程
2. 🔑 [docs/API_KEY_ERROR_GUIDE.md](docs/API_KEY_ERROR_GUIDE.md) - 错误诊断
3. ✅ [docs/GOOGLE_API_ENABLE_GUIDE.md](docs/GOOGLE_API_ENABLE_GUIDE.md) - API 启用

### 测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试
python tests/test_comprehensive.py
python tests/test_google_api_direct.py
python tests/test_dual_engines.py
```

### 开发

- 修改源代码: 编辑 `src/` 目录
- 添加测试: 在 `tests/` 目录创建新测试
- 更新文档: 编辑 `docs/` 目录相应文档

## 文件命名规范

### 测试脚本

- `test_*.py` - 测试脚本
- 使用描述性名称，如 `test_google_api_direct.py`

### 文档

- 全大写 + 下划线，如 `DEPLOYMENT_GUIDE.md`
- 例外: `README.md`, `LICENSE`

### 配置

- `*.json` - JSON 配置文件
- `*.yaml` / `*.yml` - YAML 配置文件
- `*.example.*` - 示例配置文件

## 维护建议

### 定期检查

1. 确保 `config.json` 不在 Git 中
   ```bash
   git status --ignored
   ```

2. 清理旧的测试输出
   ```bash
   rm -rf output/*
   ```

3. 更新文档保持同步

### 添加新功能

1. 在 `src/` 中实现功能
2. 在 `tests/` 中添加测试
3. 在 `docs/` 中更新文档
4. 更新 `README.md` 如有必要

## 相关资源

- [MCP 协议文档](https://modelcontextprotocol.io)
- [Crawl4AI 文档](https://crawl4ai.com/docs)
- [Google Custom Search API](https://developers.google.com/custom-search)

---

*最后更新: 2025-10-10*
