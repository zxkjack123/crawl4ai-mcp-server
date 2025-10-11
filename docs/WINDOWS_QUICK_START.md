# 🪟 Windows 快速开始

5 分钟快速在 Windows 上安装和运行 Crawl4AI MCP Server。

---

## ⚡ 一键安装

### 方式 1: PowerShell（推荐）

1. **打开 PowerShell**（以管理员身份）

2. **运行安装命令**：
   ```powershell
   # 克隆项目
   git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
   cd crawl4ai-mcp-server
   
   # 运行安装脚本
   .\setup.ps1
   ```

3. **配置 API**：
   ```powershell
   copy examples\config.example.json config.json
   notepad config.json
   ```
   填入您的 Google API 凭据

4. **测试**：
   ```powershell
   .\run_tests.ps1
   ```

### 方式 2: CMD

1. **打开 CMD**（命令提示符）

2. **运行安装命令**：
   ```cmd
   git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
   cd crawl4ai-mcp-server
   setup.bat
   ```

3. **配置和测试**（同上）

---

## 📋 前置要求

在开始之前，请确保已安装：

### ✅ Python 3.9+

**检查**：
```powershell
python --version
```

**如未安装**：
1. 访问 https://www.python.org/downloads/windows/
2. 下载 Python 3.12
3. 安装时**勾选** "Add Python to PATH"

### ✅ Git

**检查**：
```powershell
git --version
```

**如未安装**：
1. 访问 https://git-scm.com/download/win
2. 下载并安装 Git for Windows

---

## 🔧 手动安装（详细步骤）

如果自动脚本失败，可以手动执行以下步骤：

### 1. 克隆项目
```powershell
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server
```

### 2. 创建虚拟环境
```powershell
python -m venv .venv
```

### 3. 激活虚拟环境

**PowerShell**:
```powershell
.\.venv\Scripts\Activate.ps1
```

**CMD**:
```cmd
.venv\Scripts\activate.bat
```

如果 PowerShell 提示执行策略错误：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. 安装依赖
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 安装 Playwright 浏览器
```powershell
playwright install
```

### 6. 配置
```powershell
copy examples\config.example.json config.json
notepad config.json
```

### 7. 测试
```powershell
python tests\test_google_api_direct.py
```

---

## 🎯 VS Code 集成

### 配置步骤

1. **打开配置文件**：
   ```powershell
   code $env:APPDATA\Code\User\mcp.json
   ```

2. **添加配置**（注意使用双反斜杠）：
   ```json
   {
     "mcpServers": {
       "crawl4ai": {
         "command": "python",
         "args": [
           "C:\\Users\\YourName\\Projects\\crawl4ai-mcp-server\\src\\index.py"
         ],
         "env": {
           "PYTHONPATH": "C:\\Users\\YourName\\Projects\\crawl4ai-mcp-server"
         }
       }
     }
   }
   ```

3. **重启 VS Code**

详细说明：[docs/VSCODE_INTEGRATION.md](VSCODE_INTEGRATION.md)

---

## 🧪 快速测试

### 测试脚本

**运行所有测试**：
```powershell
.\run_tests.ps1  # PowerShell
run_tests.bat    # CMD
```

**单独测试**：
```powershell
# 测试 Google API
python tests\test_google_api_direct.py

# 测试双引擎
python tests\test_dual_engines.py

# 完整测试
python tests\test_comprehensive.py
```

---

## 💡 常用命令

### 激活环境
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1

# CMD
.venv\Scripts\activate.bat

# 或使用快捷方式
activate.bat
```

### 运行测试
```powershell
.\run_tests.ps1
```

### 编辑配置
```powershell
notepad config.json
```

### 查看文档
```powershell
explorer docs\
```

### 更新项目
```powershell
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## ⚠️ 常见问题

### ❌ Python 未找到

**错误**：`'python' 不是内部或外部命令`

**解决**：
1. 重新安装 Python，确保勾选 "Add Python to PATH"
2. 或手动添加 Python 到系统 PATH

### ❌ PowerShell 执行策略错误

**错误**：`无法加载文件，因为在此系统上禁止运行脚本`

**解决**：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ pip 安装慢或失败

**解决**：使用国内镜像
```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### ❌ Playwright 下载慢

**解决**：设置国内镜像
```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST="https://npmmirror.com/mirrors/playwright/"
playwright install
```

---

## 📚 更多文档

- 📖 [完整 Windows 安装指南](WINDOWS_INSTALLATION.md) - 详细步骤和故障排除
- 📖 [项目结构说明](../PROJECT_STRUCTURE.md) - 了解项目组织
- 📖 [配置说明](../examples/CONFIG.md) - 配置文件详解
- 📖 [Google API 设置](GOOGLE_API_SETUP_CN.md) - 获取 API 凭据

---

## 🚀 下一步

1. ✅ 安装完成
2. ⚙️ 配置 Google API（可选）
3. 🧪 运行测试验证
4. 🔧 集成到 VS Code
5. 📖 阅读完整文档

---

**开始使用 Crawl4AI MCP Server！** 🎉

---

*适用系统: Windows 10/11*  
*最后更新: 2025-10-11*
