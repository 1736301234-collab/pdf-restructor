"""
图形界面 - PDF转EPUB转换器

简单的GUI界面，方便使用
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path

# 确保可以导入本包
sys.path.insert(0, str(Path(__file__).parent))

from core.enhanced_pipeline import EnhancedConversionPipeline, EnhancedConfig


class PDFConverterGUI:
    """PDF转EPUB图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PDF转EPUB转换器")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)
        
        # 变量
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.enable_ocr = tk.BooleanVar(value=True)
        self.enable_ai = tk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="智能PDF转EPUB转换器",
            font=('Microsoft YaHei', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 输入文件选择
        ttk.Label(main_frame, text="PDF文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_path).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_input).grid(row=1, column=2, padx=5)
        
        # 输出文件选择
        ttk.Label(main_frame, text="输出位置:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_path).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_output).grid(row=2, column=2, padx=5)
        
        # 选项区域
        options_frame = ttk.LabelFrame(main_frame, text="转换选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Checkbutton(
            options_frame, 
            text="启用OCR（扫描版PDF需要）",
            variable=self.enable_ocr
        ).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Checkbutton(
            options_frame,
            text="启用AI智能分析",
            variable=self.enable_ai
        ).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 转换按钮
        self.convert_btn = ttk.Button(
            main_frame, 
            text="开始转换",
            command=self.start_conversion,
            style='Accent.TButton'
        )
        self.convert_btn.grid(row=4, column=0, columnspan=3, pady=20)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        self.progress.grid_remove()  # 初始隐藏
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="就绪", foreground='gray')
        self.status_label.grid(row=6, column=0, columnspan=3)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=10,
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置权重
        main_frame.rowconfigure(7, weight=1)
    
    def browse_input(self):
        """选择输入文件"""
        filename = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            # 自动设置输出路径
            if not self.output_path.get():
                output = Path(filename).with_suffix('.epub')
                self.output_path.set(str(output))
    
    def browse_output(self):
        """选择输出文件"""
        filename = filedialog.asksaveasfilename(
            title="保存EPUB文件",
            defaultextension=".epub",
            filetypes=[("EPUB文件", "*.epub"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
    
    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def start_conversion(self):
        """开始转换"""
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        
        # 验证输入
        if not input_path:
            messagebox.showerror("错误", "请选择PDF文件")
            return
        
        if not os.path.exists(input_path):
            messagebox.showerror("错误", f"文件不存在: {input_path}")
            return
        
        if not output_path:
            output_path = Path(input_path).with_suffix('.epub')
        
        # 在新线程中运行转换
        self.convert_btn.config(state='disabled')
        self.progress.grid()
        self.progress.start()
        self.status_label.config(text="正在转换...", foreground='blue')
        self.log_text.delete(1.0, tk.END)
        
        thread = threading.Thread(
            target=self.do_conversion,
            args=(input_path, output_path)
        )
        thread.daemon = True
        thread.start()
    
    def do_conversion(self, input_path, output_path):
        """执行转换"""
        try:
            self.log(f"开始转换: {input_path}")
            self.log(f"输出文件: {output_path}")
            self.log(f"OCR: {'启用' if self.enable_ocr.get() else '禁用'}")
            self.log(f"AI分析: {'启用' if self.enable_ai.get() else '禁用'}")
            self.log("-" * 50)
            
            # 创建配置
            config = EnhancedConfig(
                enable_ocr=self.enable_ocr.get(),
                enable_ai_analysis=self.enable_ai.get()
            )
            
            # 执行转换
            pipeline = EnhancedConversionPipeline(config)
            result = pipeline.convert(input_path, output_path)
            
            # 更新界面
            self.root.after(0, self.conversion_complete, result)
            
        except Exception as e:
            self.root.after(0, self.conversion_error, str(e))
    
    def conversion_complete(self, result):
        """转换完成回调"""
        self.progress.stop()
        self.progress.grid_remove()
        self.convert_btn.config(state='normal')
        
        if result.success:
            self.status_label.config(text="转换完成！", foreground='green')
            self.log("\n" + "=" * 50)
            self.log("✓ 转换成功!")
            self.log(f"输出文件: {result.output_path}")
            
            if result.stats:
                self.log("\n统计信息:")
                for key, value in result.stats.items():
                    self.log(f"  {key}: {value}")
            
            # 询问是否打开文件位置
            if messagebox.askyesno("完成", "转换成功！\n\n是否打开输出文件所在位置？"):
                self.open_file_location(result.output_path)
        else:
            self.status_label.config(text="转换失败", foreground='red')
            self.log(f"\n✗ 转换失败: {result.message}")
            messagebox.showerror("错误", f"转换失败:\n{result.message}")
    
    def conversion_error(self, error_message):
        """转换错误回调"""
        self.progress.stop()
        self.progress.grid_remove()
        self.convert_btn.config(state='normal')
        self.status_label.config(text="转换出错", foreground='red')
        self.log(f"\n✗ 错误: {error_message}")
        messagebox.showerror("错误", f"转换过程中发生错误:\n{error_message}")
    
    def open_file_location(self, file_path):
        """打开文件所在位置"""
        import subprocess
        folder = os.path.dirname(os.path.abspath(file_path))
        
        if os.name == 'nt':  # Windows
            subprocess.run(['explorer', folder])
        elif os.name == 'posix':  # macOS/Linux
            if sys.platform == 'darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])


def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('vista' if os.name == 'nt' else 'clam')
    
    app = PDFConverterGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()