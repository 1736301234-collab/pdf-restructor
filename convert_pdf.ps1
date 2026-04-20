# PDF转EPUB转换脚本 (PowerShell)
# 使用方法: .\convert_pdf.ps1 -InputPath "path\to\file.pdf"

param(
    [Parameter(Mandatory=$true, HelpMessage="PDF文件路径")]
    [string]$InputPath,
    
    [Parameter(HelpMessage="输出EPUB路径")]
    [string]$OutputPath = $null,
    
    [Parameter(HelpMessage="启用OCR")]
    [switch]$EnableOCR = $true,
    
    [Parameter(HelpMessage="启用AI分析")]
    [switch]$EnableAI = $true,
    
    [Parameter(HelpMessage="OCR分辨率")]
    [int]$OCRDPI = 300
)

# 设置编码
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    PDF转EPUB转换器" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查文件
if (-not (Test-Path $InputPath)) {
    Write-Host "[错误] 文件不存在: $InputPath" -ForegroundColor Red
    exit 1
}

$pdfFile = Get-Item $InputPath
if ($pdfFile.Extension -ne ".pdf") {
    Write-Host "[错误] 文件必须是PDF格式" -ForegroundColor Red
    exit 1
}

# 确定输出路径
if (-not $OutputPath) {
    $OutputPath = Join-Path $pdfFile.DirectoryName ($pdfFile.BaseName + "_converted.epub")
}

Write-Host "输入文件: $($pdfFile.FullName)" -ForegroundColor White
Write-Host "输出文件: $OutputPath" -ForegroundColor White
Write-Host "OCR模式: $(if ($EnableOCR) { '启用' } else { '禁用' })" -ForegroundColor Yellow
Write-Host "AI分析: $(if ($EnableAI) { '启用' } else { '禁用' })" -ForegroundColor Yellow
Write-Host "------------------------------------------" -ForegroundColor Gray

# 构建Python命令
$scriptPath = Join-Path $PSScriptRoot "test_with_user_pdf.py"
$arguments = @(
    $scriptPath,
    "`"$($pdfFile.FullName)`""
)

if ($EnableOCR) { $arguments += "--ocr" }
if ($EnableAI) { $arguments += "--ai" }
if ($OutputPath) { $arguments += "--output"; $arguments += "`"$OutputPath`"" }

# 执行转换
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[错误] 未找到Python，请先安装Python" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "开始转换..." -ForegroundColor Green
Write-Host ""

& $pythonCmd.Path @arguments

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "转换成功完成！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    
    if (Test-Path $OutputPath) {
        $fileSize = (Get-Item $OutputPath).Length / 1KB
        Write-Host "文件大小: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Cyan
        
        # 询问是否打开文件位置
        $openLocation = Read-Host "是否打开文件所在位置？(Y/N)"
        if ($openLocation -eq "Y" -or $openLocation -eq "y") {
            Start-Process "explorer.exe" -ArgumentList "/select,$OutputPath"
        }
    }
} else {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "转换失败" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
}

Write-Host ""
Read-Host "按Enter键退出"