# Crawl4AI MCP Server

这是一个基于MCP (Model Context Protocol)的网页爬虫服务器,提供网页内容抓取和转换功能。

## 文件结构

- `src/index.py`: MCP服务器主实现,使用FastMCP提供网页爬取功能
- `pyproject.toml`: 项目配置和依赖管理
- `requirements.txt`: 环境依赖列表,基于实际测试的版本

## 功能说明

服务器提供以下工具:

1. `read_url`: 爬取指定URL的网页内容,支持多种输出格式:
   - raw_markdown: 基础HTML→Markdown转换
   - markdown_with_citations: 包含内联引用的Markdown
   - references_markdown: 引用/参考文献部分
   - fit_markdown: 经过内容过滤的Markdown
   - fit_html: 生成fit_markdown的过滤后HTML
   - markdown: 默认Markdown格式

2. `search`: 执行网络搜索并返回结果
   - 支持多个搜索引擎:
     * DuckDuckGo: 无需API密钥,处理AbstractText、Results和RelatedTopics
     * Google: 需要配置API密钥和CSE ID
   - 参数说明:
     * query: 搜索查询字符串
     * num_results: 返回结果数量(默认10)
     * engine: 使用的搜索引擎(all/duckduckgo/google)

## 环境要求

- Python >= 3.9
- 依赖包版本:
  - Crawl4AI==0.4.248
  - playwright==1.50.0
  - beautifulsoup4==4.13.3
  - 其他依赖见requirements.txt

## 注意事项

1. 服务器使用专门的Python环境(crawl4ai_env)
2. 首次使用需要安装playwright浏览器:
   ```bash
   playwright install
   ```
3. 服务器使用异步操作,确保资源正确清理
4. 内容优化配置:
   - 最小词数阈值为10
   - 排除导航栏、页脚、页眉等非核心内容
   - 启用引用保留以保持URL信息完整性
   - 默认使用 markdown_with_citations 格式输出

## 更新历史

- 2025.02.08: 优化DuckDuckGo搜索实现,增强结果收集能力
- 2025.02.07: 重构项目结构,使用FastMCP实现,优化依赖管理
- 2025.02.07: 优化内容过滤配置,提高token效率并保持URL完整性