@echo off
chcp 65001 >nul
cls

echo ==========================================
echo    PDF转EPUB转换器 - 快速启动
echo ==========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python已检测到
echo.

:: 检查依赖
echo [步骤1/3] 检查依赖...
python -c "import fitz" 2>nul
if errorlevel 1 (
    echo [*] 正在安装依赖...
    pip install -r requirements.txt --quiet
)
echo [✓] 依赖检查完成
echo.

:: 启动GUI
echo [步骤2/3] 启动图形界面...
echo.
python gui_converter.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败，尝试命令行模式...
    echo.
    echo [步骤3/3] 启动命令行模式...
    echo 请拖拽PDF文件到命令行窗口，然后按回车
    echo.
    set /p pdf_file="PDF文件路径: "
    if exist "%pdf_file%" (
        python test_with_user_pdf.py "%pdf_file%" --ocr --ai
    ) else (
        echo [错误] 文件不存在！
    )
)

echo.
echo ==========================================
echo 按任意键退出...
==========================================
pause >nul