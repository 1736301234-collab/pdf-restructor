@echo off
chcp 65001 >nul
title 推送到GitHub - 1736301234-collab/pdf-restructor
cls

echo ==========================================
echo    推送到GitHub
echo    仓库: 1736301234-collab/pdf-restructor
echo ==========================================
echo.

cd /d "C:\pdf_restructor"

echo [*] 检查Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [X] Git未安装！请先安装Git
    pause
    exit /b 1
)
echo [OK] Git已安装

echo.
echo [*] 初始化Git仓库...
if not exist ".git" (
    git init
    echo [OK] 已初始化
) else (
    echo [OK] 已存在
)

echo.
echo [*] 配置用户信息...
git config user.name "PDF Restructor"
git config user.email "pdf@restructor.dev"
echo [OK] 已配置

echo.
echo [*] 添加远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/1736301234-collab/pdf-restructor.git
git remote -v
echo [OK] 远程仓库已添加

echo.
echo [*] 添加文件到Git...
git add .
echo [OK] 文件已添加

echo.
echo [*] 提交代码...
git commit -m "Initial commit: PDF to EPUB converter with OCR support and smart layout"
echo [OK] 已提交

echo.
echo [*] 推送到GitHub...
git branch -M main
git push -u origin main
if errorlevel 1 (
    echo.
    echo [!] 推送到main失败，尝试master分支...
    git branch -M master
    git push -u origin master
)

echo.
echo ==========================================
echo    推送完成！
echo ==========================================
echo.
echo 代码已推送到:
echo https://github.com/1736301234-collab/pdf-restructor
echo.
echo 启用GitHub Pages:
echo 1. 访问 https://github.com/1736301234-collab/pdf-restructor/settings/pages
echo 2. Source: Deploy from a branch
echo 3. Branch: main, Folder: /docs
echo 4. 点击 Save
echo.
echo 网页将部署到:
echo https://1736301234-collab.github.io/pdf-restructor
echo.

pause