"""
PDF解析引擎 - 负责PDF文件的读取和底层内容提取
"""

import fitz  # PyMuPDF
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from .models import BoundingBox, TextBlock, ImageBlock, TextStyle

logger = logging.getLogger(__name__)


class PDFParseError(Exception):
    """PDF解析错误"""
    pass


class PDFParser:
    """
    PDF解析引擎
    
    使用PyMuPDF(fitz)作为底层解析库，提供高性能的PDF处理能力
    """
    
    def __init__(self, file_path: str, password: Optional[str] = None):
        """
        初始化PDF解析器
        
        Args:
            file_path: PDF文件路径
            password: 解密密码（如果需要）
        """
        self.file_path = Path(file_path)
        self.password = password
        self.document: Optional[fitz.Document] = None
        self._metadata: Dict[str, Any] = {}
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")
        
        self._load_document()
    
    def _load_document(self) -> None:
        """加载PDF文档"""
        try:
            self.document = fitz.open(str(self.file_path))
            
            # 检查是否需要密码
            if self.document.is_encrypted:
                if not self.password:
                    raise PDFParseError("PDF已加密，请提供密码")
                if not self.document.authenticate(self.password):
                    raise PDFParseError("PDF密码错误")
            
            # 提取元数据
            self._extract_metadata()
            
            logger.info(f"成功加载PDF: {self.file_path}, 页数: {len(self.document)}")
            
        except Exception as e:
            raise PDFParseError(f"无法加载PDF文件: {e}")
    
    def _extract_metadata(self) -> None:
        """提取PDF元数据"""
        try:
            self._metadata = {
                'title': self.document.metadata.get('title', ''),
                'author': self.document.metadata.get('author', ''),
                'subject': self.document.metadata.get('subject', ''),
                'keywords': self.document.metadata.get('keywords', ''),
                'creator': self.document.metadata.get('creator', ''),
                'producer': self.document.metadata.get('producer', ''),
                'creation_date': self.document.metadata.get('creationDate', ''),
                'modification_date': self.document.metadata.get('modDate', '')
            }
        except Exception as e:
            logger.warning(f"提取元数据时出错: {e}")
            self._metadata = {}
    
    @property
    def page_count(self) -> int:
        """返回页面总数"""
        return len(self.document) if self.document else 0
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """返回文档元数据"""
        return self._metadata.copy()
    
    def get_page_size(self, page_number: int) -> Tuple[float, float]:
        """
        获取页面尺寸
        
        Args:
            page_number: 页码（从0开始）
            
        Returns:
            (宽度, 高度)
        """
        if not self.document or page_number < 0 or page_number >= len(self.document):
            return (0, 0)
        
        page = self.document[page_number]
        rect = page.rect
        return (rect.width, rect.height)
    
    def extract_text_blocks(self, page_number: int, 
                          min_text_length: int = 1) -> List[TextBlock]:
        """
        提取页面的文本块
        
        Args:
            page_number: 页码（从0开始）
            min_text_length: 最小文本长度（过滤噪声）
            
        Returns:
            TextBlock列表
        """
        if not self.document or page_number < 0 or page_number >= len(self.document):
            return []
        
        page = self.document[page_number]
        blocks = []
        
        try:
            # 使用"dict"模式提取文本块（保留更多结构信息）
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # 跳过非文本块
                    continue
                
                # 提取文本内容
                text_content = ""
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    if line_text:
                        text_content += line_text + " "
                
                text_content = text_content.strip()
                if len(text_content) < min_text_length:
                    continue
                
                # 获取边界框
                bbox = block.get("bbox", (0, 0, 0, 0))
                
                # 获取样式信息（使用第一个span的样式）
                style = TextStyle()
                if block.get("lines") and block["lines"]:
                    first_line = block["lines"][0]
                    if first_line.get("spans") and first_line["spans"]:
                        first_span = first_line["spans"][0]
                        style.font_name = first_span.get("font", "")
                        style.font_size = first_span.get("size", 12.0)
                        style.is_bold = "bold" in style.font_name.lower()
                        style.is_italic = "italic" in style.font_name.lower()
                        
                        # 提取颜色
                        color = first_span.get("color", 0)
                        r = (color >> 16) & 0xFF
                        g = (color >> 8) & 0xFF
                        b = color & 0xFF
                        style.color = (r, g, b)
                
                text_block = TextBlock(
                    content=text_content,
                    bbox=BoundingBox(
                        x0=bbox[0],
                        y0=bbox[1],
                        x1=bbox[2],
                        y1=bbox[3]
                    ),
                    style=style,
                    page_number=page_number
                )
                blocks.append(text_block)
            
            logger.debug(f"页面 {page_number + 1} 提取了 {len(blocks)} 个文本块")
            return blocks
            
        except Exception as e:
            logger.error(f"提取页面 {page_number + 1} 的文本时出错: {e}")
            return []
    
    def extract_images(self, page_number: int, 
                      min_size: int = 50) -> List[ImageBlock]:
        """
        提取页面的图片
        
        Args:
            page_number: 页码（从0开始）
            min_size: 最小图片尺寸（像素）
            
        Returns:
            ImageBlock列表
        """
        if not self.document or page_number < 0 or page_number >= len(self.document):
            return []
        
        page = self.document[page_number]
        images = []
        
        try:
            # 获取页面的图像列表
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = self.document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # 获取图像在页面上的位置
                # 通过搜索包含图像的矩形来定位
                image_rects = []
                for img_rect in page.get_image_rects(xref):
                    image_rects.append(img_rect)
                
                if not image_rects:
                    continue
                
                rect = image_rects[0]
                
                # 检查最小尺寸
                if rect.width < min_size or rect.height < min_size:
                    continue
                
                # 计算图像的原始尺寸
                import io
                from PIL import Image
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    width, height = pil_img.size
                except:
                    width, height = int(rect.width), int(rect.height)
                
                image_block = ImageBlock(
                    image_data=image_bytes,
                    bbox=BoundingBox(
                        x0=rect.x0,
                        y0=rect.y0,
                        x1=rect.x1,
                        y1=rect.y1
                    ),
                    width=width,
                    height=height,
                    format=image_ext.upper(),
                    page_number=page_number
                )
                images.append(image_block)
            
            logger.debug(f"页面 {page_number + 1} 提取了 {len(images)} 张图片")
            return images
            
        except Exception as e:
            logger.error(f"提取页面 {page_number + 1} 的图片时出错: {e}")
            return []
    
    def render_page_to_image(self, page_number: int, 
                            dpi: int = 150) -> Optional[bytes]:
        """
        将页面渲染为图片（用于OCR或预览）
        
        Args:
            page_number: 页码（从0开始）
            dpi: 分辨率
            
        Returns:
            PNG格式的图片数据
        """
        if not self.document or page_number < 0 or page_number >= len(self.document):
            return None
        
        page = self.document[page_number]
        
        try:
            # 设置矩阵以控制分辨率
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            return pix.tobytes("png")
        except Exception as e:
            logger.error(f"渲染页面 {page_number + 1} 时出错: {e}")
            return None
    
    def close(self) -> None:
        """关闭文档，释放资源"""
        if self.document:
            self.document.close()
            self.document = None
            logger.info("PDF文档已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False