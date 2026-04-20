"""
用户PDF测试脚本

这个脚本用于测试用户提供的PDF文件

使用方法:
    python test_with_user_pdf.py "E:\\path\\to\\your\\file.pdf"
    python test_with_user_pdf.py "E:\\path\\to\\your\\file.pdf" --ocr --ai
    python test_with_user_pdf.py "E:\\path\\to\\your\\file.pdf" --output "D:\\output\\result.epub"
"""

import sys
import os
import argparse
from pathlib import Path

# 确保可以导入本包
sys.path.insert(0, str(Path(__file__).parent))

from core.enhanced_pipeline import EnhancedConversionPipeline, EnhancedConfig


def convert_user_pdf(pdf_path: str, 
                     output_path: str = None,
                     enable_ocr: bool = True,
                     enable_ai: bool = True):
    """
    转换用户提供的PDF文件
    
    Args:
        pdf_path: PDF文件路径
        output_path: 输出EPUB路径（可选）
        enable_ocr: 是否启用OCR
        enable_ai: 是否启用AI分析
        
    Returns:
        (成功标志, 输出路径, 消息)
    """
    # 验证输入文件
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return False, None, f"文件不存在: {pdf_path}"
    
    if not pdf_file.suffix.lower() == '.pdf':
        return False, None, f"文件必须是PDF格式: {pdf_path}"
    
    # 确定输出路径
    if output_path is None:
        # 默认输出到同一目录
        output_path = pdf_file.parent / f"{pdf_file.stem}_converted.epub"
    else:
        output_path = Path(output_path)
    
    print(f"输入文件: {pdf_file}")
    print(f"输出文件: {output_path}")
    print(f"OCR模式: {'启用' if enable_ocr else '禁用'}")
    print(f"AI分析: {'启用' if enable_ai else '禁用'}")
    print("-" * 60)
    
    # 创建配置
    config = EnhancedConfig(
        enable_ocr=enable_ocr,
        enable_ai_analysis=enable_ai
    )
    
    # 执行转换
    pipeline = EnhancedConversionPipeline(config)
    result = pipeline.convert(str(pdf_file), str(output_path))
    
    return result.success, str(output_path) if result.output_path else None, result.message


def main():
    parser = argparse.ArgumentParser(
        description='转换用户PDF文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python test_with_user_pdf.py "E:\\files\\book.pdf"
  python test_with_user_pdf.py "E:\\files\\scan.pdf" --ocr
  python test_with_user_pdf.py "E:\\files\\book.pdf" --output "D:\\output\\result.epub"
  python test_with_user_pdf.py "E:\\files\\book.pdf" --no-ocr --no-ai
        '''
    )
    
    parser.add_argument('pdf_path', help='PDF文件路径（必需）')
    parser.add_argument('-o', '--output', help='输出EPUB文件路径')
    parser.add_argument('--ocr', action='store_true', default=False,
                       help='启用OCR（需要安装Tesseract，默认禁用）')
    parser.add_argument('--no-ocr', action='store_true', default=False,
                       help='禁用OCR（即使检测到扫描版PDF也不使用OCR）')
    parser.add_argument('--ai', action='store_true', default=True,
                       help='启用AI分析（默认启用）')
    parser.add_argument('--no-ai', action='store_false', dest='ai',
                       help='禁用AI分析')
    parser.add_argument('--dpi', type=int, default=300,
                       help='OCR分辨率（默认300）')
    
    args = parser.parse_args()
    
    # 处理Windows路径
    pdf_path = args.pdf_path
    if pdf_path.startswith('E:') or pdf_path.startswith('e:'):
        # 已经是绝对路径格式
        pass
    elif not os.path.isabs(pdf_path):
        # 相对路径，转换为绝对路径
        pdf_path = os.path.abspath(pdf_path)
    
    # 执行转换
    print("\n" + "="*60)
    print("PDF转EPUB转换工具")
    print("="*60 + "\n")
    
    success, output_path, message = convert_user_pdf(
        pdf_path,
        args.output,
        enable_ocr=args.ocr,
        enable_ai=args.ai
    )
    
    print("\n" + "="*60)
    if success:
        print(f"✓ 转换成功!")
        print(f"\n输出文件位置:")
        print(f"  {output_path}")
        print(f"\n文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
    else:
        print(f"✗ 转换失败")
        print(f"错误信息: {message}")
    print("="*60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())