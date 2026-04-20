"""
测试脚本 - 验证PDF转EPUB功能

使用方法:
    python test_conversion.py --input "your.pdf" --output "output.epub"
    python test_conversion.py --input "your.pdf" --ocr --ai
"""

import argparse
import sys
import os
from pathlib import Path

# 确保可以导入本包
sys.path.insert(0, str(Path(__file__).parent))

from core.pipeline import ConversionPipeline, convert_pdf_to_epub
from core.enhanced_pipeline import EnhancedConversionPipeline, EnhancedConfig, convert_pdf_to_epub_enhanced


def create_sample_pdf(output_path: str = "sample.pdf"):
    """
    创建一个示例PDF用于测试
    
    这个PDF包含：
    - 页眉和页脚
    - 标题层级
    - 正文段落
    - 简单表格
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        print("创建示例PDF...")
        
        # 尝试注册中文字体
        try:
            pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
            chinese_font = 'SimSun'
        except:
            chinese_font = 'Helvetica'
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # 创建中文样式
        title_style = ParagraphStyle(
            'ChineseTitle',
            parent=styles['Title'],
            fontName=chinese_font,
            fontSize=18,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'ChineseHeading',
            parent=styles['Heading1'],
            fontName=chinese_font,
            fontSize=14,
            spaceAfter=12
        )
        
        body_style = ParagraphStyle(
            'ChineseBody',
            parent=styles['BodyText'],
            fontName=chinese_font,
            fontSize=11,
            leading=18
        )
        
        # 构建内容
        story = []
        
        # 第一页 - 封面
        story.append(Paragraph("智能PDF转换测试文档", title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("作者: PDF Restructor Team", body_style))
        story.append(Spacer(1, 0.5*inch))
        
        # 第一章
        story.append(Paragraph("第一章 引言", heading_style))
        story.append(Paragraph(
            "这是一个用于测试PDF到EPUB转换功能的示例文档。它包含了各种排版元素，"
            "包括标题、段落、表格等。通过转换，我们希望看到这些元素能够正确地提取和重新排版。",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(
            "PDF格式是一种固定布局的文档格式，而EPUB则是一种可重排的电子书格式。"
            "转换的挑战在于理解PDF中的语义结构，并将其转换为适合电子书阅读的格式。",
            body_style
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # 第二章
        story.append(Paragraph("第二章 功能特性", heading_style))
        story.append(Paragraph(
            "本转换工具提供了以下核心特性：",
            body_style
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # 表格
        table_data = [
            ['功能', '说明', '状态'],
            ['文本提取', '从PDF提取文本内容', '✓'],
            ['标题识别', '自动识别标题层级', '✓'],
            ['页眉去除', '检测并去除页眉页脚', '✓'],
            ['段落合并', '合并跨页的段落', '✓'],
            ['图片处理', '保留并优化图片', '✓'],
            ['OCR支持', '识别扫描版PDF', '✓'],
        ]
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), chinese_font),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # 继续内容
        story.append(Paragraph("2.1 智能结构识别", heading_style))
        story.append(Paragraph(
            "通过分析字体大小、位置、格式等特征，系统能够自动识别文档的语义结构。"
            "这包括标题层级、段落边界、章节划分等。",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(
            "这种智能分析使得生成的EPUB电子书能够保留原始文档的结构，"
            "同时提供更适合电子书阅读的体验。",
            body_style
        ))
        
        # 第三章
        story.append(Paragraph("第三章 使用方法", heading_style))
        story.append(Paragraph(
            "使用本工具非常简单，只需提供PDF文件路径即可开始转换。"
            "系统会自动检测文档类型并选择最佳的处理策略。",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(
            "对于扫描版PDF，系统会自动启用OCR功能进行文字识别。"
            "对于文本版PDF，则直接提取已有文本内容。",
            body_style
        ))
        
        # 页眉页脚（通过添加页眉页脚函数）
        def add_header_footer(canvas, doc):
            canvas.saveState()
            
            # 页眉
            canvas.setFont(chinese_font, 9)
            canvas.drawString(inch, A4[1] - 0.5*inch, "PDF Restructor 测试文档")
            
            # 页脚（页码）
            canvas.drawCentredString(A4[0]/2, 0.5*inch, f"第 {doc.page} 页")
            
            canvas.restoreState()
        
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
        print(f"示例PDF已创建: {output_path}")
        return True
        
    except ImportError:
        print("警告: 未安装reportlab，无法创建示例PDF")
        print("请安装: pip install reportlab")
        return False
    except Exception as e:
        print(f"创建示例PDF失败: {e}")
        return False


def test_basic_conversion(input_path: str, output_path: str):
    """测试基本转换功能"""
    print("\n" + "="*60)
    print("测试1: 基本转换功能")
    print("="*60)
    
    result = convert_pdf_to_epub(input_path, output_path)
    
    print(f"结果: {'成功' if result.success else '失败'}")
    print(f"消息: {result.message}")
    
    if result.success and result.stats:
        print("\n统计信息:")
        for key, value in result.stats.items():
            print(f"  {key}: {value}")
    
    return result.success


def test_enhanced_conversion(input_path: str, output_path: str, 
                              enable_ocr: bool = False, enable_ai: bool = False):
    """测试增强版转换功能"""
    print("\n" + "="*60)
    print("测试2: 增强版转换功能")
    print(f"  OCR: {'启用' if enable_ocr else '禁用'}")
    print(f"  AI分析: {'启用' if enable_ai else '禁用'}")
    print("="*60)
    
    result = convert_pdf_to_epub_enhanced(
        input_path, 
        output_path,
        enable_ocr=enable_ocr,
        enable_ai=enable_ai
    )
    
    print(f"结果: {'成功' if result.success else '失败'}")
    print(f"消息: {result.message}")
    
    if result.success and result.stats:
        print("\n统计信息:")
        for key, value in result.stats.items():
            print(f"  {key}: {value}")
    
    return result.success


def main():
    parser = argparse.ArgumentParser(description='PDF转EPUB测试工具')
    parser.add_argument('--input', '-i', help='输入PDF文件路径')
    parser.add_argument('--output', '-o', default='output.epub', help='输出EPUB文件路径')
    parser.add_argument('--create-sample', action='store_true', help='创建示例PDF')
    parser.add_argument('--ocr', action='store_true', help='启用OCR功能')
    parser.add_argument('--ai', action='store_true', help='启用AI分析')
    parser.add_argument('--test-all', action='store_true', help='运行所有测试')
    
    args = parser.parse_args()
    
    # 如果没有输入文件且没有创建示例，显示帮助
    if not args.input and not args.create_sample:
        parser.print_help()
        print("\n提示: 可以使用 --create-sample 创建示例PDF进行测试")
        return
    
    # 创建示例PDF
    if args.create_sample:
        if create_sample_pdf("sample.pdf"):
            args.input = "sample.pdf"
        else:
            return
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 运行测试
    results = []
    
    # 测试1: 基本转换
    output_basic = args.output.replace('.epub', '_basic.epub')
    success = test_basic_conversion(args.input, output_basic)
    results.append(("基本转换", success, output_basic))
    
    # 测试2: 增强版（如果启用AI或OCR）
    if args.ocr or args.ai or args.test_all:
        output_enhanced = args.output.replace('.epub', '_enhanced.epub')
        success = test_enhanced_conversion(
            args.input, 
            output_enhanced,
            enable_ocr=args.ocr,
            enable_ai=args.ai
        )
        results.append(("增强版转换", success, output_enhanced))
    
    # 总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    for test_name, success, output_file in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if success:
            print(f"  输出文件: {os.path.abspath(output_file)}")
    
    # 检查依赖
    print("\n依赖检查:")
    try:
        import fitz
        print("  ✓ PyMuPDF 已安装")
    except:
        print("  ✗ PyMuPDF 未安装")
    
    try:
        from PIL import Image
        print("  ✓ Pillow 已安装")
    except:
        print("  ✗ Pillow 未安装")
    
    try:
        import pytesseract
        print("  ✓ pytesseract 已安装")
    except:
        print("  ⚠ pytesseract 未安装 (OCR功能受限)")
    
    try:
        import spacy
        print("  ✓ spacy 已安装")
    except:
        print("  ⚠ spacy 未安装 (AI分析功能受限)")


if __name__ == '__main__':
    main()