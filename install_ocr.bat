@echo off
chcp 65001 >nul
cls

echo ==========================================
echo    OCR引擎安装助手
echo ==========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [提示] 需要管理员权限来安装Tesseract
    echo 正在以管理员权限重新启动...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

echo [步骤 1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python已安装

echo.
echo [步骤 2/4] 安装Python OCR库...
echo.

echo 正在安装 pytesseract...
pip install pytesseract -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo 正在安装 Pillow（图像处理）...
pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo 正在安装 EasyOCR（可选，推荐）...
echo 注意: EasyOCR下载模型需要较长时间，请耐心等待...
pip install easyocr -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo 正在安装 PaddleOCR（可选，中文效果好）...
pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

echo [步骤 3/4] 下载并安装 Tesseract OCR...
echo.
echo 正在检查是否已安装...
tesseract --version >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Tesseract已安装
    goto :TESSERACT_DONE
)

echo 正在下载 Tesseract 安装程序...
echo 下载地址: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe
echo.

:: 使用PowerShell下载
powershell -Command "& {
    $url = 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe'
    $output = '%TEMP%\tesseract_installer.exe'
    
    Write-Host '正在下载安装程序...'
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        Write-Host '下载完成'
    } catch {
        Write-Host '下载失败，请手动下载安装'
        Write-Host '下载地址: https://github.com/UB-Mannheim/tesseract/wiki'
        exit 1
    }
}"

if errorlevel 1 (
    echo.
    echo [警告] 自动下载失败
    echo 请手动下载安装：
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo 安装时请注意：
    echo 1. 勾选"Additional language data" ^(中文数据^)
    echo 2. 记住安装路径（默认: C:\Program Files\Tesseract-OCR）
    echo 3. 安装完成后需要重启命令行窗口
    pause
    exit /b 1
)

echo.
echo 正在安装 Tesseract...
echo 安装向导即将启动，请按提示操作：
echo  - 选择安装路径（建议保持默认）
echo  - 在"Language data"页面，勾选"Chinese (Simplified)"和"Chinese (Traditional)"
echo.
pause

start /wait %TEMP%\tesseract_installer.exe

:: 添加到环境变量
echo.
echo 正在配置环境变量...
setx PATH "%PATH%;C:\Program Files\Tesseract-OCR" /M >nul 2>&1

:TESSERACT_DONE

echo.
echo [步骤 4/4] 安装中文语言包...
echo.

:: 检查中文语言包
echo 正在检查中文语言包...
tesseract --list-langs 2>nul | findstr "chi_sim" >nul
if %errorlevel% neq 0 (
    echo 正在下载中文语言包...
    
    :: 创建tessdata目录
    if not exist "C:\Program Files\Tesseract-OCR\tessdata" (
        mkdir "C:\Program Files\Tesseract-OCR\tessdata"
    )
    
    :: 下载中文训练数据
    powershell -Command "& {
        $urls = @(
            'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata',
            'https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim_vert.traineddata',
            'https://github.com/tesseract-ocr/tessdata/raw/main/chi_tra.traineddata'
        )
        
        $tessdataDir = 'C:\Program Files\Tesseract-OCR\tessdata'
        
        foreach ($url in $urls) {
            $fileName = Split-Path $url -Leaf
            $outputPath = Join-Path $tessdataDir $fileName
            
            if (-not (Test-Path $outputPath)) {
                Write-Host "正在下载 $fileName..."
                try {
                    Invoke-WebRequest -Uri $url -OutFile $outputPath -UseBasicParsing
                    Write-Host "$fileName 下载完成"
                } catch {
                    Write-Host "$fileName 下载失败"
                }
            }
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
echo 已安装：
echo   [OK] pytesseract (Python库)
echo   [OK] EasyOCR (Python库)
echo   [OK] PaddleOCR (Python库)
echo   [OK] Tesseract OCR (引擎)
echo   [OK] 中文语言包
echo.
echo 请重新打开命令行窗口，然后运行：
echo   python test_with_user_pdf.py "你的PDF路径" --ocr
echo.
pause