"""
命令行界面 - PDF转EPUB工具

使用方法：
    python -m pdf_restructor.cli input.pdf -o output.epub
    python -m pdf_restructor.cli input.pdf --title "书名" --author "作者"
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .core.pipeline import ConversionPipeline, EPUBConfig
from .__init__ import __version__


def setup_logging(verbose: bool = False) -> None:
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog='pdf-restructor',
        description='智能PDF转EPUB工具 - 提取内容并重新排版',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s book.pdf                          # 基本转换
  %(prog)s book.pdf -o mybook.epub          # 指定输出文件名
  %(prog)s book.pdf --title "书名"           # 设置元数据
  %(prog)s book.pdf --verbose               # 显示详细日志
        '''
    )
    
    # 版本信息
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # 必需参数
    parser.add_argument(
        'input',
        metavar='INPUT',
        help='输入PDF文件路径'
    )
    
    # 可选参数
    parser.add_argument(
        '-o', '--output',
        metavar='OUTPUT',
        help='输出EPUB文件路径（默认: 与输入同名）'
    )
    
    parser.add_argument(
        '-p', '--password',
        metavar='PASSWORD',
        help='PDF解密密码（如果PDF已加密）'
    )
    
    # 元数据参数
    parser.add_argument(
        '--title',
        metavar='TITLE',
        help='电子书标题'
    )
    
    parser.add_argument(
        '--author',
        metavar='AUTHOR',
        help='电子书作者'
    )
    
    parser.add_argument(
        '--language',
        metavar='LANG',
        default='zh-CN',
        help='语言代码（默认: zh-CN）'
    )
    
    # 样式参数
    parser.add_argument(
        '--font-size',
        metavar='SIZE',
        type=int,
        default=16,
        help='正文字体大小（默认: 16）'
    )
    
    parser.add_argument(
        '--line-height',
        metavar='HEIGHT',
        type=float,
        default=1.6,
        help='行高（默认: 1.6）'
    )
    
    # 处理选项
    parser.add_argument(
        '--remove-headers',
        action='store_true',
        default=True,
        help='移除页眉（默认: 启用）'
    )
    
    parser.add_argument(
        '--remove-footers',
        action='store_true',
        default=True,
        help='移除页脚（默认: 启用）'
    )
    
    parser.add_argument(
        '--no-headers',
        action='store_false',
        dest='remove_headers',
        help='保留页眉'
    )
    
    parser.add_argument(
        '--no-footers',
        action='store_false',
        dest='remove_footers',
        help='保留页脚'
    )
    
    # 其他选项
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    parser.add_argument(
        '--cover',
        action='store_true',
        default=True,
        help='生成封面（默认: 启用）'
    )
    
    return parser


def main(args: Optional[list] = None) -> int:
    """主函数"""
    # 解析参数
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)
    
    # 设置日志
    setup_logging(parsed_args.verbose)
    logger = logging.getLogger(__name__)
    
    # 验证输入文件
    input_path = Path(parsed_args.input)
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}")
        return 1
    
    if not input_path.suffix.lower() == '.pdf':
        logger.error(f"输入文件必须是PDF格式: {input_path}")
        return 1
    
    # 确定输出路径
    if parsed_args.output:
        output_path = Path(parsed_args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}.epub"
    
    # 创建EPUB配置
    epub_config = EPUBConfig(
        title=parsed_args.title or input_path.stem,
        author=parsed_args.author or "未知",
        language=parsed_args.language,
        font_size=parsed_args.font_size,
        line_height=parsed_args.line_height,
        generate_cover=parsed_args.cover
    )
    
    # 创建处理器配置
    from .core.processor import ProcessorConfig
    processor_config = ProcessorConfig(
        remove_headers=parsed_args.remove_headers,
        remove_footers=parsed_args.remove_footers
    )
    
    # 执行转换
    logger.info(f"开始转换: {input_path} -> {output_path}")
    
    pipeline = ConversionPipeline(
        epub_config=epub_config,
        processor_config=processor_config
    )
    
    result = pipeline.convert(
        str(input_path),
        str(output_path),
        password=parsed_args.password
    )
    
    if result.success:
        logger.info(result.message)
        
        # 显示统计信息
        if result.stats:
            print("\n转换统计:")
            print(f"  页数: {result.stats.get('page_count', 0)}")
            print(f"  文本块: {result.stats.get('text_blocks', 0)}")
            print(f"  图片: {result.stats.get('images', 0)}")
            print(f"  表格: {result.stats.get('tables', 0)}")
            print(f"  章节: {result.stats.get('chapters', 0)}")
        
        return 0
    else:
        logger.error(result.message)
        return 1


if __name__ == '__main__':
    sys.exit(main())