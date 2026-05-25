#!/usr/bin/env python3
"""
CIS芯片TRNG随机性测试平台 - 稳定版
使用文件传递输出，完全避免卡死
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# 测试项
TEST_ITEMS = [
    ('frequency_monobit', '单比特频数检测', 'NIST'),
    ('frequency_within_block', '块内频数检测', 'NIST'),
    ('runs', '游程检测', 'NIST'),
    ('longest_run_of_ones', '块内最长游程检测', 'NIST'),
    ('binary_matrix_rank', '二元矩阵秩检测', 'NIST'),
    ('dft_spectral', '离散傅里叶检测', 'NIST'),
    ('non_overlapping_template', '非重叠模板匹配检测', 'NIST'),
    ('overlapping_template', '重叠模板匹配检测', 'NIST'),
    ('maurers_universal', 'Maurer通用统计检测', 'NIST'),
    ('linear_complexity', '线性复杂度检测', 'NIST'),
    ('serial', '序列检测', 'NIST'),
    ('approximate_entropy', '近似熵检测', 'NIST'),
    ('cumulative_sums', '累加和检测', 'NIST'),
    ('random_excursions', '随机游程检测', 'NIST'),
    ('random_excursions_variant', '随机游程变体检测', 'NIST'),
    ('poker_test_m4', '扑克检测 (m=4)', 'GB/T'),
    ('poker_test_m8', '扑克检测 (m=8)', 'GB/T'),
    ('autocorrelation_test', '自相关检测', 'GB/T'),
    ('binary_derivative_test', '二元推导检测', 'GB/T'),
]


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CIS芯片TRNG随机性测试平台")
        self.root.geometry("900x650")

        self.file_path = None
        self.test_vars = {}
        self.running = False
        self.output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_output.txt')
        self.script_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_test.py')

        self.build_ui()
        self.poll_output()

    def build_ui(self):
        # 顶部标题
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)
        ttk.Label(top, text="CIS芯片TRNG随机性测试平台",
                 font=('微软雅黑', 14, 'bold')).pack()

        # 文件选择
        f1 = ttk.LabelFrame(self.root, text="测试文件", padding=10)
        f1.pack(fill=tk.X, padx=10, pady=5)

        btn_row = ttk.Frame(f1)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="选择文件", command=self.pick_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="使用桌面测试文件", command=self.use_desktop).pack(side=tk.LEFT, padx=5)
        self.file_lbl = ttk.Label(f1, text="未选择文件", foreground="gray")
        self.file_lbl.pack(anchor=tk.W, pady=(5, 0))

        # 测试项选择
        f2 = ttk.LabelFrame(self.root, text="测试项目", padding=10)
        f2.pack(fill=tk.X, padx=10, pady=5)

        btn_row2 = ttk.Frame(f2)
        btn_row2.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_row2, text="全选", command=self.sel_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row2, text="NIST", command=self.sel_nist).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row2, text="GB/T", command=self.sel_gbt).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row2, text="清空", command=self.sel_none).pack(side=tk.LEFT, padx=2)

        grid = ttk.Frame(f2)
        grid.pack(fill=tk.X)
        for i, (tid, name, std) in enumerate(TEST_ITEMS):
            var = tk.BooleanVar(value=True)
            self.test_vars[tid] = var
            prefix = "[NIST]" if std == 'NIST' else "[GB/T]"
            cb = ttk.Checkbutton(grid, text=f"{prefix} {name}", variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=10, pady=1)

        # 按钮
        f3 = ttk.Frame(self.root, padding=10)
        f3.pack(fill=tk.X)
        self.run_btn = ttk.Button(f3, text="开始测试", command=self.start_test)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(f3, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10)

        # 日志
        f4 = ttk.LabelFrame(self.root, text="测试日志", padding=10)
        f4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_box = tk.Text(f4, height=15, state='disabled',
                              font=('Consolas', 9), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(f4, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, msg):
        self.log_box.configure(state='normal')
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state='disabled')

    def clear_log(self):
        self.log_box.configure(state='normal')
        self.log_box.delete(1.0, tk.END)
        self.log_box.configure(state='disabled')

    def pick_file(self):
        path = filedialog.askopenfilename(filetypes=[("二进制文件", "*.bin"), ("所有文件", "*.*")])
        if path:
            self.file_path = path
            self.file_lbl.config(text=os.path.basename(path), foreground="black")

    def use_desktop(self):
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        path = os.path.join(desktop, 'CIS_TRNG测试数据.bin')
        if os.path.exists(path):
            self.file_path = path
            self.file_lbl.config(text="CIS_TRNG测试数据.bin", foreground="black")
        else:
            messagebox.showwarning("警告", "桌面找不到测试文件")

    def sel_all(self):
        for v in self.test_vars.values():
            v.set(True)

    def sel_none(self):
        for v in self.test_vars.values():
            v.set(False)

    def sel_nist(self):
        for tid, _, std in TEST_ITEMS:
            self.test_vars[tid].set(std == 'NIST')

    def sel_gbt(self):
        for tid, _, std in TEST_ITEMS:
            self.test_vars[tid].set(std == 'GB/T')

    def start_test(self):
        if self.running:
            messagebox.showwarning("警告", "测试正在运行！")
            return

        if not self.file_path:
            messagebox.showwarning("警告", "请先选择测试文件！")
            return

        selected = [tid for tid, v in self.test_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("警告", "请至少选择一个测试项目！")
            return

        self.clear_log()
        self.log("=" * 50)
        self.log(f"测试文件: {os.path.basename(self.file_path)}")
        self.log(f"测试项目: {len(selected)} 个")
        self.log("=" * 50)
        self.log("正在启动测试...")
        self.log("")

        self.running = True
        self.run_btn.configure(state='disabled')
        self.progress.start(10)

        # 清空输出文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('')

        # 生成测试脚本
        script = self._make_script(selected)
        with open(self.script_file, 'w', encoding='utf-8') as f:
            f.write(script)

        # 在新线程中启动子进程
        t = threading.Thread(target=self._run_process, daemon=True)
        t.start()

    def _run_process(self):
        """在后台线程中运行子进程"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as out:
                proc = subprocess.Popen(
                    [sys.executable, '-u', self.script_file, self.file_path],
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                proc.wait()
        except Exception as e:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(f"\n错误: {e}\n")

    def poll_output(self):
        """定期检查输出文件"""
        if self.running:
            try:
                if os.path.exists(self.output_file):
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 检查新内容
                    if hasattr(self, '_last_content'):
                        if content != self._last_content:
                            # 只显示新增的部分
                            new_content = content[len(self._last_content):]
                            for line in new_content.split('\n'):
                                if line.strip():
                                    self.log(line)
                            self._last_content = content
                    else:
                        self._last_content = content
                        for line in content.split('\n'):
                            if line.strip():
                                self.log(line)

                    # 检查是否完成
                    if not self._is_process_running():
                        self.running = False
                        self.run_btn.configure(state='normal')
                        self.progress.stop()
                        self.log("")
                        self.log("=" * 50)
                        self.log("测试完成！")
                        self.log("=" * 50)

                        # 清理临时文件
                        try:
                            os.remove(self.script_file)
                        except:
                            pass

            except Exception:
                pass

        # 每100ms检查一次
        self.root.after(100, self.poll_output)

    def _is_process_running(self):
        """检查进程是否还在运行"""
        try:
            # 通过检查输出文件是否还在增长来判断
            if not hasattr(self, '_last_size'):
                self._last_size = 0
                self._stable_count = 0

            if os.path.exists(self.output_file):
                size = os.path.getsize(self.output_file)
                if size == self._last_size:
                    self._stable_count += 1
                    # 如果文件大小稳定了1秒，认为完成
                    if self._stable_count > 10:
                        return False
                else:
                    self._stable_count = 0
                    self._last_size = size
                return True
            return False
        except:
            return False

    def _make_script(self, selected):
        """生成测试脚本"""
        return f'''# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, r"{os.path.dirname(os.path.abspath(__file__))}")

from core.nist_tests import NISTTestSuite
from core.gbt_tests import GBTTestSuite
from utils.data_loader import DataLoader

def main():
    filepath = sys.argv[1]
    selected = {selected}

    # 加载数据
    print("=" * 50)
    print("加载测试数据...")
    print("=" * 50)

    loader = DataLoader()
    bits = loader.load_from_file(filepath)
    info = loader.get_sequence_info(bits)

    print(f"序列长度: {{info['length']:,}} 比特")
    print(f"1的比例: {{info['ones_ratio']:.4f}}")
    print()

    # 运行测试
    nist_suite = NISTTestSuite()
    gbt_suite = GBTTestSuite()

    print("运行测试...")
    print("-" * 50)

    # NIST测试
    nist_results = nist_suite.run_all_tests(bits)

    nist_pass = 0
    nist_total = 0
    for name, p_value in nist_results.items():
        if name in selected:
            nist_total += 1
            status = "PASS" if p_value >= 0.01 else "FAIL"
            if status == "PASS":
                nist_pass += 1
            print(f"{{name:<35}} {{p_value:.6f}} [{{status}}]")

    # GB/T测试
    gbt_results = gbt_suite.run_all_tests(bits)

    gbt_pass = 0
    gbt_total = 0
    for name, p_value in gbt_results.items():
        if name in selected:
            gbt_total += 1
            status = "PASS" if p_value >= 0.01 else "FAIL"
            if status == "PASS":
                gbt_pass += 1
            print(f"{{name:<35}} {{p_value:.6f}} [{{status}}]")

    # 总结
    print("-" * 50)
    total_pass = nist_pass + gbt_pass
    total_tests = nist_total + gbt_total

    print(f"NIST通过率: {{nist_pass}}/{{nist_total}}")
    print(f"GB/T通过率: {{gbt_pass}}/{{gbt_total}}")
    print()
    print("=" * 50)
    print(f"总体通过率: {{total_pass}}/{{total_tests}} = {{total_pass/total_tests*100:.2f}}%")
    print("=" * 50)

if __name__ == "__main__":
    main()
'''

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = App()
    app.run()
