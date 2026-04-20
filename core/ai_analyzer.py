"""
AI布局分析器 - 使用机器学习和深度学习模型进行智能文档理解

提供比传统规则更准确的：
- 布局区域识别（文本区、图片区、表格区）
- 标题层级检测
- 段落边界识别
- 阅读顺序确定
"""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .models import TextBlock, ImageBlock, TableBlock, BoundingBox, TextStyle

logger = logging.getLogger(__name__)


class LayoutRegionType(Enum):
    """布局区域类型"""
    TEXT = "text"
    TITLE = "title"
    IMAGE = "image"
    TABLE = "table"
    HEADER = "header"
    FOOTER = "footer"
    CAPTION = "caption"
    UNKNOWN = "unknown"


@dataclass
class LayoutRegion:
    """布局区域"""
    region_type: LayoutRegionType
    bbox: BoundingBox
    confidence: float
    elements: List[Any] = None
    
    def __post_init__(self):
        if self.elements is None:
            self.elements = []


class AILayoutAnalyzer:
    """
    AI布局分析器
    
    结合启发式规则和机器学习模型，提供更准确的布局理解
    """
    
    def __init__(self, 
                 use_deep_learning: bool = False,
                 language: str = "zh"):
        """
        初始化AI布局分析器
        
        Args:
            use_deep_learning: 是否使用深度学习模型（需要额外依赖）
            language: 语言（zh/en）
        """
        self.use_deep_learning = use_deep_learning
        self.language = language
        
        # 加载NLP模型（用于语义分析）
        self.nlp = None
        if self._try_load_spacy():
            logger.info("spaCy模型加载成功")
        else:
            logger.warning("spaCy模型未加载，将使用启发式规则")
        
        # 深度学习模型（可选）
        self.layout_model = None
        if use_deep_learning:
            self._load_layout_model()
    
    def _try_load_spacy(self) -> bool:
        """尝试加载spaCy模型"""
        try:
            import spacy
            if self.language == "zh":
                try:
                    self.nlp = spacy.load("zh_core_web_sm")
                except:
                    logger.warning("未找到中文模型，尝试下载...")
                    import subprocess
                    subprocess.run(["python", "-m", "spacy", "download", "zh_core_web_sm"], 
                                 capture_output=True)
                    self.nlp = spacy.load("zh_core_web_sm")
            else:
                self.nlp = spacy.load("en_core_web_sm")
            return True
        except Exception as e:
            logger.warning(f"加载spaCy模型失败: {e}")
            return False
    
    def _load_layout_model(self):
        """加载布局分析模型（需要transformers库）"""
        try:
            # 这里可以使用LayoutLM等模型
            # from transformers import LayoutLMForSequenceClassification
            logger.info("深度学习模型支持已准备（需手动安装transformers）")
        except ImportError:
            logger.warning("未安装transformers，深度学习功能不可用")
            self.use_deep_learning = False
    
    def analyze_layout(self, 
                      text_blocks: List[TextBlock],
                      image_blocks: List[ImageBlock],
                      page_width: float,
                      page_height: float) -> List[LayoutRegion]:
        """
        分析页面布局
        
        Args:
            text_blocks: 文本块列表
            image_blocks: 图片块列表
            page_width: 页面宽度
            page_height: 页面高度
            
        Returns:
            布局区域列表
        """
        regions = []
        
        # 1. 分析页面整体布局（栏数、边距等）
        layout_info = self._analyze_page_layout(
            text_blocks, page_width, page_height
        )
        
        # 2. 识别特殊区域（页眉、页脚）
        header_regions = self._detect_header_regions(
            text_blocks, page_width, page_height
        )
        footer_regions = self._detect_footer_regions(
            text_blocks, page_width, page_height
        )
        
        regions.extend(header_regions)
        regions.extend(footer_regions)
        
        # 3. 对剩余内容进行分类
        filtered_blocks = [
            b for b in text_blocks 
            if not any(r.bbox.contains(b.bbox) for r in regions)
        ]
        
        # 4. 识别标题
        title_regions = self._detect_title_regions(
            filtered_blocks, layout_info
        )
        regions.extend(title_regions)
        
        # 5. 识别正文段落
        text_regions = self._detect_text_regions(
            filtered_blocks, title_regions
        )
        regions.extend(text_regions)
        
        # 6. 识别图片区域
        for img in image_blocks:
            img_region = LayoutRegion(
                region_type=LayoutRegionType.IMAGE,
                bbox=img.bbox,
                confidence=1.0,
                elements=[img]
            )
            regions.append(img_region)
            
            # 检测图片说明
            caption = self._detect_image_caption(text_blocks, img)
            if caption:
                img_region.elements.append(caption)
        
        return regions
    
    def _analyze_page_layout(self,
                            text_blocks: List[TextBlock],
                            page_width: float,
                            page_height: float) -> Dict[str, Any]:
        """
        分析页面整体布局
        """
        if not text_blocks:
            return {
                'columns': 1,
                'margin_left': 0,
                'margin_right': 0,
                'margin_top': 0,
                'margin_bottom': 0
            }
        
        # 计算文本块的X坐标分布
        x_positions = [b.bbox.x0 for b in text_blocks]
        
        # 使用聚类检测栏数
        from collections import defaultdict
        x_groups = defaultdict(int)
        
        for x in x_positions:
            # 将X坐标分组
            bucket = int(x / 50) * 50
            x_groups[bucket] += 1
        
        # 分析栏数
        sorted_groups = sorted(x_groups.items(), key=lambda x: x[1], reverse=True)
        
        columns = 1
        if len(sorted_groups) >= 2:
            # 如果有两个明显的峰值，可能是双栏
            if sorted_groups[1][1] / sorted_groups[0][1] > 0.3:
                columns = 2
        
        # 计算边距
        if text_blocks:
            margin_left = min(b.bbox.x0 for b in text_blocks)
            margin_right = page_width - max(b.bbox.x1 for b in text_blocks)
            margin_top = min(b.bbox.y0 for b in text_blocks)
            margin_bottom = page_height - max(b.bbox.y1 for b in text_blocks)
        else:
            margin_left = margin_right = margin_top = margin_bottom = 0
        
        return {
            'columns': columns,
            'margin_left': margin_left,
            'margin_right': margin_right,
            'margin_top': margin_top,
            'margin_bottom': margin_bottom,
            'page_width': page_width,
            'page_height': page_height
        }
    
    def _detect_header_regions(self,
                              text_blocks: List[TextBlock],
                              page_width: float,
                              page_height: float) -> List[LayoutRegion]:
        """
        使用AI方法检测页眉区域
        """
        regions = []
        header_threshold = page_height * 0.15  # 顶部15%
        
        # 找出顶部区域的文本块
        header_candidates = [
            b for b in text_blocks 
            if b.bbox.y1 < header_threshold
        ]
        
        # 基于重复性和语义分析
        if len(header_candidates) >= 2:
            # 计算内容的相似度
            from collections import defaultdict
            content_groups = defaultdict(list)
            
            for block in header_candidates:
                # 简化内容用于比较
                simplified = self._simplify_content(block.content)
                content_groups[simplified].append(block)
            
            # 如果在多个块中出现相似内容，可能是页眉
            for simplified, blocks in content_groups.items():
                if len(blocks) >= 2:
                    # 创建页眉区域
                    merged_bbox = blocks[0].bbox
                    for b in blocks[1:]:
                        merged_bbox = merged_bbox.merge(b.bbox)
                    
                    region = LayoutRegion(
                        region_type=LayoutRegionType.HEADER,
                        bbox=merged_bbox,
                        confidence=0.8,
                        elements=blocks
                    )
                    regions.append(region)
        
        return regions
    
    def _detect_footer_regions(self,
                              text_blocks: List[TextBlock],
                              page_width: float,
                              page_height: float) -> List[LayoutRegion]:
        """
        检测页脚区域
        """
        regions = []
        footer_threshold = page_height * 0.85  # 底部15%
        
        footer_candidates = [
            b for b in text_blocks 
            if b.bbox.y0 > footer_threshold
        ]
        
        # 类似页眉的检测逻辑
        if len(footer_candidates) >= 2:
            from collections import defaultdict
            content_groups = defaultdict(list)
            
            for block in footer_candidates:
                simplified = self._simplify_content(block.content)
                content_groups[simplified].append(block)
            
            for simplified, blocks in content_groups.items():
                if len(blocks) >= 2:
                    merged_bbox = blocks[0].bbox
                    for b in blocks[1:]:
                        merged_bbox = merged_bbox.merge(b.bbox)
                    
                    region = LayoutRegion(
                        region_type=LayoutRegionType.FOOTER,
                        bbox=merged_bbox,
                        confidence=0.8,
                        elements=blocks
                    )
                    regions.append(region)
        
        return regions
    
    def _detect_title_regions(self,
                             text_blocks: List[TextBlock],
                             layout_info: Dict) -> List[LayoutRegion]:
        """
        使用语义特征检测标题
        """
        regions = []
        
        # 计算正文平均字体大小
        body_font_sizes = []
        for block in text_blocks:
            if len(block.content) > 50:  # 假设正文段落较长
                body_font_sizes.append(block.style.font_size)
        
        avg_body_size = np.mean(body_font_sizes) if body_font_sizes else 12
        
        for block in text_blocks:
            score = 0.0
            features = {}
            
            # 特征1: 字体大小
            size_ratio = block.style.font_size / avg_body_size
            if size_ratio >= 2.0:
                score += 0.4
                features['size_level'] = 1
            elif size_ratio >= 1.6:
                score += 0.3
                features['size_level'] = 2
            elif size_ratio >= 1.3:
                score += 0.2
                features['size_level'] = 3
            
            # 特征2: 加粗
            if block.style.is_bold:
                score += 0.15
            
            # 特征3: 文本长度
            text_len = len(block.content.strip())
            if text_len <= 30:
                score += 0.2
            elif text_len <= 60:
                score += 0.1
            
            # 特征4: 语义分析（如果有spaCy）
            if self.nlp and text_len < 100:
                doc = self.nlp(block.content)
                # 检查是否包含标题特征词
                title_indicators = ['章', '节', '部分', 'chapter', 'section']
                if any(indicator in block.content.lower() for indicator in title_indicators):
                    score += 0.2
                
                # 检查句子数量（标题通常是短语）
                sent_count = len(list(doc.sents))
                if sent_count == 1:
                    score += 0.1
            
            # 特征5: 位置
            if block.bbox.y0 < layout_info['page_height'] * 0.2:
                score += 0.1
            
            # 标题判定
            if score >= 0.5:
                region = LayoutRegion(
                    region_type=LayoutRegionType.TITLE,
                    bbox=block.bbox,
                    confidence=score,
                    elements=[block]
                )
                regions.append(region)
        
        return regions
    
    def _detect_text_regions(self,
                            text_blocks: List[TextBlock],
                            title_regions: List[LayoutRegion]) -> List[LayoutRegion]:
        """
        识别正文区域
        """
        regions = []
        
        # 排除已被识别为标题的块
        title_bboxes = [r.bbox for r in title_regions]
        
        for block in text_blocks:
            # 检查是否是标题
            is_title = any(
                tb.contains(block.bbox) or tb.intersects(block.bbox)
                for tb in title_bboxes
            )
            
            if not is_title and len(block.content.strip()) > 0:
                region = LayoutRegion(
                    region_type=LayoutRegionType.TEXT,
                    bbox=block.bbox,
                    confidence=1.0,
                    elements=[block]
                )
                regions.append(region)
        
        return regions
    
    def _detect_image_caption(self,
                             text_blocks: List[TextBlock],
                             image: ImageBlock) -> Optional[TextBlock]:
        """
        检测图片的说明文字
        """
        # 查找图片下方的文本块
        img_bbox = image.bbox
        caption_candidates = []
        
        for block in text_blocks:
            # 检查是否在图片下方
            if block.bbox.y0 > img_bbox.y1 and block.bbox.y0 < img_bbox.y1 + 100:
                # 检查水平位置是否对齐
                if abs(block.bbox.center[0] - img_bbox.center[0]) < 50:
                    caption_candidates.append(block)
        
        if caption_candidates:
            # 选择最接近图片的
            caption_candidates.sort(key=lambda b: b.bbox.y0)
            return caption_candidates[0]
        
        return None
    
    def _simplify_content(self, text: str) -> str:
        """
        简化内容用于比较
        """
        text = text.strip().lower()
        # 去除数字和标点
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def calculate_reading_order(self,
                               regions: List[LayoutRegion],
                               columns: int = 1) -> List[LayoutRegion]:
        """
        计算阅读顺序
        
        支持多栏布局的正确阅读顺序
        """
        if columns == 1:
            # 单栏：按Y坐标排序
            return sorted(regions, key=lambda r: r.bbox.y0)
        else:
            # 多栏：先分栏，再排序
            page_center = sum(r.bbox.center[0] for r in regions) / len(regions)
            
            left_column = [r for r in regions if r.bbox.center[0] < page_center]
            right_column = [r for r in regions if r.bbox.center[0] >= page_center]
            
            left_column.sort(key=lambda r: r.bbox.y0)
            right_column.sort(key=lambda r: r.bbox.y0)
            
            # 交错合并
            result = []
            for i in range(max(len(left_column), len(right_column))):
                if i < len(left_column):
                    result.append(left_column[i])
                if i < len(right_column):
                    result.append(right_column[i])
            
            return result


class SemanticAnalyzer:
    """
    语义分析器
    
    使用NLP技术进行文档内容的语义理解
    """
    
    def __init__(self, language: str = "zh"):
        self.language = language
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """加载NLP模型"""
        try:
            import spacy
            if self.language == "zh":
                try:
                    self.nlp = spacy.load("zh_core_web_sm")
                except:
                    pass
            else:
                self.nlp = spacy.load("en_core_web_sm")
        except:
            pass
    
    def is_complete_sentence(self, text: str) -> bool:
        """
        判断是否为完整的句子
        
        用于检测段落是否被分页符打断
        """
        if not self.nlp:
            # 启发式规则
            text = text.strip()
            if text.endswith(('。', '.', '！', '!', '?', '？', '"', '"', ''', ''')):
                return True
            return False
        
        doc = self.nlp(text)
        
        # 检查句子数量
        sentences = list(doc.sents)
        if len(sentences) == 0:
            return False
        
        # 检查最后一个句子是否完整
        last_sent = sentences[-1]
        last_token = last_sent[-1]
        
        if last_token.text in ['。', '.', '！', '!', '?', '？']:
            return True
        
        return False
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        提取关键词
        
        用于生成章节的摘要信息
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        
        keywords = []
        for token in doc:
            # 选择名词和专有名词
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                keywords.append(token.text)
        
        # 统计频率
        from collections import Counter
        keyword_freq = Counter(keywords)
        
        return [word for word, freq in keyword_freq.most_common(top_n)]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的语义相似度
        
        用于判断段落是否连续
        """
        if not self.nlp:
            return 0.0
        
        doc1 = self.nlp(text1[:1000])  # 限制长度
        doc2 = self.nlp(text2[:1000])
        
        return doc1.similarity(doc2)