"""
数据加载器
支持多种数据格式的加载和预处理
"""

import os
import struct
import numpy as np
from typing import List, Tuple, Optional, Generator
import glob


class DataLoader:
    """数据加载器"""

    def __init__(self):
        self.supported_extensions = ['.bin', '.txt', '.dat', '.raw']

    def load_from_file(self, filepath: str) -> List[int]:
        """
        从文件加载比特序列

        Args:
            filepath: 文件路径

        Returns:
            List[int]: 比特序列 (0/1)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.bin':
            return self._load_binary(filepath)
        elif ext == '.txt':
            return self._load_text(filepath)
        elif ext == '.dat':
            return self._load_binary(filepath)
        elif ext == '.raw':
            return self._load_binary(filepath)
        else:
            # 尝试作为二进制文件加载
            return self._load_binary(filepath)

    def _load_binary(self, filepath: str) -> List[int]:
        """加载二进制文件"""
        with open(filepath, 'rb') as f:
            data = f.read()

        # 将每个字节转换为8位
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

        return bits

    def _load_text(self, filepath: str) -> List[int]:
        """加载文本文件（每行一个比特或连续比特串）"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除空白字符
        content = content.strip()

        # 尝试解析为连续的0/1字符串
        bits = []
        for char in content:
            if char in '01':
                bits.append(int(char))

        if not bits:
            raise ValueError(f"文件中没有找到有效的比特数据: {filepath}")

        return bits

    def load_from_directory(self, directory: str, pattern: str = '*') -> List[Tuple[str, List[int]]]:
        """
        从目录加载多个文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            List[Tuple[str, List[int]]]: (文件名, 比特序列)列表
        """
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"目录不存在: {directory}")

        results = []
        files = glob.glob(os.path.join(directory, pattern))

        for filepath in sorted(files):
            if os.path.isfile(filepath):
                ext = os.path.splitext(filepath)[1].lower()
                if ext in self.supported_extensions:
                    try:
                        bits = self.load_from_file(filepath)
                        results.append((os.path.basename(filepath), bits))
                    except Exception as e:
                        print(f"警告: 无法加载文件 {filepath}: {e}")

        return results

    def load_generator(self, directory: str, pattern: str = '*') -> Generator[Tuple[str, List[int]], None, None]:
        """
        生成器方式加载文件（节省内存）

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Yields:
            Tuple[str, List[int]]: (文件名, 比特序列)
        """
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"目录不存在: {directory}")

        files = glob.glob(os.path.join(directory, pattern))

        for filepath in sorted(files):
            if os.path.isfile(filepath):
                ext = os.path.splitext(filepath)[1].lower()
                if ext in self.supported_extensions:
                    try:
                        bits = self.load_from_file(filepath)
                        yield (os.path.basename(filepath), bits)
                    except Exception as e:
                        print(f"警告: 无法加载文件 {filepath}: {e}")

    def split_sequence(self, bits: List[int], segment_length: int = 1000000) -> List[List[int]]:
        """
        将长序列分割为多个片段

        Args:
            bits: 比特序列
            segment_length: 每段长度

        Returns:
            List[List[int]]: 分割后的序列列表
        """
        segments = []
        n = len(bits)

        for i in range(0, n, segment_length):
            end = min(i + segment_length, n)
            segment = bits[i:end]
            if len(segment) >= 100:  # 最小长度要求
                segments.append(segment)

        return segments

    def validate_sequence(self, bits: List[int], min_length: int = 1000000) -> Tuple[bool, str]:
        """
        验证序列是否符合测试要求

        Args:
            bits: 比特序列
            min_length: 最小长度要求

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not bits:
            return False, "序列为空"

        if len(bits) < min_length:
            return False, f"序列长度不足: {len(bits)} < {min_length}"

        # 检查是否只包含0和1
        unique_values = set(bits)
        if not unique_values.issubset({0, 1}):
            return False, f"序列包含非二进制值: {unique_values}"

        return True, "序列有效"

    def get_sequence_info(self, bits: List[int]) -> dict:
        """
        获取序列的基本信息

        Args:
            bits: 比特序列

        Returns:
            dict: 序列信息
        """
        if not bits:
            return {
                'length': 0,
                'ones_count': 0,
                'zeros_count': 0,
                'ones_ratio': 0.0
            }

        ones_count = sum(bits)
        zeros_count = len(bits) - ones_count

        return {
            'length': len(bits),
            'ones_count': ones_count,
            'zeros_count': zeros_count,
            'ones_ratio': ones_count / len(bits) if len(bits) > 0 else 0.0
        }

    def convert_to_numpy(self, bits: List[int]) -> np.ndarray:
        """转换为numpy数组"""
        return np.array(bits, dtype=np.int8)

    def convert_from_numpy(self, array: np.ndarray) -> List[int]:
        """从numpy数组转换"""
        return array.tolist()
