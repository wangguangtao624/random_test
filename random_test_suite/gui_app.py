#!/usr/bin/env python3
"""
CIS芯片TRNG随机性测试平台 - GUI界面
支持选择测试项目、加载数据、运行测试、查看结果
"""

import os
import sys
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from typing import Dict, List, Any

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nist_tests import NISTTestSuite
from core.gbt_tests import GBTTestSuite
from utils.data_loader import DataLoader
from utils.report_generator import ReportGenerator


# 测试项说明
TEST_DESCRIPTIONS = {
    # NIST SP 800-22 测试项
    'frequency_monobit': {
        'name': '单比特频数检测',
        'english': 'Frequency (Monobit) Test',
        'standard': 'NIST SP 800-22',
        'description': '检测整个序列中0和1的比例是否接近相等。',
        'method': '将序列中的1映射为+1，0映射为-1，求和后计算统计量。',
        'purpose': '验证TRNG输出的比特分布是否均匀，是最基本的随机性测试。'
    },
    'frequency_within_block': {
        'name': '块内频数检测',
        'english': 'Frequency Test within a Block',
        'standard': 'NIST SP 800-22',
        'description': '检测固定长度块内0和1的比例是否均匀。',
        'method': '将序列分成M位的块，计算每块中1的比例，再用卡方检验。',
        'purpose': '检测序列在局部范围内是否保持均匀分布。'
    },
    'runs': {
        'name': '游程检测',
        'english': 'Runs Test',
        'standard': 'NIST SP 800-22',
        'description': '检测序列中游程（连续相同比特）的数量是否符合随机预期。',
        'method': '统计0→1和1→0的转换次数。',
        'purpose': '验证序列中比特交替的频率是否符合随机特性。'
    },
    'longest_run_of_ones': {
        'name': '块内最长游程检测',
        'english': 'Test for Longest Run of Ones',
        'standard': 'NIST SP 800-22',
        'description': '检测块内最长连续1的长度分布是否随机。',
        'method': '将序列分块，统计各块中最长1游程的频率分布。',
        'purpose': '检测序列中是否存在异常长的连续相同比特。'
    },
    'binary_matrix_rank': {
        'name': '二元矩阵秩检测',
        'english': 'Binary Matrix Rank Test',
        'standard': 'NIST SP 800-22',
        'description': '检测序列中二元矩阵的秩分布，发现线性依赖关系。',
        'method': '构造Q×Q二元矩阵，计算秩，检查是否符合随机分布。',
        'purpose': '检测序列中的线性依赖关系，验证序列的不可预测性。'
    },
    'dft_spectral': {
        'name': '离散傅里叶检测',
        'english': 'Discrete Fourier Transform (Spectral) Test',
        'standard': 'NIST SP 800-22',
        'description': '检测序列中的周期性特征。',
        'method': '对序列做FFT，检查频谱中超过阈值的峰值数量。',
        'purpose': '发现序列中隐藏的周期性模式或重复特征。'
    },
    'non_overlapping_template': {
        'name': '非重叠模板匹配检测',
        'english': 'Non-overlapping Template Matching Test',
        'standard': 'NIST SP 800-22',
        'description': '检测特定二元模板的出现频率。',
        'method': '统计非重叠模板出现的次数，与期望值比较。',
        'purpose': '检测序列中是否存在特定的重复模式。'
    },
    'overlapping_template': {
        'name': '重叠模板匹配检测',
        'english': 'Overlapping Template Matching Test',
        'standard': 'NIST SP 800-22',
        'description': '检测重叠模式的出现频率。',
        'method': '统计重叠模板出现的次数。',
        'purpose': '检测序列中重叠模式的分布是否符合随机预期。'
    },
    'maurers_universal': {
        'name': 'Maurer通用统计检测',
        'english': "Maurer's Universal Statistical Test",
        'standard': 'NIST SP 800-22',
        'description': '检测序列是否可以被显著压缩。',
        'method': '基于Lempel-Ziv压缩原理，计算序列的可压缩性。',
        'purpose': '验证序列的信息熵是否足够高，不可被有效压缩。'
    },
    'linear_complexity': {
        'name': '线性复杂度检测',
        'english': 'Linear Complexity Test',
        'standard': 'NIST SP 800-22',
        'description': '检测序列是否可由较短的线性反馈移位寄存器(LFSR)生成。',
        'method': '使用Berlekamp-Massey算法计算线性复杂度。',
        'purpose': '验证序列的不可预测性，防止被LFSR预测。'
    },
    'serial': {
        'name': '序列检测',
        'english': 'Serial Test',
        'standard': 'NIST SP 800-22',
        'description': '检测所有可能的m位模式的出现频率是否均匀。',
        'method': '统计2^m种模式的出现次数，用卡方检验。',
        'purpose': '验证所有可能的比特组合是否等概率出现。'
    },
    'approximate_entropy': {
        'name': '近似熵检测',
        'english': 'Approximate Entropy Test',
        'standard': 'NIST SP 800-22',
        'description': '检测序列的熵值（信息量）是否符合随机预期。',
        'method': '计算近似熵，与随机序列比较。',
        'purpose': '衡量序列的复杂度和不可预测性。'
    },
    'cumulative_sums': {
        'name': '累加和检测',
        'english': 'Cumulative Sums (Cusum) Test',
        'standard': 'NIST SP 800-22',
        'description': '检测序列中偏移的最大累积和是否异常。',
        'method': '计算累积和的正向和负向最大值。',
        'purpose': '检测序列中是否存在系统性偏移。'
    },
    'random_excursions': {
        'name': '随机游程检测',
        'english': 'Random Excursions Test',
        'standard': 'NIST SP 800-22',
        'description': '检测循环随机游程中各状态的访问次数。',
        'method': '分析随机游程的8个状态（-4到-1和1到4）。',
        'purpose': '验证随机游程的统计特性是否符合预期。'
    },
    'random_excursions_variant': {
        'name': '随机游程变体检测',
        'english': 'Random Excursions Variant Test',
        'standard': 'NIST SP 800-22',
        'description': '检测随机游程中特定状态的访问次数。',
        'method': '统计18个特定状态（-9到-1和1到9）的访问频率。',
        'purpose': '更全面地验证随机游程的统计特性。'
    },
    # GB/T 32915-2016 补充测试项
    'poker_test_m4': {
        'name': '扑克检测 (m=4)',
        'english': 'Poker Test (m=4)',
        'standard': 'GB/T 32915-2016',
        'description': '检测4位子序列的出现频率是否均匀。',
        'method': '将序列分为4比特的组，统计16种可能取值的出现次数，用卡方检验。',
        'purpose': '验证短模式的分布是否符合随机预期。'
    },
    'poker_test_m8': {
        'name': '扑克检测 (m=8)',
        'english': 'Poker Test (m=8)',
        'standard': 'GB/T 32915-2016',
        'description': '检测8位子序列的出现频率是否均匀。',
        'method': '将序列分为8比特的组，统计256种可能取值的出现次数，用卡方检验。',
        'purpose': '验证较长模式的分布是否符合随机预期。'
    },
    'autocorrelation_test': {
        'name': '自相关检测',
        'english': 'Autocorrelation Test',
        'standard': 'GB/T 32915-2016',
        'description': '检测序列与其移位版本的相关性。',
        'method': '计算序列与不同位移版本的异或结果，统计0的个数。',
        'purpose': '检测序列中是否存在周期性或相关性。'
    },
    'binary_derivative_test': {
        'name': '二元推导检测',
        'english': 'Binary Derivative Test',
        'standard': 'GB/T 32915-2016',
        'description': '对序列逐级进行差分（异或相邻比特），检查各级推导序列的均衡性。',
        'method': '计算差分序列，检查各级推导序列中0和1的比例。',
        'purpose': '检测序列的高阶统计特性。'
    }
}


class RandomTestPlatform:
    """随机性测试平台GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("CIS芯片TRNG随机性测试平台")
        self.root.geometry("1200x800")

        # 数据
        self.data_files = []
        self.test_results = None
        self.selected_tests = {}

        # 线程控制
        self.is_running = False
        self.should_stop = False
        self.message_queue = queue.Queue()

        # 创建UI
        self.create_widgets()

        # 启动消息处理
        self.process_queue()

    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="CIS芯片TRNG随机性测试平台",
                               font=('Microsoft YaHei', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 左侧：测试项目选择
        left_frame = ttk.LabelFrame(main_frame, text="测试项目选择", padding="10")
        left_frame.grid(row=1, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 创建测试项目选择区域
        self.create_test_selection(left_frame)

        # 右侧上部：数据文件选择
        right_top_frame = ttk.LabelFrame(main_frame, text="数据文件", padding="10")
        right_top_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        self.create_data_selection(right_top_frame)

        # 右侧下部：测试结果和日志
        right_bottom_frame = ttk.LabelFrame(main_frame, text="测试结果与日志", padding="10")
        right_bottom_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.create_result_area(right_bottom_frame)

        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="全选", command=self.select_all_tests).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="反选", command=self.invert_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="NIST全选", command=self.select_nist_tests).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="GB/T全选", command=self.select_gbt_tests).pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(button_frame, text="开始测试", command=self.run_tests)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止测试", command=self.stop_tests, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="生成报告", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)

    def create_test_selection(self, parent):
        """创建测试项目选择区域"""
        # 创建Canvas和滚动条
        canvas = tk.Canvas(parent, width=350, height=600)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # NIST测试项
        nist_label = ttk.Label(scrollable_frame, text="NIST SP 800-22 测试项 (15项)",
                              font=('Microsoft YaHei', 10, 'bold'))
        nist_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        row = 1
        for test_id, info in TEST_DESCRIPTIONS.items():
            if info['standard'] == 'NIST SP 800-22':
                var = tk.BooleanVar(value=True)
                self.selected_tests[test_id] = var

                cb = ttk.Checkbutton(scrollable_frame, text=f"{info['name']}",
                                    variable=var)
                cb.grid(row=row, column=0, sticky=tk.W, pady=1)

                # 添加详情按钮
                detail_btn = ttk.Button(scrollable_frame, text="详情",
                                       command=lambda t=test_id: self.show_test_detail(t))
                detail_btn.grid(row=row, column=1, sticky=tk.E, pady=1, padx=(5, 0))

                row += 1

        # GB/T测试项
        gbt_label = ttk.Label(scrollable_frame, text="\nGB/T 32915-2016 补充测试项 (4项)",
                             font=('Microsoft YaHei', 10, 'bold'))
        gbt_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1

        for test_id, info in TEST_DESCRIPTIONS.items():
            if info['standard'] == 'GB/T 32915-2016':
                var = tk.BooleanVar(value=True)
                self.selected_tests[test_id] = var

                cb = ttk.Checkbutton(scrollable_frame, text=f"{info['name']}",
                                    variable=var)
                cb.grid(row=row, column=0, sticky=tk.W, pady=1)

                detail_btn = ttk.Button(scrollable_frame, text="详情",
                                       command=lambda t=test_id: self.show_test_detail(t))
                detail_btn.grid(row=row, column=1, sticky=tk.E, pady=1, padx=(5, 0))

                row += 1

        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_data_selection(self, parent):
        """创建数据文件选择区域"""
        # 文件选择按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame, text="选择单个文件",
                   command=self.select_single_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="选择目录",
                   command=self.select_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空",
                   command=self.clear_files).pack(side=tk.LEFT, padx=5)

        # 文件列表
        self.file_listbox = tk.Listbox(parent, height=8)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)

        # 文件信息
        self.file_info_label = ttk.Label(parent, text="未选择文件")
        self.file_info_label.pack(fill=tk.X, pady=(5, 0))

    def create_result_area(self, parent):
        """创建测试结果和日志区域"""
        # 创建Notebook（标签页）
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 日志标签页
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="测试日志")

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 结果标签页
        result_frame = ttk.Frame(notebook)
        notebook.add(result_frame, text="测试结果")

        self.result_text = scrolledtext.ScrolledText(result_frame, height=20)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 进度条
        self.progress = ttk.Progressbar(parent, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(parent, text="就绪")
        self.status_label.pack(fill=tk.X, pady=(5, 0))

    def process_queue(self):
        """处理消息队列（在主线程中调用）"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == 'log':
                    self.log_text.insert(tk.END, data + "\n")
                    self.log_text.see(tk.END)

                elif msg_type == 'progress':
                    self.progress['value'] = data

                elif msg_type == 'status':
                    self.status_label.config(text=data)

                elif msg_type == 'result':
                    self.display_results(data)

                elif msg_type == 'done':
                    self.is_running = False
                    self.start_button.config(state='normal')
                    self.stop_button.config(state='disabled')
                    messagebox.showinfo("完成", "测试已完成！")

                elif msg_type == 'error':
                    self.is_running = False
                    self.start_button.config(state='normal')
                    self.stop_button.config(state='disabled')
                    messagebox.showerror("错误", data)

        except queue.Empty:
            pass

        # 每100ms检查一次队列
        self.root.after(100, self.process_queue)

    def log(self, message):
        """记录日志（线程安全）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_queue.put(('log', f"[{timestamp}] {message}"))

    def update_progress(self, value):
        """更新进度条（线程安全）"""
        self.message_queue.put(('progress', value))

    def update_status(self, text):
        """更新状态（线程安全）"""
        self.message_queue.put(('status', text))

    def show_test_detail(self, test_id):
        """显示测试项详情"""
        info = TEST_DESCRIPTIONS[test_id]

        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"测试详情 - {info['name']}")
        detail_window.geometry("500x400")

        # 创建详情内容
        frame = ttk.Frame(detail_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=info['name'],
                 font=('Microsoft YaHei', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=info['english'],
                 font=('Microsoft YaHei', 10)).pack(anchor=tk.W)
        ttk.Label(frame, text=f"标准: {info['standard']}",
                 font=('Microsoft YaHei', 10)).pack(anchor=tk.W, pady=(10, 0))

        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)

        ttk.Label(frame, text="测试目的:",
                 font=('Microsoft YaHei', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=info['purpose'],
                 wraplength=450).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(frame, text="检测方法:",
                 font=('Microsoft YaHei', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=info['method'],
                 wraplength=450).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(frame, text="详细说明:",
                 font=('Microsoft YaHei', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text=info['description'],
                 wraplength=450).pack(anchor=tk.W, pady=(0, 10))

        # 通过标准
        ttk.Label(frame, text="通过标准:",
                 font=('Microsoft YaHei', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(frame, text="P-value ≥ 0.01").pack(anchor=tk.W)

        ttk.Button(frame, text="关闭", command=detail_window.destroy).pack(pady=20)

    def select_single_file(self):
        """选择单个文件"""
        filepath = filedialog.askopenfilename(
            title="选择测试数据文件",
            filetypes=[
                ("二进制文件", "*.bin"),
                ("文本文件", "*.txt"),
                ("数据文件", "*.dat"),
                ("原始数据", "*.raw"),
                ("所有文件", "*.*")
            ]
        )

        if filepath:
            self.data_files = [filepath]
            self.update_file_list()

    def select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory(title="选择测试数据目录")

        if directory:
            # 扫描目录中的文件
            self.data_files = []
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.bin', '.txt', '.dat', '.raw']:
                        self.data_files.append(filepath)

            self.update_file_list()

    def clear_files(self):
        """清空文件列表"""
        self.data_files = []
        self.update_file_list()

    def update_file_list(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)

        for filepath in self.data_files:
            self.file_listbox.insert(tk.END, os.path.basename(filepath))

        if self.data_files:
            self.file_info_label.config(text=f"已选择 {len(self.data_files)} 个文件")
        else:
            self.file_info_label.config(text="未选择文件")

    def select_all_tests(self):
        """全选测试项"""
        for var in self.selected_tests.values():
            var.set(True)

    def invert_selection(self):
        """反选测试项"""
        for var in self.selected_tests.values():
            var.set(not var.get())

    def select_nist_tests(self):
        """选择所有NIST测试项"""
        for test_id, var in self.selected_tests.items():
            if TEST_DESCRIPTIONS[test_id]['standard'] == 'NIST SP 800-22':
                var.set(True)
            else:
                var.set(False)

    def select_gbt_tests(self):
        """选择所有GB/T测试项"""
        for test_id, var in self.selected_tests.items():
            if TEST_DESCRIPTIONS[test_id]['standard'] == 'GB/T 32915-2016':
                var.set(True)
            else:
                var.set(False)

    def run_tests(self):
        """运行测试"""
        if self.is_running:
            messagebox.showwarning("警告", "测试正在运行中！")
            return

        if not self.data_files:
            messagebox.showwarning("警告", "请先选择测试数据文件！")
            return

        # 获取选中的测试项
        selected = [test_id for test_id, var in self.selected_tests.items() if var.get()]
        if not selected:
            messagebox.showwarning("警告", "请至少选择一个测试项目！")
            return

        # 确认开始测试
        if not messagebox.askyesno("确认", f"即将开始测试\n\n文件数: {len(self.data_files)}\n测试项: {len(selected)}\n\n是否继续？"):
            return

        # 更新UI状态
        self.is_running = True
        self.should_stop = False
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')

        # 清空日志和结果
        self.log_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)

        # 启动测试线程
        thread = threading.Thread(target=self._run_tests_thread, args=(selected,), daemon=True)
        thread.start()

    def stop_tests(self):
        """停止测试"""
        if self.is_running:
            self.should_stop = True
            self.update_status("正在停止...")
            self.log("正在停止测试...")

    def _run_tests_thread(self, selected_tests):
        """测试线程"""
        try:
            loader = DataLoader()
            nist_suite = NISTTestSuite()
            gbt_suite = GBTTestSuite()

            all_results = []
            total_files = len(self.data_files)

            self.log("=" * 60)
            self.log("开始测试...")
            self.log(f"选中的测试项: {len(selected_tests)} 个")
            self.log(f"测试文件数: {total_files} 个")
            self.log("=" * 60)

            for file_idx, filepath in enumerate(self.data_files):
                # 检查是否需要停止
                if self.should_stop:
                    self.log("测试已被用户停止")
                    break

                self.log(f"\n处理文件 {file_idx + 1}/{total_files}: {os.path.basename(filepath)}")
                self.update_status(f"处理文件 {file_idx + 1}/{total_files}")

                # 加载数据
                try:
                    bits = loader.load_from_file(filepath)
                    info = loader.get_sequence_info(bits)
                    self.log(f"  序列长度: {info['length']:,} 比特")
                    self.log(f"  1的比例: {info['ones_ratio']:.4f}")
                except Exception as e:
                    self.log(f"  错误: 无法加载文件 - {e}")
                    continue

                # 验证序列
                valid, msg = loader.validate_sequence(bits)
                if not valid:
                    self.log(f"  警告: {msg}")
                    continue

                # 分割序列
                segments = loader.split_sequence(bits, segment_length=1000000)
                self.log(f"  分割为 {len(segments)} 个测试片段")

                # 运行测试
                for seg_idx, segment in enumerate(segments):
                    # 检查是否需要停止
                    if self.should_stop:
                        self.log("测试已被用户停止")
                        break

                    self.log(f"  测试片段 {seg_idx + 1}/{len(segments)}...")
                    self.update_status(f"文件 {file_idx + 1}/{total_files} - 片段 {seg_idx + 1}/{len(segments)}")

                    result = {'file': os.path.basename(filepath), 'segment': seg_idx}

                    # 运行NIST测试
                    try:
                        nist_results = nist_suite.run_all_tests(segment)
                        for test_id in selected_tests:
                            if test_id in nist_results:
                                result[test_id] = nist_results[test_id]
                    except Exception as e:
                        self.log(f"    NIST测试错误: {e}")

                    # 运行GB/T测试
                    try:
                        gbt_results = gbt_suite.run_all_tests(segment)
                        for test_id in selected_tests:
                            if test_id in gbt_results:
                                result[test_id] = gbt_results[test_id]
                    except Exception as e:
                        self.log(f"    GB/T测试错误: {e}")

                    all_results.append(result)

                    # 更新进度
                    progress = ((file_idx * len(segments) + seg_idx + 1) /
                               (total_files * len(segments)) * 100)
                    self.update_progress(progress)

                if self.should_stop:
                    break

            # 计算统计结果
            if all_results:
                self.test_results = self._calculate_statistics(all_results, selected_tests)

                # 显示结果
                self.message_queue.put(('result', self.test_results))

                self.log("\n" + "=" * 60)
                self.log("测试完成！")
                self.log("=" * 60)
            else:
                self.log("\n没有有效的测试结果")

            # 通知完成
            self.message_queue.put(('done', None))

        except Exception as e:
            self.log(f"\n错误: {e}")
            self.message_queue.put(('error', str(e)))

    def _calculate_statistics(self, all_results, selected_tests):
        """计算统计结果"""
        if not all_results:
            return {}

        statistics = {}

        for test_id in selected_tests:
            p_values = [r.get(test_id) for r in all_results if test_id in r]

            if p_values:
                pass_count = sum(1 for p in p_values if p >= 0.01)
                pass_rate = pass_count / len(p_values)

                statistics[test_id] = {
                    'pass_rate': pass_rate,
                    'pass_count': pass_count,
                    'total_count': len(p_values),
                    'min_p_value': min(p_values),
                    'max_p_value': max(p_values),
                    'avg_p_value': sum(p_values) / len(p_values)
                }

        return statistics

    def display_results(self, results):
        """显示测试结果"""
        self.result_text.delete(1.0, tk.END)

        self.result_text.insert(tk.END, "=" * 70 + "\n")
        self.result_text.insert(tk.END, "测试结果汇总\n")
        self.result_text.insert(tk.END, "=" * 70 + "\n\n")

        # 按标准分组显示
        nist_tests = {k: v for k, v in results.items()
                     if TEST_DESCRIPTIONS[k]['standard'] == 'NIST SP 800-22'}
        gbt_tests = {k: v for k, v in results.items()
                    if TEST_DESCRIPTIONS[k]['standard'] == 'GB/T 32915-2016'}

        if nist_tests:
            self.result_text.insert(tk.END, "NIST SP 800-22 测试结果:\n")
            self.result_text.insert(tk.END, "-" * 70 + "\n")
            self.result_text.insert(tk.END, f"{'测试项':<30} {'通过率':>10} {'通过/总数':>15} {'状态':>8}\n")
            self.result_text.insert(tk.END, "-" * 70 + "\n")

            for test_id, stats in nist_tests.items():
                name = TEST_DESCRIPTIONS[test_id]['name']
                pass_rate = stats['pass_rate']
                status = "PASS" if pass_rate >= 0.98 else "FAIL"

                self.result_text.insert(tk.END,
                    f"{name:<30} {pass_rate*100:>9.2f}% "
                    f"{stats['pass_count']:>6}/{stats['total_count']:<6} "
                    f"{status:>8}\n")

            nist_pass_rate = sum(s['pass_rate'] for s in nist_tests.values()) / len(nist_tests)
            self.result_text.insert(tk.END, "-" * 70 + "\n")
            self.result_text.insert(tk.END, f"{'NIST总体通过率':<30} {nist_pass_rate*100:>9.2f}%\n\n")

        if gbt_tests:
            self.result_text.insert(tk.END, "GB/T 32915-2016 补充测试结果:\n")
            self.result_text.insert(tk.END, "-" * 70 + "\n")
            self.result_text.insert(tk.END, f"{'测试项':<30} {'通过率':>10} {'通过/总数':>15} {'状态':>8}\n")
            self.result_text.insert(tk.END, "-" * 70 + "\n")

            for test_id, stats in gbt_tests.items():
                name = TEST_DESCRIPTIONS[test_id]['name']
                pass_rate = stats['pass_rate']
                status = "PASS" if pass_rate >= 0.98 else "FAIL"

                self.result_text.insert(tk.END,
                    f"{name:<30} {pass_rate*100:>9.2f}% "
                    f"{stats['pass_count']:>6}/{stats['total_count']:<6} "
                    f"{status:>8}\n")

            gbt_pass_rate = sum(s['pass_rate'] for s in gbt_tests.values()) / len(gbt_tests)
            self.result_text.insert(tk.END, "-" * 70 + "\n")
            self.result_text.insert(tk.END, f"{'GB/T总体通过率':<30} {gbt_pass_rate*100:>9.2f}%\n\n")

        # 总体结论
        overall_pass_rate = sum(s['pass_rate'] for s in results.values()) / len(results)
        self.result_text.insert(tk.END, "=" * 70 + "\n")
        self.result_text.insert(tk.END, f"总体通过率: {overall_pass_rate*100:.2f}%\n")

        if overall_pass_rate >= 0.98:
            self.result_text.insert(tk.END, "测试结论: 通过\n")
        else:
            self.result_text.insert(tk.END, "测试结论: 未通过\n")

        self.result_text.insert(tk.END, "=" * 70 + "\n")

    def generate_report(self):
        """生成报告"""
        if not self.test_results:
            messagebox.showwarning("警告", "请先运行测试！")
            return

        # 选择保存目录
        output_dir = filedialog.askdirectory(title="选择报告保存目录")
        if not output_dir:
            return

        try:
            # 准备结果数据
            results = {
                'file_count': len(self.data_files),
                'total_bits': 1000000 * len(self.data_files),
                'significance_level': 0.01,
                'nist_results': {},
                'gbt_results': {},
                'nist_pass_rate': 0,
                'gbt_pass_rate': 0,
                'overall_pass_rate': 0
            }

            nist_rates = []
            gbt_rates = []

            for test_id, stats in self.test_results.items():
                if TEST_DESCRIPTIONS[test_id]['standard'] == 'NIST SP 800-22':
                    results['nist_results'][test_id] = stats['pass_rate']
                    nist_rates.append(stats['pass_rate'])
                else:
                    results['gbt_results'][test_id] = stats['pass_rate']
                    gbt_rates.append(stats['pass_rate'])

            if nist_rates:
                results['nist_pass_rate'] = sum(nist_rates) / len(nist_rates)
            if gbt_rates:
                results['gbt_pass_rate'] = sum(gbt_rates) / len(gbt_rates)

            all_rates = nist_rates + gbt_rates
            if all_rates:
                results['overall_pass_rate'] = sum(all_rates) / len(all_rates)

            # 生成报告
            report_gen = ReportGenerator(output_dir)
            text_path = report_gen.generate_text_report(results)
            html_path = report_gen.generate_html_report(results)
            json_path = report_gen.generate_json_report(results)

            self.log(f"\n报告已生成:")
            self.log(f"  文本报告: {text_path}")
            self.log(f"  HTML报告: {html_path}")
            self.log(f"  JSON结果: {json_path}")

            messagebox.showinfo("成功", f"报告已生成到:\n{output_dir}")

            # 打开报告目录
            os.startfile(output_dir)

        except Exception as e:
            self.log(f"生成报告错误: {e}")
            messagebox.showerror("错误", f"生成报告时出错: {e}")


def main():
    """主函数"""
    root = tk.Tk()
    app = RandomTestPlatform(root)
    root.mainloop()


if __name__ == '__main__':
    main()
