"""
数据加载器单元测试
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import DataLoader


class TestDataLoader:
    """数据加载器测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.loader = DataLoader()

    def test_load_bin_file(self, sample_bin_file):
        """应能加载.bin文件"""
        bits = self.loader.load_from_file(sample_bin_file)

        assert isinstance(bits, list)
        assert len(bits) > 0
        assert all(b in [0, 1] for b in bits)

    def test_load_txt_file(self, sample_txt_file):
        """应能加载.txt文件"""
        bits = self.loader.load_from_file(sample_txt_file)

        assert isinstance(bits, list)
        assert len(bits) > 0
        assert all(b in [0, 1] for b in bits)

    def test_load_nonexistent_file(self, temp_dir):
        """加载不存在的文件应抛出异常"""
        filepath = os.path.join(temp_dir, 'nonexistent.bin')

        with pytest.raises(FileNotFoundError):
            self.loader.load_from_file(filepath)

    def test_validate_valid_sequence(self, random_bits):
        """有效序列应通过验证"""
        valid, msg = self.loader.validate_sequence(random_bits, min_length=1000)

        assert valid is True
        assert msg == "序列有效"

    def test_validate_short_sequence(self):
        """短序列应验证失败"""
        short_bits = [0, 1, 0] * 10
        valid, msg = self.loader.validate_sequence(short_bits, min_length=1000)

        assert valid is False
        assert "长度不足" in msg

    def test_validate_empty_sequence(self):
        """空序列应验证失败"""
        valid, msg = self.loader.validate_sequence([])

        assert valid is False
        assert "为空" in msg

    def test_validate_non_binary_sequence(self):
        """非二进制序列应验证失败"""
        invalid_bits = [0, 1, 2, 3] * 100000  # 足够长以通过长度检查
        valid, msg = self.loader.validate_sequence(invalid_bits, min_length=1000)

        assert valid is False
        assert "非二进制" in msg

    def test_get_sequence_info(self, random_bits):
        """应能获取序列信息"""
        info = self.loader.get_sequence_info(random_bits)

        assert 'length' in info
        assert 'ones_count' in info
        assert 'zeros_count' in info
        assert 'ones_ratio' in info

        assert info['length'] == len(random_bits)
        assert info['ones_count'] + info['zeros_count'] == len(random_bits)
        assert 0 <= info['ones_ratio'] <= 1

    def test_get_sequence_info_empty(self):
        """空序列应返回零值信息"""
        info = self.loader.get_sequence_info([])

        assert info['length'] == 0
        assert info['ones_count'] == 0
        assert info['zeros_count'] == 0
        assert info['ones_ratio'] == 0.0

    def test_split_sequence(self, random_bits):
        """应能正确分割序列"""
        segments = self.loader.split_sequence(random_bits, segment_length=10000)

        assert len(segments) > 1
        assert all(len(seg) >= 100 for seg in segments)

        # 验证分割后的总长度
        total_length = sum(len(seg) for seg in segments)
        assert total_length == len(random_bits)

    def test_convert_to_numpy(self, random_bits):
        """应能转换为numpy数组"""
        array = self.loader.convert_to_numpy(random_bits)

        assert isinstance(array, np.ndarray)
        assert array.dtype == np.int8
        assert len(array) == len(random_bits)

    def test_convert_from_numpy(self):
        """应能从numpy数组转换"""
        array = np.array([0, 1, 0, 1], dtype=np.int8)
        bits = self.loader.convert_from_numpy(array)

        assert isinstance(bits, list)
        assert bits == [0, 1, 0, 1]

    def test_supported_extensions(self):
        """应支持.bin/.txt/.dat/.raw格式"""
        assert '.bin' in self.loader.supported_extensions
        assert '.txt' in self.loader.supported_extensions
        assert '.dat' in self.loader.supported_extensions
        assert '.raw' in self.loader.supported_extensions

    def test_load_from_directory(self, sample_data_dir):
        """应能从目录加载多个文件"""
        results = self.loader.load_from_directory(sample_data_dir)

        assert len(results) == 3
        assert all(isinstance(name, str) for name, _ in results)
        assert all(isinstance(bits, list) for _, bits in results)
