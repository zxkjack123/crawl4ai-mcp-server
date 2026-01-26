# Crawl4AI MCP Server - Quick Start Guide

Welcome! This guide will help you get the Crawl4AI MCP Server up and running quickly.

## 📋 What You Have

✅ **Virtual Environment**: `.venv` directory created and configured
✅ **Dependencies Installed**: All Python packages installed
✅ **Playwright Browsers**: Browser engines downloaded (Chromium, Firefox, WebKit)
✅ **Configuration File**: `config.json` created from template

## 🚀 Quick Start

### 1. Test the Server

```bash
# Navigate to the project directory
cd /home/gw/opt/crawl4ai-mcp-server

# Activate virtual environment
source .venv/bin/activate

# Run the server (MCP stdio)
./scripts/run_mcp_with_env.sh
```

The server should start without errors. Press `Ctrl+C` to stop it when ready.

### 2. Choose Your Integration

**For VS Code Users:**
👉 Read [VSCODE_INTEGRATION.md](./VSCODE_INTEGRATION.md)

**For Cherry Studio Users:**
👉 Read [CHERRY_STUDIO_INTEGRATION.md](./CHERRY_STUDIO_INTEGRATION.md)

**For Advanced Deployment:**
👉 Read [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

## 🔧 Server Configuration

### Location
```
/home/gw/opt/crawl4ai-mcp-server/
```

### Key Files
- **Server Entry Point**: `src/index.py` (recommended launcher: `scripts/run_mcp_with_env.sh`)
- **Search Module**: `src/search.py`
- **Configuration**: `config.json`
- **Dependencies**: `requirements.txt`

### Python Executable Path
```
/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python
```

## 🛠️ Available Tools

### 1. **search** - Web Search
Search the web using DuckDuckGo (default) or Google.

**Parameters:**
- `query`: Search query string
- `num_results`: Number of results (default: 10)
- `engine`: "duckduckgo" (default) or "google"

**Example Usage:**
```json
{
  "query": "Python async programming",
  "num_results": 5,
  "engine": "duckduckgo"
}
```

### 2. **read_url** - Content Extraction
Extract and format web page content optimized for LLMs.

**Parameters:**
- `url`: The webpage URL to crawl
- `format`: Output format (default: "markdown_with_citations")
  - `raw_markdown`: Basic HTML→Markdown
  - `markdown_with_citations`: Markdown with inline references
  - `references_markdown`: Just the references/citations
  - `fit_markdown`: LLM-optimized clean content
  - `fit_html`: Filtered HTML

**Example Usage:**
```json
{
  "url": "https://docs.python.org/3/",
  "format": "markdown_with_citations"
}
```

## 📝 Configuration Options

### Optional: Google Search

If you want to use Google search instead of (or in addition to) DuckDuckGo:

1. Get Google API credentials:
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Custom Search API
   - Create API key and Custom Search Engine

2. Edit `config.json`:
```json
{
  "google": {
    "api_key": "your-google-api-key",
    "cse_id": "your-google-cse-id"
  }
}
```

**Note:** DuckDuckGo works without any API keys!

## 🔗 Integration Paths

### Path 1: VS Code with Copilot

**Best for:** Developers using VS Code as their primary IDE

**Configuration:**
```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "crawl4ai": {
          "command": "/home/gw/opt/crawl4ai-mcp-server/scripts/run_mcp_with_env.sh",
          "args": []
        }
      }
    }
  }
}
```

**Full Guide:** [VSCODE_INTEGRATION.md](./VSCODE_INTEGRATION.md)

### Path 2: Cherry Studio

**Best for:** Users who prefer a standalone AI assistant application

**Configuration:**
```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "/home/gw/opt/crawl4ai-mcp-server/scripts/run_mcp_with_env.sh",
      "args": []
    }
  }
}
```

**Full Guide:** [CHERRY_STUDIO_INTEGRATION.md](./CHERRY_STUDIO_INTEGRATION.md)

### Path 3: Claude Desktop

**Using Smithery (Automated):**
```bash
npx -y @smithery/cli install @weidwonder/crawl4ai-mcp-server --client claude
```

**Manual Configuration:**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "/home/gw/opt/crawl4ai-mcp-server/scripts/run_mcp_with_env.sh",
      "args": []
    }
  }
}
```

## ✅ Verification Checklist

Before integration, verify:

- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Python version 3.9+: `python --version`
- [ ] Dependencies installed: `pip list | grep crawl4ai`
- [ ] Playwright installed: `playwright --version`
- [ ] Server starts without errors: `./scripts/run_mcp_with_env.sh`
- [ ] Config file exists: `ls -la config.json`

## 🐛 Common Issues

### Issue: Server Won't Start

**Check:**
```bash
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
./scripts/run_mcp_with_env.sh
```

Look for error messages about missing dependencies or configuration issues.

### Issue: Import Errors

**Solution:**
```bash
source .venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

### Issue: Playwright Errors

**Solution:**
```bash
source .venv/bin/activate
playwright install chromium
```

### Issue: Permission Denied

**Solution:**
```bash
chmod +x .venv/bin/python
chmod +x scripts/run_mcp_with_env.sh
```

## 📚 Usage Examples

### Example 1: Research Assistant
```
Prompt: "Search for 'Python asyncio tutorial' and summarize the top 3 results"
```

### Example 2: Documentation Reader
```
Prompt: "Read https://fastapi.tiangolo.com/ and explain how to create a simple API"
```

### Example 3: Competitive Analysis
```
Prompt: "Search for 'best VSCode extensions 2025' and list the top recommendations"
```

## 🎯 Next Steps

1. **Choose your integration path** (VS Code or Cherry Studio)
2. **Follow the detailed integration guide**
3. **Test the tools** with simple queries
4. **Explore advanced features** (custom formats, search engines)
5. **Optimize configuration** for your use case

## 📖 Documentation

- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Advanced deployment options
- [VS Code Integration](./VSCODE_INTEGRATION.md) - VS Code setup guide
- [Cherry Studio Integration](./CHERRY_STUDIO_INTEGRATION.md) - Cherry Studio setup guide
- [README](./README.md) - Project overview

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Look for error messages when starting the server
2. **Review the troubleshooting sections** in the integration guides
3. **Test the server independently**: Run it manually to isolate issues
4. **Check GitHub issues**: See if others have encountered similar problems

## 🎉 You're Ready!

Your Crawl4AI MCP Server is set up and ready to use. Choose your integration path and follow the detailed guide to connect it to your AI assistant.

**Recommended Next Action:**
- For VS Code users: Open [VSCODE_INTEGRATION.md](./VSCODE_INTEGRATION.md)
- For Cherry Studio users: Open [CHERRY_STUDIO_INTEGRATION.md](./CHERRY_STUDIO_INTEGRATION.md)

Happy crawling! 🕷️✨
