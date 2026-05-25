#!/usr/bin/env python3
"""
CIS芯片TRNG随机性测试平台 - 现代化UI
使用ttkbootstrap提供现代化界面，向导式流程，测试原理说明
"""

import os
import sys
import json
import subprocess
import threading
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledFrame, ScrolledText
    from ttkbootstrap.dialogs import Messagebox
except ImportError:
    print("请先安装ttkbootstrap: pip install ttkbootstrap")
    sys.exit(1)

import tkinter as tk
from tkinter import filedialog

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试项定义
NIST_TESTS = [
    {"id": "frequency", "name": "单比特频数检测", "desc": "检查0和1的数量是否大致相等",
     "analogy": "就像抛硬币，如果抛1000次，正面和反面应该各接近500次",
     "purpose": "验证随机序列中0和1的分布是否均匀", "icon": "📊"},
    {"id": "block_frequency", "name": "块内频数检测", "desc": "检查每个小块中0和1的比例",
     "analogy": "把一长串数字切成小段，每段里0和1都应该差不多",
     "purpose": "检测局部区域的随机性", "icon": "📊"},
    {"id": "runs", "name": "游程检测", "desc": "检查连续相同比特的出现频率",
     "analogy": "就像检查天气预报，连续晴天和连续雨天不应该太长",
     "purpose": "验证比特交替的频率是否随机", "icon": "🔄"},
    {"id": "longest_run", "name": "最长游程检测", "desc": "检查最长连续相同比特的长度",
     "analogy": "连续出现10次正面的硬币可能有问题",
     "purpose": "检测是否存在异常长的连续序列", "icon": "📏"},
    {"id": "matrix_rank", "name": "二元矩阵秩检测", "desc": "检查矩阵的秩分布",
     "analogy": "把数字排成方阵，看行和列是否线性独立",
     "purpose": "检测序列中的线性依赖关系", "icon": "🔢"},
    {"id": "dft", "name": "离散傅里叶变换检测", "desc": "检查频谱中的周期性模式",
     "analogy": "听音乐时看频谱，随机信号应该没有明显的主旋律",
     "purpose": "检测序列中的周期性特征", "icon": "📈"},
    {"id": "non_overlapping_template", "name": "非重叠模板匹配检测", "desc": "检查特定模式的出现频率",
     "analogy": "在随机文本中找特定单词，出现次数应该符合预期",
     "purpose": "检测特定比特模式是否异常频繁", "icon": "🔍"},
    {"id": "overlapping_template", "name": "重叠模板匹配检测", "desc": "检查重叠模式的出现频率",
     "analogy": "允许重叠地找模式，统计出现次数",
     "purpose": "更全面地检测模式匹配", "icon": "🔍"},
    {"id": "maurers_universal", "name": "Maurer通用检测", "desc": "检测序列的压缩程度",
     "analogy": "真正随机的序列很难压缩，就像噪音无法简化",
     "purpose": "评估序列的信息熵", "icon": "📦"},
    {"id": "linear_complexity", "name": "线性复杂度检测", "desc": "检查生成序列所需的最短线性反馈移位寄存器长度",
     "analogy": "用简单的规则能生成的序列不够随机",
     "purpose": "检测序列是否可被简单算法预测", "icon": "⚙️"},
    {"id": "serial", "name": "序列检测", "desc": "检查所有m比特模式的出现频率",
     "analogy": "掷两个骰子，每种组合出现次数应该差不多",
     "purpose": "检测所有比特模式的均匀性", "icon": "🎲"},
    {"id": "approximate_entropy", "name": "近似熵检测", "desc": "检测序列的可预测性",
     "analogy": "随机序列越不可预测，熵值越高",
     "purpose": "评估序列的随机性和不可预测性", "icon": "🌡️"},
    {"id": "cumulative_sums", "name": "累加和检测", "desc": "检查累加和的偏移程度",
     "analogy": "随机游走不应该总是朝一个方向走",
     "purpose": "检测序列中的偏差趋势", "icon": "📉"},
    {"id": "random_excursions", "name": "随机游程检测", "desc": "检查随机游程访问各状态的次数",
     "analogy": "醉汉走路，每个方向被访问的次数应该均衡",
     "purpose": "检测随机游程的状态分布", "icon": "🚶"},
    {"id": "random_excursions_variant", "name": "随机游程变体检测", "desc": "检查特定状态的访问次数",
     "analogy": "醉汉是否在某个地方停留太久",
     "purpose": "检测特定状态的异常访问", "icon": "🚶"},
]

GBT_TESTS = [
    {"id": "poker", "name": "扑克检测", "desc": "检查m比特分组的出现频率",
     "analogy": "扑克牌的每种花色出现次数应该均衡",
     "purpose": "检测比特分组的均匀性", "icon": "🃏"},
    {"id": "autocorrelation", "name": "自相关检测", "desc": "检查序列与自身移位后的相关性",
     "analogy": "把数字序列错开几位再比较，应该看不出规律",
     "purpose": "检测序列的自相关特性", "icon": "🔗"},
    {"id": "binary_derivative", "name": "二元推导检测", "desc": "检查相邻比特异或后的随机性",
     "analogy": "把相邻两个数做异或，结果也应该随机",
     "purpose": "检测序列的推导随机性", "icon": "🔀"},
]

# 颜色方案
COLORS = {
    "primary": "#2196F3",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "bg": "#F5F5F5",
    "text": "#212121",
    "light_text": "#757575",
}


class ModernTestPlatform:
    """现代化测试平台主类"""

    def __init__(self):
        self.root = ttk.Window(
            title="CIS芯片TRNG随机性测试平台",
            themename="cosmo",
            size=(1200, 800),
            minsize=(1000, 600)
        )
        self.root.place_window_center()

        # 状态变量
        self.current_step = 0
        self.selected_file = None
        self.selected_tests = {}
        self.test_running = False
        self.process = None
        self.output_file = None
        self.marker_file = None

        # 初始化测试选择
        for t in NIST_TESTS + GBT_TESTS:
            self.selected_tests[t["id"]] = tk.BooleanVar(value=True)

        # 创建界面
        self._create_ui()

    def _create_ui(self):
        """创建主界面"""
        # 顶部标题栏
        header = ttk.Frame(self.root, bootstyle=PRIMARY)
        header.pack(fill=X, padx=0, pady=0)

        title_frame = ttk.Frame(header, bootstyle=PRIMARY)
        title_frame.pack(fill=X, padx=20, pady=10)

        ttk.Label(
            title_frame,
            text="CIS芯片TRNG随机性测试平台",
            font=("微软雅黑", 18, "bold"),
            bootstyle=PRIMARY
        ).pack(side=LEFT)

        # 主题切换按钮
        themes = ["cosmo", "flatly", "darkly", "journal", "litera", "minty", "pulse", "sandstone", "united", "yeti"]
        self.theme_var = tk.StringVar(value="cosmo")
        theme_menu = ttk.OptionMenu(
            title_frame, self.theme_var, "cosmo", *themes,
            command=self._change_theme
        )
        theme_menu.pack(side=RIGHT, padx=5)

        ttk.Label(
            title_frame,
            text="主题:",
            font=("微软雅黑", 10),
            bootstyle=PRIMARY
        ).pack(side=RIGHT)

        # 进度条
        self.progress_frame = ttk.Frame(header, bootstyle=PRIMARY)
        self.progress_frame.pack(fill=X, padx=20, pady=(0, 10))
        self._update_progress_bar()

        # 主内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # 左侧导航
        nav_frame = ttk.Frame(main_frame, width=200, bootstyle=LIGHT)
        nav_frame.pack(side=LEFT, fill=Y, padx=(0, 10))
        nav_frame.pack_propagate(False)

        self.nav_buttons = []
        nav_items = [
            ("📋 测试向导", 0),
            ("📖 测试说明", 1),
            ("📊 测试结果", 2),
            ("⚙️ 设置", 3),
        ]

        for text, step in nav_items:
            btn = ttk.Button(
                nav_frame,
                text=text,
                bootstyle=OUTLINE,
                command=lambda s=step: self._switch_page(s),
                width=15
            )
            btn.pack(fill=X, padx=10, pady=5)
            self.nav_buttons.append(btn)

        # 右侧内容区
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # 创建各页面
        self._create_wizard_page()
        self._create_explanation_page()
        self._create_results_page()
        self._create_settings_page()

        # 底部状态栏
        status_frame = ttk.Frame(self.root, bootstyle=INFO)
        status_frame.pack(fill=X, side=BOTTOM)

        self.status_label = ttk.Label(
            status_frame,
            text="就绪 | 请选择测试数据文件",
            font=("微软雅黑", 9),
            bootstyle=INFO
        )
        self.status_label.pack(fill=X, padx=10, pady=5)

        # 默认显示向导页面
        self._switch_page(0)

    def _update_progress_bar(self):
        """更新顶部进度条"""
        for widget in self.progress_frame.winfo_children():
            widget.destroy()

        steps = ["准备数据", "选择测试", "执行测试", "查看结果"]
        for i, step in enumerate(steps):
            # 步骤圆圈
            circle_frame = ttk.Frame(self.progress_frame)
            circle_frame.pack(side=LEFT, padx=5)

            if i < self.current_step:
                style = SUCCESS
                text = "✓"
            elif i == self.current_step:
                style = PRIMARY
                text = str(i + 1)
            else:
                style = SECONDARY
                text = str(i + 1)

            circle = ttk.Label(
                circle_frame,
                text=text,
                font=("微软雅黑", 12, "bold"),
                width=3,
                anchor=CENTER,
                bootstyle=style
            )
            circle.pack()

            ttk.Label(
                circle_frame,
                text=step,
                font=("微软雅黑", 8),
                bootstyle=style
            ).pack()

            # 连接线
            if i < len(steps) - 1:
                line = ttk.Label(
                    self.progress_frame,
                    text="─" * 5,
                    font=("微软雅黑", 10),
                    bootstyle=SECONDARY
                )
                line.pack(side=LEFT, padx=2, pady=(10, 0))

    def _change_theme(self, theme_name):
        """切换主题"""
        self.root.style.theme_use(theme_name)

    def _switch_page(self, page_index):
        """切换页面"""
        # 隐藏所有页面
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()

        # 更新导航按钮状态
        for i, btn in enumerate(self.nav_buttons):
            if i == page_index:
                btn.configure(bootstyle=PRIMARY)
            else:
                btn.configure(bootstyle=OUTLINE)

        # 显示对应页面
        if page_index == 0:
            self.wizard_frame.pack(fill=BOTH, expand=True)
        elif page_index == 1:
            self.explanation_frame.pack(fill=BOTH, expand=True)
        elif page_index == 2:
            self.results_frame.pack(fill=BOTH, expand=True)
        elif page_index == 3:
            self.settings_frame.pack(fill=BOTH, expand=True)

    def _create_wizard_page(self):
        """创建向导页面"""
        self.wizard_frame = ttk.Frame(self.content_frame)

        # 向导步骤内容
        self.wizard_steps = ttk.Frame(self.wizard_frame)
        self.wizard_steps.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # 创建各步骤
        self._create_step0_data_prep()
        self._create_step1_test_select()
        self._create_step2_execution()
        self._create_step3_results()

        # 底部导航按钮
        btn_frame = ttk.Frame(self.wizard_frame)
        btn_frame.pack(fill=X, padx=10, pady=10)

        self.btn_prev = ttk.Button(
            btn_frame,
            text="← 上一步",
            bootstyle=OUTLINE,
            command=self._prev_step,
            state=DISABLED
        )
        self.btn_prev.pack(side=LEFT, padx=5)

        self.btn_next = ttk.Button(
            btn_frame,
            text="下一步 →",
            bootstyle=PRIMARY,
            command=self._next_step
        )
        self.btn_next.pack(side=LEFT, padx=5)

        self.btn_start = ttk.Button(
            btn_frame,
            text="▶ 开始测试",
            bootstyle=SUCCESS,
            command=self._start_test,
            state=DISABLED
        )
        self.btn_start.pack(side=RIGHT, padx=5)

        # 显示第一步
        self._show_wizard_step(0)

    def _create_step0_data_prep(self):
        """步骤0: 数据准备"""
        frame = ttk.Frame(self.wizard_steps)
        self.step0_frame = frame

        ttk.Label(
            frame,
            text="📋 步骤1: 准备测试数据",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # 输入件说明
        info_frame = ttk.Labelframe(frame, text="输入件要求", padding=10)
        info_frame.pack(fill=X, pady=5)

        info_text = """数据来源: CIS芯片TRNG硬件输出
文件格式: .bin（二进制）或 .txt（文本）
序列长度: 每组 ≥ 1,000,000 比特（1Mbit）
序列组数: ≥ 1000组（用于统计分析）
采集条件: 多批次、不同时段，覆盖温度/电压变化"""

        ttk.Label(
            info_frame,
            text=info_text,
            font=("微软雅黑", 10),
            justify=LEFT
        ).pack(anchor=W)

        # 采集指导
        guide_frame = ttk.Labelframe(frame, text="数据采集方法", padding=10)
        guide_frame.pack(fill=X, pady=5)

        guide_text = """• UART串口输出
• SPI接口读取
• 专用调试接口
• 芯片测试模式输出"""

        ttk.Label(
            guide_frame,
            text=guide_text,
            font=("微软雅黑", 10),
            justify=LEFT
        ).pack(anchor=W)

        # 文件选择
        file_frame = ttk.Labelframe(frame, text="选择数据文件", padding=10)
        file_frame.pack(fill=X, pady=5)

        file_btn_frame = ttk.Frame(file_frame)
        file_btn_frame.pack(fill=X)

        ttk.Button(
            file_btn_frame,
            text="📁 选择文件",
            bootstyle=PRIMARY,
            command=self._select_file
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            file_btn_frame,
            text="📂 选择文件夹",
            bootstyle=OUTLINE,
            command=self._select_directory
        ).pack(side=LEFT, padx=5)

        self.file_label = ttk.Label(
            file_frame,
            text="未选择文件",
            font=("微软雅黑", 10),
            foreground=COLORS["light_text"]
        )
        self.file_label.pack(anchor=W, pady=(10, 0))

        # 验证结果
        self.validate_label = ttk.Label(
            file_frame,
            text="",
            font=("微软雅黑", 10)
        )
        self.validate_label.pack(anchor=W, pady=(5, 0))

    def _create_step1_test_select(self):
        """步骤1: 测试项选择"""
        frame = ttk.Frame(self.wizard_steps)
        self.step1_frame = frame

        ttk.Label(
            frame,
            text="📊 步骤2: 选择测试项目",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # 快捷选择按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X, pady=5)

        ttk.Button(
            btn_frame,
            text="全选",
            bootstyle=OUTLINE,
            command=lambda: self._select_all_tests(True)
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="全不选",
            bootstyle=OUTLINE,
            command=lambda: self._select_all_tests(False)
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="NIST全部",
            bootstyle=OUTLINE,
            command=self._select_nist
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="GB/T全部",
            bootstyle=OUTLINE,
            command=self._select_gbt
        ).pack(side=LEFT, padx=5)

        # 测试项列表（滚动）
        scroll_frame = ScrolledFrame(frame, autohide=True)
        scroll_frame.pack(fill=BOTH, expand=True, pady=5)

        # NIST测试
        nist_frame = ttk.Labelframe(scroll_frame, text="NIST SP 800-22 (15项)", padding=10)
        nist_frame.pack(fill=X, pady=5)

        for test in NIST_TESTS:
            test_row = ttk.Frame(nist_frame)
            test_row.pack(fill=X, pady=2)

            cb = ttk.Checkbutton(
                test_row,
                text=f"{test['icon']} {test['name']}",
                variable=self.selected_tests[test["id"]],
                bootstyle=PRIMARY
            )
            cb.pack(side=LEFT)

            ttk.Label(
                test_row,
                text=f"- {test['desc']}",
                font=("微软雅黑", 9),
                foreground=COLORS["light_text"]
            ).pack(side=LEFT, padx=10)

        # GB/T测试
        gbt_frame = ttk.Labelframe(scroll_frame, text="GB/T 32915-2016 (3项补充)", padding=10)
        gbt_frame.pack(fill=X, pady=5)

        for test in GBT_TESTS:
            test_row = ttk.Frame(gbt_frame)
            test_row.pack(fill=X, pady=2)

            cb = ttk.Checkbutton(
                test_row,
                text=f"{test['icon']} {test['name']}",
                variable=self.selected_tests[test["id"]],
                bootstyle=SUCCESS
            )
            cb.pack(side=LEFT)

            ttk.Label(
                test_row,
                text=f"- {test['desc']}",
                font=("微软雅黑", 9),
                foreground=COLORS["light_text"]
            ).pack(side=LEFT, padx=10)

    def _create_step2_execution(self):
        """步骤2: 测试执行"""
        frame = ttk.Frame(self.wizard_steps)
        self.step2_frame = frame

        ttk.Label(
            frame,
            text="▶ 步骤3: 执行测试",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # 进度显示
        progress_frame = ttk.Labelframe(frame, text="测试进度", padding=10)
        progress_frame.pack(fill=X, pady=5)

        self.test_progress = ttk.Progressbar(
            progress_frame,
            bootstyle=SUCCESS,
            mode=DETERMINATE
        )
        self.test_progress.pack(fill=X, pady=5)

        self.progress_label = ttk.Label(
            progress_frame,
            text="等待开始...",
            font=("微软雅黑", 10)
        )
        self.progress_label.pack(anchor=W)

        # 日志区域
        log_frame = ttk.Labelframe(frame, text="测试日志", padding=10)
        log_frame.pack(fill=BOTH, expand=True, pady=5)

        self.log_text = ScrolledText(
            log_frame,
            font=("Consolas", 9),
            height=15,
            autohide=True
        )
        self.log_text.pack(fill=BOTH, expand=True)

    def _create_step3_results(self):
        """步骤3: 测试结果"""
        frame = ttk.Frame(self.wizard_steps)
        self.step3_frame = frame

        ttk.Label(
            frame,
            text="📈 步骤4: 查看结果",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # 结果摘要
        self.summary_frame = ttk.Labelframe(frame, text="测试结果摘要", padding=10)
        self.summary_frame.pack(fill=X, pady=5)

        self.summary_label = ttk.Label(
            self.summary_frame,
            text="测试完成后将在此显示结果",
            font=("微软雅黑", 11)
        )
        self.summary_label.pack(anchor=W)

        # 详细结果
        detail_frame = ttk.Labelframe(frame, text="详细结果", padding=10)
        detail_frame.pack(fill=BOTH, expand=True, pady=5)

        self.detail_text = ScrolledText(
            detail_frame,
            font=("Consolas", 9),
            height=15,
            autohide=True
        )
        self.detail_text.pack(fill=BOTH, expand=True)

    def _create_explanation_page(self):
        """创建测试说明页面"""
        self.explanation_frame = ttk.Frame(self.content_frame)

        ttk.Label(
            self.explanation_frame,
            text="📖 测试项目说明",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, padx=10, pady=10)

        # 测试项选择
        select_frame = ttk.Frame(self.explanation_frame)
        select_frame.pack(fill=X, padx=10, pady=5)

        ttk.Label(
            select_frame,
            text="选择测试项:",
            font=("微软雅黑", 11)
        ).pack(side=LEFT)

        all_tests = NIST_TESTS + GBT_TESTS
        test_names = [t["name"] for t in all_tests]
        self.explain_var = tk.StringVar(value=test_names[0])

        test_menu = ttk.OptionMenu(
            select_frame, self.explain_var, test_names[0], *test_names,
            command=lambda _: self._update_explanation()
        )
        test_menu.pack(side=LEFT, padx=10)

        # 说明内容
        scroll_frame = ScrolledFrame(self.explanation_frame, autohide=True)
        scroll_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.explain_content = ttk.Frame(scroll_frame)
        self.explain_content.pack(fill=BOTH, expand=True)

        self._update_explanation()

    def _update_explanation(self):
        """更新测试说明内容"""
        for widget in self.explain_content.winfo_children():
            widget.destroy()

        all_tests = NIST_TESTS + GBT_TESTS
        test_name = self.explain_var.get()
        test = next((t for t in all_tests if t["name"] == test_name), None)

        if not test:
            return

        # 测试名称
        ttk.Label(
            self.explain_content,
            text=f"{test['icon']} {test['name']}",
            font=("微软雅黑", 18, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # 一句话概述
        overview_frame = ttk.Labelframe(self.explain_content, text="一句话概述", padding=10)
        overview_frame.pack(fill=X, pady=5)

        ttk.Label(
            overview_frame,
            text=test["desc"],
            font=("微软雅黑", 12)
        ).pack(anchor=W)

        # 测试目的
        purpose_frame = ttk.Labelframe(self.explain_content, text="测试目的", padding=10)
        purpose_frame.pack(fill=X, pady=5)

        ttk.Label(
            purpose_frame,
            text=test["purpose"],
            font=("微软雅黑", 11)
        ).pack(anchor=W)

        # 生活类比
        analogy_frame = ttk.Labelframe(self.explain_content, text="生活类比", padding=10)
        analogy_frame.pack(fill=X, pady=5)

        ttk.Label(
            analogy_frame,
            text=test["analogy"],
            font=("微软雅黑", 11),
            wraplength=600
        ).pack(anchor=W)

        # 通过标准
        criteria_frame = ttk.Labelframe(self.explain_content, text="通过标准", padding=10)
        criteria_frame.pack(fill=X, pady=5)

        ttk.Label(
            criteria_frame,
            text="• P-value ≥ 0.01\n• 通过率 ≥ 98%（在1000组测试中）",
            font=("微软雅黑", 11)
        ).pack(anchor=W)

        # 原理图解
        diagram_frame = ttk.Labelframe(self.explain_content, text="原理图解", padding=10)
        diagram_frame.pack(fill=X, pady=5)

        canvas = tk.Canvas(diagram_frame, width=600, height=150, bg="white")
        canvas.pack(pady=5)
        self._draw_test_diagram(canvas, test["id"])

    def _draw_test_diagram(self, canvas, test_id):
        """绘制测试原理图"""
        canvas.delete("all")

        if test_id == "frequency":
            # 0和1的频数图
            canvas.create_text(300, 20, text="0和1的频数应该接近相等", font=("微软雅黑", 10))
            canvas.create_rectangle(50, 50, 200, 130, fill=COLORS["primary"], outline="")
            canvas.create_text(125, 90, text="0: 50.02%", fill="white", font=("微软雅黑", 10, "bold"))
            canvas.create_rectangle(250, 50, 400, 130, fill=COLORS["success"], outline="")
            canvas.create_text(325, 90, text="1: 49.98%", fill="white", font=("微软雅黑", 10, "bold"))
            canvas.create_line(450, 40, 450, 140, fill=COLORS["error"], width=2, dash=(5, 5))
            canvas.create_text(500, 90, text="理想: 50%", font=("微软雅黑", 9))

        elif test_id == "runs":
            # 游程检测图
            canvas.create_text(300, 20, text="游程: 连续相同比特的序列", font=("微软雅黑", 10))
            bits = "0011101000110101110"
            x = 50
            for i, b in enumerate(bits):
                color = COLORS["primary"] if b == "1" else COLORS["warning"]
                canvas.create_rectangle(x, 60, x + 25, 90, fill=color, outline="")
                canvas.create_text(x + 12, 75, text=b, fill="white", font=("Consolas", 10, "bold"))
                x += 30
            canvas.create_text(300, 120, text="游程数 = 10 (转换次数)", font=("微软雅黑", 10))

        elif test_id == "poker":
            # 扑克检测图
            canvas.create_text(300, 20, text="扑克检测: 检查m比特分组的均匀性", font=("微软雅黑", 10))
            groups = ["0000", "0001", "0010", "0011", "0100", "0101", "0110", "0111"]
            x = 30
            for i, g in enumerate(groups):
                h = 30 + (i * 10)
                canvas.create_rectangle(x, 130 - h, x + 50, 130, fill=COLORS["primary"], outline="")
                canvas.create_text(x + 25, 115 - h // 2, text=g, fill="white", font=("Consolas", 8))
                x += 70
            canvas.create_text(300, 145, text="各分组出现次数应接近", font=("微软雅黑", 9))

        else:
            canvas.create_text(300, 75, text="原理图解", font=("微软雅黑", 12))
            canvas.create_text(300, 100, text="请查看详细文档了解测试原理", font=("微软雅黑", 10))

    def _create_results_page(self):
        """创建测试结果页面"""
        self.results_frame = ttk.Frame(self.content_frame)

        ttk.Label(
            self.results_frame,
            text="📊 测试结果",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, padx=10, pady=10)

        # 输出件说明
        output_frame = ttk.Labelframe(self.results_frame, text="输出件说明", padding=10)
        output_frame.pack(fill=X, padx=10, pady=5)

        output_text = """测试完成后将生成以下文件:
• 文本报告 (.txt): 包含所有测试结果
• HTML报告 (.html): 包含图表的可视化报告
• JSON结果 (.json): 程序可读的详细数据
• 图表文件 (.png): 测试通过率的可视化图表"""

        ttk.Label(
            output_frame,
            text=output_text,
            font=("微软雅黑", 10),
            justify=LEFT
        ).pack(anchor=W)

        # 通过标准
        criteria_frame = ttk.Labelframe(self.results_frame, text="通过标准", padding=10)
        criteria_frame.pack(fill=X, padx=10, pady=5)

        criteria_text = """• 单项测试 P-value ≥ 0.01
• 总体通过率 ≥ 98%
• 测试序列长度 ≥ 1Mbit/组
• 测试序列组数 ≥ 1000组
• 显著性水平 α = 0.01

P-value含义:
• P-value ≥ 0.01: 测试通过，序列表现出随机性
• P-value < 0.01: 测试失败，序列可能存在非随机特征
• P-value越接近1，随机性越好"""

        ttk.Label(
            criteria_frame,
            text=criteria_text,
            font=("微软雅黑", 10),
            justify=LEFT
        ).pack(anchor=W)

        # 结果历史
        history_frame = ttk.Labelframe(self.results_frame, text="测试结果历史", padding=10)
        history_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.results_text = ScrolledText(
            history_frame,
            font=("Consolas", 9),
            height=10,
            autohide=True
        )
        self.results_text.pack(fill=BOTH, expand=True)

        # 打开报告目录按钮
        ttk.Button(
            self.results_frame,
            text="📂 打开报告目录",
            bootstyle=OUTLINE,
            command=self._open_reports_dir
        ).pack(anchor=W, padx=10, pady=10)

    def _create_settings_page(self):
        """创建设置页面"""
        self.settings_frame = ttk.Frame(self.content_frame)

        ttk.Label(
            self.settings_frame,
            text="⚙️ 设置",
            font=("微软雅黑", 16, "bold")
        ).pack(anchor=W, padx=10, pady=10)

        # 测试参数
        param_frame = ttk.Labelframe(self.settings_frame, text="测试参数", padding=10)
        param_frame.pack(fill=X, padx=10, pady=5)

        # 显著性水平
        alpha_frame = ttk.Frame(param_frame)
        alpha_frame.pack(fill=X, pady=5)

        ttk.Label(
            alpha_frame,
            text="显著性水平 (α):",
            font=("微软雅黑", 10)
        ).pack(side=LEFT)

        self.alpha_var = tk.StringVar(value="0.01")
        ttk.Entry(
            alpha_frame,
            textvariable=self.alpha_var,
            width=10
        ).pack(side=LEFT, padx=10)

        ttk.Label(
            alpha_frame,
            text="(默认: 0.01)",
            font=("微软雅黑", 9),
            foreground=COLORS["light_text"]
        ).pack(side=LEFT)

        # 输出目录
        output_frame = ttk.Frame(param_frame)
        output_frame.pack(fill=X, pady=5)

        ttk.Label(
            output_frame,
            text="输出目录:",
            font=("微软雅黑", 10)
        ).pack(side=LEFT)

        self.output_dir_var = tk.StringVar(value="./reports")
        ttk.Entry(
            output_frame,
            textvariable=self.output_dir_var,
            width=30
        ).pack(side=LEFT, padx=10)

        ttk.Button(
            output_frame,
            text="选择",
            bootstyle=OUTLINE,
            command=self._select_output_dir
        ).pack(side=LEFT)

        # NIST测试说明
        nist_info = ttk.Labelframe(self.settings_frame, text="NIST SP 800-22 标准", padding=10)
        nist_info.pack(fill=X, padx=10, pady=5)

        ttk.Label(
            nist_info,
            text="美国国家标准与技术研究院发布的随机数测试标准\n包含15项统计测试，广泛用于评估随机数生成器质量",
            font=("微软雅黑", 10)
        ).pack(anchor=W)

        # GB/T测试说明
        gbt_info = ttk.Labelframe(self.settings_frame, text="GB/T 32915-2016 标准", padding=10)
        gbt_info.pack(fill=X, padx=10, pady=5)

        ttk.Label(
            gbt_info,
            text="中国国家标准，基于NIST标准扩展\n包含NIST的15项测试，额外增加扑克检测、自相关检测、二元推导检测",
            font=("微软雅黑", 10)
        ).pack(anchor=W)

    # === 事件处理 ===

    def _select_file(self):
        """选择数据文件"""
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
            self.selected_file = filepath
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)

            self.file_label.configure(
                text=f"已选择: {filename} ({filesize:,} 字节)",
                foreground=COLORS["success"]
            )

            # 验证文件
            self._validate_file(filepath)

    def _select_directory(self):
        """选择数据目录"""
        dirpath = filedialog.askdirectory(title="选择测试数据目录")

        if dirpath:
            self.selected_file = dirpath
            file_count = len([f for f in os.listdir(dirpath)
                            if f.endswith(('.bin', '.txt', '.dat', '.raw'))])

            self.file_label.configure(
                text=f"已选择目录: {os.path.basename(dirpath)} ({file_count}个文件)",
                foreground=COLORS["success"]
            )

            self.validate_label.configure(
                text="✓ 目录已选择，将测试所有数据文件",
                foreground=COLORS["success"]
            )

    def _validate_file(self, filepath):
        """验证数据文件"""
        try:
            filesize = os.path.getsize(filepath)
            min_size = 125000  # 1Mbit = 125KB

            if filesize < min_size:
                self.validate_label.configure(
                    text=f"⚠ 文件太小: {filesize:,} 字节 (最小需要 {min_size:,} 字节)",
                    foreground=COLORS["warning"]
                )
            else:
                groups = filesize // min_size
                self.validate_label.configure(
                    text=f"✓ 文件有效: 约 {groups} 组测试数据",
                    foreground=COLORS["success"]
                )
        except Exception as e:
            self.validate_label.configure(
                text=f"✗ 验证失败: {e}",
                foreground=COLORS["error"]
            )

    def _select_all_tests(self, select):
        """全选/全不选"""
        for var in self.selected_tests.values():
            var.set(select)

    def _select_nist(self):
        """选择所有NIST测试"""
        for test in NIST_TESTS:
            self.selected_tests[test["id"]].set(True)
        for test in GBT_TESTS:
            self.selected_tests[test["id"]].set(False)

    def _select_gbt(self):
        """选择所有GB/T测试"""
        for test in GBT_TESTS:
            self.selected_tests[test["id"]].set(True)
        for test in NIST_TESTS:
            self.selected_tests[test["id"]].set(False)

    def _select_output_dir(self):
        """选择输出目录"""
        dirpath = filedialog.askdirectory(title="选择报告输出目录")
        if dirpath:
            self.output_dir_var.set(dirpath)

    def _open_reports_dir(self):
        """打开报告目录"""
        output_dir = self.output_dir_var.get()
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            Messagebox.show_warning("目录不存在", "报告目录尚未创建")

    def _prev_step(self):
        """上一步"""
        if self.current_step > 0:
            self.current_step -= 1
            self._show_wizard_step(self.current_step)

    def _next_step(self):
        """下一步"""
        # 验证当前步骤
        if self.current_step == 0 and not self.selected_file:
            Messagebox.show_warning("提示", "请先选择测试数据文件")
            return

        if self.current_step == 1:
            selected = [k for k, v in self.selected_tests.items() if v.get()]
            if not selected:
                Messagebox.show_warning("提示", "请至少选择一个测试项目")
                return

        if self.current_step < 3:
            self.current_step += 1
            self._show_wizard_step(self.current_step)

    def _show_wizard_step(self, step):
        """显示向导步骤"""
        # 隐藏所有步骤
        for widget in self.wizard_steps.winfo_children():
            widget.pack_forget()

        # 显示对应步骤
        if step == 0:
            self.step0_frame.pack(fill=BOTH, expand=True)
            self.btn_prev.configure(state=DISABLED)
            self.btn_next.configure(state=NORMAL)
            self.btn_start.configure(state=DISABLED)
        elif step == 1:
            self.step1_frame.pack(fill=BOTH, expand=True)
            self.btn_prev.configure(state=NORMAL)
            self.btn_next.configure(state=NORMAL)
            self.btn_start.configure(state=DISABLED)
        elif step == 2:
            self.step2_frame.pack(fill=BOTH, expand=True)
            self.btn_prev.configure(state=NORMAL)
            self.btn_next.configure(state=DISABLED)
            self.btn_start.configure(state=NORMAL)
        elif step == 3:
            self.step3_frame.pack(fill=BOTH, expand=True)
            self.btn_prev.configure(state=NORMAL)
            self.btn_next.configure(state=DISABLED)
            self.btn_start.configure(state=DISABLED)

        self._update_progress_bar()

    def _start_test(self):
        """开始测试"""
        if self.test_running:
            return

        if not self.selected_file:
            Messagebox.show_warning("提示", "请先选择测试数据文件")
            return

        selected_tests = [k for k, v in self.selected_tests.items() if v.get()]
        if not selected_tests:
            Messagebox.show_warning("提示", "请至少选择一个测试项目")
            return

        self.test_running = True
        self.btn_start.configure(state=DISABLED, text="测试中...")
        self.status_label.configure(text="测试进行中...")

        # 清空日志
        self.log_text.delete("1.0", END)
        self.test_progress["value"] = 0

        # 创建临时文件
        self.output_file = os.path.join(tempfile.gettempdir(), "trng_test_output.txt")
        self.marker_file = os.path.join(tempfile.gettempdir(), "trng_test_done.marker")

        # 删除旧的标记文件
        if os.path.exists(self.marker_file):
            os.remove(self.marker_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

        # 启动测试线程
        thread = threading.Thread(
            target=self._run_test_process,
            args=(selected_tests,),
            daemon=True
        )
        thread.start()

        # 开始轮询结果
        self._poll_test_result()

    def _run_test_process(self, selected_tests):
        """在子进程中运行测试"""
        try:
            # 构建命令
            script_dir = os.path.dirname(os.path.abspath(__file__))
            main_script = os.path.join(script_dir, "main.py")

            if os.path.isdir(self.selected_file):
                cmd = [sys.executable, main_script, "--data-dir", self.selected_file]
            else:
                cmd = [sys.executable, main_script, "--file", self.selected_file]

            cmd.extend(["--output", self.output_dir_var.get()])
            cmd.extend(["--alpha", self.alpha_var.get()])

            # 运行子进程
            with open(self.output_file, "w", encoding="utf-8") as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                process.wait()

            # 写入完成标记
            with open(self.marker_file, "w") as f:
                f.write("done")

        except Exception as e:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(f"\n错误: {e}\n")
            with open(self.marker_file, "w") as f:
                f.write("error")

    def _poll_test_result(self):
        """轮询测试结果"""
        if not self.test_running:
            return

        # 更新日志
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    current = self.log_text.get("1.0", END).rstrip()
                    if content != current:
                        self.log_text.delete("1.0", END)
                        self.log_text.insert(END, content)
                        self.log_text.see(END)

                        # 更新进度
                        lines = content.split("\n")
                        for line in lines:
                            if "测试片段" in line:
                                try:
                                    parts = line.split("/")
                                    if len(parts) >= 2:
                                        current = int(parts[0].split()[-1])
                                        total = int(parts[1].split()[0])
                                        progress = (current / total) * 100
                                        self.test_progress["value"] = progress
                                        self.progress_label.configure(
                                            text=f"测试进度: {current}/{total}"
                                        )
                                except:
                                    pass
            except:
                pass

        # 检查是否完成
        if os.path.exists(self.marker_file):
            self._on_test_complete()
            return

        # 继续轮询
        self.root.after(200, self._poll_test_result)

    def _on_test_complete(self):
        """测试完成处理"""
        self.test_running = False
        self.test_progress["value"] = 100
        self.progress_label.configure(text="测试完成!")
        self.btn_start.configure(state=NORMAL, text="▶ 重新测试")
        self.status_label.configure(text="测试完成 | 查看结果页面获取详细报告")

        # 读取最终输出
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    self.log_text.delete("1.0", END)
                    self.log_text.insert(END, content)
            except:
                pass

        # 检查是否成功
        if os.path.exists(self.marker_file):
            try:
                with open(self.marker_file, "r") as f:
                    status = f.read().strip()

                if status == "done":
                    Messagebox.show_info("测试完成", "测试已完成！请查看结果页面。")
                    self._update_results_page()
                else:
                    Messagebox.show_error("测试失败", "测试过程中发生错误，请查看日志。")
            except:
                pass

        # 清理临时文件
        try:
            if os.path.exists(self.marker_file):
                os.remove(self.marker_file)
        except:
            pass

    def _update_results_page(self):
        """更新结果页面"""
        output_dir = self.output_dir_var.get()

        # 查找最新的报告文件
        if os.path.exists(output_dir):
            report_files = [f for f in os.listdir(output_dir) if f.endswith(('.txt', '.html', '.json'))]
            if report_files:
                # 找最新的文本报告
                txt_files = [f for f in report_files if f.endswith('.txt')]
                if txt_files:
                    latest = max(txt_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
                    report_path = os.path.join(output_dir, latest)

                    try:
                        with open(report_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        self.results_text.delete("1.0", END)
                        self.results_text.insert(END, content)

                        # 更新摘要
                        self.summary_label.configure(
                            text=f"测试报告已生成: {latest}\n请查看详细结果或打开报告目录"
                        )
                    except:
                        pass

        # 切换到结果页面
        self.current_step = 3
        self._show_wizard_step(3)

    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """主函数"""
    app = ModernTestPlatform()
    app.run()


if __name__ == "__main__":
    main()
