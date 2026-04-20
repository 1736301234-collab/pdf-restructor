"""
布局处理器 - 执行排版优化操作

包括：去除干扰元素、合并段落、优化阅读顺序、
清理空白等操作
"""

import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from .models import (
    TextBlock, ImageBlock, TableBlock, ContentElement,
    ElementType, Chapter, DocumentStructure, BoundingBox
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """处理器配置"""
    remove_headers: bool = True  # 是否移除页眉
    remove_footers: bool = True  # 是否移除页脚
    remove_page_numbers: bool = True  # 是否移除页码
    remove_empty_paragraphs: bool = True  # 是否移除空段落
    merge_hyphenated_words: bool = True  # 是否合并连字符断开的单词
    normalize_whitespace: bool = True  # 是否规范化空白字符
    min_paragraph_length: int = 10  # 最小段落长度


class LayoutProcessor:
    """
    布局处理器
    
    负责清理和优化提取的内容，生成适合电子书阅读的线性内容
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        self.config = config or ProcessorConfig()
    
    def process(self, structure: DocumentStructure) -> DocumentStructure:
        """
        处理文档结构
        
        Args:
            structure: 原始文档结构
            
        Returns:
            处理后的文档结构
        """
        logger.info("开始处理文档布局...")
        
        # 1. 清理章节内容
        logger.debug("清理章节内容...")
        for chapter in structure.chapters:
            chapter.elements = self._clean_chapter_elements(chapter.elements)
        
        # 2. 移除空章节
        structure.chapters = [
            ch for ch in structure.chapters 
            if ch.elements and len(ch.elements) > 0
        ]
        
        # 3. 合并相邻的短段落
        if self.config.min_paragraph_length > 0:
            logger.debug("合并短段落...")
            for chapter in structure.chapters:
                chapter.elements = self._merge_short_paragraphs(chapter.elements)
        
        # 4. 规范化文本
        if self.config.normalize_whitespace:
            logger.debug("规范化文本格式...")
            for chapter in structure.chapters:
                chapter.elements = self._normalize_text(chapter.elements)
        
        # 5. 处理连字符
        if self.config.merge_hyphenated_words:
            logger.debug("处理连字符...")
            for chapter in structure.chapters:
                chapter.elements = self._merge_hyphenated_words(chapter.elements)
        
        logger.info(f"布局处理完成，剩余 {sum(len(ch.elements) for ch in structure.chapters)} 个内容元素")
        
        return structure
    
    def _clean_chapter_elements(self, elements: List[ContentElement]) -> List[ContentElement]:
        """
        清理章节中的元素
        
        移除不需要的元素，如页眉页脚、页码、空段落等
        """
        cleaned = []
        
        for element in elements:
            # 跳过页眉
            if element.element_type == ElementType.HEADER and self.config.remove_headers:
                continue
            
            # 跳过页脚
            if element.element_type == ElementType.FOOTER and self.config.remove_footers:
                continue
            
            # 跳过页码
            if element.element_type == ElementType.PAGE_NUMBER and self.config.remove_page_numbers:
                continue
            
            # 检查空段落
            if element.element_type == ElementType.PARAGRAPH:
                if isinstance(element.content, TextBlock):
                    text = element.content.content.strip()
                    if not text or len(text) < self.config.min_paragraph_length:
                        continue
            
            cleaned.append(element)
        
        return cleaned
    
    def _merge_short_paragraphs(self, elements: List[ContentElement]) -> List[ContentElement]:
        """
        合并相邻的短段落
        
        有时一个段落被错误地分成多个短段落
        """
        if len(elements) < 2:
            return elements
        
        merged = []
        i = 0
        
        while i < len(elements):
            current = elements[i]
            
            # 检查是否可以合并
            if (current.element_type == ElementType.PARAGRAPH and
                isinstance(current.content, TextBlock)):
                
                current_text = current.content.content.strip()
                
                # 如果当前段落很短，尝试合并下一个
                if len(current_text) < self.config.min_paragraph_length:
                    # 查找下一个同类型的段落
                    next_para_idx = i + 1
                    while (next_para_idx < len(elements) and
                           elements[next_para_idx].element_type != ElementType.PARAGRAPH):
                        next_para_idx += 1
                    
                    if next_para_idx < len(elements):
                        next_element = elements[next_para_idx]
                        if isinstance(next_element.content, TextBlock):
                            next_text = next_element.content.content.strip()
                            
                            # 合并
                            merged_text = current_text + " " + next_text
                            merged_block = TextBlock(
                                content=merged_text,
                                bbox=current.content.bbox.merge(next_element.content.bbox),
                                style=current.content.style,
                                page_number=current.content.page_number,
                                reading_order=current.content.reading_order
                            )
                            
                            merged.append(ContentElement(
                                element_type=ElementType.PARAGRAPH,
                                content=merged_block
                            ))
                            i = next_para_idx + 1
                            continue
            
            merged.append(current)
            i += 1
        
        return merged
    
    def _normalize_text(self, elements: List[ContentElement]) -> List[ContentElement]:
        """
        规范化文本格式
        
        包括：统一换行、去除多余空白、处理特殊字符等
        """
        for element in elements:
            if element.element_type == ElementType.PARAGRAPH:
                if isinstance(element.content, TextBlock):
                    text = element.content.content
                    
                    # 规范化空白
                    text = re.sub(r'\s+', ' ', text)
                    text = text.strip()
                    
                    # 处理常见的PDF特殊字符
                    text = text.replace('\x00', '')  # 空字符
                    text = text.replace('\x0c', '')  # 换页符
                    text = text.replace('\x0b', ' ')  # 垂直制表符
                    
                    element.content.content = text
            
            elif element.element_type == ElementType.TITLE:
                if isinstance(element.content, TextBlock):
                    text = element.content.content
                    text = re.sub(r'\s+', ' ', text).strip()
                    element.content.content = text
        
        return elements
    
    def _merge_hyphenated_words(self, elements: List[ContentElement]) -> List[ContentElement]:
        """
        合并被连字符断开的单词
        
        例如："informa-\ntion" -> "information"
        """
        for i, element in enumerate(elements):
            if element.element_type == ElementType.PARAGRAPH:
                if isinstance(element.content, TextBlock):
                    text = element.content.content
                    
                    # 查找连字符断开的单词模式
                    # 匹配：单词-换行-单词
                    pattern = r'(\w+)-\s*\n\s*(\w+)'
                    text = re.sub(pattern, r'\1\2', text)
                    
                    element.content.content = text
        
        return elements
    
    def _detect_page_numbers(self, elements: List[ContentElement]) -> List[int]:
        """
        检测页码元素
        
        返回页码元素的索引列表
        """
        page_number_indices = []
        
        for i, element in enumerate(elements):
            if element.element_type in [ElementType.PARAGRAPH, ElementType.UNKNOWN]:
                if isinstance(element.content, TextBlock):
                    text = element.content.content.strip()
                    
                    # 页码特征：纯数字，或者 "- 1 -" 格式
                    if re.match(r'^-?\s*\d+\s*-?$', text):
                        # 进一步验证：位置通常在页面底部
                        bbox = element.content.bbox
                        # 这里假设有页面高度信息
                        page_number_indices.append(i)
                    
                    # 罗马数字页码
                    elif re.match(r'^[IVXivx]+$', text):
                        page_number_indices.append(i)
        
        return page_number_indices
    
    def optimize_images(self, structure: DocumentStructure, 
                       max_width: int = 800) -> DocumentStructure:
        """
        优化图片
        
        Args:
            structure: 文档结构
            max_width: 最大宽度
            
        Returns:
            优化后的文档结构
        """
        logger.info("优化图片...")
        
        for image in structure.images:
            if image.width > max_width:
                # 计算缩放比例
                scale = max_width / image.width
                new_width = max_width
                new_height = int(image.height * scale)
                
                # 这里应该使用Pillow进行实际的缩放
                # image.image_data = resize_image(image.image_data, new_width, new_height)
                image.width = new_width
                image.height = new_height
        
        return structure
    
    def reorder_elements(self, structure: DocumentStructure) -> DocumentStructure:
        """
        重新排序元素
        
        确保阅读顺序正确
        """
        for chapter in structure.chapters:
            # 按阅读顺序排序
            chapter.elements.sort(key=lambda e: self._get_element_reading_order(e))
        
        return structure
    
    def _get_element_reading_order(self, element: ContentElement) -> int:
        """
        获取元素的阅读顺序
        """
        if isinstance(element.content, TextBlock):
            return element.content.reading_order
        elif isinstance(element.content, ImageBlock):
            return element.content.page_number * 10000
        elif isinstance(element.content, TableBlock):
            return element.content.page_number * 10000 + 5000
        return 0