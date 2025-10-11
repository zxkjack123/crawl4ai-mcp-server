@echo off
REM 快速激活虚拟环境

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
    echo.
    echo 💡 常用命令：
    echo    python tests\test_google_api_direct.py  - 测试 Google API
    echo    python tests\test_comprehensive.py      - 完整测试
    echo    notepad config.json                     - 编辑配置
    echo    deactivate                              - 退出虚拟环境
    echo.
) else (
    echo ❌ 虚拟环境不存在！
    echo 请先运行 setup.bat 创建虚拟环境
    pause
)
