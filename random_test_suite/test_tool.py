#!/usr/bin/env python3
"""
测试工具验证脚本
验证测试套件的功能是否正常
"""

import os
import sys
import numpy as np

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nist_tests import NISTTestSuite
from core.gbt_tests import GBTTestSuite
from utils.data_loader import DataLoader


def test_nist_suite():
    """测试NIST测试套件"""
    print("=" * 60)
    print("测试 NIST SP 800-22 测试套件")
    print("=" * 60)

    suite = NISTTestSuite()

    # 生成测试序列
    np.random.seed(42)
    test_sequence = np.random.randint(0, 2, 10000).tolist()

    print(f"测试序列长度: {len(test_sequence)}")
    print()

    # 运行所有测试
    try:
        results = suite.run_all_tests(test_sequence)

        print("测试结果:")
        print("-" * 60)
        for test_name, p_value in results.items():
            status = "PASS" if p_value >= 0.01 else "FAIL"
            print(f"  {test_name:<40} P-value: {p_value:.6f} [{status}]")

        print("-" * 60)
        print("NIST测试套件验证完成!")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False


def test_gbt_suite():
    """测试GB/T测试套件"""
    print("\n" + "=" * 60)
    print("测试 GB/T 32915-2016 补充测试套件")
    print("=" * 60)

    suite = GBTTestSuite()

    # 生成测试序列
    np.random.seed(42)
    test_sequence = np.random.randint(0, 2, 10000).tolist()

    print(f"测试序列长度: {len(test_sequence)}")
    print()

    # 运行所有测试
    try:
        results = suite.run_all_tests(test_sequence)

        print("测试结果:")
        print("-" * 60)
        for test_name, p_value in results.items():
            status = "PASS" if p_value >= 0.01 else "FAIL"
            print(f"  {test_name:<40} P-value: {p_value:.6f} [{status}]")

        print("-" * 60)
        print("GB/T测试套件验证完成!")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False


def test_data_loader():
    """测试数据加载器"""
    print("\n" + "=" * 60)
    print("测试数据加载器")
    print("=" * 60)

    loader = DataLoader()

    # 创建测试数据目录
    test_dir = './test_data'
    os.makedirs(test_dir, exist_ok=True)

    # 生成测试文件
    np.random.seed(42)
    test_bits = np.random.randint(0, 2, 1000).tolist()

    # 测试二进制文件
    bin_path = os.path.join(test_dir, 'test.bin')
    bytes_data = bytearray()
    for i in range(0, len(test_bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(test_bits):
                byte = (byte << 1) | test_bits[i + j]
            else:
                byte = byte << 1
        bytes_data.append(byte)

    with open(bin_path, 'wb') as f:
        f.write(bytes_data)

    # 测试加载
    try:
        loaded_bits = loader.load_from_file(bin_path)
        print(f"二进制文件加载测试: {'通过' if len(loaded_bits) > 0 else '失败'}")

        # 测试序列信息
        info = loader.get_sequence_info(loaded_bits)
        print(f"序列信息: 长度={info['length']}, 1的比例={info['ones_ratio']:.4f}")

        # 测试验证
        valid, msg = loader.validate_sequence(loaded_bits, min_length=100)
        print(f"序列验证: {'通过' if valid else '失败'} - {msg}")

        print("数据加载器验证完成!")
        return True

    except Exception as e:
        print(f"错误: {e}")
        return False

    finally:
        # 清理测试文件
        if os.path.exists(bin_path):
            os.remove(bin_path)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)


def main():
    """运行所有测试"""
    print("CIS芯片TRNG随机性测试套件 - 功能验证")
    print("=" * 60)
    print()

    results = []

    # 测试NIST套件
    results.append(("NIST测试套件", test_nist_suite()))

    # 测试GB/T套件
    results.append(("GB/T测试套件", test_gbt_suite()))

    # 测试数据加载器
    results.append(("数据加载器", test_data_loader()))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "通过" if passed else "失败"
        print(f"  {name:<20} {status}")
        if not passed:
            all_passed = False

    print("-" * 60)
    if all_passed:
        print("所有测试通过! 工具可以正常使用。")
    else:
        print("部分测试失败，请检查错误信息。")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
