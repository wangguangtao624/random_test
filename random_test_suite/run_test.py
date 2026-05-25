#!/usr/bin/env python3
"""
直接运行测试 - 简单版本
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nist_tests import NISTTestSuite
from core.gbt_tests import GBTTestSuite
from utils.data_loader import DataLoader


def main():
    # 测试文件路径
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    filepath = os.path.join(desktop, 'CIS_TRNG测试数据.bin')

    # 检查文件是否存在
    if not os.path.exists(filepath):
        print(f"错误: 找不到测试文件 {filepath}")
        return

    print("=" * 60)
    print("CIS芯片TRNG随机性测试")
    print("=" * 60)
    print(f"测试文件: {filepath}")
    print()

    # 加载数据
    loader = DataLoader()
    bits = loader.load_from_file(filepath)
    info = loader.get_sequence_info(bits)

    print(f"序列长度: {info['length']:,} 比特")
    print(f"1的比例: {info['ones_ratio']:.4f}")
    print()

    # 运行NIST测试
    print("运行 NIST SP 800-22 测试...")
    print("-" * 60)

    nist_suite = NISTTestSuite()
    nist_results = nist_suite.run_all_tests(bits)

    nist_pass = 0
    for name, p_value in nist_results.items():
        status = "PASS" if p_value >= 0.01 else "FAIL"
        if status == "PASS":
            nist_pass += 1
        print(f"{name:<35} P-value: {p_value:.6f} [{status}]")

    print("-" * 60)
    print(f"NIST通过率: {nist_pass}/{len(nist_results)}")
    print()

    # 运行GB/T测试
    print("运行 GB/T 32915-2016 补充测试...")
    print("-" * 60)

    gbt_suite = GBTTestSuite()
    gbt_results = gbt_suite.run_all_tests(bits)

    gbt_pass = 0
    for name, p_value in gbt_results.items():
        status = "PASS" if p_value >= 0.01 else "FAIL"
        if status == "PASS":
            gbt_pass += 1
        print(f"{name:<35} P-value: {p_value:.6f} [{status}]")

    print("-" * 60)
    print(f"GB/T通过率: {gbt_pass}/{len(gbt_results)}")
    print()

    # 总结
    total_pass = nist_pass + gbt_pass
    total_tests = len(nist_results) + len(gbt_results)
    print("=" * 60)
    print(f"总体通过率: {total_pass}/{total_tests} = {total_pass/total_tests*100:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
    input("\n按回车键退出...")
