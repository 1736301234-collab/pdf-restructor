"""
OCR处理器 - 支持扫描版PDF的文字识别

支持多种OCR引擎：
- Tesseract: 开源OCR引擎
- EasyOCR: 深度学习OCR，支持多语言
"""

import io
import logging
import os
import shutil
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import tempfile

from .models import TextBlock, BoundingBox, TextStyle

logger = logging.getLogger(__name__)


def find_tesseract_cmd() -> Optional[str]:
    """查找Tesseract可执行文件路径"""
    # 常见安装路径
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
        r"D:\Tesseract-OCR\tesseract.exe",
    ]
    
    # 检查每个路径
    for path in possible_paths:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            logger.info(f"找到Tesseract: {expanded}")
            return expanded
    
    # 从PATH环境变量查找
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        logger.info(f"从PATH找到Tesseract: {tesseract_path}")
        return tesseract_path
    
    return None


def configure_tesseract():
    """配置Tesseract路径"""
    tesseract_cmd = find_tesseract_cmd()
    
    if tesseract_cmd:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            # 设置TESSDATA_PREFIX
            tessdata_dir = os.path.join(os.path.dirname(tesseract_cmd), 'tessdata')
            if os.path.exists(tessdata_dir):
                os.environ['TESSDATA_PREFIX'] = tessdata_dir
                logger.info(f"设置TESSDATA_PREFIX: {tessdata_dir}")
            
            return True
        except ImportError:
            pass
    
    return False


@dataclass
class OCRResult:
    """OCR结果"""
    text: str
    confidence: float
    bbox: BoundingBox
    page_number: int


class OCRHandler:
    """
    OCR处理器
    
    封装多种OCR引擎，自动选择最佳方案
    """
    
    def __init__(self, 
                 engine: str = "auto",
                 language: str = "chi_sim+eng",
                 easyocr_langs: List[str] = None):
        """
        初始化OCR处理器
        
        Args:
            engine: OCR引擎 ('tesseract', 'easyocr', 'auto')
            language: Tesseract语言代码
            easyocr_langs: EasyOCR语言列表
        """
        self.engine = engine
        self.language = language
        self.easyocr_langs = easyocr_langs or ['ch_sim', 'en']
        
        # OCR引擎实例
        self.tesseract_available = False
        self.easyocr_available = False
        
        # 配置Tesseract
        if configure_tesseract():
            self.tesseract_available = True
            logger.info("Tesseract已配置")
        
        self._init_engines()
    
    def _init_engines(self):
        """初始化可用的OCR引擎"""
        # 检查Tesseract（已在上一步配置）
        if self.tesseract_available:
            try:
                import pytesseract
                version = pytesseract.get_tesseract_version()
                logger.info(f"Tesseract OCR 已可用，版本: {version}")
                self.tesseract_available = True
            except Exception as e:
                logger.warning(f"Tesseract测试失败: {e}")
                self.tesseract_available = False
        
        # 如果Tesseract不可用，尝试EasyOCR
        if not self.tesseract_available and self.engine in ['easyocr', 'auto']:
            try:
                import easyocr
                self.easyocr_class = easyocr.Reader
                self.easyocr_langs_store = self.easyocr_langs
                self.easyocr_reader = None
                self.easyocr_available = True
                logger.info("EasyOCR 已可用（延迟初始化）")
            except Exception as e:
                logger.warning(f"EasyOCR不可用: {e}")
        
        # 如果都没找到，给用户提示
        if not self.tesseract_available and not self.easyocr_available:
            logger.error("未找到可用的OCR引擎！请确保已安装Tesseract或EasyOCR")
        
        # 自动选择引擎
        if self.engine == 'auto':
            if self.tesseract_available:
                self.engine = 'tesseract'
                logger.info("自动选择引擎: Tesseract")
            elif self.easyocr_available:
                self.engine = 'easyocr'
                logger.info("自动选择引擎: EasyOCR")
    
    def process_page(self, 
                    image_data: bytes,
                    page_number: int = 0) -> List[OCRResult]:
        """
        处理单页图像
        
        Args:
            image_data: PNG/JPEG图像数据
            page_number: 页码
            
        Returns:
            OCR结果列表
        """
        if self.engine == 'tesseract':
            return self._process_with_tesseract(image_data, page_number)
        elif self.engine == 'easyocr':
            return self._process_with_easyocr(image_data, page_number)
        else:
            raise ValueError(f"未知的OCR引擎: {self.engine}")
    
    def _process_with_tesseract(self, 
                               image_data: bytes,
                               page_number: int) -> List[OCRResult]:
        """使用Tesseract处理"""
        import pytesseract
        from PIL import Image
        
        # 加载图像
        img = Image.open(io.BytesIO(image_data))
        
        # 获取详细数据
        data = pytesseract.image_to_data(
            img,
            lang=self.language,
            output_type=pytesseract.Output.DICT
        )
        
        results = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue
            
            confidence = float(data['conf'][i])
            if confidence < 30:
                continue
            
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            bbox = BoundingBox(
                x0=float(x),
                y0=float(y),
                x1=float(x + w),
                y1=float(y + h)
            )
            
            result = OCRResult(
                text=text,
                confidence=confidence / 100.0,
                bbox=bbox,
                page_number=page_number
            )
            results.append(result)
        
        return results
    
    def _process_with_easyocr(self, 
                             image_data: bytes,
                             page_number: int) -> List[OCRResult]:
        """使用EasyOCR处理"""
        import numpy as np
        from PIL import Image
        
        # 确保EasyOCR实例已初始化
        if self.easyocr_reader is None:
            try:
                self.easyocr_reader = self.easyocr_class(
                    self.easyocr_langs_store, 
                    gpu=False
                )
            except Exception as e:
                logger.error(f"EasyOCR初始化失败: {e}")
                return []
        
        # 加载图像
        img = Image.open(io.BytesIO(image_data))
        img_array = np.array(img)
        
        # 执行OCR
        ocr_results = self.easyocr_reader.readtext(img_array)
        
        results = []
        for (bbox_coords, text, confidence) in ocr_results:
            xs = [p[0] for p in bbox_coords]
            ys = [p[1] for p in bbox_coords]
            
            bbox = BoundingBox(
                x0=min(xs),
                y0=min(ys),
                x1=max(xs),
                y1=max(ys)
            )
            
            result = OCRResult(
                text=text,
                confidence=confidence,
                bbox=bbox,
                page_number=page_number
            )
            results.append(result)
        
        return results
    
    def convert_to_textblocks(self, 
                             ocr_results: List[OCRResult]) -> List[TextBlock]:
        """
        将OCR结果转换为TextBlock
        """
        blocks = []
        
        for result in ocr_results:
            # 估算字体大小
            font_size = result.bbox.height * 0.8
            
            style = TextStyle(
                font_name="OCR",
                font_size=font_size,
                is_bold=False,
                is_italic=False
            )
            
            block = TextBlock(
                content=result.text,
                bbox=result.bbox,
                style=style,
                page_number=result.page_number,
                confidence=result.confidence
            )
            blocks.append(block)
        
        return blocks


class ScannedPDFProcessor:
    """
    扫描版PDF处理器
    
    将PDF页面渲染为图像，然后进行OCR识别
    """
    
    def __init__(self, 
                 ocr_handler: Optional[OCRHandler] = None,
                 dpi: int = 300):
        """
        初始化处理器
        
        Args:
            ocr_handler: OCR处理器实例
            dpi: 渲染分辨率
        """
        self.ocr_handler = ocr_handler or OCRHandler()
        self.dpi = dpi
    
    def process_pdf(self, parser) -> List[TextBlock]:
        """
        处理扫描版PDF
        
        Args:
            parser: PDFParser实例
            
        Returns:
            文本块列表
        """
        all_blocks = []
        
        logger.info(f"开始OCR处理，共 {parser.page_count} 页")
        
        for page_num in range(parser.page_count):
            logger.debug(f"OCR处理第 {page_num + 1} 页")
            
            # 渲染页面为图像
            image_data = parser.render_page_to_image(page_num, dpi=self.dpi)
            
            if image_data:
                # OCR识别
                ocr_results = self.ocr_handler.process_page(image_data, page_num)
                
                # 转换为TextBlock
                blocks = self.ocr_handler.convert_to_textblocks(ocr_results)
                
                all_blocks.extend(blocks)
            
            # 进度报告
            if (page_num + 1) % 10 == 0:
                logger.info(f"OCR进度: {page_num + 1}/{parser.page_count}")
        
        logger.info(f"OCR完成，共识别 {len(all_blocks)} 个文本块")
        
        return all_blocks