# Crawl4AI MCP Server - 测试运行脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Crawl4AI MCP Server - 运行测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 激活虚拟环境
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "🔌 激活虚拟环境..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
    Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "❌ 虚拟环境不存在！请先运行 setup.ps1" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 检查配置文件
if (-not (Test-Path "config.json")) {
    Write-Host "❌ 配置文件不存在！" -ForegroundColor Red
    Write-Host "请先复制并配置：" -ForegroundColor Yellow
    Write-Host "   copy examples\config.example.json config.json" -ForegroundColor White
    Write-Host "   notepad config.json" -ForegroundColor White
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试 1: Google API 直接测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python tests\test_google_api_direct.py
$test1Result = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试 2: 双引擎测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python tests\test_dual_engines.py
$test2Result = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试 3: 综合功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python tests\test_comprehensive.py
$test3Result = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试结果总结" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($test1Result -eq 0) {
    Write-Host "✅ Google API 测试: 通过" -ForegroundColor Green
} else {
    Write-Host "❌ Google API 测试: 失败" -ForegroundColor Red
}

if ($test2Result -eq 0) {
    Write-Host "✅ 双引擎测试: 通过" -ForegroundColor Green
} else {
    Write-Host "❌ 双引擎测试: 失败" -ForegroundColor Red
}

if ($test3Result -eq 0) {
    Write-Host "✅ 综合功能测试: 通过" -ForegroundColor Green
} else {
    Write-Host "❌ 综合功能测试: 失败" -ForegroundColor Red
}

Write-Host ""

if ($test1Result -eq 0 -and $test2Result -eq 0 -and $test3Result -eq 0) {
    Write-Host "🎉 所有测试通过！系统运行正常！" -ForegroundColor Green
} else {
    Write-Host "⚠️  部分测试失败，请检查配置和网络连接" -ForegroundColor Yellow
    Write-Host "📖 查看文档: docs\WINDOWS_INSTALLATION.md" -ForegroundColor Cyan
}

Write-Host ""
