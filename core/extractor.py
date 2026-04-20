"""
内容提取器 - 从PDF中提取文本、图片、表格等内容元素
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from .parser import PDFParser
from .models import (
    TextBlock, ImageBlock, TableBlock, TableCell, 
    BoundingBox, TextStyle
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """内容提取配置"""
    min_text_length: int = 1  # 最小文本长度
    min_image_width: int = 50  # 最小图片宽度
    min_image_height: int = 50  # 最小图片高度
    extract_tables: bool = True  # 是否提取表格
    extract_hidden_text: bool = True  # 是否提取隐藏文本
    merge_split_paragraphs: bool = True  # 是否合并跨页段落


class ContentExtractor:
    """
    内容提取器
    
    负责从PDF中提取结构化的内容元素
    """
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self.parser: Optional[PDFParser] = None
    
    def extract(self, parser: PDFParser) -> Tuple[List[TextBlock], List[ImageBlock], List[TableBlock]]:
        """
        从PDF中提取所有内容
        
        Args:
            parser: PDF解析器实例
            
        Returns:
            (文本块列表, 图片块列表, 表格块列表)
        """
        self.parser = parser
        all_text_blocks = []
        all_image_blocks = []
        all_table_blocks = []
        
        logger.info(f"开始提取内容，共 {parser.page_count} 页")
        
        for page_num in range(parser.page_count):
            logger.debug(f"处理第 {page_num + 1} 页")
            
            # 提取文本
            text_blocks = parser.extract_text_blocks(
                page_num, 
                min_text_length=self.config.min_text_length
            )
            all_text_blocks.extend(text_blocks)
            
            # 提取图片
            image_blocks = parser.extract_images(
                page_num,
                min_size=min(self.config.min_image_width, self.config.min_image_height)
            )
            all_image_blocks.extend(image_blocks)
            
            # 表格提取（简化版，实际可使用专门的表格检测库）
            if self.config.extract_tables:
                table_blocks = self._extract_tables_from_page(page_num, text_blocks)
                all_table_blocks.extend(table_blocks)
        
        # 后处理
        if self.config.merge_split_paragraphs:
            all_text_blocks = self._merge_split_paragraphs(all_text_blocks)
        
        # 计算阅读顺序
        all_text_blocks = self._calculate_reading_order(all_text_blocks)
        
        logger.info(f"提取完成: {len(all_text_blocks)} 个文本块, "
                   f"{len(all_image_blocks)} 张图片, "
                   f"{len(all_table_blocks)} 个表格")
        
        return all_text_blocks, all_image_blocks, all_table_blocks
    
    def _extract_tables_from_page(self, page_num: int, 
                                  text_blocks: List[TextBlock]) -> List[TableBlock]:
        """
        从页面中提取表格（简化实现）
        
        注：完整实现需要使用专门的表格检测库如camelot或table-transformer
        """
        tables = []
        
        # 简单的表格检测：查找对齐的文本块
        if len(text_blocks) < 4:
            return tables
        
        # 按垂直位置排序
        sorted_blocks = sorted(text_blocks, key=lambda b: b.bbox.y0)
        
        # 检测可能的表格行（具有相似Y坐标的文本块组）
        rows = []
        current_row = [sorted_blocks[0]]
        
        for block in sorted_blocks[1:]:
            # 如果Y坐标接近，认为是同一行
            if abs(block.bbox.y0 - current_row[0].bbox.y0) < 5:
                current_row.append(block)
            else:
                if len(current_row) >= 2:  # 至少2列
                    rows.append(current_row)
                current_row = [block]
        
        # 如果有多个行且列数一致，可能是表格
        if len(rows) >= 2:
            col_counts = [len(row) for row in rows]
            if max(col_counts) == min(col_counts) and col_counts[0] >= 2:
                # 创建表格
                table_cells = []
                for row_idx, row in enumerate(rows):
                    # 按X坐标排序
                    sorted_row = sorted(row, key=lambda b: b.bbox.x0)
                    row_cells = []
                    for col_idx, cell_block in enumerate(sorted_row):
                        cell = TableCell(
                            content=cell_block.content,
                            row=row_idx,
                            col=col_idx,
                            bbox=cell_block.bbox
                        )
                        row_cells.append(cell)
                    table_cells.append(row_cells)
                
                # 合并边界框
                if table_cells and table_cells[0]:
                    first_cell = table_cells[0][0]
                    last_cell = table_cells[-1][-1]
                    bbox = BoundingBox(
                        x0=first_cell.bbox.x0 if first_cell.bbox else 0,
                        y0=first_cell.bbox.y0 if first_cell.bbox else 0,
                        x1=last_cell.bbox.x1 if last_cell.bbox else 0,
                        y1=last_cell.bbox.y1 if last_cell.bbox else 0
                    )
                else:
                    bbox = BoundingBox(0, 0, 0, 0)
                
                table = TableBlock(
                    cells=table_cells,
                    bbox=bbox,
                    page_number=page_num,
                    confidence=0.6
                )
                tables.append(table)
        
        return tables
    
    def _merge_split_paragraphs(self, text_blocks: List[TextBlock]) -> List[TextBlock]:
        """
        合并被分页符打断的段落
        
        检查连续页面末尾和开头的文本块，如果符合段落特征则合并
        """
        if len(text_blocks) < 2:
            return text_blocks
        
        # 按页码和阅读顺序排序
        sorted_blocks = sorted(text_blocks, key=lambda b: (b.page_number, b.bbox.y0))
        
        merged_blocks = []
        i = 0
        while i < len(sorted_blocks):
            current_block = sorted_blocks[i]
            
            # 检查是否是页面最后一行且可能是不完整的段落
            if i + 1 < len(sorted_blocks):
                next_block = sorted_blocks[i + 1]
                
                # 如果是跨页的文本块
                if (next_block.page_number == current_block.page_number + 1 and
                    self._is_continuation(current_block, next_block)):
                    
                    # 合并内容
                    merged_content = current_block.content.rstrip()
                    # 如果末尾有连字符，去掉连字符
                    if merged_content.endswith('-'):
                        merged_content = merged_content[:-1]
                    else:
                        merged_content += ' '
                    merged_content += next_block.content.lstrip()
                    
                    # 更新边界框（取并集）
                    merged_bbox = current_block.bbox.merge(next_block.bbox)
                    
                    # 创建新的合并块
                    merged_block = TextBlock(
                        content=merged_content,
                        bbox=merged_bbox,
                        style=current_block.style,  # 使用第一个块的样式
                        page_number=current_block.page_number,
                        confidence=min(current_block.confidence, next_block.confidence)
                    )
                    
                    merged_blocks.append(merged_block)
                    i += 2  # 跳过下一个块
                    continue
            
            merged_blocks.append(current_block)
            i += 1
        
        return merged_blocks
    
    def _is_continuation(self, block1: TextBlock, block2: TextBlock) -> bool:
        """
        判断两个文本块是否是同一段落的延续
        
        判断依据：
        1. 字体样式相同
        2. 缩进一致
        3. 文本内容连贯（block1不以标点结尾）
        """
        # 检查样式是否一致
        if (block1.style.font_name != block2.style.font_name or
            abs(block1.style.font_size - block2.style.font_size) > 0.5):
            return False
        
        # 检查block1是否以标点结尾（完整的句子）
        text1 = block1.content.strip()
        if text1 and text1[-1] in '.。!！?？""''':
            return False
        
        # 检查缩进是否一致
        if abs(block1.bbox.x0 - block2.bbox.x0) > 10:
            return False
        
        return True
    
    def _calculate_reading_order(self, text_blocks: List[TextBlock]) -> List[TextBlock]:
        """
        计算文本块的阅读顺序
        
        基于垂直位置优先，水平位置其次的原则
        同时考虑多栏布局
        """
        if not text_blocks:
            return []
        
        # 按页面分组
        page_groups = {}
        for block in text_blocks:
            page_num = block.page_number
            if page_num not in page_groups:
                page_groups[page_num] = []
            page_groups[page_num].append(block)
        
        # 对每个页面的文本块计算阅读顺序
        ordered_blocks = []
        for page_num in sorted(page_groups.keys()):
            page_blocks = page_groups[page_num]
            
            # 检测栏数（通过X坐标分布）
            x_positions = [b.bbox.x0 for b in page_blocks]
            if len(x_positions) < 2:
                column_count = 1
            else:
                # 简单的栏检测：计算X坐标的聚类
                sorted_x = sorted(set(x_positions))
                if len(sorted_x) >= 2:
                    avg_gap = sum(sorted_x[i+1] - sorted_x[i] 
                                for i in range(len(sorted_x)-1)) / (len(sorted_x)-1)
                    if avg_gap > 100:  # 如果平均间隔大于100，可能是多栏
                        column_count = 2
                    else:
                        column_count = 1
                else:
                    column_count = 1
            
            # 根据栏数排序
            if column_count == 1:
                # 单栏：按Y坐标排序
                page_blocks.sort(key=lambda b: b.bbox.y0)
            else:
                # 多栏：先按栏排序，再按Y排序
                # 简单的栏检测：基于X坐标
                mid_x = sum(b.bbox.x0 for b in page_blocks) / len(page_blocks)
                left_column = [b for b in page_blocks if b.bbox.x0 < mid_x]
                right_column = [b for b in page_blocks if b.bbox.x0 >= mid_x]
                
                left_column.sort(key=lambda b: b.bbox.y0)
                right_column.sort(key=lambda b: b.bbox.y0)
                
                # 交错合并（左栏在前）
                page_blocks = []
                i = 0
                while i < len(left_column) or i < len(right_column):
                    if i < len(left_column):
                        page_blocks.append(left_column[i])
                    if i < len(right_column):
                        page_blocks.append(right_column[i])
                    i += 1
            
            # 设置阅读顺序
            for idx, block in enumerate(page_blocks):
                block.reading_order = idx
            
            ordered_blocks.extend(page_blocks)
        
        return ordered_blocks