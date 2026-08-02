# Crawl4AI MCP Server - Deployment Guide

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Virtual environment support
- Playwright (for web crawling)

## Installation Steps

### 1. Clone and Setup Virtual Environment

```bash
cd /home/gw/opt/crawl4ai-mcp-server

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# (Optional) Install system dependencies for Playwright
# sudo playwright install-deps
```

### 3. Configure the Server

```bash
# Copy the example env file and edit with your API keys
cp .env.example .env
```

Supported search engines (DuckDuckGo works without any keys):

| Engine | Required Env Vars | Notes |
|---|---|---|
| DuckDuckGo | — | Free, no API key |
| Google CSE | `GOOGLE_API_KEY`, `GOOGLE_CSE_ID` | 100 queries/day free |
| Brave | `BRAVE_API_KEY` | 2,000 queries/month free |
| SearXNG | `SEARXNG_BASE_URL` | Self-hosted, unlimited |

Edit `.env` to add the keys you need.  All keys are optional — the server
will use whichever engines are configured.

### 4. Test the Server

```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Run the server directly
cd src
python index.py
```

The server should start and be ready to accept MCP connections.

## Server Capabilities

### Available Tools

1. **search** - Web search using DuckDuckGo (default) or Google
   - No API key required for DuckDuckGo
   - Returns comprehensive search results with titles, links, and snippets

2. **read_url** - LLM-optimized web page content extraction
   - Multiple output formats (markdown, markdown_with_citations, fit_markdown, etc.)
   - Intelligent content filtering
   - Preserves references and citations

## Deployment Options

### Option 1: Local Development

Run the server locally for development and testing:

```bash
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
cd src
python index.py
```

### Option 2: Background Service

Create a systemd service file for Linux:

```bash
sudo nano /etc/systemd/system/crawl4ai-mcp.service
```

Add the following content:

```ini
[Unit]
Description=Crawl4AI MCP Server
After=network.target

[Service]
Type=simple
User=gw
WorkingDirectory=/home/gw/opt/crawl4ai-mcp-server/src
ExecStart=/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python index.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable crawl4ai-mcp
sudo systemctl start crawl4ai-mcp
sudo systemctl status crawl4ai-mcp
```

### Option 3: Docker Deployment

A Dockerfile is provided in the repository. Build and run:

```bash
docker build -t crawl4ai-mcp-server .
docker run -d --name crawl4ai-mcp crawl4ai-mcp-server
```

## Troubleshooting

### Playwright Browser (Chromium) Missing

`read_url` uses Playwright to launch a headless Chromium browser. If the browser binary
was never installed (or the install step was skipped), `read_url` fails with:

```
BrowserType.launch: Executable doesn't exist at /home/gw/.cache/ms-playwright/chromium-1155/chrome-linux/chrome
```

> ⚠️ **Impact**: Only `read_url` (browser crawling) is affected. `search` (Brave / Google /
> SearXNG HTTP engines) and the MCP HTTP endpoint keep working — they do **not** need a browser.

Fix — install the Chromium binaries with the project's venv:

```bash
cd crawl4ai-mcp-server
.venv/bin/python -m playwright install chromium   # installs chromium + headless-shell + ffmpeg
# Optional: system libs for Chromium (may need sudo)
.venv/bin/python -m playwright install-deps chromium
```

Verify the browsers are present:

```bash
ls /home/gw/.cache/ms-playwright/   # should show chromium-<build> and chromium_headless_shell-<build>
.venv/bin/python -m playwright install --dry-run   # shows what's missing
```

After installing, **restart** the service so the running process picks up the browser path
(see *Deployment Options → Background Service*).

### Browser Cannot Reach the Internet (Proxy Required)

If `read_url` returns `net::ERR_EMPTY_RESPONSE` while `search` works, the headless browser is
likely being launched **without** the proxy that this environment needs for outbound internet
(e.g. a local Clash/mihomo on `127.0.0.1:7890`).

- Symptom: raw `chromium.launch()` succeeds but `page.goto("https://...")` fails with
  `net::ERR_EMPTY_RESPONSE` / `ERR_CONNECTION_*`.
- The crawl4ai MCP server **handles this automatically** in most setups via
  `CRAWL4AI_HTTP_PROXY` / `HTTPS_PROXY` / `CRAWL4AI_ALLOW_PROXY_REWRITE` in `.env` — a fallback
  crawler is created with the resolved proxy.
- Manual check (browser with proxy):
  ```bash
  .venv/bin/python -c "
  from playwright.async_api import async_playwright
  import asyncio
  async def m():
      async with async_playwright() as p:
          b = await p.chromium.launch(headless=True)
          pg = await (await b.new_context(proxy={'server':'http://127.0.0.1:7890'})).new_page()
          await pg.goto('https://example.com'); print(await pg.title()); await b.close()
  asyncio.run(m())"
  ```

### Python Environment Issues

```bash
# Verify Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Port Conflicts / Duplicate Instance Holds 8011

If the service repeatedly crashes with `[Errno 98] address already in use` and enters an
`activating (auto-restart)` loop, another instance is already bound to the configured port:

```bash
# Find who owns the port
ss -tlnp | grep 8011        # shows pid; e.g. another crawl4ai.service or python process

# If a duplicate systemd unit exists, stop & disable the redundant one
sudo systemctl disable --now crawl4ai.service   # e.g. a stale system-level unit fighting the user-level one

# Ensure exactly ONE managed instance owns the port, then restart it
systemctl --user restart crawl4ai-mcp.service
```

> **Key**: Prefer a single user-level `systemd --user` unit (`~/.config/systemd/user/crawl4ai-mcp.service`)
> with `Restart=on-failure` + `loginctl enable-linger` instead of a system-level `crawl4ai.service`,
> so only one process binds `0.0.0.0:8011` at boot. See README "MCP 服务器常驻 HTTP 服务模式".

## Security Considerations

1. **API Keys**: Keep your `config.json` file secure and never commit it to version control
2. **Network Access**: The server needs internet access to crawl web pages
3. **Resource Limits**: Consider setting resource limits if running as a service
4. **Firewall**: Only expose the server to trusted clients

## Performance Optimization

1. **Browser Configuration**: Adjust browser settings in `src/index.py` for your needs
2. **Caching**: The server uses cache bypass by default; consider enabling caching for frequently accessed pages
3. **Concurrent Requests**: Adjust async configurations based on your system resources

## Next Steps

After deployment, integrate the server with:
- [VS Code Integration Guide](./VSCODE_INTEGRATION.md)
- [Cherry Studio Integration Guide](./CHERRY_STUDIO_INTEGRATION.md)
