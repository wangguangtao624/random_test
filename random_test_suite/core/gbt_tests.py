"""
GB/T 32915-2016 补充测试实现
实现扑克检测、自相关检测、二元推导检测
"""

import numpy as np
from scipy import stats
from typing import List, Tuple, Dict
import math


class GBTTestSuite:
    """GB/T 32915-2016 补充测试套件"""

    def __init__(self, significance_level: float = 0.01):
        self.alpha = significance_level
        self.test_names = [
            'poker_test',
            'autocorrelation_test',
            'binary_derivative_test'
        ]

    def run_all_tests(self, sequence: List[int]) -> Dict[str, float]:
        """
        执行所有GB/T补充测试

        Args:
            sequence: 比特序列 (list of 0/1)

        Returns:
            Dict: 测试名称 -> P-value
        """
        results = {}

        # 确保序列长度足够
        n = len(sequence)
        if n < 100:
            raise ValueError(f"序列长度不足: {n} < 100")

        # 转换为numpy数组提高效率
        bits = np.array(sequence, dtype=np.int8)

        # 执行各项测试
        results['poker_test_m4'] = self.poker_test(bits, m=4)
        results['poker_test_m8'] = self.poker_test(bits, m=8)
        results['autocorrelation_test'] = self.autocorrelation_test(bits)
        results['binary_derivative_test'] = self.binary_derivative_test(bits)

        return results

    def poker_test(self, bits: np.ndarray, m: int = 4) -> float:
        """
        扑克检测
        检测m位子序列的出现频率

        Args:
            bits: 比特序列
            m: 分组长度 (4或8)

        Returns:
            float: P-value
        """
        n = len(bits)
        num_groups = n // m

        if num_groups < 1:
            return 0.0

        # 统计每种取值的出现次数
        counts = {}
        for i in range(num_groups):
            # 将m位转换为整数
            value = 0
            for j in range(m):
                value = (value << 1) | bits[i * m + j]
            counts[value] = counts.get(value, 0) + 1

        # 计算卡方统计量
        expected = num_groups / (2**m)
        chi_squared = 0

        for count in counts.values():
            chi_squared += (count - expected)**2

        chi_squared /= expected

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, 2**m - 1)

        return p_value

    def autocorrelation_test(self, bits: np.ndarray, max_shift: int = 100) -> float:
        """
        自相关检测
        检测序列与其移位版本的相关性

        Args:
            bits: 比特序列
            max_shift: 最大位移量

        Returns:
            float: P-value (取所有位移中的最小值)
        """
        n = len(bits)

        if max_shift > n // 2:
            max_shift = n // 2

        p_values = []

        for d in range(1, max_shift + 1):
            # 计算自相关系数
            # A(d) = Σ(Xi XOR Xi+d) for i=0 to n-d-1
            xor_result = np.logical_xor(bits[:n-d], bits[d:n]).astype(np.int8)

            # 统计异或结果中0的个数
            zero_count = np.sum(xor_result == 0)

            # 计算统计量
            # 在随机假设下，0的个数应接近(n-d)/2
            expected = (n - d) / 2
            variance = (n - d) / 4

            if variance > 0:
                z = (zero_count - expected) / math.sqrt(variance)
                # 计算P-value
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                p_values.append(p_value)

        if not p_values:
            return 0.0

        # 返回最小的P-value
        return min(p_values)

    def binary_derivative_test(self, bits: np.ndarray, max_levels: int = 10) -> float:
        """
        二元推导检测
        对序列逐级进行差分（异或相邻比特），检查各级推导序列中0和1的比例是否均衡

        Args:
            bits: 比特序列
            max_levels: 最大推导级数

        Returns:
            float: P-value (取所有级数中的最小值)
        """
        n = len(bits)
        current_sequence = bits.copy()

        p_values = []

        for level in range(max_levels):
            # 检查当前序列长度
            if len(current_sequence) < 10:
                break

            # 计算0和1的个数
            ones_count = np.sum(current_sequence)
            zeros_count = len(current_sequence) - ones_count

            # 计算统计量
            # 在随机假设下，0和1的个数应接近相等
            total = len(current_sequence)
            expected = total / 2
            variance = total / 4

            if variance > 0:
                z = (ones_count - expected) / math.sqrt(variance)
                # 计算P-value
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                p_values.append(p_value)

            # 计算差分序列
            new_sequence = np.logical_xor(current_sequence[:-1], current_sequence[1:]).astype(np.int8)
            current_sequence = new_sequence

        if not p_values:
            return 0.0

        # 返回最小的P-value
        return min(p_values)

    def run_extended_tests(self, bits: np.ndarray) -> Dict[str, float]:
        """
        运行扩展测试（可选）

        Args:
            bits: 比特序列

        Returns:
            Dict: 测试名称 -> P-value
        """
        results = {}

        # 运行不同参数的扑克测试
        for m in [4, 8]:
            results[f'poker_test_m{m}'] = self.poker_test(bits, m=m)

        # 运行不同位移量的自相关测试
        for d in [1, 2, 5, 10]:
            results[f'autocorrelation_d{d}'] = self._autocorrelation_single_shift(bits, d)

        # 运行不同级数的二元推导测试
        results['binary_derivative_levels'] = self._binary_derivative_levels(bits)

        return results

    def _autocorrelation_single_shift(self, bits: np.ndarray, d: int) -> float:
        """单一位移量的自相关检测"""
        n = len(bits)

        if d >= n:
            return 0.0

        # 计算自相关系数
        xor_result = np.logical_xor(bits[:n-d], bits[d:n]).astype(np.int8)
        zero_count = np.sum(xor_result == 0)

        # 计算统计量
        expected = (n - d) / 2
        variance = (n - d) / 4

        if variance <= 0:
            return 0.0

        z = (zero_count - expected) / math.sqrt(variance)
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))

        return p_value

    def _binary_derivative_levels(self, bits: np.ndarray) -> Dict[int, float]:
        """各级二元推导检测的结果"""
        n = len(bits)
        current_sequence = bits.copy()

        results = {}
        level = 0

        while len(current_sequence) >= 10 and level < 10:
            # 计算0和1的个数
            ones_count = np.sum(current_sequence)
            zeros_count = len(current_sequence) - ones_count

            # 计算统计量
            total = len(current_sequence)
            expected = total / 2
            variance = total / 4

            if variance > 0:
                z = (ones_count - expected) / math.sqrt(variance)
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
                results[f'level_{level}'] = p_value

            # 计算差分序列
            new_sequence = np.logical_xor(current_sequence[:-1], current_sequence[1:]).astype(np.int8)
            current_sequence = new_sequence
            level += 1

        return results
