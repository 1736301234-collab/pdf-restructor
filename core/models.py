"""
数据模型 - 定义PDF处理过程中使用的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class ElementType(Enum):
    """内容元素类型"""
    TITLE = "title"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"
    HEADER = "header"  # 页眉
    FOOTER = "footer"  # 页脚
    PAGE_NUMBER = "page_number"  # 页码
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """边界框 - 定义元素在页面上的位置"""
    x0: float  # 左上角x坐标
    y0: float  # 左上角y坐标
    x1: float  # 右下角x坐标
    y1: float  # 右下角y坐标
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def contains(self, other: 'BoundingBox') -> bool:
        """检查是否包含另一个边界框"""
        return (self.x0 <= other.x0 and self.y0 <= other.y0 and
                self.x1 >= other.x1 and self.y1 >= other.y1)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """检查是否与另一个边界框相交"""
        return not (self.x1 < other.x0 or self.x0 > other.x1 or
                   self.y1 < other.y0 or self.y0 > other.y1)
    
    def merge(self, other: 'BoundingBox') -> 'BoundingBox':
        """合并两个边界框"""
        return BoundingBox(
            x0=min(self.x0, other.x0),
            y0=min(self.y0, other.y0),
            x1=max(self.x1, other.x1),
            y1=max(self.y1, other.y1)
        )


@dataclass
class TextStyle:
    """文本样式"""
    font_name: str = ""
    font_size: float = 12.0
    is_bold: bool = False
    is_italic: bool = False
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB
    alignment: str = "left"  # left, center, right, justify


@dataclass
class TextBlock:
    """文本块"""
    content: str
    bbox: BoundingBox
    style: TextStyle
    page_number: int
    confidence: float = 1.0  # 置信度
    reading_order: int = 0  # 阅读顺序
    is_header: bool = False
    is_footer: bool = False
    
    @property
    def is_empty(self) -> bool:
        return not self.content.strip()
    
    @property
    def text_length(self) -> int:
        return len(self.content.strip())


@dataclass
class ImageBlock:
    """图像块"""
    image_data: bytes
    bbox: BoundingBox
    width: int
    height: int
    format: str  # PNG, JPEG等
    page_number: int
    alt_text: str = ""  # 替代文本
    caption: Optional[str] = None  # 图片说明


@dataclass
class TableCell:
    """表格单元格"""
    content: str
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    bbox: Optional[BoundingBox] = None


@dataclass
class TableBlock:
    """表格块"""
    cells: List[List[TableCell]] = field(default_factory=list)
    bbox: Optional[BoundingBox] = None
    page_number: int = 0
    caption: Optional[str] = None
    confidence: float = 0.0
    
    @property
    def row_count(self) -> int:
        return len(self.cells) if self.cells else 0
    
    @property
    def col_count(self) -> int:
        return len(self.cells[0]) if self.cells and self.cells[0] else 0


@dataclass
class ContentElement:
    """内容元素 - 统一的内容容器"""
    element_type: ElementType
    content: Any  # TextBlock, ImageBlock, TableBlock等
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_text(self) -> bool:
        return isinstance(self.content, TextBlock)
    
    @property
    def is_image(self) -> bool:
        return isinstance(self.content, ImageBlock)
    
    @property
    def is_table(self) -> bool:
        return isinstance(self.content, TableBlock)


@dataclass
class Chapter:
    """章节"""
    title: str
    level: int  # 1-6级标题
    elements: List[ContentElement] = field(default_factory=list)
    start_page: int = 0
    end_page: int = 0
    children: List['Chapter'] = field(default_factory=list)  # 子章节
    
    @property
    def element_count(self) -> int:
        return len(self.elements)


@dataclass
class DocumentStructure:
    """文档结构"""
    title: str = ""
    author: str = ""
    subject: str = ""
    keywords: str = ""
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    chapters: List[Chapter] = field(default_factory=list)
    header_elements: List[ContentElement] = field(default_factory=list)
    footer_elements: List[ContentElement] = field(default_factory=list)
    images: List[ImageBlock] = field(default_factory=list)
    tables: List[TableBlock] = field(default_factory=list)
    
    @property
    def total_pages(self) -> int:
        if not self.chapters:
            return 0
        return max(chapter.end_page for chapter in self.chapters)
    
    @property
    def chapter_count(self) -> int:
        return len(self.chapters)
    
    def get_flattened_elements(self) -> List[ContentElement]:
        """获取扁平化的元素列表"""
        elements = []
        for chapter in self.chapters:
            elements.extend(chapter.elements)
        return elements