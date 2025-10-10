# Crawl4AI MCP Server - Deployment Guide

## Prerequisites

- Python 3.9 or higher
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
# Copy the demo config to create your config file
cp config_demo.json config.json
```

Edit `config.json` to add your API keys (optional, only if you want to use Google search):

```json
{
    "google": {
        "api_key": "your-google-api-key",
        "cse_id": "your-google-cse-id"
    }
}
```

**Note**: Google search is optional. DuckDuckGo search works without any API keys.

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

### Playwright Installation Issues

If you encounter issues with Playwright browser installation:

```bash
# Try installing browsers again
playwright install chromium  # Install only Chromium if needed

# Check Playwright installation
playwright --version
```

### Python Environment Issues

```bash
# Verify Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Port Conflicts

If the server fails to start due to port conflicts, check and modify the port in the MCP client configuration.

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
