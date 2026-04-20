"""
增强版转换管道 - 集成AI布局和OCR功能
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .parser import PDFParser
from .extractor import ContentExtractor, ExtractionConfig
from .analyzer import StructureAnalyzer
from .processor import LayoutProcessor, ProcessorConfig
from .generator import EPUBGenerator, EPUBConfig
from .ai_analyzer import AILayoutAnalyzer, SemanticAnalyzer
from .ocr_handler import OCRHandler, ScannedPDFProcessor
from .pipeline import ConversionResult
from .models import DocumentStructure

logger = logging.getLogger(__name__)


@dataclass
class EnhancedConfig:
    """增强版配置"""
    # OCR配置（默认关闭，需要手动安装OCR依赖后开启）
    enable_ocr: bool = False
    ocr_engine: str = "tesseract"  # tesseract（推荐）, easyocr, paddle
    ocr_language: str = "chi_sim+eng"
    ocr_dpi: int = 300
    
    # AI分析配置
    enable_ai_analysis: bool = True
    use_deep_learning: bool = False
    language: str = "zh"
    
    # 传统配置
    extraction_config: ExtractionConfig = field(default_factory=ExtractionConfig)
    processor_config: ProcessorConfig = field(default_factory=ProcessorConfig)
    epub_config: EPUBConfig = field(default_factory=EPUBConfig)


class EnhancedConversionPipeline:
    """
    增强版转换管道
    
    集成AI布局和OCR功能的完整转换流程
    """
    
    def __init__(self, config: Optional[EnhancedConfig] = None):
        self.config = config or EnhancedConfig()
        
        # 初始化AI分析器
        self.ai_analyzer: Optional[AILayoutAnalyzer] = None
        if self.config.enable_ai_analysis:
            try:
                self.ai_analyzer = AILayoutAnalyzer(
                    use_deep_learning=self.config.use_deep_learning,
                    language=self.config.language
                )
                logger.info("AI分析器已初始化")
            except Exception as e:
                logger.warning(f"AI分析器初始化失败: {e}")
        
        # 初始化OCR处理器
        self.ocr_handler: Optional[OCRHandler] = None
        if self.config.enable_ocr:
            try:
                self.ocr_handler = OCRHandler(
                    engine=self.config.ocr_engine,
                    language=self.config.ocr_language
                )
                logger.info("OCR处理器已初始化")
            except Exception as e:
                logger.warning(f"OCR处理器初始化失败: {e}")
        
        # 初始化其他组件
        self.extractor = ContentExtractor(self.config.extraction_config)
        self.analyzer = StructureAnalyzer()
        self.processor = LayoutProcessor(self.config.processor_config)
        self.generator = EPUBGenerator(self.config.epub_config)
    
    def convert(self, 
                input_path: str, 
                output_path: str,
                password: Optional[str] = None) -> ConversionResult:
        """
        执行增强版转换
        
        Args:
            input_path: 输入PDF文件路径
            output_path: 输出EPUB文件路径
            password: PDF解密密码
            
        Returns:
            转换结果
        """
        try:
            logger.info(f"开始增强版转换: {input_path} -> {output_path}")
            
            # 验证输入
            input_file = Path(input_path)
            if not input_file.exists():
                return ConversionResult(
                    success=False,
                    message=f"输入文件不存在: {input_path}",
                    output_path=None
                )
            
            # 步骤1: 解析PDF
            logger.info("步骤1/6: 解析PDF文件...")
            with PDFParser(str(input_path), password) as parser:
                metadata = parser.metadata
                page_count = parser.page_count
                
                logger.info(f"PDF解析成功: {page_count} 页")
                
                # 步骤2: 检测是否为扫描版并处理
                logger.info("步骤2/6: 内容提取（OCR/文本）...")
                
                # 先尝试提取文本
                text_blocks, image_blocks, table_blocks = self.extractor.extract(parser)
                
                # 检测是否需要OCR
                total_text_length = sum(len(b.content) for b in text_blocks)
                avg_text_per_page = total_text_length / page_count if page_count > 0 else 0
                
                is_scanned = avg_text_per_page < 100
                
                if is_scanned and self.config.enable_ocr:
                    if self.ocr_handler and self.ocr_handler.tesseract_available:
                        logger.info(f"检测到扫描版PDF，启用OCR（平均 {avg_text_per_page:.0f} 字符/页）")
                        
                        try:
                            # 使用OCR处理
                            scanned_processor = ScannedPDFProcessor(
                                self.ocr_handler,
                                dpi=self.config.ocr_dpi
                            )
                            text_blocks = scanned_processor.process_pdf(parser)
                            
                            # 扫描版通常没有图片和表格
                            image_blocks = []
                            table_blocks = []
                            
                            logger.info(f"OCR识别完成: {len(text_blocks)} 个文本块")
                        except Exception as e:
                            logger.warning(f"OCR处理失败: {e}")
                            logger.warning(f"退回到文本提取模式")
                            # 继续使用已提取的文本块
                    else:
                        # OCR不可用但检测到扫描版 - 自动降级
                        logger.warning(f"=" * 60)
                        logger.warning(f"检测到扫描版PDF，但OCR引擎不可用")
                        logger.warning(f"平均文本: {avg_text_per_page:.0f} 字符/页")
                        logger.warning(f"=" * 60)
                        logger.warning(f"如需OCR识别，请安装Tesseract:")
                        logger.warning(f"https://github.com/UB-Mannheim/tesseract/wiki")
                        logger.warning(f"")
                        logger.warning(f"尝试使用现有文本内容继续...")
                        
                        # 尝试用原始文本块（虽然可能很少）
                        if not text_blocks or len(text_blocks) < 5:
                            # 扫描版且没有可提取文本
                            logger.error(f"PDF为扫描版且无可提取内容")
                            return ConversionResult(
                                success=False,
                                message="PDF为扫描版且无可提取内容。如需OCR识别，请安装Tesseract OCR。",
                                output_path=None,
                                stats={'ocr_needed': True}
                            )
                else:
                    logger.info(f"使用文本提取（平均 {avg_text_per_page:.0f} 字符/页）")
                
                # 步骤3: AI布局分析（可选）
                if self.config.enable_ai_analysis and self.ai_analyzer:
                    logger.info("步骤3/6: AI布局分析...")
                    
                    # 获取第一页的尺寸
                    page_width, page_height = parser.get_page_size(0)
                    
                    # AI分析
                    layout_regions = self.ai_analyzer.analyze_layout(
                        text_blocks, image_blocks, page_width, page_height
                    )
                    
                    logger.info(f"AI分析完成: {len(layout_regions)} 个区域")
                    
                    # 使用AI分析结果优化提取
                    text_blocks = self._apply_ai_analysis(
                        text_blocks, layout_regions
                    )
                else:
                    logger.info("步骤3/6: 跳过AI分析")
                
                # 步骤4: 结构分析
                logger.info("步骤4/6: 分析文档结构...")
                structure = self.analyzer.analyze(
                    text_blocks, image_blocks, table_blocks, metadata
                )
                
                logger.info(f"结构分析完成: {structure.chapter_count} 章节")
                
                # 步骤5: 布局处理
                logger.info("步骤5/6: 处理布局...")
                processed_structure = self.processor.process(structure)
                
                # 更新EPUB配置
                if processed_structure.title:
                    self.config.epub_config.title = processed_structure.title
                if processed_structure.author:
                    self.config.epub_config.author = processed_structure.author
                
                # 步骤6: 生成EPUB
                logger.info("步骤6/6: 生成EPUB...")
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
                    'is_scanned': is_scanned,
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
                    message=f"转换成功！{'(OCR模式)' if is_scanned else '(文本模式)'}",
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
    
    def _apply_ai_analysis(self, 
                          text_blocks: List,
                          layout_regions: list) -> List:
        """
        应用AI分析结果优化文本块
        
        根据布局区域类型调整文本块的属性
        """
        from .ai_analyzer import LayoutRegionType
        
        # 创建区域查找表
        region_map = {}
        for region in layout_regions:
            for element in region.elements:
                if hasattr(element, 'bbox'):
                    region_map[id(element)] = region
        
        # 更新文本块
        for block in text_blocks:
            if id(block) in region_map:
                region = region_map[id(block)]
                
                # 根据区域类型设置属性
                if region.region_type == LayoutRegionType.HEADER:
                    block.is_header = True
                elif region.region_type == LayoutRegionType.FOOTER:
                    block.is_footer = True
                
                # 可以添加更多属性...
        
        return text_blocks


# 便捷函数
def convert_pdf_to_epub_enhanced(input_path: str,
                                 output_path: str,
                                 password: Optional[str] = None,
                                 enable_ocr: bool = True,
                                 enable_ai: bool = True,
                                 **config_kwargs) -> ConversionResult:
    """
    便捷函数：增强版PDF转EPUB
    
    示例：
        result = convert_pdf_to_epub_enhanced(
            "scan.pdf",
            "output.epub",
            enable_ocr=True,      # 启用OCR
            enable_ai=True,       # 启用AI分析
            ocr_engine="paddle"   # 使用PaddleOCR
        )
    
    Args:
        input_path: 输入PDF路径
        output_path: 输出EPUB路径
        password: PDF密码
        enable_ocr: 是否启用OCR
        enable_ai: 是否启用AI分析
        **config_kwargs: 其他配置
        
    Returns:
        转换结果
    """
    config = EnhancedConfig(
        enable_ocr=enable_ocr,
        enable_ai_analysis=enable_ai
    )
    
    # 应用其他配置
    for key, value in config_kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    pipeline = EnhancedConversionPipeline(config)
    return pipeline.convert(input_path, output_path, password)