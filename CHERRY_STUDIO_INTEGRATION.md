# Cherry Studio Integration Guide for Crawl4AI MCP Server

This guide provides detailed instructions for integrating the Crawl4AI MCP server with Cherry Studio.

## Prerequisites

- Cherry Studio installed and running
- Crawl4AI MCP server deployed and accessible
- Basic understanding of MCP (Model Context Protocol)

## What is Cherry Studio?

Cherry Studio is an AI-powered desktop application that supports various AI models and can be extended with MCP servers to provide additional capabilities like web scraping, search, and content extraction.

## Integration Methods

### Method 1: Using Cherry Studio Settings (Recommended)

#### Step 1: Open Cherry Studio Settings

1. Launch Cherry Studio
2. Click on the **Settings** icon (usually a gear icon)
3. Navigate to **Extensions** or **MCP Servers** section

#### Step 2: Add MCP Server

Look for an option to add a new MCP server. You'll need to provide:

```json
{
  "name": "Crawl4AI",
  "type": "stdio",
  "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
  "args": [
    "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
  ],
  "env": {
    "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src"
  }
}
```

#### Step 3: Save and Restart

1. Save the configuration
2. Restart Cherry Studio
3. The Crawl4AI tools should now be available

### Method 2: Using Configuration File

#### Step 1: Locate Cherry Studio Config Directory

The configuration directory varies by operating system:

- **Linux**: `~/.config/cherry-studio/`
- **macOS**: `~/Library/Application Support/cherry-studio/`
- **Windows**: `%APPDATA%\cherry-studio\`

#### Step 2: Create or Edit MCP Configuration

Create or edit the file `mcp_servers.json` in the config directory:

```bash
# Linux
nano ~/.config/cherry-studio/mcp_servers.json

# macOS
nano ~/Library/Application\ Support/cherry-studio/mcp_servers.json

# Windows
notepad %APPDATA%\cherry-studio\mcp_servers.json
```

Add the following configuration:

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
      "args": [
        "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
      ],
      "env": {
        "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src"
      }
    }
  }
}
```

**For Windows users**, adjust paths:

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "C:\\path\\to\\crawl4ai-mcp-server\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\crawl4ai-mcp-server\\src\\index.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\crawl4ai-mcp-server\\src"
      }
    }
  }
}
```

#### Step 3: Restart Cherry Studio

Close and reopen Cherry Studio to load the new configuration.

### Method 3: Using Cherry Studio CLI (if available)

If Cherry Studio provides a CLI for managing extensions:

```bash
cherry-studio mcp add \
  --name crawl4ai \
  --command /home/gw/opt/crawl4ai-mcp-server/.venv/bin/python \
  --args /home/gw/opt/crawl4ai-mcp-server/src/index.py
```

## Verification

### Step 1: Check MCP Server Status

In Cherry Studio:
1. Go to **Settings** → **Extensions** or **MCP Servers**
2. Look for "Crawl4AI" in the list
3. Check if the status shows as "Connected" or "Active"

### Step 2: View Available Tools

In the chat interface, the available tools should be listed. Look for:
- `search` - Web search tool
- `read_url` - URL content extraction tool

### Step 3: Test the Integration

Try these test commands in Cherry Studio:

**Test 1: Simple Search**
```
Search for "Python web scraping tutorial" using crawl4ai
```

**Test 2: Read URL**
```
Use crawl4ai to read the content from https://docs.python.org/3/tutorial/
```

**Test 3: Combined Workflow**
```
Search for "FastAPI documentation" and then read the first result
```

## Usage Examples

### Example 1: Research Assistant

**Prompt:**
```
I need to research the latest trends in AI. Please:
1. Search for "AI trends 2025"
2. Read the top 3 results
3. Summarize the key trends mentioned
```

Cherry Studio will use the Crawl4AI tools to:
- Execute the search
- Extract content from multiple URLs
- Provide a comprehensive summary

### Example 2: Documentation Helper

**Prompt:**
```
I'm learning React. Can you search for React hooks documentation and explain the useState hook with examples?
```

The assistant will:
- Search for React documentation
- Extract relevant content about hooks
- Provide explained examples

### Example 3: Competitive Analysis

**Prompt:**
```
Research what features the top 5 project management tools offer. Search for "best project management software 2025" and summarize their key features.
```

### Example 4: Content Extraction

**Prompt:**
```
Read https://github.com/trending/python and tell me about the most popular Python projects this week
```

## Advanced Configuration

### Custom Search Settings

Create a custom configuration file for search preferences:

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
      "args": [
        "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
      ],
      "env": {
        "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src",
        "DEFAULT_SEARCH_ENGINE": "duckduckgo",
        "DEFAULT_NUM_RESULTS": "10"
      }
    }
  }
}
```

### Google Search Configuration

If you want to use Google search:

1. Get Google Custom Search API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Custom Search API
   - Create credentials and get API key
   - Create a Custom Search Engine and get CSE ID

2. Update the server configuration file:

```bash
# Edit the config.json in the server directory
nano /home/gw/opt/crawl4ai-mcp-server/config.json
```

Add your credentials:

```json
{
  "google": {
    "api_key": "your-google-api-key",
    "cse_id": "your-google-cse-id"
  }
}
```

3. Restart the MCP server and Cherry Studio

### Timeout Configuration

For slow connections or large websites:

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
      "args": [
        "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
      ],
      "timeout": 60000,
      "env": {
        "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src"
      }
    }
  }
}
```

## Troubleshooting

### Issue: MCP Server Not Connecting

**Symptoms:**
- Cherry Studio shows "Connection Failed" or similar error
- Tools are not available in the chat interface

**Solutions:**

1. **Verify Python Path:**
```bash
# Test if Python is accessible
/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python --version
```

2. **Test Server Manually:**
```bash
# Run the server directly to see errors
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
cd src
python index.py
```

3. **Check Logs:**
Look for Cherry Studio logs (location varies by OS):
- Linux: `~/.config/cherry-studio/logs/`
- macOS: `~/Library/Logs/cherry-studio/`
- Windows: `%APPDATA%\cherry-studio\logs\`

4. **Verify Configuration Syntax:**
Use a JSON validator to ensure your configuration is valid:
```bash
python -m json.tool < ~/.config/cherry-studio/mcp_servers.json
```

### Issue: Tools Show But Don't Work

**Symptoms:**
- Tools appear in Cherry Studio
- Commands fail with errors

**Solutions:**

1. **Check Dependencies:**
```bash
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
pip list | grep -E "(crawl4ai|playwright|mcp)"
```

2. **Reinstall Playwright Browsers:**
```bash
source .venv/bin/activate
playwright install
```

3. **Test Individual Tools:**
Create a test script to verify tools work independently

### Issue: Slow Response Times

**Symptoms:**
- Tools take a long time to respond
- Timeouts occur frequently

**Solutions:**

1. **Increase Timeout:**
Update the timeout in your configuration to 60000ms or more

2. **Use Faster Search Engine:**
DuckDuckGo is generally faster than Google for simple searches

3. **Optimize Content Extraction:**
Use `fit_markdown` format instead of `markdown_with_citations` for faster processing

### Issue: Permission Denied

**Symptoms:**
- Error messages about file access
- Cannot execute Python or scripts

**Solutions:**

```bash
# Fix Python executable permissions
chmod +x /home/gw/opt/crawl4ai-mcp-server/.venv/bin/python

# Fix script permissions
chmod +x /home/gw/opt/crawl4ai-mcp-server/src/index.py

# Verify ownership
ls -la /home/gw/opt/crawl4ai-mcp-server/
```

### Issue: Module Import Errors

**Symptoms:**
- "ModuleNotFoundError" in logs
- Server fails to start

**Solutions:**

1. **Verify Virtual Environment:**
```bash
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
python -c "import crawl4ai; import mcp; print('Imports OK')"
```

2. **Reinstall Dependencies:**
```bash
source .venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

3. **Check PYTHONPATH:**
Ensure PYTHONPATH in configuration includes the src directory

## Best Practices

### 1. Resource Management

- **Monitor Memory**: Web crawling can be memory-intensive
- **Limit Concurrent Requests**: Don't overwhelm the server with too many simultaneous requests
- **Use Appropriate Formats**: Choose `fit_markdown` for faster processing when citations aren't needed

### 2. Search Optimization

- **Be Specific**: Use specific search queries for better results
- **Limit Results**: Request only the number of results you need (default is 10)
- **Use DuckDuckGo**: Prefer DuckDuckGo for anonymous, API-free searches

### 3. Content Extraction

- **Choose the Right Format**:
  - `markdown_with_citations`: When you need references
  - `fit_markdown`: For clean, LLM-optimized content
  - `raw_markdown`: For complete page content
  
- **Handle Large Pages**: Be patient with large or complex websites

### 4. Privacy and Ethics

- **Respect Robots.txt**: The crawler respects website robots.txt files
- **Rate Limiting**: Don't make rapid successive requests to the same domain
- **Copyright**: Be aware of copyright when extracting and using content
- **API Keys**: Keep your API keys secure

## Integration Tips

### Tip 1: Create Custom Prompts

Save common workflows as custom prompts in Cherry Studio:

```
Research Template:
1. Search for "[TOPIC]"
2. Read the top 3 results
3. Summarize key points
4. Provide actionable insights
```

### Tip 2: Combine with Other Tools

Use Crawl4AI alongside other MCP servers for enhanced functionality:
- Database queries + web research
- File operations + content extraction
- API calls + search results

### Tip 3: Batch Processing

For multiple URLs:

```
Read and summarize these URLs:
1. https://example.com/article1
2. https://example.com/article2
3. https://example.com/article3
```

## Performance Optimization

### 1. Server-Side

Edit `/home/gw/opt/crawl4ai-mcp-server/src/index.py`:

```python
# Adjust browser configuration for better performance
browser_config = BrowserConfig(
    headless=True,
    browser_type="chromium",  # or "firefox", "webkit"
    viewport_width=1280,
    viewport_height=720
)
```

### 2. Client-Side

In Cherry Studio settings:
- Adjust timeout values
- Enable response caching if available
- Configure concurrent request limits

## Security Considerations

1. **Isolate the Virtual Environment**: Keep the MCP server in its own environment
2. **Monitor Logs**: Regularly check for suspicious activity
3. **Update Dependencies**: Keep all packages up to date
4. **Limit Network Access**: Use firewall rules if possible
5. **Secure Configuration**: Protect config files with API keys

## Additional Resources

- [Cherry Studio Documentation](https://github.com/kangfenmao/cherry-studio)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Crawl4AI GitHub](https://github.com/crawl4ai/crawl4ai)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## Support and Community

If you encounter issues:
1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review the Crawl4AI MCP server logs
3. Check Cherry Studio's issue tracker
4. Visit the project GitHub repository

## Updates and Maintenance

### Updating the MCP Server

```bash
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
git pull origin main
pip install -r requirements.txt --upgrade
playwright install
```

### Updating Cherry Studio

Follow Cherry Studio's update procedure (usually automatic or through app settings).

### Checking for Breaking Changes

Before updating, review:
- Crawl4AI changelog
- MCP protocol updates
- Cherry Studio release notes

## Conclusion

The Crawl4AI MCP server provides powerful web scraping and search capabilities to Cherry Studio. With proper configuration and usage, it can significantly enhance your AI assistant's ability to access and process web content.

For questions or issues, refer to the troubleshooting section or consult the project documentation.
