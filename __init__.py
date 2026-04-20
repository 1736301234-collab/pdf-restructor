"""
智能PDF重构工具 - PDF to EPUB Converter

一个能够从PDF中提取内容、理解文档结构、去除排版噪声，
并生成真正可重排EPUB电子书的智能工具。
"""

__version__ = "1.0.0"
__author__ = "PDF Restructor Team"

from .core.parser import PDFParser
from .core.extractor import ContentExtractor
from .core.analyzer import StructureAnalyzer
from .core.processor import LayoutProcessor
from .core.generator import EPUBGenerator
from .core.pipeline import ConversionPipeline

__all__ = [
    "PDFParser",
    "ContentExtractor",
    "StructureAnalyzer",
    "LayoutProcessor",
    "EPUBGenerator",
    "ConversionPipeline"
]