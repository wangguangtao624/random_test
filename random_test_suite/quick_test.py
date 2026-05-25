#!/usr/bin/env python3
"""
快速测试脚本
用于快速验证工具功能
"""

import os
import sys
import random

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nist_tests import NISTTestSuite
from core.gbt_tests import GBTTestSuite
from utils.data_loader import DataLoader


def generate_test_data(length=100000):
    """生成测试数据"""
    print(f"生成 {length:,} 比特的测试数据...")
    return [random.randint(0, 1) for _ in range(length)]


def save_test_data(bits, filepath):
    """保存测试数据"""
    # 将比特打包为字节
    bytes_data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
            else:
                byte = byte << 1
        bytes_data.append(byte)

    with open(filepath, 'wb') as f:
        f.write(bytes_data)

    print(f"测试数据已保存到: {filepath}")


def run_quick_test():
    """运行快速测试"""
    print("=" * 60)
    print("CIS芯片TRNG随机性测试套件 - 快速测试")
    print("=" * 60)
    print()

    # 生成测试数据
    test_bits = generate_test_data(100000)

    # 创建测试数据目录
    test_dir = './test_data'
    os.makedirs(test_dir, exist_ok=True)

    # 保存测试数据
    test_file = os.path.join(test_dir, 'quick_test.bin')
    save_test_data(test_bits, test_file)

    # 创建数据加载器
    loader = DataLoader()

    # 加载数据
    print("\n加载测试数据...")
    loaded_bits = loader.load_from_file(test_file)

    # 验证数据
    valid, msg = loader.validate_sequence(loaded_bits, min_length=1000)
    print(f"数据验证: {'通过' if valid else '失败'} - {msg}")

    # 获取数据信息
    info = loader.get_sequence_info(loaded_bits)
    print(f"数据信息:")
    print(f"  长度: {info['length']:,} 比特")
    print(f"  1的个数: {info['ones_count']:,}")
    print(f"  0的个数: {info['zeros_count']:,}")
    print(f"  1的比例: {info['ones_ratio']:.4f}")

    # 运行NIST测试
    print("\n" + "-" * 60)
    print("运行 NIST SP 800-22 测试...")
    print("-" * 60)

    nist_suite = NISTTestSuite()
    try:
        nist_results = nist_suite.run_all_tests(loaded_bits)

        print("\nNIST测试结果:")
        print("-" * 60)
        nist_pass_count = 0
        for test_name, p_value in nist_results.items():
            status = "PASS" if p_value >= 0.01 else "FAIL"
            if status == "PASS":
                nist_pass_count += 1
            print(f"  {test_name:<40} P-value: {p_value:.6f} [{status}]")

        print("-" * 60)
        print(f"NIST测试通过率: {nist_pass_count}/{len(nist_results)}")

    except Exception as e:
        print(f"NIST测试错误: {e}")

    # 运行GB/T测试
    print("\n" + "-" * 60)
    print("运行 GB/T 32915-2016 补充测试...")
    print("-" * 60)

    gbt_suite = GBTTestSuite()
    try:
        gbt_results = gbt_suite.run_all_tests(loaded_bits)

        print("\nGB/T测试结果:")
        print("-" * 60)
        gbt_pass_count = 0
        for test_name, p_value in gbt_results.items():
            status = "PASS" if p_value >= 0.01 else "FAIL"
            if status == "PASS":
                gbt_pass_count += 1
            print(f"  {test_name:<40} P-value: {p_value:.6f} [{status}]")

        print("-" * 60)
        print(f"GB/T测试通过率: {gbt_pass_count}/{len(gbt_results)}")

    except Exception as e:
        print(f"GB/T测试错误: {e}")

    # 清理测试文件
    try:
        os.remove(test_file)
        os.rmdir(test_dir)
        print(f"\n已清理测试文件")
    except:
        pass

    # 总结
    print("\n" + "=" * 60)
    print("快速测试完成!")
    print("=" * 60)
    print("\n下一步:")
    print("1. 将CIS芯片的TRNG输出数据放入 data 目录")
    print("2. 运行完整测试: python main.py --data-dir ./data")
    print("3. 查看 reports 目录下的测试报告")
    print()


if __name__ == '__main__':
    run_quick_test()
