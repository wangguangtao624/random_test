"""
Pytest配置文件
提供测试fixtures和通用工具
"""

import os
import sys
import tempfile
import random
import pytest
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def random_bits():
    """生成100,000位真随机序列"""
    return [random.SystemRandom().randint(0, 1) for _ in range(100000)]


@pytest.fixture
def random_bits_large():
    """生成1,000,000位真随机序列"""
    return [random.SystemRandom().randint(0, 1) for _ in range(1000000)]


@pytest.fixture
def all_zeros():
    """全0序列"""
    return [0] * 100000


@pytest.fixture
def all_ones():
    """全1序列"""
    return [1] * 100000


@pytest.fixture
def alternating_bits():
    """交替序列 010101..."""
    return [i % 2 for i in range(100000)]


@pytest.fixture
def biased_bits():
    """有偏序列 (60% 为 1)"""
    return [1 if random.random() < 0.6 else 0 for _ in range(100000)]


@pytest.fixture
def periodic_bits():
    """周期序列 (周期=100)"""
    pattern = [random.randint(0, 1) for _ in range(100)]
    return [pattern[i % 100] for i in range(100000)]


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_bin_file(temp_dir, random_bits_large):
    """创建临时.bin测试文件（1M比特）"""
    filepath = os.path.join(temp_dir, 'test.bin')

    # 将比特打包为字节
    bytes_data = bytearray()
    for i in range(0, len(random_bits_large), 8):
        byte = 0
        for j in range(8):
            if i + j < len(random_bits_large):
                byte = (byte << 1) | random_bits_large[i + j]
            else:
                byte = byte << 1
        bytes_data.append(byte)

    with open(filepath, 'wb') as f:
        f.write(bytes_data)

    return filepath


@pytest.fixture
def sample_txt_file(temp_dir, random_bits_large):
    """创建临时.txt测试文件（1M比特）"""
    filepath = os.path.join(temp_dir, 'test.txt')

    with open(filepath, 'w') as f:
        for i in range(0, len(random_bits_large), 100):
            line = ''.join(str(b) for b in random_bits_large[i:i+100])
            f.write(line + '\n')

    return filepath


@pytest.fixture
def sample_data_dir(temp_dir):
    """创建包含多个测试文件的目录"""
    data_dir = os.path.join(temp_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    # 生成3个测试文件，每个1M比特
    for idx in range(3):
        bits = [random.SystemRandom().randint(0, 1) for _ in range(1000000)]
        filepath = os.path.join(data_dir, f'sample_{idx+1}.bin')

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

    return data_dir


@pytest.fixture
def output_dir(temp_dir):
    """创建输出目录"""
    out_dir = os.path.join(temp_dir, 'reports')
    os.makedirs(out_dir, exist_ok=True)
    return out_dir
