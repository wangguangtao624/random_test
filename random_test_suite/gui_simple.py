#!/usr/bin/env python3
"""
CIS芯片TRNG随机性测试平台 - 简化版GUI
使用subprocess运行测试，避免线程问题
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# 测试项说明
TEST_ITEMS = [
    {'id': 'frequency_monobit', 'name': '单比特频数检测', 'standard': 'NIST'},
    {'id': 'frequency_within_block', 'name': '块内频数检测', 'standard': 'NIST'},
    {'id': 'runs', 'name': '游程检测', 'standard': 'NIST'},
    {'id': 'longest_run_of_ones', 'name': '块内最长游程检测', 'standard': 'NIST'},
    {'id': 'binary_matrix_rank', 'name': '二元矩阵秩检测', 'standard': 'NIST'},
    {'id': 'dft_spectral', 'name': '离散傅里叶检测', 'standard': 'NIST'},
    {'id': 'non_overlapping_template', 'name': '非重叠模板匹配检测', 'standard': 'NIST'},
    {'id': 'overlapping_template', 'name': '重叠模板匹配检测', 'standard': 'NIST'},
    {'id': 'maurers_universal', 'name': 'Maurer通用统计检测', 'standard': 'NIST'},
    {'id': 'linear_complexity', 'name': '线性复杂度检测', 'standard': 'NIST'},
    {'id': 'serial', 'name': '序列检测', 'standard': 'NIST'},
    {'id': 'approximate_entropy', 'name': '近似熵检测', 'standard': 'NIST'},
    {'id': 'cumulative_sums', 'name': '累加和检测', 'standard': 'NIST'},
    {'id': 'random_excursions', 'name': '随机游程检测', 'standard': 'NIST'},
    {'id': 'random_excursions_variant', 'name': '随机游程变体检测', 'standard': 'NIST'},
    {'id': 'poker_test_m4', 'name': '扑克检测 (m=4)', 'standard': 'GB/T'},
    {'id': 'poker_test_m8', 'name': '扑克检测 (m=8)', 'standard': 'GB/T'},
    {'id': 'autocorrelation_test', 'name': '自相关检测', 'standard': 'GB/T'},
    {'id': 'binary_derivative_test', 'name': '二元推导检测', 'standard': 'GB/T'},
]


class SimpleTestPlatform:
    """简化版测试平台"""

    def __init__(self, root):
        self.root = root
        self.root.title("CIS芯片TRNG随机性测试平台")
        self.root.geometry("1000x700")

        self.data_file = None
        self.process = None

        self.create_widgets()

    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title = ttk.Label(main_frame, text="CIS芯片TRNG随机性测试平台",
                         font=('Microsoft YaHei', 16, 'bold'))
        title.pack(pady=(0, 10))

        # 上部：文件选择和测试项
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # 文件选择
        file_frame = ttk.LabelFrame(top_frame, text="测试数据文件", padding="10")
        file_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="选择文件", command=self.select_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="使用桌面测试文件", command=self.use_desktop_file).pack(side=tk.LEFT, padx=5)

        self.file_label = ttk.Label(file_frame, text="未选择文件", foreground="gray")
        self.file_label.pack(fill=tk.X, pady=(5, 0))

        # 测试项选择
        test_frame = ttk.LabelFrame(top_frame, text="测试项目", padding="10")
        test_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 全选/反选按钮
        btn_frame2 = ttk.Frame(test_frame)
        btn_frame2.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(btn_frame2, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="NIST", command=self.select_nist).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="GB/T", command=self.select_gbt).pack(side=tk.LEFT, padx=2)

        # 测试项复选框（使用Canvas实现滚动）
        canvas = tk.Canvas(test_frame, height=150)
        scrollbar = ttk.Scrollbar(test_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.test_vars = {}
        for i, item in enumerate(TEST_ITEMS):
            var = tk.BooleanVar(value=True)
            self.test_vars[item['id']] = var

            prefix = "[NIST]" if item['standard'] == 'NIST' else "[GB/T]"
            cb = ttk.Checkbutton(scrollable_frame, text=f"{prefix} {item['name']}", variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=5, pady=1)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 中部：按钮
        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill=tk.X, pady=10)

        self.run_button = ttk.Button(mid_frame, text="开始测试", command=self.run_test)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(mid_frame, text="停止", command=self.stop_test, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(mid_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 下部：日志输出
        log_frame = ttk.LabelFrame(main_frame, text="测试日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def select_file(self):
        """选择文件"""
        filepath = filedialog.askopenfilename(
            title="选择测试数据文件",
            filetypes=[("二进制文件", "*.bin"), ("所有文件", "*.*")]
        )
        if filepath:
            self.data_file = filepath
            self.file_label.config(text=os.path.basename(filepath), foreground="black")

    def use_desktop_file(self):
        """使用桌面测试文件"""
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        filepath = os.path.join(desktop, 'CIS_TRNG测试数据.bin')

        if os.path.exists(filepath):
            self.data_file = filepath
            self.file_label.config(text="CIS_TRNG测试数据.bin", foreground="black")
        else:
            messagebox.showwarning("警告", "桌面找不到测试文件！")

    def select_all(self):
        """全选"""
        for var in self.test_vars.values():
            var.set(True)

    def select_nist(self):
        """选择NIST测试"""
        for item in TEST_ITEMS:
            self.test_vars[item['id']].set(item['standard'] == 'NIST')

    def select_gbt(self):
        """选择GB/T测试"""
        for item in TEST_ITEMS:
            self.test_vars[item['id']].set(item['standard'] == 'GB/T')

    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run_test(self):
        """运行测试"""
        if not self.data_file:
            messagebox.showwarning("警告", "请先选择测试文件！")
            return

        if not os.path.exists(self.data_file):
            messagebox.showwarning("警告", "测试文件不存在！")
            return

        # 获取选中的测试项
        selected = [item['id'] for item in TEST_ITEMS if self.test_vars[item['id']].get()]
        if not selected:
            messagebox.showwarning("警告", "请至少选择一个测试项目！")
            return

        # 清空日志
        self.log_text.delete(1.0, tk.END)

        # 更新UI状态
        self.run_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress.start()

        self.log("=" * 60)
        self.log("开始测试...")
        self.log(f"测试文件: {os.path.basename(self.data_file)}")
        self.log(f"测试项目: {len(selected)} 个")
        self.log("=" * 60)

        # 创建测试脚本
        script = self.create_test_script(self.data_file, selected)

        # 写入临时脚本文件
        script_path = os.path.join(os.path.dirname(__file__), '_temp_test.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script)

        # 在子进程中运行测试
        try:
            self.process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1
            )

            # 读取输出
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log(line.strip())
                    self.root.update_idletasks()

            # 等待完成
            self.process.wait()

            if self.process.returncode == 0:
                self.log("\n" + "=" * 60)
                self.log("测试完成！")
                self.log("=" * 60)
            else:
                self.log(f"\n测试结束，返回码: {self.process.returncode}")

        except Exception as e:
            self.log(f"\n错误: {e}")

        finally:
            # 清理
            self.progress.stop()
            self.run_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.process = None

            # 删除临时脚本
            try:
                os.remove(script_path)
            except:
                pass

    def stop_test(self):
        """停止测试"""
        if self.process:
            self.process.terminate()
            self.log("\n测试已停止")

    def create_test_script(self, data_file, selected_tests):
        """创建测试脚本"""
        script = f'''
import os
import sys
sys.path.insert(0, r"{os.path.dirname(os.path.abspath(__file__))}")

from core.nist_tests import NISTTestSuite
from core.gbt_tests import GBTTestSuite
from utils.data_loader import DataLoader

def main():
    filepath = r"{data_file}"
    selected = {selected_tests}

    print("=" * 60)
    print("加载测试数据...")
    print("=" * 60)

    loader = DataLoader()
    bits = loader.load_from_file(filepath)
    info = loader.get_sequence_info(bits)

    print(f"序列长度: {{info['length']:,}} 比特")
    print(f"1的比例: {{info['ones_ratio']:.4f}}")
    print()

    # 运行NIST测试
    nist_suite = NISTTestSuite()
    gbt_suite = GBTTestSuite()

    nist_tests = [t for t in selected if 'poker' not in t and 'autocorrelation' not in t and 'binary_derivative' not in t]
    gbt_tests = [t for t in selected if t not in nist_tests]

    nist_pass = 0
    gbt_pass = 0

    if nist_tests:
        print("运行 NIST SP 800-22 测试...")
        print("-" * 60)

        nist_results = nist_suite.run_all_tests(bits)

        for name, p_value in nist_results.items():
            if name in nist_tests:
                status = "PASS" if p_value >= 0.01 else "FAIL"
                if status == "PASS":
                    nist_pass += 1
                print(f"{{name:<35}} P-value: {{p_value:.6f}} [{{status}}]")

        print("-" * 60)
        print(f"NIST通过率: {{nist_pass}}/{{len(nist_tests)}}")
        print()

    if gbt_tests:
        print("运行 GB/T 32915-2016 补充测试...")
        print("-" * 60)

        gbt_results = gbt_suite.run_all_tests(bits)

        for name, p_value in gbt_results.items():
            if name in gbt_tests:
                status = "PASS" if p_value >= 0.01 else "FAIL"
                if status == "PASS":
                    gbt_pass += 1
                print(f"{{name:<35}} P-value: {{p_value:.6f}} [{{status}}]")

        print("-" * 60)
        print(f"GB/T通过率: {{gbt_pass}}/{{len(gbt_tests)}}")
        print()

    # 总结
    total_pass = nist_pass + gbt_pass
    total_tests = len(selected)
    print("=" * 60)
    print(f"总体通过率: {{total_pass}}/{{total_tests}} = {{total_pass/total_tests*100:.2f}}%")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''
        return script


def main():
    root = tk.Tk()
    app = SimpleTestPlatform(root)
    root.mainloop()


if __name__ == '__main__':
    main()
