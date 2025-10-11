@echo off
REM Crawl4AI MCP Server - Windows CMD 安装脚本
REM 自动化安装和配置流程

chcp 65001 >nul
echo ========================================
echo   Crawl4AI MCP Server - Windows 安装
echo ========================================
echo.

REM 检查 Python
echo 🔍 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python！
    echo 请访问 https://www.python.org/downloads/windows/ 下载并安装 Python 3.9+
    pause
    exit /b 1
)
echo ✅ Python 已安装
echo.

REM 检查虚拟环境是否已存在
if exist .venv (
    echo ⚠️  虚拟环境已存在
    set /p response="是否删除并重新创建? (y/N): "
    if /i "%response%"=="y" (
        echo 🗑️  删除旧的虚拟环境...
        rmdir /s /q .venv
    ) else (
        echo 保留现有虚拟环境
        goto :skip_venv
    )
)

REM 创建虚拟环境
echo 📦 创建虚拟环境...
python -m venv .venv
if %errorlevel% neq 0 (
    echo ❌ 创建虚拟环境失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境创建成功

:skip_venv
echo.

REM 激活虚拟环境
echo 🔌 激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 激活虚拟环境失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境已激活
echo.

REM 升级 pip
echo ⬆️  升级 pip...
python -m pip install --upgrade pip -q
echo ✅ pip 升级成功
echo.

REM 安装依赖
echo 📥 安装项目依赖...
echo    这可能需要几分钟时间...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    echo 请检查网络连接或尝试使用国内镜像：
    echo pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    pause
    exit /b 1
)
echo ✅ 依赖安装成功
echo.

REM 安装 Playwright 浏览器
echo 🌐 安装 Playwright 浏览器...
echo    这将下载约 300-400 MB 数据...
playwright install
if %errorlevel% neq 0 (
    echo ⚠️  Playwright 安装失败
    echo 如果网络较慢，可以设置镜像：
    echo set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
    echo playwright install
)
echo ✅ Playwright 浏览器安装成功
echo.

REM 检查配置文件
if not exist config.json (
    echo ⚙️  配置文件不存在，创建示例配置...
    copy examples\config.example.json config.json >nul
    echo ✅ 已创建 config.json
    echo.
    echo ⚠️  请编辑 config.json 填入您的 API 凭据：
    echo    notepad config.json
    echo.
    echo 📖 获取 API Key 的方法请参考：
    echo    docs\GOOGLE_API_SETUP_CN.md
) else (
    echo ✅ 配置文件已存在
)

echo.
echo ========================================
echo   🎉 安装完成！
echo ========================================
echo.
echo 📝 下一步：
echo    1. 编辑配置文件：notepad config.json
echo    2. 运行测试：run_tests.bat
echo    3. 查看文档：explorer docs\
echo.
echo 🚀 快速测试命令：
echo    python tests\test_google_api_direct.py
echo.
echo 💡 激活虚拟环境：
echo    .venv\Scripts\activate.bat
echo.
echo 📚 完整文档：
echo    https://github.com/zxkjack123/crawl4ai-mcp-server
echo.
pause
