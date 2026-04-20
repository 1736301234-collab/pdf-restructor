"""
结构分析器 - 理解文档的语义结构

包括：标题层级识别、段落识别、章节识别、列表识别、
页眉页脚识别、阅读顺序确定等
"""

import re
import logging
from typing import List, Tuple, Optional, Dict
from collections import defaultdict
from .models import (
    TextBlock, ImageBlock, TableBlock, ContentElement,
    ElementType, Chapter, DocumentStructure, BoundingBox
)

logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """
    结构分析器
    
    通过分析文本的字体、位置、格式等特征，识别文档的语义结构
    """
    
    def __init__(self, 
                 title_size_ratio_threshold: float = 1.2,
                 header_region_ratio: float = 0.15,
                 footer_region_ratio: float = 0.15):
        """
        初始化结构分析器
        
        Args:
            title_size_ratio_threshold: 标题字体大小相对于正文的倍数阈值
            header_region_ratio: 页眉区域占页面高度的比例
            footer_region_ratio: 页脚区域占页面高度的比例
        """
        self.title_size_ratio_threshold = title_size_ratio_threshold
        self.header_region_ratio = header_region_ratio
        self.footer_region_ratio = footer_region_ratio
        
        # 运行时状态
        self.page_sizes: Dict[int, Tuple[float, float]] = {}
        self.header_patterns: Dict[int, List[str]] = defaultdict(list)
        self.footer_patterns: Dict[int, List[str]] = defaultdict(list)
    
    def analyze(self, 
                text_blocks: List[TextBlock],
                image_blocks: List[ImageBlock],
                table_blocks: List[TableBlock],
                metadata: Dict) -> DocumentStructure:
        """
        分析文档结构
        
        Args:
            text_blocks: 文本块列表
            image_blocks: 图片块列表
            table_blocks: 表格块列表
            metadata: 文档元数据
            
        Returns:
            文档结构对象
        """
        logger.info("开始分析文档结构...")
        
        if not text_blocks:
            logger.warning("没有文本块可供分析")
            return DocumentStructure()
        
        # 1. 检测页眉页脚
        logger.debug("检测页眉页脚...")
        header_elements, footer_elements = self._detect_headers_footers(text_blocks)
        
        # 2. 过滤页眉页脚
        filtered_blocks = [b for b in text_blocks 
                          if b not in [h.content for h in header_elements] 
                          and b not in [f.content for f in footer_elements]]
        
        # 3. 识别标题
        logger.debug("识别标题层级...")
        titles = self._detect_titles(filtered_blocks)
        
        # 4. 识别段落
        logger.debug("识别段落...")
        paragraphs = self._detect_paragraphs(filtered_blocks, titles)
        
        # 5. 识别章节
        logger.debug("构建章节结构...")
        chapters = self._build_chapters(titles, paragraphs, image_blocks, table_blocks)
        
        # 6. 构建文档结构
        structure = DocumentStructure(
            title=metadata.get('title', ''),
            author=metadata.get('author', ''),
            subject=metadata.get('subject', ''),
            keywords=metadata.get('keywords', ''),
            creation_date=metadata.get('creation_date', ''),
            modification_date=metadata.get('modification_date', ''),
            chapters=chapters,
            header_elements=header_elements,
            footer_elements=footer_elements,
            images=image_blocks,
            tables=table_blocks
        )
        
        logger.info(f"结构分析完成: 检测到 {len(chapters)} 个章节, "
                   f"{len(header_elements)} 个页眉, {len(footer_elements)} 个页脚")
        
        return structure
    
    def _detect_titles(self, text_blocks: List[TextBlock]) -> List[Tuple[TextBlock, int]]:
        """
        检测标题及其层级
        
        返回：(标题文本块, 标题级别) 列表
        """
        if not text_blocks:
            return []
        
        # 计算正文的平均字体大小
        body_font_sizes = []
        for block in text_blocks:
            text = block.content.strip()
            # 排除明显的标题（很短）和页眉页脚
            if len(text) > 20:
                body_font_sizes.append(block.style.font_size)
        
        if body_font_sizes:
            avg_body_size = sum(body_font_sizes) / len(body_font_sizes)
        else:
            avg_body_size = 12.0
        
        titles = []
        
        for block in text_blocks:
            text = block.content.strip()
            if not text:
                continue
            
            # 标题特征检测
            title_score = 0
            level = 0
            
            # 1. 字体大小
            size_ratio = block.style.font_size / avg_body_size
            if size_ratio >= 2.0:
                title_score += 4
                level = 1
            elif size_ratio >= 1.6:
                title_score += 3
                level = 2
            elif size_ratio >= 1.4:
                title_score += 2
                level = 3
            elif size_ratio >= self.title_size_ratio_threshold:
                title_score += 1
                level = 4
            
            # 2. 字体加粗
            if block.style.is_bold:
                title_score += 1
                if level == 0:
                    level = 5
            
            # 3. 文本长度（标题通常较短）
            text_length = len(text)
            if text_length <= 20:
                title_score += 2
            elif text_length <= 50:
                title_score += 1
            else:
                title_score -= 1  # 太长的文本不太可能是标题
            
            # 4. 全大写（可能是标题）
            if text.isupper() and text_length > 3:
                title_score += 1
            
            # 5. 数字开头（如 "1. 第一章"）
            if re.match(r'^\d+[.\s]', text):
                title_score += 1
            
            # 6. 章节关键词
            title_keywords = ['chapter', 'section', 'part', 'chapter', 
                            '章', '节', '部分', '第']
            if any(keyword in text.lower() for keyword in title_keywords):
                title_score += 2
            
            # 7. 位置（标题通常在页面上部）
            if block.bbox.y0 < 200:  # 页面顶部区域
                title_score += 1
            
            # 标题判定阈值
            if title_score >= 3 and level > 0:
                titles.append((block, level))
        
        # 按阅读顺序和页码排序
        titles.sort(key=lambda x: (x[0].page_number, x[0].reading_order))
        
        # 标题层级修正：确保高级标题在前
        self._correct_title_levels(titles)
        
        return titles
    
    def _correct_title_levels(self, titles: List[Tuple[TextBlock, int]]) -> None:
        """
        修正标题层级，确保层级顺序正确
        
        例如：不能出现一级标题后紧跟三级标题
        """
        if len(titles) < 2:
            return
        
        for i in range(1, len(titles)):
            prev_level = titles[i-1][1]
            curr_level = titles[i][1]
            
            # 如果当前标题级别跳跃太大，进行调整
            if curr_level > prev_level + 1:
                # 调整为 prev_level + 1
                titles[i] = (titles[i][0], prev_level + 1)
    
    def _detect_paragraphs(self, text_blocks: List[TextBlock], 
                          titles: List[Tuple[TextBlock, int]]) -> List[ContentElement]:
        """
        识别段落
        
        将文本块分组为段落
        """
        # 获取标题文本块的ID集合
        title_block_ids = {id(t[0]) for t in titles}
        
        paragraphs = []
        current_paragraph = []
        
        for block in text_blocks:
            # 跳过标题
            if id(block) in title_block_ids:
                # 先保存之前的段落
                if current_paragraph:
                    merged = self._merge_blocks_to_paragraph(current_paragraph)
                    paragraphs.append(merged)
                    current_paragraph = []
                continue
            
            # 判断是否是新段落的开始
            if current_paragraph:
                prev_block = current_paragraph[-1]
                
                # 检查是否是同一段落的延续
                if self._is_same_paragraph(prev_block, block):
                    current_paragraph.append(block)
                else:
                    # 新段落
                    merged = self._merge_blocks_to_paragraph(current_paragraph)
                    paragraphs.append(merged)
                    current_paragraph = [block]
            else:
                current_paragraph.append(block)
        
        # 处理最后一个段落
        if current_paragraph:
            merged = self._merge_blocks_to_paragraph(current_paragraph)
            paragraphs.append(merged)
        
        return paragraphs
    
    def _is_same_paragraph(self, block1: TextBlock, block2: TextBlock) -> bool:
        """
        判断两个文本块是否属于同一段落
        """
        # 字体大小差异
        if abs(block1.style.font_size - block2.style.font_size) > 0.5:
            return False
        
        # 水平位置差异（缩进）
        if abs(block1.bbox.x0 - block2.bbox.x0) > 20:
            return False
        
        # 垂直间距
        vertical_gap = block2.bbox.y0 - block1.bbox.y1
        avg_line_height = block1.style.font_size * 1.5
        
        # 如果间距大于平均行高，可能是新段落
        if vertical_gap > avg_line_height * 2:
            return False
        
        return True
    
    def _merge_blocks_to_paragraph(self, blocks: List[TextBlock]) -> ContentElement:
        """
        将多个文本块合并为一个段落
        """
        if not blocks:
            return None
        
        # 合并文本
        texts = []
        for i, block in enumerate(blocks):
            text = block.content.strip()
            if i > 0 and texts and not texts[-1].endswith('-'):
                texts.append(' ')
            texts.append(text)
        
        merged_text = ''.join(texts)
        
        # 合并边界框
        bbox = blocks[0].bbox
        for block in blocks[1:]:
            bbox = bbox.merge(block.bbox)
        
        # 创建新的文本块
        merged_block = TextBlock(
            content=merged_text,
            bbox=bbox,
            style=blocks[0].style,  # 使用第一个块的样式
            page_number=blocks[0].page_number,
            reading_order=blocks[0].reading_order
        )
        
        return ContentElement(
            element_type=ElementType.PARAGRAPH,
            content=merged_block
        )
    
    def _detect_headers_footers(self, text_blocks: List[TextBlock]) -> Tuple[List[ContentElement], List[ContentElement]]:
        """
        检测页眉和页脚
        
        基于位置和重复性进行检测
        """
        if not text_blocks:
            return [], []
        
        # 获取页面尺寸
        page_blocks_dict = defaultdict(list)
        for block in text_blocks:
            page_blocks_dict[block.page_number].append(block)
        
        if not page_blocks_dict:
            return [], []
        
        # 计算平均页面高度
        page_heights = []
        for blocks in page_blocks_dict.values():
            if blocks:
                max_y = max(b.bbox.y1 for b in blocks)
                page_heights.append(max_y)
        
        if page_heights:
            avg_page_height = sum(page_heights) / len(page_heights)
        else:
            avg_page_height = 800
        
        header_region = avg_page_height * self.header_region_ratio
        footer_region_start = avg_page_height * (1 - self.footer_region_ratio)
        
        # 收集候选页眉页脚
        header_candidates = []
        footer_candidates = []
        
        for blocks in page_blocks_dict.values():
            for block in blocks:
                # 检查是否在页眉区域
                if block.bbox.y1 < header_region:
                    header_candidates.append(block)
                # 检查是否在页脚区域
                elif block.bbox.y0 > footer_region_start:
                    footer_candidates.append(block)
        
        # 基于重复性确定真正的页眉页脚
        headers = self._filter_by_repetition(header_candidates, min_pages=2)
        footers = self._filter_by_repetition(footer_candidates, min_pages=2)
        
        # 转换为ContentElement
        header_elements = [
            ContentElement(element_type=ElementType.HEADER, content=h)
            for h in headers
        ]
        footer_elements = [
            ContentElement(element_type=ElementType.FOOTER, content=f)
            for f in footers
        ]
        
        return header_elements, footer_elements
    
    def _filter_by_repetition(self, candidates: List[TextBlock], 
                              min_pages: int = 2) -> List[TextBlock]:
        """
        基于跨页重复性过滤候选元素
        
        真正的页眉页脚会在多个页面上重复出现
        """
        if not candidates:
            return []
        
        # 按内容分组
        content_groups = defaultdict(list)
        for block in candidates:
            # 简化文本用于比较（去除数字，保留主要文本）
            simplified = self._simplify_for_comparison(block.content)
            content_groups[simplified].append(block)
        
        # 找出在多个页面上重复出现的
        repeated = []
        for content, blocks in content_groups.items():
            # 统计出现的页面数
            pages = set(b.page_number for b in blocks)
            if len(pages) >= min_pages:
                # 选择最典型的一个（中间位置的）
                repeated.append(blocks[len(blocks) // 2])
        
        return repeated
    
    def _simplify_for_comparison(self, text: str) -> str:
        """
        简化文本用于比较
        
        去除页码数字等变化的部分
        """
        # 去除数字
        text = re.sub(r'\d+', '', text)
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()
    
    def _build_chapters(self, 
                       titles: List[Tuple[TextBlock, int]],
                       paragraphs: List[ContentElement],
                       images: List[ImageBlock],
                       tables: List[TableBlock]) -> List[Chapter]:
        """
        构建章节结构
        """
        if not titles:
            # 如果没有检测到标题，将所有内容放在一个章节
            all_elements = paragraphs.copy()
            
            # 添加图片和表格
            for img in images:
                all_elements.append(ContentElement(
                    element_type=ElementType.IMAGE,
                    content=img
                ))
            for table in tables:
                all_elements.append(ContentElement(
                    element_type=ElementType.TABLE,
                    content=table
                ))
            
            # 按阅读顺序排序
            all_elements.sort(key=lambda e: self._get_element_order(e))
            
            return [Chapter(
                title="正文",
                level=1,
                elements=all_elements,
                start_page=1,
                end_page=max((p.content.page_number for p in paragraphs if isinstance(p.content, TextBlock)), default=1)
            )]
        
        # 有标题的情况
        chapters = []
        title_stack = []  # 用于处理嵌套章节
        
        for i, (title_block, level) in enumerate(titles):
            # 创建章节
            chapter = Chapter(
                title=title_block.content.strip(),
                level=level,
                elements=[ContentElement(
                    element_type=ElementType.TITLE,
                    content=title_block
                )],
                start_page=title_block.page_number
            )
            
            # 确定父章节
            while title_stack and title_stack[-1][1] >= level:
                title_stack.pop()
            
            if title_stack:
                # 添加到父章节
                title_stack[-1][0].children.append(chapter)
            else:
                # 顶级章节
                chapters.append(chapter)
            
            title_stack.append((chapter, level))
            
            # 确定章节的内容范围
            next_title_idx = i + 1
            if next_title_idx < len(titles):
                next_title = titles[next_title_idx][0]
                end_page = next_title.page_number - 1
            else:
                end_page = max((p.content.page_number for p in paragraphs 
                              if isinstance(p.content, TextBlock)), default=title_block.page_number)
            
            chapter.end_page = end_page
            
            # 添加属于这个章节的内容（段落、图片、表格）
            self._add_content_to_chapter(chapter, paragraphs, images, tables)
        
        return chapters
    
    def _add_content_to_chapter(self, chapter: Chapter,
                               paragraphs: List[ContentElement],
                               images: List[ImageBlock],
                               tables: List[TableBlock]) -> None:
        """
        将内容添加到章节
        """
        # 添加段落
        for para in paragraphs:
            if isinstance(para.content, TextBlock):
                if chapter.start_page <= para.content.page_number <= chapter.end_page:
                    chapter.elements.append(para)
        
        # 添加图片
        for img in images:
            if chapter.start_page <= img.page_number <= chapter.end_page:
                chapter.elements.append(ContentElement(
                    element_type=ElementType.IMAGE,
                    content=img
                ))
        
        # 添加表格
        for table in tables:
            if chapter.start_page <= table.page_number <= chapter.end_page:
                chapter.elements.append(ContentElement(
                    element_type=ElementType.TABLE,
                    content=table
                ))
        
        # 按阅读顺序排序
        chapter.elements.sort(key=lambda e: self._get_element_order(e))
    
    def _get_element_order(self, element: ContentElement) -> int:
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