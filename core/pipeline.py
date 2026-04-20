"""
转换管道 - 主处理流程

协调各个模块，完成从PDF到EPUB的完整转换流程
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .parser import PDFParser
from .extractor import ContentExtractor, ExtractionConfig
from .analyzer import StructureAnalyzer
from .processor import LayoutProcessor, ProcessorConfig
from .generator import EPUBGenerator, EPUBConfig
from .models import DocumentStructure

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    message: str
    output_path: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class ConversionPipeline:
    """
    转换管道
    
    协调整个PDF到EPUB的转换流程
    """
    
    def __init__(self, 
                 extraction_config: Optional[ExtractionConfig] = None,
                 processor_config: Optional[ProcessorConfig] = None,
                 epub_config: Optional[EPUBConfig] = None):
        """
        初始化转换管道
        
        Args:
            extraction_config: 内容提取配置
            processor_config: 布局处理配置
            epub_config: EPUB生成配置
        """
        self.extraction_config = extraction_config or ExtractionConfig()
        self.processor_config = processor_config or ProcessorConfig()
        self.epub_config = epub_config or EPUBConfig()
        
        # 初始化各个模块
        self.parser: Optional[PDFParser] = None
        self.extractor = ContentExtractor(self.extraction_config)
        self.analyzer = StructureAnalyzer()
        self.processor = LayoutProcessor(self.processor_config)
        self.generator = EPUBGenerator(self.epub_config)
    
    def convert(self, 
                input_path: str, 
                output_path: str,
                password: Optional[str] = None) -> ConversionResult:
        """
        执行PDF到EPUB的转换
        
        Args:
            input_path: 输入PDF文件路径
            output_path: 输出EPUB文件路径
            password: PDF解密密码（如果需要）
            
        Returns:
            转换结果
        """
        try:
            logger.info(f"开始转换: {input_path} -> {output_path}")
            
            # 验证输入
            input_file = Path(input_path)
            if not input_file.exists():
                return ConversionResult(
                    success=False,
                    message=f"输入文件不存在: {input_path}",
                    output_path=None
                )
            
            if not input_file.suffix.lower() == '.pdf':
                return ConversionResult(
                    success=False,
                    message=f"输入文件必须是PDF格式: {input_path}",
                    output_path=None
                )
            
            # 步骤1: 解析PDF
            logger.info("步骤1/5: 解析PDF文件...")
            with PDFParser(str(input_path), password) as parser:
                metadata = parser.metadata
                page_count = parser.page_count
                
                logger.info(f"PDF解析成功: {page_count} 页")
                
                # 步骤2: 提取内容
                logger.info("步骤2/5: 提取内容...")
                text_blocks, image_blocks, table_blocks = self.extractor.extract(parser)
                
                logger.info(f"内容提取完成: {len(text_blocks)} 文本块, "
                           f"{len(image_blocks)} 图片, "
                           f"{len(table_blocks)} 表格")
                
                # 步骤3: 分析结构
                logger.info("步骤3/5: 分析文档结构...")
                structure = self.analyzer.analyze(
                    text_blocks, image_blocks, table_blocks, metadata
                )
                
                logger.info(f"结构分析完成: {structure.chapter_count} 章节, "
                           f"{len(structure.header_elements)} 页眉, "
                           f"{len(structure.footer_elements)} 页脚")
                
                # 步骤4: 处理布局
                logger.info("步骤4/5: 处理布局...")
                processed_structure = self.processor.process(structure)
                
                # 更新EPUB配置中的元数据
                if processed_structure.title:
                    self.epub_config.title = processed_structure.title
                if processed_structure.author:
                    self.epub_config.author = processed_structure.author
                
                # 步骤5: 生成EPUB
                logger.info("步骤5/5: 生成EPUB...")
                success = self.generator.generate(processed_structure, output_path)
                
                if not success:
                    return ConversionResult(
                        success=False,
                        message="EPUB生成失败",
                        output_path=None
                    )
                
                # 收集统计信息
                stats = {
                    'input_file': str(input_path),
                    'output_file': str(output_path),
                    'page_count': page_count,
                    'text_blocks': len(text_blocks),
                    'images': len(image_blocks),
                    'tables': len(table_blocks),
                    'chapters': processed_structure.chapter_count,
                    'header_elements': len(processed_structure.header_elements),
                    'footer_elements': len(processed_structure.footer_elements)
                }
                
                logger.info(f"转换成功: {output_path}")
                
                return ConversionResult(
                    success=True,
                    message=f"转换成功！生成文件: {output_path}",
                    output_path=output_path,
                    stats=stats
                )
                
        except Exception as e:
            logger.exception("转换过程中发生错误")
            return ConversionResult(
                success=False,
                message=f"转换失败: {str(e)}",
                output_path=None
            )
    
    def convert_batch(self, 
                     input_paths: list,
                     output_dir: str,
                     password: Optional[str] = None) -> list:
        """
        批量转换
        
        Args:
            input_paths: 输入PDF文件路径列表
            output_dir: 输出目录
            password: PDF解密密码
            
        Returns:
            转换结果列表
        """
        results = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for input_path in input_paths:
            input_file = Path(input_path)
            output_path = output_dir / f"{input_file.stem}.epub"
            
            result = self.convert(input_path, str(output_path), password)
            results.append(result)
        
        return results


# 便捷的函数接口
def convert_pdf_to_epub(input_path: str, 
                       output_path: str,
                       password: Optional[str] = None,
                       **config_kwargs) -> ConversionResult:
    """
    便捷的PDF转EPUB函数
    
    示例：
        result = convert_pdf_to_epub(
            input_path="book.pdf",
            output_path="book.epub",
            title="我的书",
            author="作者名"
        )
    
    Args:
        input_path: 输入PDF路径
        output_path: 输出EPUB路径
        password: PDF密码
        **config_kwargs: 配置参数（title, author, language等）
        
    Returns:
        转换结果
    """
    # 创建配置
    epub_config = EPUBConfig()
    for key, value in config_kwargs.items():
        if hasattr(epub_config, key):
            setattr(epub_config, key, value)
    
    # 创建管道并执行转换
    pipeline = ConversionPipeline(epub_config=epub_config)
    return pipeline.convert(input_path, output_path, password)