[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/weidwonder-crawl4ai-mcp-server-badge.png)](https://mseep.ai/app/weidwonder-crawl4ai-mcp-server)

# Crawl4AI MCP Server

[![smithery badge](https://smithery.ai/badge/@weidwonder/crawl4ai-mcp-server)](https://smithery.ai/server/@weidwonder/crawl4ai-mcp-server)

这是一个基于MCP (Model Context Protocol)的智能信息获取服务器,为AI助手系统提供强大的搜索能力和面向LLM优化的网页内容理解功能。通过多引擎搜索和智能内容提取,帮助AI系统高效获取和理解互联网信息,将网页内容转换为最适合LLM处理的格式。

## 特性

- 🔍 强大的多引擎搜索能力,支持DuckDuckGo和Google
- 📚 面向LLM优化的网页内容提取,智能过滤非核心内容
- 🎯 专注信息价值,自动识别和保留关键内容
- 📝 多种输出格式,支持引用溯源
- 🚀 基于FastMCP的高性能异步设计

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

#### 2. 配置 Google API（可选）

如果需要使用 Google 搜索引擎，请参考以下文档：

- 📖 [Google API 配置指南](docs/GOOGLE_API_SETUP_CN.md) - 详细中文教程
- 📖 [配置说明](examples/CONFIG.md) - 快速配置指南

**注意**: DuckDuckGo 搜索引擎无需配置即可使用。

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

### 项目信息
- 📁 [项目结构](PROJECT_STRUCTURE.md) - 目录组织说明
- 📝 [快速参考](QUICK_REFERENCE.md) - 常用命令和链接
- 🔄 [重构总结](REFACTOR_SUMMARY.md) - 项目重构记录

---

## 使用方法

服务器提供以下工具:

### search
强大的网络搜索工具,支持多个搜索引擎:

- DuckDuckGo搜索(默认): 无需API密钥,全面处理AbstractText、Results和RelatedTopics
- Google搜索: 需要配置API密钥,提供精准搜索结果
- 支持同时使用多个引擎获取更全面的结果

参数说明:
- `query`: 搜索查询字符串
- `num_results`: 返回结果数量(默认10)
- `engine`: 搜索引擎选择
  - "duckduckgo": DuckDuckGo搜索(默认)
  - "google": Google搜索(需要API密钥)
  - "all": 同时使用所有可用的搜索引擎

示例:
```python
# DuckDuckGo搜索(默认)
{
    "query": "python programming",
    "num_results": 5
}

# 使用所有可用引擎
{
    "query": "python programming",
    "num_results": 5,
    "engine": "all"
}
```

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

示例:
```python
# DuckDuckGo搜索(默认)
{
    "query": "python programming",
    "num_results": 5
}

# Google搜索
{
    "query": "python programming",
    "num_results": 5,
    "engine": "google"
}
```

如需使用Google搜索,需要在config.json中配置API密钥:
```json
{
    "google": {
        "api_key": "your-api-key",
        "cse_id": "your-cse-id"
    }
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