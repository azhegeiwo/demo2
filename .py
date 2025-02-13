import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading

class DatConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("微信DAT图片转换器 v2.0")
        master.geometry("700x450")

        # 样式配置
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)
        self.style.configure('TFrame', padding=10)

        # 创建主框架
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 模式选择
        self.mode_var = tk.StringVar(value='file')
        ttk.Label(self.main_frame, text="转换模式:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.file_mode_btn = ttk.Radiobutton(
            self.main_frame, text="单个文件", variable=self.mode_var, value='file')
        self.dir_mode_btn = ttk.Radiobutton(
            self.main_frame, text="整个目录", variable=self.mode_var, value='dir')
        self.file_mode_btn.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.dir_mode_btn.grid(row=0, column=2, padx=5, sticky=tk.W)

        # 输入路径选择
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(self.input_frame, text="输入路径:").pack(side=tk.LEFT, padx=5)
        self.path_entry = ttk.Entry(self.input_frame, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.browse_btn = ttk.Button(
            self.input_frame, text="浏览...", command=self.browse_path)
        self.browse_btn.pack(side=tk.RIGHT, padx=5)

        # 输出路径选择
        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(self.output_frame, text="输出目录:").pack(side=tk.LEFT, padx=5)
        self.output_entry = ttk.Entry(self.output_frame, width=50)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.output_browse_btn = ttk.Button(
            self.output_frame, text="浏览...", command=self.browse_output_dir)
        self.output_browse_btn.pack(side=tk.RIGHT, padx=5)

        # 转换按钮
        self.convert_btn = ttk.Button(
            self.main_frame, text="开始转换", command=self.start_conversion)
        self.convert_btn.grid(row=3, column=0, columnspan=3, pady=10)

        # 日志区域
        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW)
        
        self.log_text = tk.Text(self.log_frame, height=15, state=tk.DISABLED)
        self.scrollbar = ttk.Scrollbar(
            self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 布局配置
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)

    def browse_path(self):
        if self.mode_var.get() == 'file':
            path = filedialog.askopenfilename(
                title="选择DAT文件",
                filetypes=[("DAT文件", "*.dat")])
        else:
            path = filedialog.askdirectory(title="选择包含DAT文件的目录")
        
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def decrypt_dat(self, dat_path):
        try:
            with open(dat_path, 'rb') as f:
                data = bytearray(f.read())
            
            if not data:
                return None

            # 自动检测加密key（基于JPEG文件头）
            key = data[0] ^ 0xFF
            if (data[1] ^ key) != 0xD8:  # 验证JPEG文件头
                return None

            return bytes([b ^ key for b in data])
        
        except Exception as e:
            self.log_message(f"错误: {str(e)}")
            return None

    def convert_files(self):
        input_path = self.path_entry.get()
        output_dir = self.output_entry.get()
        
        if not input_path or not output_dir:
            messagebox.showwarning("警告", "请先选择输入路径和输出目录！")
            return

        os.makedirs(output_dir, exist_ok=True)

        if self.mode_var.get() == 'file':
            dat_files = [input_path]
        else:
            dat_files = []
            for root, _, files in os.walk(input_path):
                for file in files:
                    if file.lower().endswith('.dat'):
                        dat_files.append(os.path.join(root, file))

        total = len(dat_files)
        success = 0
        
        for dat_path in dat_files:
            try:
                jpg_data = self.decrypt_dat(dat_path)
                if not jpg_data:
                    self.log_message(f"跳过非图片文件: {os.path.basename(dat_path)}")
                    continue

                # 生成输出路径
                if self.mode_var.get() == 'dir':
                    # 保持目录结构
                    relative_path = os.path.relpath(dat_path, input_path)
                    output_relative = os.path.splitext(relative_path)[0] + "_converted.jpg"
                    output_path = os.path.join(output_dir, output_relative)
                else:
                    # 直接使用文件名
                    file_name = os.path.basename(dat_path)
                    output_base = os.path.splitext(file_name)[0] + "_converted.jpg"
                    output_path = os.path.join(output_dir, output_base)

                # 创建目标目录
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, 'wb') as f:
                    f.write(jpg_data)
                
                success += 1
                self.log_message(f"转换成功: {os.path.relpath(output_path, output_dir)}")
            
            except Exception as e:
                self.log_message(f"转换失败: {os.path.basename(dat_path)} - {str(e)}")

        messagebox.showinfo(
            "完成", 
            f"转换完成！\n成功: {success}\n失败: {total - success}\n总计: {total}"
        )

    def start_conversion(self):
        threading.Thread(target=self.convert_files, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = DatConverterApp(root)
    root.mainloop()
