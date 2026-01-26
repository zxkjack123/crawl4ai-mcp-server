# 🪟 Windows 安装指南

本指南专门针对 Windows 用户，提供详细的安装和配置步骤。

---

## 📋 系统要求

- **操作系统**: Windows 10/11（64位）
- **Python**: 3.9 或更高版本
- **Git**: 最新版本
- **磁盘空间**: 至少 500 MB
- **网络**: 需要访问互联网（用于下载依赖和 Playwright 浏览器）

---

## 🚀 快速安装（推荐）

### 方式 1: 使用自动安装脚本

1. **下载项目**
   ```powershell
   git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
   cd crawl4ai-mcp-server
   ```

2. **运行安装脚本**
   ```powershell
   # PowerShell (推荐)
   .\setup.ps1
   
   # 或者使用 CMD
   setup.bat
   ```

3. **配置 API**
   ```powershell
   copy examples\config.example.json config.json
   notepad config.json
   ```
   填入您的 Google API Key 和 CSE ID

4. **测试**
   ```powershell
   .\run_tests.bat
   ```

---

## 📦 详细安装步骤

### 步骤 1: 安装 Python

#### 检查 Python 是否已安装

打开 PowerShell 或 CMD，运行：
```powershell
python --version
```

如果显示 Python 3.9 或更高版本，跳到步骤 2。

#### 下载安装 Python

1. 访问 [Python 官网](https://www.python.org/downloads/windows/)
2. 下载最新的 Python 3.12 安装程序
3. 运行安装程序
4. **重要**: 勾选 "Add Python to PATH"
5. 点击 "Install Now"

#### 验证安装

```powershell
python --version
pip --version
```

应该显示类似：
```
Python 3.12.x
pip 24.x.x
```

### 步骤 2: 安装 Git

#### 检查 Git 是否已安装

```powershell
git --version
```

#### 下载安装 Git

1. 访问 [Git 官网](https://git-scm.com/download/win)
2. 下载 Git for Windows
3. 运行安装程序，使用默认选项
4. 安装完成后重启终端

#### 验证安装

```powershell
git --version
```

### 步骤 3: 克隆项目

#### 使用 PowerShell

```powershell
# 进入您想要存放项目的目录
cd C:\Projects  # 或您喜欢的路径

# 克隆项目
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git

# 进入项目目录
cd crawl4ai-mcp-server
```

#### 使用 Git Bash（推荐）

如果安装了 Git for Windows，您可以使用 Git Bash：

```bash
cd /c/Projects
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server
```

### 步骤 4: 创建虚拟环境

#### PowerShell

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1
```

**注意**: 如果遇到权限错误，以管理员身份运行 PowerShell 并执行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### CMD

```cmd
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate.bat
```

#### Git Bash

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
source .venv/Scripts/activate
```

#### 验证虚拟环境

激活后，提示符应该显示 `(.venv)`：
```
(.venv) PS C:\Projects\crawl4ai-mcp-server>
```

### 步骤 5: 安装依赖

确保虚拟环境已激活，然后运行：

```powershell
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

**预期输出**:
```
Successfully installed crawl4ai-0.4.248 playwright-1.50.0 ...
```

### 步骤 6: 安装 Playwright 浏览器

```powershell
playwright install
```

这将下载 Chromium、Firefox 和 WebKit 浏览器（约 300-400 MB）。

**预期输出**:
```
Downloading Chromium ...
Downloading Firefox ...
Downloading Webkit ...
```

### 步骤 7: 配置 API

#### 复制配置文件

```powershell
copy examples\config.example.json config.json
```

#### 编辑配置

```powershell
# 使用记事本
notepad config.json

# 或使用 VS Code
code config.json
```

填入您的 Google API 凭据：
```json
{
    "google": {
        "api_key": "AIzaSy...",
      "cse_id": "YOUR_GOOGLE_CSE_ID"
    }
}
```

**获取 API 凭据**: 参见 [docs/GOOGLE_API_SETUP_CN.md](GOOGLE_API_SETUP_CN.md)

### 步骤 8: 测试安装

```powershell
# 测试 Google API
python tests\test_google_api_direct.py

# 测试双引擎
python tests\test_dual_engines.py

# 完整测试
python tests\test_comprehensive.py
```

---

## 🔧 VS Code 集成 (Windows)

### 配置 MCP Server

1. **打开 VS Code 配置目录**
   ```powershell
   # Windows 11/10
   code $env:APPDATA\Code\User\mcp.json
   ```

2. **添加配置**（注意 Windows 路径使用双反斜杠）
   ```json
   {
     "mcpServers": {
       "crawl4ai": {
         "command": "python",
         "args": [
           "C:\\Projects\\crawl4ai-mcp-server\\src\\index.py"
         ],
         "env": {
           "PYTHONPATH": "C:\\Projects\\crawl4ai-mcp-server"
         }
       }
     }
   }
   ```

3. **重启 VS Code**

详细步骤参见: [docs/VSCODE_INTEGRATION.md](VSCODE_INTEGRATION.md)

---

## 🛠️ 辅助脚本

项目提供了 Windows 批处理脚本简化操作：

### setup.bat / setup.ps1
自动执行安装步骤：
```powershell
.\setup.ps1  # PowerShell
setup.bat    # CMD
```

### run_tests.bat / run_tests.ps1
快速运行测试：
```powershell
.\run_tests.ps1
```

### activate.bat
快速激活虚拟环境：
```cmd
activate.bat
```

---

## ⚠️ 常见问题

### 问题 1: PowerShell 脚本执行策略错误

**错误信息**:
```
无法加载文件 .venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本
```

**解决方案**:
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 2: Python 命令未找到

**错误信息**:
```
'python' 不是内部或外部命令
```

**解决方案**:
1. 重新安装 Python，确保勾选 "Add Python to PATH"
2. 或手动添加到 PATH：
   - 打开"系统属性" → "环境变量"
   - 在"用户变量"中找到 `Path`
   - 添加 Python 安装路径，如：`C:\Users\YourName\AppData\Local\Programs\Python\Python312`

### 问题 3: pip 安装依赖失败

**错误信息**:
```
ERROR: Could not find a version that satisfies the requirement...
```

**解决方案**:
```powershell
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像（如果网络慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 4: Playwright 安装浏览器失败

**解决方案**:
```powershell
# 设置环境变量使用国内镜像
$env:PLAYWRIGHT_DOWNLOAD_HOST="https://npmmirror.com/mirrors/playwright/"
playwright install
```

### 问题 5: Git 克隆速度慢

**解决方案**:
```powershell
# 使用 GitHub 镜像
git clone https://ghproxy.com/https://github.com/zxkjack123/crawl4ai-mcp-server.git
```

### 问题 6: 路径中包含空格

如果项目路径包含空格（如 `C:\My Projects\crawl4ai-mcp-server`），某些命令可能失败。

**解决方案**:
- 使用引号包裹路径
- 或使用不包含空格的路径

### 问题 7: 中文字符显示乱码

**解决方案**:
```powershell
# 设置 PowerShell 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

---

## 🎯 快速命令参考

### PowerShell

```powershell
# 克隆项目
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server

# 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
playwright install

# 配置
copy examples\config.example.json config.json
notepad config.json

# 测试
python tests\test_google_api_direct.py
```

### CMD

```cmd
git clone https://github.com/zxkjack123/crawl4ai-mcp-server.git
cd crawl4ai-mcp-server
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install
copy examples\config.example.json config.json
notepad config.json
python tests\test_google_api_direct.py
```

---

## 📚 相关文档

- [快速参考](../QUICK_REFERENCE.md)
- [配置说明](../examples/CONFIG.md)
- [VS Code 集成](VSCODE_INTEGRATION.md)
- [Google API 设置](GOOGLE_API_SETUP_CN.md)
- [项目结构](../PROJECT_STRUCTURE.md)

---

## 💡 小贴士

1. **使用 PowerShell 而非 CMD**: PowerShell 功能更强大
2. **使用 VS Code**: 内置终端支持更好
3. **定期更新**: `git pull origin main` 获取最新代码
4. **使用虚拟环境**: 避免依赖冲突
5. **阅读错误信息**: 大部分问题都有明确的错误提示

---

## 🆘 获取帮助

- 📖 查看 [docs/](.) 目录获取完整文档
- 🐛 遇到问题？查看本文档的"常见问题"部分
- 💬 提交 Issue: https://github.com/zxkjack123/crawl4ai-mcp-server/issues

---

**祝您在 Windows 上使用愉快！** 🎉

---

*最后更新: 2025-10-11*  
*适用系统: Windows 10/11*
