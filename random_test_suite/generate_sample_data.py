#!/usr/bin/env python3
"""
生成示例测试数据
用于验证测试套件的功能
"""

import os
import random
import argparse
from typing import List


def generate_random_bits(length: int, bias: float = 0.5) -> List[int]:
    """
    生成随机比特序列

    Args:
        length: 序列长度
        bias: 1的概率 (0.5为无偏)

    Returns:
        List[int]: 比特序列
    """
    return [1 if random.random() < bias else 0 for _ in range(length)]


def generate_truly_random_sequence(length: int) -> List[int]:
    """
    生成高质量随机序列（模拟良好TRNG）

    Args:
        length: 序列长度

    Returns:
        List[int]: 比特序列
    """
    # 使用系统随机源
    return [random.SystemRandom().randint(0, 1) for _ in range(length)]


def generate_biased_sequence(length: int, bias: float = 0.6) -> List[int]:
    """
    生成有偏序列（用于测试失败情况）

    Args:
        length: 序列长度
        bias: 1的概率

    Returns:
        List[int]: 比特序列
    """
    return [1 if random.random() < bias else 0 for _ in range(length)]


def generate_periodic_sequence(length: int, period: int = 100) -> List[int]:
    """
    生成周期性序列（用于测试失败情况）

    Args:
        length: 序列长度
        period: 周期长度

    Returns:
        List[int]: 比特序列
    """
    pattern = [random.randint(0, 1) for _ in range(period)]
    sequence = []
    for i in range(length):
        sequence.append(pattern[i % period])
    return sequence


def save_binary_file(bits: List[int], filepath: str):
    """保存为二进制文件"""
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


def save_text_file(bits: List[int], filepath: str):
    """保存为文本文件"""
    with open(filepath, 'w') as f:
        # 每行100个比特
        for i in range(0, len(bits), 100):
            line = ''.join(str(b) for b in bits[i:i+100])
            f.write(line + '\n')


def main():
    parser = argparse.ArgumentParser(description='生成示例测试数据')
    parser.add_argument('--output', '-o', default='./data', help='输出目录')
    parser.add_argument('--count', '-n', type=int, default=10, help='生成文件数量')
    parser.add_argument('--length', '-l', type=int, default=1000000, help='每个文件的比特长度')
    parser.add_argument('--type', choices=['random', 'biased', 'periodic', 'mixed'],
                       default='mixed', help='数据类型')
    parser.add_argument('--format', choices=['bin', 'txt', 'both'], default='both',
                       help='文件格式')

    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    print(f"生成 {args.count} 个测试文件...")
    print(f"每个文件长度: {args.length:,} 比特")
    print(f"数据类型: {args.type}")
    print(f"输出目录: {args.output}")
    print()

    for i in range(args.count):
        # 根据类型生成数据
        if args.type == 'random':
            bits = generate_truly_random_sequence(args.length)
        elif args.type == 'biased':
            bits = generate_biased_sequence(args.length, bias=0.6)
        elif args.type == 'periodic':
            bits = generate_periodic_sequence(args.length, period=100)
        else:  # mixed
            if i < args.count * 0.7:  # 70%随机
                bits = generate_truly_random_sequence(args.length)
            elif i < args.count * 0.85:  # 15%有偏
                bits = generate_biased_sequence(args.length, bias=0.6)
            else:  # 15%周期
                bits = generate_periodic_sequence(args.length, period=100)

        # 保存文件
        if args.format in ['bin', 'both']:
            bin_path = os.path.join(args.output, f'sample_{i+1:04d}.bin')
            save_binary_file(bits, bin_path)

        if args.format in ['txt', 'both']:
            txt_path = os.path.join(args.output, f'sample_{i+1:04d}.txt')
            save_text_file(bits, txt_path)

        print(f"  生成文件 {i+1}/{args.count}", end='\r')

    print(f"\n完成！已生成 {args.count} 个文件到 {args.output}")


if __name__ == '__main__':
    main()
