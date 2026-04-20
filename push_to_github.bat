@echo off
chcp 65001 >nul
title 推送到GitHub
cls

echo ==========================================
echo    推送到GitHub脚本
echo ==========================================
echo.

set "PROJECT_DIR=C:\pdf_restructor"
cd /d "%PROJECT_DIR%"

echo [1/6] 检查Git是否安装...
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git未安装！
    echo 请访问 https://git-scm.com/download/win 下载安装
    pause
    exit /b 1
)
echo [OK] Git已安装

echo.
echo [2/6] 初始化Git仓库...
if not exist ".git" (
    git init
    echo [OK] Git仓库已初始化
) else (
    echo [OK] Git仓库已存在
)

echo.
echo [3/6] 配置Git用户信息...
echo.
echo 请输入你的GitHub用户名:
set /p GIT_USERNAME="用户名: "
echo 请输入你的GitHub邮箱:
set /p GIT_EMAIL="邮箱: "

git config user.name "%GIT_USERNAME%"
git config user.email "%GIT_EMAIL%"
echo [OK] Git用户信息已配置

echo.
echo [4/6] 添加远程仓库...
echo.
echo 请输入你的GitHub用户名（用于仓库地址）:
set /p GITHUB_USER="GitHub用户名: "

if exist ".git\config" (
    git remote remove origin 2>nul
)
git remote add origin https://github.com/%GITHUB_USER%/pdf-restructor.git
echo [OK] 远程仓库已添加

echo.
echo [5/6] 提交代码...
git add .
git commit -m "Initial commit: PDF to EPUB converter with OCR and smart layout"
echo [OK] 代码已提交

echo.
echo [6/6] 推送到GitHub...
echo.
echo 正在推送到GitHub...
git push -u origin main
if errorlevel 1 (
    echo.
    echo [警告] 推送到main分支失败，尝试master分支...
    git push -u origin master
)

echo.
echo ==========================================
echo    完成！
echo ==========================================
echo.
echo 你的项目已推送到:
echo https://github.com/%GITHUB_USER%/pdf-restructor
echo.
echo 启用GitHub Pages:
echo 1. 访问 https://github.com/%GITHUB_USER%/pdf-restructor/settings/pages
echo 2. Source 选择 "Deploy from a branch"
echo 3. Branch 选择 main, 文件夹选择 /docs
echo 4. 点击 Save
echo.
echo 网页地址:
echo https://%GITHUB_USER%.github.io/pdf-restructor
echo.

pause