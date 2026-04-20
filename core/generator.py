"""
EPUB生成器 - 生成符合EPUB标准的电子书文件
"""

import os
import re
import io
import zipfile
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from .models import (
    TextBlock, ImageBlock, TableBlock, ContentElement,
    ElementType, Chapter, DocumentStructure
)

logger = logging.getLogger(__name__)


@dataclass
class EPUBConfig:
    """EPUB生成配置"""
    title: str = ""
    author: str = ""
    language: str = "zh-CN"
    publisher: str = "PDF Restructor"
    description: str = ""
    rights: str = ""
    
    # 样式配置
    font_size: int = 16
    line_height: float = 1.6
    font_family: str = "'Songti SC', 'SimSun', serif"
    paragraph_indent: int = 2  # 字符数
    
    # 输出配置
    generate_cover: bool = True
    embed_images: bool = True
    image_quality: int = 85
    max_image_width: int = 800
    
    # 文件配置
    css_filename: str = "style.css"
    toc_filename: str = "toc.xhtml"
    nav_filename: str = "nav.xhtml"


class EPUBGenerator:
    """
    EPUB生成器
    
    将处理后的文档结构转换为符合EPUB 3.0标准的电子书文件
    """
    
    def __init__(self, config: Optional[EPUBConfig] = None):
        self.config = config or EPUBConfig()
        self.image_counter = 0
        self.images_to_embed: Dict[str, bytes] = {}
    
    def generate(self, structure: DocumentStructure, output_path: str) -> bool:
        """
        生成EPUB文件
        
        Args:
            structure: 处理后的文档结构
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        try:
            logger.info(f"开始生成EPUB: {output_path}")
            
            # 准备EPUB内容
            epub_content = self._prepare_epub_content(structure)
            
            # 创建EPUB文件
            self._create_epub_file(epub_content, output_path)
            
            logger.info(f"EPUB生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成EPUB时出错: {e}")
            return False
    
    def _prepare_epub_content(self, structure: DocumentStructure) -> Dict[str, Any]:
        """
        准备EPUB内容
        """
        content = {
            'mimetype': 'application/epub+zip',
            'container_xml': self._generate_container_xml(),
            'content_opf': self._generate_content_opf(structure),
            'toc_ncx': self._generate_toc_ncx(structure),
            'nav_xhtml': self._generate_nav_xhtml(structure),
            'style_css': self._generate_style_css(),
            'chapters': [],
            'images': {}
        }
        
        # 生成章节内容
        for i, chapter in enumerate(structure.chapters):
            chapter_filename = f"chapter_{i+1:03d}.xhtml"
            chapter_content = self._generate_chapter_xhtml(chapter, chapter_filename)
            content['chapters'].append({
                'filename': chapter_filename,
                'content': chapter_content,
                'title': chapter.title
            })
        
        # 准备图片
        for img in structure.images:
            self.image_counter += 1
            img_filename = f"image_{self.image_counter:04d}.{img.format.lower()}"
            content['images'][img_filename] = img.image_data
        
        return content
    
    def _generate_container_xml(self) -> str:
        """
        生成META-INF/container.xml
        """
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
    
    def _generate_content_opf(self, structure: DocumentStructure) -> str:
        """
        生成OEBPS/content.opf
        
        EPUB包文件，包含元数据和资源清单
        """
        # 生成唯一ID
        import uuid
        book_id = str(uuid.uuid4())
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # 章节清单
        item_list = []
        for i, chapter in enumerate(structure.chapters):
            item_list.append(f'        <item id="chapter_{i+1}" href="chapters/chapter_{i+1:03d}.xhtml" media-type="application/xhtml+xml"/>')
        
        # 图片清单
        for img_name in self.images_to_embed.keys():
            ext = Path(img_name).suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                media_type = 'image/jpeg'
            elif ext == '.png':
                media_type = 'image/png'
            elif ext == '.gif':
                media_type = 'image/gif'
            else:
                media_type = 'image/jpeg'
            item_list.append(f'        <item id="{Path(img_name).stem}" href="images/{img_name}" media-type="{media_type}"/>')
        
        # 构建manifest
        manifest = '\n'.join(item_list)
        
        # 章节引用（spine）
        itemref_list = []
        for i in range(len(structure.chapters)):
            itemref_list.append(f'        <itemref idref="chapter_{i+1}"/>')
        itemrefs = '\n'.join(itemref_list)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="bookid">{book_id}</dc:identifier>
        <dc:title>{self._escape_xml(structure.title or self.config.title or "无标题")}</dc:title>
        <dc:creator>{self._escape_xml(structure.author or self.config.author or "未知")}</dc:creator>
        <dc:language>{self.config.language}</dc:language>
        <dc:publisher>{self._escape_xml(self.config.publisher)}</dc:publisher>
        <dc:date>{timestamp}</dc:date>
        <meta property="dcterms:modified">{timestamp}</meta>
    </metadata>
    <manifest>
        <item id="toc" href="{self.config.toc_filename}" media-type="application/xhtml+xml" properties="nav"/>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        <item id="css" href="styles/{self.config.css_filename}" media-type="text/css"/>
{manifest}
    </manifest>
    <spine toc="ncx">
        <itemref idref="toc"/>
{itemrefs}
    </spine>
</package>'''
    
    def _generate_toc_ncx(self, structure: DocumentStructure) -> str:
        """
        生成OEBPS/toc.ncx
        
        传统格式的目录（NCX），用于兼容性
        """
        nav_points = []
        play_order = 1
        
        for i, chapter in enumerate(structure.chapters):
            nav_points.append(f'''
        <navPoint id="chapter_{i+1}" playOrder="{play_order}">
            <navLabel>
                <text>{self._escape_xml(chapter.title)}</text>
            </navLabel>
            <content src="chapters/chapter_{i+1:03d}.xhtml"/>
        </navPoint>''')
            play_order += 1
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content=""/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{self._escape_xml(structure.title or self.config.title or "无标题")}</text>
    </docTitle>
    <navMap>
{chr(10).join(nav_points)}
    </navMap>
</ncx>'''
    
    def _generate_nav_xhtml(self, structure: DocumentStructure) -> str:
        """
        生成OEBPS/nav.xhtml
        
        EPUB 3.0格式的导航文档
        """
        toc_items = []
        
        for i, chapter in enumerate(structure.chapters):
            toc_items.append(f'                <li><a href="chapters/chapter_{i+1:03d}.xhtml">{self._escape_xml(chapter.title)}</a></li>')
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>目录</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="styles/style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>目录</h1>
        <ol>
{chr(10).join(toc_items)}
        </ol>
    </nav>
</body>
</html>'''
    
    def _generate_style_css(self) -> str:
        """
        生成OEBPS/styles/style.css
        
        优化的EPUB样式，支持更好的中文排版和字体调整
        """
        indent_em = self.config.paragraph_indent * 0.5
        
        # 字体回退栈配置
        font_stacks = {
            'serif': "'Source Han Serif CN', 'Noto Serif CJK SC', 'Source Han Serif SC', 'STSong', 'SimSun', 'Songti SC', 'FangSong', serif",
            'sans-serif': "'Source Han Sans CN', 'Noto Sans CJK SC', 'Source Han Sans SC', 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif",
            'monospace': "'Noto Sans Mono CJK SC', 'SF Mono', 'Monaco', 'Inconsolata', 'PingFang SC', 'Microsoft YaHei Mono', monospace"
        }
        
        # 根据配置选择字体
        if 'serif' in self.config.font_family.lower():
            selected_font = font_stacks['serif']
        elif 'sans' in self.config.font_family.lower() or 'heiti' in self.config.font_family.lower():
            selected_font = font_stacks['sans-serif']
        else:
            selected_font = self.config.font_family
        
        return f'''/* EPUB样式表 - 优化版 */

/* ========================================
   基础样式
   ======================================== */

/* 阅读器变量支持 - 允许阅读器覆盖 */
:root {{
    --font-size: {self.config.font_size}px;
    --line-height: {self.config.line_height};
    --text-color: #333;
    --bg-color: #fff;
    --link-color: #0066cc;
    --heading-color: #222;
}}

/* 基础样式 */
body {{
    font-family: {selected_font};
    font-size: var(--font-size, {self.config.font_size}px);
    line-height: var(--line-height, {self.config.line_height});
    color: var(--text-color, #333);
    background-color: var(--bg-color, #fff);
    margin: 0;
    padding: 1.5em;
    text-align: justify;
    text-align-last: left;
    -webkit-hyphens: auto;
    -moz-hyphens: auto;
    hyphens: auto;
    word-wrap: break-word;
    overflow-wrap: break-word;
}}

/* 链接样式 */
a {{
    color: var(--link-color, #0066cc);
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

/* ========================================
   标题样式 - 层级清晰
   ======================================== */

h1, h2, h3, h4, h5, h6 {{
    font-weight: 600;
    color: var(--heading-color, #222);
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    line-height: 1.3;
    page-break-after: avoid;
    page-break-inside: avoid;
}}

h1 {{ 
    font-size: 2em;
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1em;
    border-bottom: 2px solid #ddd;
    padding-bottom: 0.5em;
}}

h2 {{ 
    font-size: 1.6em;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.3em;
}}

h3 {{ font-size: 1.3em; }}

h4 {{ font-size: 1.15em; }}

h5 {{ font-size: 1.05em; }}

h6 {{ font-size: 1em; font-weight: normal; color: #555; }}

/* ========================================
   段落样式 - 首行缩进
   ======================================== */

p {{
    margin: 0;
    margin-bottom: 0.8em;
    text-indent: {indent_em}em;
}}

p:first-of-type {{
    text-indent: 0;
}}

/* 特殊段落 */
p.no-indent {{
    text-indent: 0;
}}

p.center {{
    text-align: center;
    text-indent: 0;
}}

p.right {{
    text-align: right;
    text-indent: 0;
}}

/* ========================================
   章节样式
   ======================================== */

.chapter {{
    page-break-before: always;
}}

.chapter:first-of-type {{
    page-break-before: auto;
}}

.chapter-title {{
    text-align: center;
    margin-top: 3em;
    margin-bottom: 2em;
}}

/* ========================================
   图片样式 - 响应式
   ======================================== */

img {{
    max-width: 100%;
    max-height: 80vh;
    height: auto;
    display: block;
    margin: 1.5em auto;
    page-break-inside: avoid;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

figure {{
    margin: 2em 0;
    text-align: center;
    page-break-inside: avoid;
}}

figcaption {{
    font-size: 0.9em;
    color: #666;
    margin-top: 0.8em;
    text-align: center;
    font-style: italic;
}}

/* ========================================
   表格样式
   ======================================== */

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    page-break-inside: avoid;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}}

thead {{
    background-color: #f5f5f5;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 0.8em;
    text-align: left;
    vertical-align: top;
}}

th {{
    font-weight: 600;
    background-color: #f5f5f5;
    color: #222;
}}

tr:nth-child(even) {{
    background-color: #fafafa;
}}

caption {{
    font-weight: 600;
    margin-bottom: 0.8em;
    text-align: center;
    caption-side: top;
}}

/* ========================================
   列表样式
   ======================================== */

ul, ol {{
    margin: 1em 0;
    padding-left: 2.5em;
}}

li {{
    margin-bottom: 0.5em;
    line-height: 1.6;
}}

li::marker {{
    color: #666;
}}

/* 嵌套列表 */
li > ul, li > ol {{
    margin: 0.5em 0;
}}

/* ========================================
   引用和注释
   ======================================== */

blockquote {{
    margin: 1.5em 2em;
    padding: 1em;
    border-left: 4px solid #ccc;
    background-color: #f9f9f9;
    font-style: italic;
    color: #555;
}}

blockquote p {{
    text-indent: 0;
    margin: 0;
}}

blockquote p + p {{
    margin-top: 0.8em;
}}

/* ========================================
   代码和预格式化文本
   ======================================== */

code {{
    font-family: {font_stacks['monospace']};
    font-size: 0.9em;
    background-color: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
}}

pre {{
    font-family: {font_stacks['monospace']};
    font-size: 0.85em;
    line-height: 1.4;
    background-color: #f4f4f4;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    margin: 1.5em 0;
}}

pre code {{
    background-color: transparent;
    padding: 0;
}}

/* ========================================
   目录样式
   ======================================== */

nav#toc {{
    font-size: 1.1em;
}}

nav#toc h1 {{
    font-size: 1.5em;
    margin-bottom: 1em;
    border-bottom: 2px solid #333;
    padding-bottom: 0.5em;
}}

nav#toc ol {{
    list-style: none;
    padding-left: 0;
}}

nav#toc li {{
    margin-bottom: 0.6em;
}}

nav#toc li.level-2 {{
    padding-left: 1.5em;
    font-size: 0.95em;
}}

nav#toc li.level-3 {{
    padding-left: 3em;
    font-size: 0.9em;
}}

nav#toc a {{
    text-decoration: none;
    color: #333;
    display: block;
    padding: 0.3em 0;
    border-bottom: 1px dotted #ddd;
}}

nav#toc a:hover {{
    background-color: #f5f5f5;
}}

/* ========================================
   分页控制
   ======================================== */

.page-break {{
    page-break-before: always;
}}

.page-break-after {{
    page-break-after: always;
}}

/* 避免孤行寡行 */
h1, h2, h3, h4, h5, h6 {{
    orphans: 3;
    widows: 3;
}}

p {{
    orphans: 2;
    widows: 2;
}}

/* ========================================
   响应式调整（针对移动设备）
   ======================================== */

@media screen and (max-width: 600px) {{
    body {{
        padding: 1em;
        font-size: {self.config.font_size - 1}px;
    }}
    
    h1 {{ font-size: 1.6em; }}
    h2 {{ font-size: 1.4em; }}
    h3 {{ font-size: 1.2em; }}
    
    ul, ol {{
        padding-left: 2em;
    }}
    
    blockquote {{
        margin: 1em 1em;
        padding: 0.8em;
    }}
}}

/* ========================================
   夜间模式支持（阅读器可能覆盖）
   ======================================== */

@media (prefers-color-scheme: dark) {{
    :root {{
        --text-color: #ddd;
        --bg-color: #2a2a2a;
        --link-color: #66b3ff;
        --heading-color: #eee;
    }}
    
    img {{
        opacity: 0.9;
    }}
    
    blockquote {{
        background-color: #3a3a3a;
        border-left-color: #666;
    }}
    
    code, pre {{
        background-color: #3a3a3a;
    }}
}}''

/* 标题样式 */
h1, h2, h3, h4, h5, h6 {{
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
}}

h1 {{ font-size: 1.8em; }}
h2 {{ font-size: 1.5em; }}
h3 {{ font-size: 1.3em; }}
h4 {{ font-size: 1.1em; }}
h5 {{ font-size: 1em; }}
h6 {{ font-size: 0.9em; }}

/* 段落样式 */
p {{
    margin: 0;
    margin-bottom: 0.8em;
    text-indent: {indent_em}em;
}}

p:first-of-type {{
    text-indent: 0;
}}

/* 图片样式 */
img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}}

/* 表格样式 */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
}}

th {{
    background-color: #f5f5f5;
    font-weight: bold;
}}

/* 列表样式 */
ul, ol {{
    margin: 0.5em 0;
    padding-left: 2em;
}}

li {{
    margin-bottom: 0.3em;
}}

/* 目录样式 */
nav#toc {{
    font-size: 1.1em;
}}

nav#toc h1 {{
    font-size: 1.5em;
    margin-bottom: 1em;
}}

nav#toc ol {{
    list-style: none;
    padding-left: 0;
}}

nav#toc li {{
    margin-bottom: 0.5em;
}}

nav#toc a {{
    text-decoration: none;
    color: #333;
}}

nav#toc a:hover {{
    text-decoration: underline;
}}

/* 分页控制 */
.chapter {{
    page-break-before: always;
}}

.chapter:first-of-type {{
    page-break-before: auto;
}}'''
    
    def _generate_chapter_xhtml(self, chapter: Chapter, filename: str) -> str:
        """
        生成章节XHTML内容
        """
        content_parts = []
        
        # 添加章节标题
        if chapter.title:
            content_parts.append(f'<h1 class="chapter-title">{self._escape_xml(chapter.title)}</h1>')
        
        # 处理内容元素
        for element in chapter.elements:
            html = self._element_to_html(element)
            if html:
                content_parts.append(html)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{self._escape_xml(chapter.title)}</title>
    <meta charset="utf-8"/>
    <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
    <div class="chapter">
{chr(10).join(content_parts)}
    </div>
</body>
</html>'''
    
    def _element_to_html(self, element: ContentElement) -> str:
        """
        将内容元素转换为HTML
        """
        if element.element_type == ElementType.TITLE:
            return self._title_to_html(element)
        elif element.element_type == ElementType.PARAGRAPH:
            return self._paragraph_to_html(element)
        elif element.element_type == ElementType.IMAGE:
            return self._image_to_html(element)
        elif element.element_type == ElementType.TABLE:
            return self._table_to_html(element)
        elif element.element_type == ElementType.LIST:
            return self._list_to_html(element)
        else:
            return ""
    
    def _title_to_html(self, element: ContentElement) -> str:
        """
        标题转HTML
        """
        if not isinstance(element.content, TextBlock):
            return ""
        
        block = element.content
        text = block.content.strip()
        
        # 根据字体大小判断标题级别
        if block.style.font_size >= 20:
            tag = "h2"
        elif block.style.font_size >= 16:
            tag = "h3"
        else:
            tag = "h4"
        
        return f'<{tag}>{self._escape_xml(text)}</{tag}>'
    
    def _paragraph_to_html(self, element: ContentElement) -> str:
        """
        段落转HTML
        """
        if not isinstance(element.content, TextBlock):
            return ""
        
        text = element.content.content.strip()
        if not text:
            return ""
        
        # 检测是否为列表项
        if re.match(r'^[\d一二三四五六七八九十]+[\.、\s]', text):
            return f'<p class="list-item">{self._escape_xml(text)}</p>'
        
        return f'<p>{self._escape_xml(text)}</p>'
    
    def _image_to_html(self, element: ContentElement) -> str:
        """
        图片转HTML
        """
        if not isinstance(element.content, ImageBlock):
            return ""
        
        img = element.content
        
        # 注册图片
        self.image_counter += 1
        img_filename = f"image_{self.image_counter:04d}.{img.format.lower()}"
        self.images_to_embed[img_filename] = img.image_data
        
        alt = self._escape_xml(img.alt_text or "图片")
        
        html = f'<img src="../images/{img_filename}" alt="{alt}"'
        
        if img.caption:
            caption = self._escape_xml(img.caption)
            return f'<figure>{html}/><figcaption>{caption}</figcaption></figure>'
        
        return html + '/>'
    
    def _table_to_html(self, element: ContentElement) -> str:
        """
        表格转HTML
        """
        if not isinstance(element.content, TableBlock):
            return ""
        
        table = element.content
        rows = []
        
        for row_cells in table.cells:
            cells_html = []
            for cell in row_cells:
                tag = "th" if cell.is_header else "td"
                content = self._escape_xml(cell.content)
                
                # 处理跨行跨列
                attrs = []
                if cell.row_span > 1:
                    attrs.append(f'rowspan="{cell.row_span}"')
                if cell.col_span > 1:
                    attrs.append(f'colspan="{cell.col_span}"')
                
                attr_str = " " + " ".join(attrs) if attrs else ""
                cells_html.append(f'<{tag}{attr_str}>{content}</{tag}>')
            
            rows.append(f'<tr>{"".join(cells_html)}</tr>')
        
        caption = ""
        if table.caption:
            caption = f'<caption>{self._escape_xml(table.caption)}</caption>'
        
        return f'<table>{caption}{"".join(rows)}</table>'
    
    def _list_to_html(self, element: ContentElement) -> str:
        """
        列表转HTML
        """
        # 简化实现，实际应该处理嵌套列表
        return ""
    
    def _escape_xml(self, text: str) -> str:
        """
        转义XML特殊字符
        """
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))
    
    def _create_epub_file(self, content: Dict[str, Any], output_path: str) -> None:
        """
        创建EPUB文件
        
        EPUB本质上是一个ZIP文件，包含特定的目录结构
        """
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. mimetype（必须第一个，且未压缩）
            zf.writestr('mimetype', content['mimetype'], compress_type=zipfile.ZIP_STORED)
            
            # 2. META-INF/container.xml
            zf.writestr('META-INF/container.xml', content['container_xml'])
            
            # 3. OEBPS/content.opf
            zf.writestr('OEBPS/content.opf', content['content_opf'])
            
            # 4. OEBPS/toc.ncx
            zf.writestr('OEBPS/toc.ncx', content['toc_ncx'])
            
            # 5. OEBPS/nav.xhtml
            zf.writestr(f'OEBPS/{self.config.toc_filename}', content['nav_xhtml'])
            
            # 6. OEBPS/styles/style.css
            zf.writestr(f'OEBPS/styles/{self.config.css_filename}', content['style_css'])
            
            # 7. 章节文件
            for chapter in content['chapters']:
                zf.writestr(f"OEBPS/chapters/{chapter['filename']}", chapter['content'])
            
            # 8. 图片
            for img_name, img_data in content['images'].items():
                zf.writestr(f"OEBPS/images/{img_name}", img_data)
            
            # 记录实际嵌入的图片
            for img_name, img_data in self.images_to_embed.items():
                zf.writestr(f"OEBPS/images/{img_name}", img_data)
        
        logger.info(f"EPUB文件已创建: {output_path}")