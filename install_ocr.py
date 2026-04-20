#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR安装脚本
自动安装和配置OCR引擎
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path


def run_command(cmd, description=""):
    """运行命令并显示结果"""
    if description:
        print(f"\n[执行] {description}")
        print(f"命令: {cmd}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.returncode != 0:
        print(f"[警告] 命令执行失败: {result.stderr}")
        return False
    
    return True


def check_python():
    """检查Python版本"""
    print("="*60)
    print("检查Python环境...")
    print("="*60)
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[错误] Python版本过低: {version.major}.{version.minor}")
        print("需要 Python 3.8 或更高版本")
        return False
    
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_python_packages():
    """安装Python包"""
    print("\n" + "="*60)
    print("安装Python OCR库...")
    print("="*60)
    
    packages = [
        ("pytesseract", "pytesseract"),
        ("Pillow", "Pillow"),
        ("numpy", "numpy"),
        ("easyocr", "easyocr（可选，需要较长时间下载模型）"),
        ("paddleocr", "paddleocr（可选，中文效果好）"),
    ]
    
    # 使用清华镜像加速
    pip_cmd = [sys.executable, "-m", "pip", "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    
    for package, desc in packages:
        print(f"\n[安装] {desc}")
        result = subprocess.run(
            pip_cmd + [package],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[OK] {package} 安装成功")
        else:
            print(f"[警告] {package} 安装失败")
            print(f"错误: {result.stderr[:200]}")
    
    return True


def download_file(url, output_path, description=""):
    """下载文件"""
    if description:
        print(f"[下载] {description}")
    
    try:
        urllib.request.urlretrieve(url, output_path)
        return True
    except urllib.error.URLError as e:
        print(f"[错误] 下载失败: {e}")
        return False
    except Exception as e:
        print(f"[错误] 下载异常: {e}")
        return False


def install_tesseract():
    """安装Tesseract OCR"""
    print("\n" + "="*60)
    print("安装Tesseract OCR...")
    print("="*60)
    
    # 检查是否已安装
    result = subprocess.run(
        ["tesseract", "--version"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Tesseract已安装")
        print(result.stdout[:200])
        return True
    
    print("Tesseract未安装，需要手动安装")
    print("\n请按以下步骤操作：")
    print("1. 访问: https://github.com/UB-Mannheim/tesseract/wiki")
    print("2. 下载 Windows 安装包（64位）")
    print("3. 运行安装程序，注意：")
    print("   - 安装路径保持默认: C:\\Program Files\\Tesseract-OCR")
    print("   - 在'Language data'页面，勾选 'Chinese (Simplified)'")
    print("   - 勾选 'Chinese (Traditional)'")
    print("4. 安装完成后，将安装路径添加到系统环境变量PATH")
    print("5. 重新打开命令行窗口")
    print("\n或者直接下载：")
    print("https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe")
    
    # 询问是否自动下载
    print("\n是否自动下载安装程序？(需要管理员权限) [Y/N]", end=" ")
    choice = input().strip().lower()
    
    if choice == 'y':
        installer_url = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe"
        temp_path = os.path.join(os.environ.get('TEMP', '.'), 'tesseract_installer.exe')
        
        print("正在下载安装程序...")
        if download_file(installer_url, temp_path, "Tesseract安装程序"):
            print(f"下载完成: {temp_path}")
            print("正在启动安装向导...")
            os.startfile(temp_path)
            print("\n请完成安装后按Enter继续...")
            input()
        else:
            print("[错误] 自动下载失败，请手动下载安装")
    
    return False


def install_chinese_data():
    """安装中文语言包"""
    print("\n" + "="*60)
    print("安装中文语言包...")
    print("="*60)
    
    # 查找tessdata目录
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tessdata",
        r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
    ]
    
    tessdata_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            tessdata_dir = path
            break
    
    if not tessdata_dir:
        print("[警告] 未找到tessdata目录，跳过语言包安装")
        print("请确保Tesseract已正确安装")
        return False
    
    print(f"[OK] 找到tessdata目录: {tessdata_dir}")
    
    # 语言包文件
    lang_files = [
        ("chi_sim.traineddata", "简体中文"),
        ("chi_sim_vert.traineddata", "简体中文竖排"),
        ("chi_tra.traineddata", "繁体中文"),
        ("eng.traineddata", "英文"),
    ]
    
    base_url = "https://github.com/tesseract-ocr/tessdata/raw/main/"
    
    for filename, desc in lang_files:
        filepath = os.path.join(tessdata_dir, filename)
        
        if os.path.exists(filepath):
            print(f"[OK] {desc} 语言包已存在")
            continue
        
        url = base_url + filename
        print(f"[下载] {desc} 语言包...")
        
        if download_file(url, filepath, desc):
            print(f"[OK] {desc} 下载完成")
        else:
            print(f"[警告] {desc} 下载失败")
    
    return True


def test_installation():
    """测试安装"""
    print("\n" + "="*60)
    print("测试安装...")
    print("="*60)
    
    # 测试pytesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"[OK] pytesseract: {version}")
    except Exception as e:
        print(f"[警告] pytesseract: {e}")
    
    # 测试EasyOCR
    try:
        import easyocr
        print("[OK] EasyOCR 已安装")
    except Exception as e:
        print(f"[信息] EasyOCR: {e}")
    
    # 测试PaddleOCR
    try:
        import paddleocr
        print("[OK] PaddleOCR 已安装")
    except Exception as e:
        print(f"[信息] PaddleOCR: {e}")
    
    return True


def print_usage():
    """打印使用方法"""
    print("\n" + "="*60)
    print("安装完成！")
    print("="*60)
    print("\n现在你可以使用OCR功能转换扫描版PDF了：")
    print("\n  python test_with_user_pdf.py \"你的PDF路径\" --ocr")
    print("\n或者使用图形界面：")
    print("\n  python gui_converter.py")
    print("\n在图形界面中勾选'OCR'选项即可")
    print("="*60)


def main():
    """主函数"""
    print("="*60)
    print("OCR引擎安装助手")
    print("="*60)
    print()
    
    # 检查Python
    if not check_python():
        print("\n[错误] Python检查失败，无法继续")
        return 1
    
    # 安装Python包
    install_python_packages()
    
    # 安装Tesseract
    install_tesseract()
    
    # 安装中文语言包
    install_chinese_data()
    
    # 测试安装
    test_installation()
    
    # 打印使用方法
    print_usage()
    
    input("\n按Enter键退出...")
    return 0


if __name__ == "__main__":
    sys.exit(main())