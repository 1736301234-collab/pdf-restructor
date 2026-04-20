# GitHub 推送指南

## 🚀 一键推送到GitHub

### 步骤1：初始化Git仓库（在项目目录）

```bash
cd C:\pdf_restructor

# 初始化Git仓库
git init

# 配置用户信息（修改成你的名字和邮箱）
git config user.name "你的名字"
git config user.email "your.email@example.com"
```

### 步骤2：在GitHub创建仓库

1. 访问 https://github.com/new
2. 仓库名：`pdf-restructor`
3. 描述：`智能PDF转EPUB工具 - 支持OCR和智能排版`
4. 选择 **Public**（开源）
5. **不要** 勾选 "Initialize this repository with a README"
6. 点击 **Create repository**

### 步骤3：连接远程仓库

```bash
# 添加远程仓库（替换yourusername为你的GitHub用户名）
git remote add origin https://github.com/yourusername/pdf-restructor.git

# 验证连接
git remote -v
```

### 步骤4：提交代码

```bash
# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: PDF to EPUB converter with OCR support"

# 推送到GitHub
git push -u origin main
```

## 📋 完整命令（复制粘贴）

```bash
cd C:\pdf_restructor
git init
git config user.name "你的名字"
git config user.email "your.email@example.com"
git remote add origin https://github.com/yourusername/pdf-restructor.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

## 🔧 常见问题

### 需要登录？
当运行 `git push` 时，会弹出GitHub登录窗口，输入你的GitHub账号和密码即可。

### 如果显示 "fatal: not a git repository"
说明不在git仓库目录，确保在 `C:\pdf_restructor` 目录运行。

### 如果推送失败
```bash
# 尝试强制推送（谨慎使用）
git push -u origin main --force

# 或者先拉取再推送
git pull origin main --rebase
git push origin main
```

### 分支名可能是master
如果显示错误，尝试：
```bash
git push -u origin master
```

## 🌐 启用GitHub Pages

推送成功后，启用GitHub Pages展示网页：

1. 打开 https://github.com/yourusername/pdf-restructor
2. 点击 **Settings**（设置）
3. 左侧菜单选择 **Pages**
4. **Source** 选择 **Deploy from a branch**
5. **Branch** 选择 **main**，文件夹选择 **/docs**
6. 点击 **Save**

等待几分钟后，访问：
```
https://yourusername.github.io/pdf-restructor
```

## 📚 Git常用命令

```bash
# 查看状态
git status

# 查看提交历史
git log --oneline

# 添加文件
git add 文件名

# 提交更改
git commit -m "提交说明"

# 推送到GitHub
git push

# 拉取更新
git pull
```

## ✅ 成功标志

推送成功后，访问：
- 代码：https://github.com/yourusername/pdf-restructor
- 网页：https://yourusername.github.io/pdf-restructor

## 🆘 需要帮助？

如果遇到问题：
1. 检查Git是否安装：`git --version`
2. 检查远程仓库：`git remote -v`
3. 检查当前分支：`git branch`
4. 查看详细错误：`git push -v origin main`
