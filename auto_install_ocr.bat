@echo off
:: 自动安装OCR - 一键完成所有操作
:: 以管理员权限运行

%1 mshta vbscript:CreateObject("Shell.Application").ShellExecute("cmd.exe","/c %~s0 ::","","runas",1)(window.close)&&exit

cd /d "%~dp0"
chcp 65001 >nul
cls

echo ============================================
echo    自动安装OCR引擎
echo ============================================
echo.

:: 创建安装目录
set "INSTALL_DIR=%USERPROFILE%\OCR_Tools"
mkdir "%INSTALL_DIR%" 2>nul
cd /d "%INSTALL_DIR%"

echo [1/4] 安装Python OCR库...
pip install pytesseract Pillow numpy -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
if errorlevel 1 (
    pip install pytesseract Pillow numpy --quiet
)

echo [2/4] 下载Tesseract便携版...
echo 正在从GitHub下载...

:: 使用PowerShell下载
powershell -Command "
    $url = 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.1.20230401/tesseract-ocr-w64-setup-v5.3.1.20230401.exe'
    $output = '%INSTALL_DIR%\tesseract.exe'
    
    if (-not (Test-Path $output)) {
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Write-Host '下载完成'
        } catch {
            Write-Host 'GitHub下载失败，尝试镜像...'
            $mirrorUrl = 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe'
            try {
                Invoke-WebRequest -Uri $mirrorUrl -OutFile $output -UseBasicParsing
                Write-Host '下载完成'
            } catch {
                exit 1
            }
        }
    } else {
        Write-Host '文件已存在'
    }
"

if not exist "%INSTALL_DIR%\tesseract.exe" (
    echo [错误] 下载失败
    echo 请手动下载：
    echo https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)

echo [3/4] 运行安装程序...
echo 请在安装向导中：
echo - 点击"Next"接受协议
echo - 点击"Next"选择安装组件（建议全选）
echo - 点击"Install"开始安装
echo - 安装完成后点击"Finish"
echo.
pause

start /wait "%INSTALL_DIR%\tesseract.exe"

echo.
echo [4/4] 配置环境变量...

:: 查找安装路径
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=C:\Program Files\Tesseract-OCR"
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=C:\Program Files (x86)\Tesseract-OCR"
) else (
    echo 请输入Tesseract安装路径（例如 C:\Program Files\Tesseract-OCR）：
    set /p TESS_PATH="路径: "
)

:: 添加到环境变量
echo 正在添加到系统PATH...
setx PATH "%PATH%;%TESS_PATH%" /M >nul 2>&1

:: 设置TESSDATA_PREFIX
setx TESSDATA_PREFIX "%TESS_PATH%\tessdata" /M >nul 2>&1

echo.
echo ============================================
echo    安装完成！
echo ============================================
echo.
echo Tesseract已安装到: %TESS_PATH%
echo.
echo 请重新打开命令行窗口，然后运行：
echo   cd C:\pdf_restructor
echo   python test_with_user_pdf.py "PDF路径" --ocr
echo.

pause