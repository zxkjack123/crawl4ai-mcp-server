# Crawl4AI MCP Server - Windows PowerShell 安装脚本
# 自动化安装和配置流程

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Crawl4AI MCP Server - Windows 安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "🔍 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python！" -ForegroundColor Red
    Write-Host "请访问 https://www.python.org/downloads/windows/ 下载并安装 Python 3.9+" -ForegroundColor Yellow
    exit 1
}

# 检查 Python 版本
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-Host "❌ Python 版本过低（需要 3.9+）" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# 检查虚拟环境是否已存在
if (Test-Path ".venv") {
    Write-Host "⚠️  虚拟环境已存在" -ForegroundColor Yellow
    $response = Read-Host "是否删除并重新创建? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "🗑️  删除旧的虚拟环境..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
    } else {
        Write-Host "保留现有虚拟环境" -ForegroundColor Green
        $skipVenv = $true
    }
}

# 创建虚拟环境
if (-not $skipVenv) {
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 创建虚拟环境失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
}

Write-Host ""

# 激活虚拟环境
Write-Host "🔌 激活虚拟环境..." -ForegroundColor Yellow
$activateScript = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "❌ 找不到激活脚本" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 升级 pip
Write-Host "⬆️  升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ pip 升级成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  pip 升级失败，继续安装..." -ForegroundColor Yellow
}

Write-Host ""

# 安装依赖
Write-Host "📥 安装项目依赖..." -ForegroundColor Yellow
Write-Host "   这可能需要几分钟时间..." -ForegroundColor Gray

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "❌ 依赖安装失败" -ForegroundColor Red
    Write-Host "请检查网络连接或尝试使用国内镜像：" -ForegroundColor Yellow
    Write-Host "pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple" -ForegroundColor Gray
    exit 1
}

Write-Host ""

# 安装 Playwright 浏览器
Write-Host "🌐 安装 Playwright 浏览器..." -ForegroundColor Yellow
Write-Host "   这将下载约 300-400 MB 数据..." -ForegroundColor Gray

playwright install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Playwright 浏览器安装成功" -ForegroundColor Green
} else {
    Write-Host "⚠️  Playwright 安装失败" -ForegroundColor Yellow
    Write-Host "如果网络较慢，可以设置镜像：" -ForegroundColor Gray
    Write-Host "`$env:PLAYWRIGHT_DOWNLOAD_HOST='https://npmmirror.com/mirrors/playwright/'" -ForegroundColor Gray
    Write-Host "playwright install" -ForegroundColor Gray
}

Write-Host ""

# 检查配置文件
if (-not (Test-Path "config.json")) {
    Write-Host "⚙️  配置文件不存在，创建示例配置..." -ForegroundColor Yellow
    Copy-Item "examples\config.example.json" "config.json"
    Write-Host "✅ 已创建 config.json" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  请编辑 config.json 填入您的 API 凭据：" -ForegroundColor Yellow
    Write-Host "   notepad config.json" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📖 获取 API Key 的方法请参考：" -ForegroundColor Cyan
    Write-Host "   docs\GOOGLE_API_SETUP_CN.md" -ForegroundColor Gray
} else {
    Write-Host "✅ 配置文件已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 下一步：" -ForegroundColor Yellow
Write-Host "   1. 编辑配置文件：notepad config.json" -ForegroundColor White
Write-Host "   2. 运行测试：.\run_tests.ps1" -ForegroundColor White
Write-Host "   3. 查看文档：explorer docs\" -ForegroundColor White
Write-Host ""
Write-Host "🚀 快速测试命令：" -ForegroundColor Yellow
Write-Host "   python tests\test_google_api_direct.py" -ForegroundColor White
Write-Host ""
Write-Host "💡 激活虚拟环境：" -ForegroundColor Yellow
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "📚 完整文档：" -ForegroundColor Yellow
Write-Host "   https://github.com/zxkjack123/crawl4ai-mcp-server" -ForegroundColor White
Write-Host ""
