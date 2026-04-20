# PDF Restructor - 智能PDF转EPUB工具

一个能够将PDF文档智能转换为可重排EPUB电子书的工具。不同于传统的PDF转换器仅仅保留原有格式，本工具能够**理解文档结构**，去除页眉页脚等排版噪声，重新排版成真正适合电子书阅读的格式。

## ✨ 核心特性

- **🧠 智能结构识别**：自动识别标题层级、段落、章节结构
- **🧹 智能清理**：自动去除页眉、页脚、页码等干扰元素
- **🔄 段落合并**：智能合并被分页符打断的段落
- **📊 表格处理**：保留表格结构并适当重排
- **🖼️ 图片处理**：保留并优化图片，支持自动生成封面
- **📱 可重排文本**：生成的EPUB可在任意设备上调整字体大小和样式

## 📦 安装

### 环境要求
- Python 3.8+
- Windows / Linux / macOS

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/pdf-restructor.git
cd pdf-restructor

# 安装依赖
pip install -r requirements.txt

# 或者使用 pip 安装（如果使用 PyPI）
pip install pdf-restructor
```

## 🚀 使用方法

### 命令行使用

```bash
# 基本转换
python -m pdf_restructor input.pdf

# 指定输出文件名
python -m pdf_restructor input.pdf -o output.epub

# 设置元数据
python -m pdf_restructor book.pdf --title "书名" --author "作者名"

# 加密PDF转换
python -m pdf_restrator encrypted.pdf --password "mypassword"

# 查看帮助
python -m pdf_restructor --help
```

### Python API 使用

```python
from pdf_restructor import ConversionPipeline

# 创建转换管道
pipeline = ConversionPipeline()

# 执行转换
result = pipeline.convert("input.pdf", "output.epub")

if result.success:
    print(f"转换成功: {result.output_path}")
    print(f"统计: {result.stats}")
else:
    print(f"转换失败: {result.message}")

# 使用配置参数
from pdf_restructor import EPUBConfig

config = EPUBConfig(
    title="我的书",
    author="作者",
    language="zh-CN",
    font_size=16,
    line_height=1.6
)

pipeline = ConversionPipeline(epub_config=config)
result = pipeline.convert("input.pdf", "output.epub")
```

### 批量转换

```python
from pdf_restructor import ConversionPipeline

pipeline = ConversionPipeline()

# 批量转换
pdf_files = ["book1.pdf", "book2.pdf", "book3.pdf"]
results = pipeline.convert_batch(pdf_files, "output_dir/")

for result in results:
    if result.success:
        print(f"✓ {result.output_path}")
    else:
        print(f"✗ {result.message}")
```

## ⚙️ 配置选项

### EPUB 配置

```python
from pdf_restructor import EPUBConfig

config = EPUBConfig(
    title="书名",
    author="作者",
    language="zh-CN",  # 语言代码
    publisher="出版社",
    font_size=16,  # 正文字号
    line_height=1.6,  # 行高
    font_family="'Songti SC', 'SimSun', serif",  # 字体
    paragraph_indent=2,  # 段落缩进（字符数）
    generate_cover=True,  # 是否生成封面
    embed_images=True,  # 是否嵌入图片
    image_quality=85  # 图片质量
)
```

### 处理器配置

```python
from pdf_restructor import ProcessorConfig

config = ProcessorConfig(
    remove_headers=True,  # 移除页眉
    remove_footers=True,  # 移除页脚
    remove_page_numbers=True,  # 移除页码
    remove_empty_paragraphs=True,  # 移除空段落
    merge_hyphenated_words=True,  # 合并连字符断开的单词
    normalize_whitespace=True,  # 规范化空白
    min_paragraph_length=10  # 最小段落长度
)
```

## 🏗️ 架构设计

```
PDF输入
    ↓
[PDF解析引擎]  ← 使用 PyMuPDF 提取原始内容
    ↓
[内容提取器]   ← 提取文本、图片、表格
    ↓
[结构分析器]   ← 识别标题、段落、章节、页眉页脚
    ↓
[布局处理器]   ← 去除干扰元素，合并段落，优化布局
    ↓
[EPUB生成器]   ← 生成标准EPUB文件
    ↓
EPUB输出
```

## 📁 项目结构

```
pdf_restructor/
├── core/                    # 核心模块
│   ├── __init__.py
│   ├── models.py           # 数据模型
│   ├── parser.py           # PDF解析引擎
│   ├── extractor.py        # 内容提取器
│   ├── analyzer.py         # 结构分析器
│   ├── processor.py        # 布局处理器
│   ├── generator.py        # EPUB生成器
│   └── pipeline.py         # 转换管道
├── cli.py                  # 命令行界面
├── requirements.txt        # 依赖文件
└── README.md              # 说明文档
```

## 🔍 技术细节

### 标题检测算法

基于以下特征识别标题：
- 字体大小（相对于正文的比例）
- 字体加粗
- 文本长度（标题通常较短）
- 全大写
- 章节关键词（如"第X章"）
- 页面位置（顶部）

### 页眉页脚检测

基于以下特征识别：
- 位置（页面顶部或底部区域）
- 跨页重复性
- 字体特征
- 内容特征（通常是数字或简短文本）

### 段落合并

检测并合并在PDF中被分页符打断的段落：
- 检查连续页面的文本块
- 比较字体样式和缩进
- 分析句子是否完整
- 处理连字符断开的情况

## 🎯 适用场景

- ✅ 学术论文和报告
- ✅ 技术文档和手册
- ✅ 小说和文学作品
- ✅ 教材和讲义
- ✅ 会议论文集
- ⚠️ 复杂排版杂志（可能需要手动调整）
- ⚠️ 扫描版PDF（需要先进行OCR）

## ⚠️ 注意事项

1. **复杂布局**：复杂的多栏布局可能需要额外的配置
2. **扫描版PDF**：需要先进行OCR才能提取文本
3. **数学公式**：公式可能无法完美转换，建议使用专门的工具
4. **表格**：复杂表格的转换可能需要手动调整

## 🔧 高级配置

### 自定义样式

可以通过修改生成的EPUB中的 `styles/style.css` 文件来自定义样式。

### 插件扩展

支持自定义处理插件（开发中）：

```python
from pdf_restructor.core.pipeline import PDFProcessorPlugin

class CustomProcessor(PDFProcessorPlugin):
    def process(self, context):
        # 自定义处理逻辑
        return context
```

## 📝 更新日志

### v1.0.0 (2024-01-20)
- ✨ 初始版本发布
- ✨ 支持基本PDF转EPUB
- ✨ 智能结构识别
- ✨ 页眉页脚去除
- ✨ 命令行工具

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

如有问题或建议，欢迎通过以下方式联系：
- GitHub Issues: [https://github.com/yourusername/pdf-restructor/issues](https://github.com/yourusername/pdf-restructor/issues)
- Email: your.email@example.com

---

**让PDF阅读更舒适！** 📚✨