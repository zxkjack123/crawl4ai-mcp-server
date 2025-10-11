@echo off
REM Crawl4AI MCP Server - 测试运行脚本 (CMD)

chcp 65001 >nul
echo ========================================
echo   Crawl4AI MCP Server - 运行测试
echo ========================================
echo.

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    echo 🔌 激活虚拟环境...
    call .venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ❌ 虚拟环境不存在！请先运行 setup.bat
    pause
    exit /b 1
)

echo.

REM 检查配置文件
if not exist config.json (
    echo ❌ 配置文件不存在！
    echo 请先复制并配置：
    echo    copy examples\config.example.json config.json
    echo    notepad config.json
    pause
    exit /b 1
)

echo ========================================
echo   测试 1: Google API 直接测试
echo ========================================
python tests\test_google_api_direct.py
set test1=%errorlevel%

echo.
echo ========================================
echo   测试 2: 双引擎测试
echo ========================================
python tests\test_dual_engines.py
set test2=%errorlevel%

echo.
echo ========================================
echo   测试 3: 综合功能测试
echo ========================================
python tests\test_comprehensive.py
set test3=%errorlevel%

echo.
echo ========================================
echo   测试结果总结
echo ========================================

if %test1% equ 0 (
    echo ✅ Google API 测试: 通过
) else (
    echo ❌ Google API 测试: 失败
)

if %test2% equ 0 (
    echo ✅ 双引擎测试: 通过
) else (
    echo ❌ 双引擎测试: 失败
)

if %test3% equ 0 (
    echo ✅ 综合功能测试: 通过
) else (
    echo ❌ 综合功能测试: 失败
)

echo.

if %test1% equ 0 if %test2% equ 0 if %test3% equ 0 (
    echo 🎉 所有测试通过！系统运行正常！
) else (
    echo ⚠️  部分测试失败，请检查配置和网络连接
    echo 📖 查看文档: docs\WINDOWS_INSTALLATION.md
)

echo.
pause
