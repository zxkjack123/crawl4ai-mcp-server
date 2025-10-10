# VS Code Integration Guide for Crawl4AI MCP Server

This guide shows you how to integrate the Crawl4AI MCP server with VS Code's Copilot features.

## Prerequisites

- VS Code installed
- GitHub Copilot extension installed and activated
- Crawl4AI MCP server deployed and running
- VS Code version 1.85.0 or higher

## Integration Methods

### Method 1: Using VS Code Settings (Recommended)

#### Step 1: Locate VS Code Settings

1. Open VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Preferences: Open User Settings (JSON)"
4. Press Enter

#### Step 2: Add MCP Server Configuration

Add the following configuration to your `settings.json`:

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
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
  }
}
```

**Important**: Adjust the paths according to your installation directory.

#### Step 3: Restart VS Code

Close and reopen VS Code for the changes to take effect.

### Method 2: Using MCP Configuration File

#### Step 1: Create MCP Configuration Directory

```bash
mkdir -p ~/.config/Code/User/globalStorage/github.copilot-chat/
```

For VS Code Insiders:
```bash
mkdir -p ~/.config/Code\ -\ Insiders/User/globalStorage/github.copilot-chat/
```

#### Step 2: Create MCP Configuration File

Create a file named `mcp_servers.json`:

```bash
nano ~/.config/Code/User/globalStorage/github.copilot-chat/mcp_servers.json
```

Add the following content:

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

#### Step 3: Restart VS Code

Close and reopen VS Code.

### Method 3: Using Workspace Settings

For project-specific integration:

#### Step 1: Create Workspace Settings

In your project root, create or edit `.vscode/settings.json`:

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "crawl4ai": {
          "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
          "args": [
            "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
          ]
        }
      }
    }
  }
}
```

## Verification

### Step 1: Check MCP Server Connection

1. Open VS Code
2. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
3. Type "Developer: Show Logs"
4. Select "GitHub Copilot"
5. Look for logs mentioning MCP server connections

### Step 2: Test the Integration

1. Open GitHub Copilot Chat in VS Code
2. Try using the Crawl4AI tools:

**Test Search:**
```
@crawl4ai search for "Python web scraping best practices"
```

**Test URL Reading:**
```
@crawl4ai read the content from https://docs.python.org/3/
```

## Usage Examples

### Example 1: Web Search

```
Ask Copilot: "Use the crawl4ai search tool to find recent articles about FastAPI"
```

### Example 2: Content Extraction

```
Ask Copilot: "Use crawl4ai to read https://github.com/trending and summarize the trending repositories"
```

### Example 3: Research Workflow

```
Ask Copilot: "Search for 'async Python patterns' and then read the top 3 results to provide me with a comprehensive guide"
```

## Advanced Configuration

### Configuring Timeouts

Add timeout settings to your configuration:

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "crawl4ai": {
          "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
          "args": [
            "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
          ],
          "timeout": 30000,
          "env": {
            "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src"
          }
        }
      }
    }
  }
}
```

### Using Environment Variables

If you need to configure API keys or other settings:

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "crawl4ai": {
          "command": "/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python",
          "args": [
            "/home/gw/opt/crawl4ai-mcp-server/src/index.py"
          ],
          "env": {
            "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src",
            "GOOGLE_API_KEY": "your-api-key",
            "GOOGLE_CSE_ID": "your-cse-id"
          }
        }
      }
    }
  }
}
```

## Troubleshooting

### Issue: MCP Server Not Connecting

**Solution 1**: Check Python Path
```bash
# Verify the Python path is correct
/home/gw/opt/crawl4ai-mcp-server/.venv/bin/python --version
```

**Solution 2**: Check Server Logs
```bash
# Run the server manually to see error messages
cd /home/gw/opt/crawl4ai-mcp-server
source .venv/bin/activate
cd src
python index.py
```

**Solution 3**: Check VS Code Extension Logs
1. Open Command Palette
2. "Developer: Show Logs"
3. Select "GitHub Copilot"
4. Look for error messages

### Issue: Tools Not Available in Copilot

**Solution**: Restart VS Code and verify the configuration:
1. Close all VS Code windows
2. Reopen VS Code
3. Open a new chat session with Copilot
4. Try mentioning @crawl4ai

### Issue: Permission Denied

**Solution**: Make sure the Python executable has execute permissions:
```bash
chmod +x /home/gw/opt/crawl4ai-mcp-server/.venv/bin/python
```

### Issue: Module Not Found Errors

**Solution**: Verify PYTHONPATH is set correctly:
```json
{
  "env": {
    "PYTHONPATH": "/home/gw/opt/crawl4ai-mcp-server/src:/home/gw/opt/crawl4ai-mcp-server"
  }
}
```

## Best Practices

1. **Use Absolute Paths**: Always use absolute paths in configuration files
2. **Environment Isolation**: Keep the virtual environment activated only for the server
3. **Log Monitoring**: Regularly check logs for errors or issues
4. **Update Regularly**: Keep both VS Code and the MCP server updated
5. **Resource Management**: Monitor system resources when crawling large websites

## Security Notes

1. **API Keys**: Never commit configuration files with API keys to version control
2. **Network Access**: The server needs internet access; ensure your firewall rules allow it
3. **Content Filtering**: Be aware of the content being crawled and processed
4. **Rate Limiting**: Respect website rate limits when crawling

## Additional Resources

- [VS Code Copilot Documentation](https://code.visualstudio.com/docs/copilot/overview)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Crawl4AI Documentation](https://github.com/crawl4ai/crawl4ai)

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review VS Code extension logs
3. Test the server independently
4. Check the GitHub repository for updates and issues
