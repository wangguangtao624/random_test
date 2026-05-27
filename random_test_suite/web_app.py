#!/usr/bin/env python3
"""
CIS芯片TRNG随机性测试平台 - Web版
Flask后端 + Bootstrap 5前端
"""

import os
import sys
import json
import uuid
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nist_tests_ng import NISTTestSuiteNistrng
from core.gbt_tests import GBTTestSuite
from core.statistics import calculate_pass_rate
from utils.data_loader import DataLoader
from utils.report_generator import ReportGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['REPORT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'web_reports')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

# 任务存储
tasks = {}
history = []

# nistrng测试名到内部名的映射
NISTRNG_NAME_MAP = {
    'Monobit': 'frequency_monobit',
    'Frequency Within Block': 'frequency_within_block',
    'Runs': 'runs',
    'Longest Run Ones In A Block': 'longest_run_of_ones',
    'Binary Matrix Rank': 'binary_matrix_rank',
    'Discrete Fourier Transform': 'dft_spectral',
    'Non Overlapping Template Matching': 'non_overlapping_template',
    'Overlapping Template Matching': 'overlapping_template',
    'Maurers Universal': 'maurers_universal',
    'Linear Complexity': 'linear_complexity',
    'Serial': 'serial',
    'Approximate Entropy': 'approximate_entropy',
    'Cumulative Sums': 'cumulative_sums',
    'Random Excursion': 'random_excursions',
    'Random Excursion Variant': 'random_excursions_variant'
}

# 内部名到nistrng测试对象的映射 (延迟初始化)
NIST_TEST_OBJECTS = {}

ALL_NIST_IDS = list(NISTRNG_NAME_MAP.values())
ALL_GBT_IDS = ['poker_test_m4', 'poker_test_m8', 'autocorrelation_test', 'binary_derivative_test']


def get_nistrng_test_by_name(internal_name):
    """根据内部名获取nistrng测试对象"""
    import nistrng
    if not NIST_TEST_OBJECTS:
        for test in nistrng.SP800_22R1A_BATTERY:
            mapped = NISTRNG_NAME_MAP.get(test.name, test.name)
            NIST_TEST_OBJECTS[mapped] = test
    return NIST_TEST_OBJECTS.get(internal_name)


def get_source_files():
    """获取项目源文件列表"""
    base = os.path.dirname(os.path.abspath(__file__))
    source_files = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'uploads', 'web_reports',
                                                  'test_reports', 'test_reports_fixed',
                                                  'verification_reports', 'verification_reports_10',
                                                  'reports', '.pytest_cache', 'node_modules']]
        for f in files:
            if f.endswith(('.py', '.ini', '.txt', '.md', '.bat', '.json')):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, base)
                source_files.append({
                    'name': f,
                    'path': rel_path,
                    'size': os.path.getsize(full_path),
                    'type': os.path.splitext(f)[1]
                })
    source_files.sort(key=lambda x: x['path'])
    return source_files


def get_test_info():
    """获取测试项信息（含公式和流程）"""
    nist_tests = [
        {"id": "frequency_monobit", "name": "单比特频数检测 (Frequency Monobit)", "standard": "NIST SP 800-22",
         "desc": "检测序列中0和1的比例是否均衡",
         "analogy": "抛硬币1000次，正面和反面应该各接近500次",
         "purpose": "验证随机序列中0和1的分布是否均匀",
         "formula": "s_n = |∑(2x_i - 1)| / √n,  P = erfc(s_n / √2)",
         "formula_detail": "将0/1序列转换为+1/-1序列，求和后取绝对值，除以√n得到统计量s_n，再通过互补误差函数计算P-value",
         "code_flow": [
             "输入: 比特序列 X[]，长度 n",
             "将 0→+1, 1→-1 转换为 S[]",
             "计算 S_sum = ΣS[i]",
             "计算 s_obs = |S_sum| / √n",
             "P-value = erfc(s_obs / √2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "预检验: 序列长度 ≥ 100",
             "比特转换: 0→+1, 1→-1",
             "累加求和: S = Σ(2x_i - 1)",
             "计算统计量: s_obs = |S| / √n",
             "查表/计算: P = erfc(s_obs/√2)",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "frequency_within_block", "name": "块内频数检测 (Frequency Within Block)", "standard": "NIST SP 800-22",
         "desc": "检测每个子块中0和1的比例是否均衡",
         "analogy": "把长序列切成小段，每段里0和1都应该差不多",
         "purpose": "检测局部区域的随机性",
         "formula": "χ² = 4M · Σ(π_i - 0.5)²,  P = igamc(M/2, χ²/2)",
         "formula_detail": "将序列分为N个长度为M的块，计算每块中1的比例π_i，构造χ²统计量，自由度为N",
         "code_flow": [
             "输入: 比特序列 X[]，块大小 M=128",
             "计算块数 N = ⌊n/M⌋",
             "对每块计算 π_i = (1的个数)/M",
             "计算 χ² = 4M · Σ(π_i - 0.5)²",
             "P-value = igamc(N/2, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "将序列分为N个长度M的块",
             "统计每块中1的比例π_i",
             "计算χ²统计量",
             "不完全Gamma函数计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "runs", "name": "游程检测 (Runs Test)", "standard": "NIST SP 800-22",
         "desc": "检测连续相同比特(游程)的总数是否符合预期",
         "analogy": "天气预报中连续晴天和连续雨天的交替频率应该是随机的",
         "purpose": "验证比特交替的频率是否随机",
         "formula": "V_n = Σ|r(i)-r(i+1)| + 1,  P = erfc(|V_n - 2nπ(1-π)| / (2√(2n)·π(1-π)))",
         "formula_detail": "先通过频率预检验，统计游程总数V_n，与期望值2nπ(1-π)比较",
         "code_flow": [
             "输入: 比特序列 X[]，长度 n",
             "预检验: 计算 π = (1的个数)/n, 检查|π-0.5| < 2/√n",
             "计算游程数 V_n = 1 + Σ|X[i]-X[i+1]|",
             "计算期望 E = 2nπ(1-π)",
             "P-value = erfc(|V_n - E| / (2√(2n)π(1-π)))",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "预检验: 计算1的比例，检查是否在阈值内",
             "统计游程数(连续相同比特的段数)",
             "计算期望游程数",
             "正态近似计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "longest_run_of_ones", "name": "最长游程检测 (Longest Run of Ones)", "standard": "NIST SP 800-22",
         "desc": "检测每个子块中最长连续1的长度分布",
         "analogy": "连续出现很多次正面的硬币可能有问题",
         "purpose": "检测是否存在异常长的连续序列",
         "formula": "χ² = Σ(v_k - N·π_k)² / (N·π_k),  P = igamc(3/2, χ²/2)",
         "formula_detail": "将序列分块，统计每块最长游程，按长度分组后做χ²检验",
         "code_flow": [
             "输入: 比特序列 X[]，块大小 M",
             "分块: N = ⌊n/M⌋",
             "对每块计算最长连续1的长度 L",
             "按L值分组: v_k = 落入第k组的块数",
             "计算χ²统计量",
             "P-value = igamc(自由度/2, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "按M位分块",
             "统计每块中最长连续1的长度",
             "将最长游程按长度范围分组",
             "χ²检验各组频率",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "binary_matrix_rank", "name": "二元矩阵秩检测 (Binary Matrix Rank)", "standard": "NIST SP 800-22",
         "desc": "检测序列构成的二元矩阵的秩分布",
         "analogy": "把数字排成方阵，看行和列是否线性独立",
         "purpose": "检测序列中的线性依赖关系",
         "formula": "χ² = Σ(F_k - N·π_k)² / (N·π_k),  P = igamc(1, χ²/2)",
         "formula_detail": "将序列构造为M×Q矩阵，计算秩，统计满秩/缺1/缺2+的频率做χ²检验",
         "code_flow": [
             "输入: 比特序列 X[]，矩阵大小 M×Q=32×32",
             "构造 N = ⌊n/(M·Q)⌋ 个矩阵",
             "对每个矩阵计算GF(2)上的秩",
             "统计: F_32(满秩), F_31(缺1), F_30(缺2+)",
             "χ²检验: 与理论概率比较",
             "P-value = igamc(1, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "构造32×32二元矩阵",
             "高斯消元计算GF(2)上的秩",
             "统计满秩/缺秩矩阵数量",
             "χ²检验秩分布",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "dft_spectral", "name": "离散傅里叶变换检测 (DFT Spectral)", "standard": "NIST SP 800-22",
         "desc": "检测频谱中的周期性模式和峰值",
         "analogy": "听音乐时看频谱，随机信号应该没有明显的主旋律",
         "purpose": "检测序列中的周期性特征",
         "formula": "N peaks < T = √(n·ln(1/0.05)) 的峰数应符合正态分布",
         "formula_detail": "对序列做DFT，取模，统计超过阈值T的峰值数量，与期望值比较",
         "code_flow": [
             "输入: 比特序列 X[]，长度 n",
             "转换: 0→-1, 1→+1 得到 S[]",
             "DFT: T = FFT(S)",
             "取模: |T_i| = √(Re² + Im²)",
             "阈值: T = √(n·ln(1/0.05))",
             "统计: N_peaks = |T_i| < T 的个数",
             "P-value = erfc((N_peaks - 0.95n/2) / √(n·0.95·0.05/2))",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "转换为±1序列",
             "执行FFT变换",
             "计算频谱幅度",
             "统计低于阈值的峰值数",
             "正态近似计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "non_overlapping_template", "name": "非重叠模板匹配检测 (Non-overlapping Template)", "standard": "NIST SP 800-22",
         "desc": "检测特定m位模式的出现频率",
         "analogy": "在随机文本中找特定单词，出现次数应该符合预期",
         "purpose": "检测特定比特模式是否异常频繁",
         "formula": "χ² = Σ(W_j - (N-M+1)/2^M)² / ((N-M+1)/2^M),  P = igamc(1, χ²/2)",
         "formula_detail": "用滑动窗口在序列中匹配模板，统计匹配次数，与期望值比较做χ²检验",
         "code_flow": [
             "输入: 比特序列 X[]，模板 B (m位)",
             "滑动窗口匹配: 非重叠方式扫描",
             "统计: W = 匹配次数",
             "期望: μ = (n-m+1)/2^m",
             "χ² = (W - μ)² / μ",
             "P-value = igamc(1, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "选择模板(如000000001)",
             "非重叠滑动窗口匹配",
             "统计模板出现次数",
             "χ²检验与期望频率",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "overlapping_template", "name": "重叠模板匹配检测 (Overlapping Template)", "standard": "NIST SP 800-22",
         "desc": "检测重叠模式的出现频率",
         "analogy": "允许重叠地找模式，统计出现次数",
         "purpose": "更全面地检测模式匹配",
         "formula": "χ² = Σ(v_j - N·π_j)² / (N·π_j),  P = igamc(4/2, χ²/2)",
         "formula_detail": "用重叠窗口匹配模板，将匹配间隔分为若干组，做χ²检验",
         "code_flow": [
             "输入: 比特序列 X[]，模板 B (m位，通常111111111)",
             "重叠窗口扫描整个序列",
             "统计: v_j = 间隔落入第j组的次数",
             "分组: 0,1,2,3,4,≥5",
             "χ²检验各组频率",
             "P-value = igamc(4/2, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "选择模板(如111111111)",
             "重叠滑动窗口匹配",
             "记录连续匹配的间隔",
             "将间隔分组后χ²检验",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "maurers_universal", "name": "Maurer通用检测 (Maurer's Universal)", "standard": "NIST SP 800-22",
         "desc": "检测序列是否可以被无损压缩",
         "analogy": "真正随机的序列很难压缩，就像噪音无法简化",
         "purpose": "评估序列的信息熵",
         "formula": "f_n = (1/K)·Σlog₂(Q_j),  c = 0.7 - 0.8/L + (4+32/L)·K^(-1/3)/15,  P = erfc(|f_n-E|/(√2·c·σ))",
         "formula_detail": "将序列分段，用前段建立模板库，统计后段各块在模板库中首次出现的距离",
         "code_flow": [
             "输入: 比特序列 X[]，块大小 L=10",
             "初始化段: Q = 2^L 个模板(前n个块)",
             "测试段: K = ⌊n/L⌋ - Q 个块",
             "对每个测试块j: 记录与上次出现的距离Q_j",
             "f_n = (1/K)·Σlog₂(Q_j)",
             "标准化后计算P-value",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "选择块大小L",
             "前段: 建立模板出现位置表",
             "后段: 统计每个新块与上次出现的距离",
             "计算对数距离统计量",
             "标准化后计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "linear_complexity", "name": "线性复杂度检测 (Linear Complexity)", "standard": "NIST SP 800-22",
         "desc": "检测生成序列所需的最短线性反馈移位寄存器(LFSR)长度",
         "analogy": "用简单规则能生成的序列不够随机",
         "purpose": "检测序列是否可被简单算法预测",
         "formula": "χ² = Σ(T_j - μ)² / σ²,  P = igamc(6/2, χ²/2)",
         "formula_detail": "用Berlekamp-Massey算法计算每块的线性复杂度，与期望值n/2比较",
         "code_flow": [
             "输入: 比特序列 X[]，块大小 M=500",
             "分块: N = ⌊n/M⌋",
             "对每块用BM算法计算线性复杂度 L_i",
             "计算 T_i = (-1)^M · (L_i - M/2) + 2/9",
             "按T值分组统计",
             "χ²检验各组频率",
             "P-value = igamc(自由度/2, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "按M位分块",
             "对每块执行BM算法求线性复杂度",
             "计算与期望值的偏差T_i",
             "将T_i分组后χ²检验",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "serial", "name": "序列检测 (Serial Test)", "standard": "NIST SP 800-22",
         "desc": "检测所有m比特重叠模式的出现频率",
         "analogy": "掷两个骰子，每种组合出现次数应该差不多",
         "purpose": "检测所有比特模式的均匀性",
         "formula": "ψ²_m = (2^m/n)·Σ(v_i)² - n,  Δψ² = ψ²_m - ψ²_{m-1},  Δ²ψ² = ψ²_m - 2ψ²_{m-1} + ψ²_{m-2}",
         "formula_detail": "统计所有2^m种m位重叠模式的频率，构造ψ²统计量，取差值消除趋势",
         "code_flow": [
             "输入: 比特序列 X[]，模式长度 m",
             "扩展序列: X[n]=X[1], X[n+1]=X[2] (循环)",
             "统计所有2^m种m位模式的出现次数 v_i",
             "ψ²_m = (2^m/n)·Σv_i² - n",
             "计算 Δψ² = ψ²_m - ψ²_{m-1}",
             "计算 Δ²ψ² = ψ²_m - 2ψ²_{m-1} + ψ²_{m-2}",
             "P-value = igamc(自由度/2, Δ²ψ²/2)",
             "输出: 两个P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "扩展为循环序列",
             "统计所有m位重叠模式频率",
             "计算ψ²统计量",
             "取差值消除趋势",
             "χ²检验计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "approximate_entropy", "name": "近似熵检测 (Approximate Entropy)", "standard": "NIST SP 800-22",
         "desc": "检测序列的可预测性和规律性",
         "analogy": "随机序列越不可预测，熵值越高",
         "purpose": "评估序列的随机性和不可预测性",
         "formula": "ApEn(m) = φ_m - φ_{m+1},  φ_m = Σln(C_i^m),  χ² = 2n[ln2 - ApEn(m)]",
         "formula_detail": "统计m位和m+1位模式的频率，计算近似熵，与理论值ln2比较",
         "code_flow": [
             "输入: 比特序列 X[]，模式长度 m",
             "扩展: 循环扩展序列",
             "对k=m和k=m+1: 统计所有2^k种模式频率 C_i^k",
             "计算 φ_k = ΣC_i^k · ln(C_i^k)",
             "ApEn(m) = φ_m - φ_{m+1}",
             "χ² = 2n·[ln2 - ApEn(m)]",
             "P-value = igamc(2^{m-1}, χ²/2)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "循环扩展序列",
             "统计m位和m+1位模式频率",
             "计算各模式的对数频率",
             "计算近似熵ApEn",
             "χ²检验计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "cumulative_sums", "name": "累加和检测 (Cumulative Sums)", "standard": "NIST SP 800-22",
         "desc": "检测累加和的最大偏移是否异常",
         "analogy": "随机游走不应该总是朝一个方向走",
         "purpose": "检测序列中的偏差趋势",
         "formula": "Z = max|S_i|,  S_i = Σ(2x_j - 1),  P = 1 - Σ[Φ((4k±1)Z/√n) - Φ((4k-3)Z/√n)]",
         "formula_detail": "将序列转换为±1后累加，取正向和反向的最大偏移Z，通过正态分布计算P-value",
         "code_flow": [
             "输入: 比特序列 X[]，长度 n",
             "转换: S_i = 2x_i - 1 (0→-1, 1→+1)",
             "累加: S_k = Σ_{i=0}^{k} S_i (正向)",
             "Z = max|S_k|",
             "同样计算反向累加的Z'",
             "取 Z = max(Z, Z')",
             "P-value = 1 - Σ[Φ函数组合]",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "转换为±1序列",
             "正向累加求和",
             "反向累加求和",
             "取两个方向的最大偏移",
             "正态分布计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "random_excursions", "name": "随机游程检测 (Random Excursion)", "standard": "NIST SP 800-22",
         "desc": "检测随机游程访问各状态的次数分布",
         "analogy": "醉汉走路，每个方向被访问的次数应该均衡",
         "purpose": "检测随机游程的状态分布",
         "formula": "χ² = Σ(x_k - J·π_k)² / (J·π_k),  P = igamc(5/2, χ²/2)",
         "formula_detail": "构造±1累加游程，统计循环中各状态(-4到+4)的访问次数，做χ²检验",
         "code_flow": [
             "输入: 比特序列 X[]",
             "转换: S_i = 2x_i - 1",
             "累加: S_k = ΣS_i, 附加 S_n+1=0, S_0=0",
             "统计循环数 J",
             "对每个循环: 统计访问状态-4,-3,...,3,4的次数 x_k",
             "χ²检验各状态访问频率",
             "P-value = igamc(5/2, χ²/2)",
             "输出: 对每个状态一个P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "转换为±1序列并累加",
             "识别循环(从0出发回到0)",
             "统计每个循环中各状态的访问次数",
             "对各状态分别χ²检验",
             "判断: 所有状态P ≥ 0.01 则通过"
         ]},
        {"id": "random_excursions_variant", "name": "随机游程变体检测 (Random Excursion Variant)", "standard": "NIST SP 800-22",
         "desc": "检测特定状态的访问次数是否异常",
         "analogy": "醉汉是否在某个地方停留太久",
         "purpose": "检测特定状态的异常访问",
         "formula": "P = erfc(|J_x - J| / √(2·J·(4|x|-2))),  J_x = 访问状态x的循环数",
         "formula_detail": "统计访问特定状态(如-9到-1, 1到9)的循环数，与总循环数比较",
         "code_flow": [
             "输入: 比特序列 X[]",
             "转换: S_i = 2x_i - 1",
             "累加: S_k = ΣS_i, 附加 S_n+1=0",
             "统计总循环数 J",
             "对每个状态 x ∈ {-9,...,-1,1,...,9}:",
             "  J_x = 访问过状态x的循环数",
             "  P_x = erfc(|J_x - J| / √(2J(4|x|-2)))",
             "输出: 18个P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "转换为±1序列并累加",
             "识别循环",
             "对18个特定状态分别统计",
             "正态近似计算各状态P-value",
             "判断: 所有状态P ≥ 0.01 则通过"
         ]},
    ]

    gbt_tests = [
        {"id": "poker_test", "name": "扑克检测 (Poker Test)", "standard": "GB/T 32915-2016",
         "desc": "检测m比特分组的出现频率是否均匀",
         "analogy": "扑克牌的每种花色出现次数应该均衡",
         "purpose": "检测比特分组的均匀性",
         "formula": "χ² = (2^m/N)·Σn_i² - N,  P = 1 - χ²cdf(χ², 2^m-1)",
         "formula_detail": "将序列分为m位一组，统计2^m种取值的出现频率，构造χ²统计量",
         "code_flow": [
             "输入: 比特序列 X[]，分组长度 m=4 或 8",
             "分组: N = ⌊n/m⌋ 组",
             "统计每种m位取值的出现次数 n_i",
             "χ² = (2^m/N)·Σn_i² - N",
             "P-value = 1 - χ²cdf(χ², 2^m-1)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "按m位分组(m=4或8)",
             "统计各组取值出现次数",
             "计算χ²统计量",
             "卡方分布计算P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "autocorrelation_test", "name": "自相关检测 (Autocorrelation Test)", "standard": "GB/T 32915-2016",
         "desc": "检测序列与自身移位后的相关性",
         "analogy": "把数字序列错开几位再比较，应该看不出规律",
         "purpose": "检测序列的自相关特性",
         "formula": "A(d) = Σ(X_i ⊕ X_{i+d}),  z = (A(d) - (n-d)/2) / √((n-d)/4),  P = 2·(1-Φ(|z|))",
         "formula_detail": "对多个位移量d，计算XOR后0的个数，与期望值(n-d)/2比较，取最小P-value",
         "code_flow": [
             "输入: 比特序列 X[]，最大位移 d_max=100",
             "对每个 d = 1, 2, ..., d_max:",
             "  A(d) = Σ(X_i ⊕ X_{i+d})",
             "  零计数 = n - d - A(d)",
             "  z = (零计数 - (n-d)/2) / √((n-d)/4)",
             "  P_d = 2·(1-Φ(|z|))",
             "P-value = min(P_1, P_2, ..., P_d_max)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "对多个位移量d执行:",
             "  序列与移位版本逐位XOR",
             "  统计异或结果中0的个数",
             "  计算z统计量和P-value",
             "取所有位移中最小的P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
        {"id": "binary_derivative_test", "name": "二元推导检测 (Binary Derivative)", "standard": "GB/T 32915-2016",
         "desc": "检测相邻比特异或后的随机性",
         "analogy": "把相邻两个数做异或，结果也应该随机",
         "purpose": "检测序列的推导随机性",
         "formula": "D_i = X_i ⊕ X_{i+1},  z = (ones - n/2) / √(n/4),  P = 2·(1-Φ(|z|))",
         "formula_detail": "对序列逐级差分(相邻异或)，检查各级推导序列中0/1比例，取最小P-value",
         "code_flow": [
             "输入: 比特序列 X[]，最大级数=10",
             "current = X[]",
             "对每级 level = 0, 1, ..., 9:",
             "  统计 current 中1的个数 ones",
             "  n = len(current)",
             "  z = (ones - n/2) / √(n/4)",
             "  P_level = 2·(1-Φ(|z|))",
             "  current = 相邻异或(current)",
             "P-value = min(P_0, ..., P_9)",
             "输出: P-value"
         ],
         "test_flow": [
             "读取待测比特序列",
             "对每一级执行:",
             "  统计当前序列的0/1比例",
             "  计算z统计量和P-value",
             "  相邻比特异或生成新序列",
             "取所有级中最小的P-value",
             "判断: P ≥ 0.01 则通过"
         ]},
    ]

    return {"nist": nist_tests, "gbt": gbt_tests}


def run_test_task(task_id, filepath, alpha, selected_tests):
    """后台运行测试任务，逐项执行并报告进度"""
    try:
        tasks[task_id]['status'] = 'running'
        tasks[task_id]['progress'] = 0
        tasks[task_id]['message'] = '正在加载数据...'

        loader = DataLoader()
        bits = loader.load_from_file(filepath)
        info = loader.get_sequence_info(bits)

        # 验证
        valid, msg = loader.validate_sequence(bits, min_length=1000)
        if not valid:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['message'] = msg
            tasks[task_id]['progress'] = 100
            return

        # 分割序列
        segments = loader.split_sequence(bits, segment_length=1000000)
        total_segments = len(segments)

        tasks[task_id]['progress'] = 5
        tasks[task_id]['message'] = f'数据已加载: {info["length"]:,} 比特, {total_segments} 个测试片段'

        # 确定要执行的测试
        nist_to_run = [t for t in selected_tests if t in ALL_NIST_IDS]
        gbt_to_run = [t for t in selected_tests if t in ALL_GBT_IDS]
        total_tests = len(nist_to_run) + len(gbt_to_run)

        if total_tests == 0:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['message'] = '未选择任何测试项'
            tasks[task_id]['progress'] = 100
            return

        # 初始化测试套件
        nist_suite = NISTTestSuiteNistrng(significance_level=alpha)
        gbt_suite = GBTTestSuite(significance_level=alpha)

        # 逐段逐项执行测试
        nist_all_results = {t: [] for t in nist_to_run}
        gbt_all_results = {t: [] for t in gbt_to_run}

        completed_tests = 0
        base_progress = 5
        test_progress_range = 85  # 5% ~ 90%

        for seg_idx, segment in enumerate(segments):
            seg_progress = base_progress + (seg_idx / total_segments) * test_progress_range

            # 执行NIST测试（逐项）
            for test_name in nist_to_run:
                try:
                    tasks[task_id]['message'] = f'片段 {seg_idx+1}/{total_segments}: 正在执行 {test_name}...'
                    tasks[task_id]['progress'] = int(seg_progress)

                    # 使用nistrng逐项执行
                    import nistrng
                    import numpy as np
                    bits_np = np.array(segment, dtype=np.int8)
                    packed = nistrng.pack_sequence(bits_np)

                    nist_test_obj = get_nistrng_test_by_name(test_name)
                    if nist_test_obj:
                        results = nistrng.run_by_name_battery(
                            nist_test_obj.name, packed,
                            nistrng.SP800_22R1A_BATTERY,
                            check_eligibility=True
                        )
                        if results and results[0] is not None:
                            result, extra = results
                            p_value = result.score
                        else:
                            p_value = 0.0
                    else:
                        p_value = 0.0

                    nist_all_results[test_name].append(p_value)
                except Exception as e:
                    nist_all_results[test_name].append(0.0)
                    print(f"NIST测试 {test_name} 错误: {e}")

            # 执行GB/T测试（逐项）
            for test_name in gbt_to_run:
                try:
                    tasks[task_id]['message'] = f'片段 {seg_idx+1}/{total_segments}: 正在执行 {test_name}...'
                    tasks[task_id]['progress'] = int(seg_progress)

                    import numpy as np
                    bits_np = np.array(segment, dtype=np.int8)

                    if test_name == 'poker_test_m4':
                        p_value = gbt_suite.poker_test(bits_np, m=4)
                    elif test_name == 'poker_test_m8':
                        p_value = gbt_suite.poker_test(bits_np, m=8)
                    elif test_name == 'autocorrelation_test':
                        p_value = gbt_suite.autocorrelation_test(bits_np)
                    elif test_name == 'binary_derivative_test':
                        p_value = gbt_suite.binary_derivative_test(bits_np)
                    else:
                        p_value = 0.0

                    gbt_all_results[test_name].append(p_value)
                except Exception as e:
                    gbt_all_results[test_name].append(0.0)
                    print(f"GB/T测试 {test_name} 错误: {e}")

        # 计算通过率
        tasks[task_id]['progress'] = 90
        tasks[task_id]['message'] = '正在计算通过率...'

        nist_pass_rates = {}
        for test_name, p_values in nist_all_results.items():
            if p_values:
                nist_pass_rates[test_name] = calculate_pass_rate(p_values, alpha)

        gbt_pass_rates = {}
        for test_name, p_values in gbt_all_results.items():
            if p_values:
                gbt_pass_rates[test_name] = calculate_pass_rate(p_values, alpha)

        nist_overall = sum(nist_pass_rates.values()) / len(nist_pass_rates) if nist_pass_rates else 0
        gbt_overall = sum(gbt_pass_rates.values()) / len(gbt_pass_rates) if gbt_pass_rates else 0

        total_weight = len(nist_pass_rates) + len(gbt_pass_rates)
        if total_weight > 0:
            overall = (nist_overall * len(nist_pass_rates) + gbt_overall * len(gbt_pass_rates)) / total_weight
        else:
            overall = 0

        result = {
            'file': os.path.basename(filepath),
            'file_count': 1,
            'total_bits': info['length'],
            'segment_count': total_segments,
            'significance_level': alpha,
            'nist_results': nist_pass_rates,
            'gbt_results': gbt_pass_rates,
            'nist_pass_rate': nist_overall,
            'gbt_pass_rate': gbt_overall,
            'overall_pass_rate': overall
        }

        # 生成报告
        tasks[task_id]['progress'] = 95
        tasks[task_id]['message'] = '正在生成报告...'

        report_dir = os.path.join(app.config['REPORT_FOLDER'], task_id)
        os.makedirs(report_dir, exist_ok=True)
        report_gen = ReportGenerator(report_dir)

        text_path = report_gen.generate_text_report(result)
        html_path = report_gen.generate_html_report(result)
        json_path = report_gen.generate_json_report(result)

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        tasks[task_id]['result'] = result
        tasks[task_id]['html_report'] = html_content
        tasks[task_id]['report_files'] = {
            'text': os.path.basename(text_path),
            'html': os.path.basename(html_path),
            'json': os.path.basename(json_path)
        }
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['progress'] = 100
        tasks[task_id]['message'] = '测试完成'
        tasks[task_id]['completed_at'] = datetime.now().isoformat()

        history_entry = {
            'task_id': task_id,
            'file': os.path.basename(filepath),
            'completed_at': tasks[task_id]['completed_at'],
            'overall_pass_rate': overall,
            'nist_pass_rate': nist_overall,
            'gbt_pass_rate': gbt_overall,
            'total_bits': info['length'],
            'status': 'pass' if overall >= 0.98 else 'fail'
        }
        history.insert(0, history_entry)

    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['message'] = f'{str(e)}\n{traceback.format_exc()}'
        tasks[task_id]['progress'] = 100


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    loader = DataLoader()
    try:
        bits = loader.load_from_file(filepath)
        info = loader.get_sequence_info(bits)
        valid, msg = loader.validate_sequence(bits, min_length=1000)

        return jsonify({
            'success': True,
            'filepath': filepath,
            'filename': file.filename,
            'info': info,
            'valid': valid,
            'message': msg
        })
    except Exception as e:
        return jsonify({'error': f'文件加载失败: {str(e)}'}), 400


@app.route('/api/test/run', methods=['POST'])
def run_test():
    data = request.json
    filepath = data.get('filepath')
    alpha = data.get('alpha', 0.01)
    selected_tests = data.get('selected_tests', ALL_NIST_IDS + ALL_GBT_IDS)

    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 400

    task_id = uuid.uuid4().hex[:12]
    tasks[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'progress': 0,
        'message': '等待开始...',
        'created_at': datetime.now().isoformat(),
        'filepath': filepath,
        'alpha': alpha
    }

    thread = threading.Thread(target=run_test_task, args=(task_id, filepath, alpha, selected_tests))
    thread.daemon = True
    thread.start()

    return jsonify({'task_id': task_id})


@app.route('/api/test/status/<task_id>')
def test_status(task_id):
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404

    task = tasks[task_id]
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message']
    })


@app.route('/api/test/result/<task_id>')
def test_result(task_id):
    if task_id not in tasks:
        return jsonify({'error': '任务不存在'}), 404

    task = tasks[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': '测试未完成'}), 400

    return jsonify({
        'task_id': task_id,
        'result': task.get('result'),
        'html_report': task.get('html_report'),
        'report_files': task.get('report_files'),
        'completed_at': task.get('completed_at')
    })


@app.route('/api/report/<task_id>/<filename>')
def download_report(task_id, filename):
    report_dir = os.path.join(app.config['REPORT_FOLDER'], task_id)
    if not os.path.exists(os.path.join(report_dir, filename)):
        return jsonify({'error': '报告不存在'}), 404
    return send_from_directory(report_dir, filename, as_attachment=True)


@app.route('/api/history')
def get_history():
    return jsonify(history)


@app.route('/api/tests/info')
def tests_info():
    return jsonify(get_test_info())


@app.route('/api/source/files')
def source_files():
    return jsonify(get_source_files())


@app.route('/api/source/content')
def source_content():
    rel_path = request.args.get('path', '')
    if not rel_path:
        return jsonify({'error': '未指定文件路径'}), 400

    base = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.normpath(os.path.join(base, rel_path))

    if not full_path.startswith(os.path.normpath(base)):
        return jsonify({'error': '非法路径'}), 403

    if not os.path.exists(full_path):
        return jsonify({'error': '文件不存在'}), 404

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'path': rel_path,
            'content': content,
            'size': os.path.getsize(full_path)
        })
    except UnicodeDecodeError:
        return jsonify({'error': '文件无法以文本方式读取'}), 400


if __name__ == '__main__':
    print("=" * 60)
    print("CIS芯片TRNG随机性测试平台 - Web版")
    print("=" * 60)
    print("启动地址: http://localhost:5001")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5001, debug=False)
