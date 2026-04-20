@echo off
chcp 65001 >nul
title OCR安装助手
cls

echo ==========================================
echo    OCR安装助手 - 快速版
echo ==========================================
echo.
echo 这将安装OCR支持，用于扫描版PDF转换
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python
    echo 请先安装Python 3.8+：
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python已检测到
echo.

:: 安装Python包
echo [*] 正在安装Python OCR库（使用清华镜像加速）
echo.

pip install pytesseract Pillow numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] 安装失败，尝试使用默认镜像...
    pip install pytesseract Pillow numpy
)

echo.
echo [OK] Python库安装完成
echo.

:: 检查Tesseract
echo [*] 检查Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [警告] Tesseract未安装
echo.
    echo 请手动安装Tesseract：
    echo 1. 下载：https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. 安装时勾选"Chinese (Simplified)"语言包
    echo 3. 添加安装路径到系统环境变量
    echo.
    echo 或者使用这个直接下载链接：
    echo https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe
    echo.
    echo 安装完成后，请重新运行此脚本
    pause
    exit /b 1
)

echo [OK] Tesseract已安装
echo.

:: 检查中文语言包
echo [*] 检查中文语言包...
tesseract --list-langs 2>nul | findstr "chi_sim" >nul
if errorlevel 1 (
    echo [警告] 中文语言包未安装
    echo 正在自动下载中文语言包...
    
    :: 检查tessdata目录
    if not exist "C:\Program Files\Tesseract-OCR\tessdata" (
        mkdir "C:\Program Files\Tesseract-OCR\tessdata" 2>nul
    )
    
    :: 下载中文训练数据
    powershell -Command "& {
        $url = 'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata'
        $output = 'C:\Program Files\Tesseract-OCR\tessdata\chi_sim.traineddata'
        
        if (-not (Test-Path $output)) {
            try {
                Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
                Write-Host '[OK] 中文语言包下载完成'
            } catch {
                Write-Host '[错误] 下载失败，请手动下载'
                Write-Host '下载地址: https://github.com/tesseract-ocr/tessdata'
            }
        } else {
            Write-Host '[OK] 中文语言包已存在'
        }
    }"
) else (
    echo [OK] 中文语言包已安装
)

echo.
echo ==========================================
echo    安装完成！
echo ==========================================
echo.
echo 你现在可以使用OCR功能了：
echo.
echo   python test_with_user_pdf.py "PDF路径" --ocr
echo.
echo 或者使用图形界面，勾选'OCR'选项
echo.

pause