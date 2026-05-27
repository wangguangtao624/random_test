"""
NIST SP 800-22 统计测试套件 - 基于 nistrng 库
来源: University of Siena SAILab (https://github.com/InsaneMonster/NistRng)
许可证: BSD-3-Clause
"""

import numpy as np
from typing import Dict, List, Any

try:
    import nistrng
    NISTRNG_AVAILABLE = True
except ImportError:
    NISTRNG_AVAILABLE = False
    print("警告: nistrng 未安装，请运行: pip install nistrng")


class NISTTestSuiteNistrng:
    """基于 nistrng 库的 NIST SP 800-22 测试套件"""

    # nistrng 测试名称到原测试名称的映射
    # nistrng 返回的名称是带空格的大写形式
    TEST_NAME_MAPPING = {
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

    # 所有测试名称（用于报告）
    TEST_NAMES = [
        'frequency_monobit',
        'frequency_within_block',
        'runs',
        'longest_run_of_ones',
        'binary_matrix_rank',
        'dft_spectral',
        'non_overlapping_template',
        'overlapping_template',
        'maurers_universal',
        'linear_complexity',
        'serial',
        'approximate_entropy',
        'cumulative_sums',
        'random_excursions',
        'random_excursions_variant'
    ]

    def __init__(self, significance_level: float = 0.01):
        """
        初始化测试套件

        Args:
            significance_level: 显著性水平 (默认 0.01)
        """
        self.alpha = significance_level

        if not NISTRNG_AVAILABLE:
            raise ImportError("nistrng 未安装，请运行: pip install nistrng")

    def run_all_tests(self, sequence) -> Dict[str, float]:
        """
        运行所有15项 NIST SP 800-22 测试

        Args:
            sequence: 比特序列 (list 或 numpy array)

        Returns:
            Dict[str, float]: {测试名: p_value}
        """
        # 转换为 numpy array
        if isinstance(sequence, list):
            bits = np.array(sequence, dtype=np.int8)
        else:
            bits = np.array(sequence, dtype=np.int8)

        # 确保序列长度足够
        if len(bits) < 100:
            raise ValueError(f"序列长度不足: {len(bits)} < 100")

        # 打包序列（nistrng 需要8位打包格式）
        packed = nistrng.pack_sequence(bits)

        # 运行测试
        results = nistrng.run_all_battery(
            packed,
            nistrng.SP800_22R1A_BATTERY,
            check_eligibility=True
        )

        # 转换结果格式
        output = {}
        for item in results:
            if item is not None:
                result, extra = item
                # 映射到原测试名称
                mapped_name = self.TEST_NAME_MAPPING.get(result.name, result.name)
                output[mapped_name] = result.score

        # 对于未运行的测试，填充默认值
        for test_name in self.TEST_NAMES:
            if test_name not in output:
                output[test_name] = 0.0

        return output

    def run_single_test(self, sequence, test_name: str) -> float:
        """
        运行单个测试

        Args:
            sequence: 比特序列
            test_name: 测试名称

        Returns:
            float: P-value
        """
        # 转换为 numpy array
        if isinstance(sequence, list):
            bits = np.array(sequence, dtype=np.int8)
        else:
            bits = np.array(sequence, dtype=np.int8)

        # 打包序列
        packed = nistrng.pack_sequence(bits)

        # 查找对应的 nistrng 测试名称
        nistrng_name = None
        for n_name, o_name in self.TEST_NAME_MAPPING.items():
            if o_name == test_name:
                nistrng_name = n_name
                break

        if nistrng_name is None:
            raise ValueError(f"未知的测试名称: {test_name}")

        # 运行单个测试
        try:
            result = nistrng.run_by_name_battery(
                nistrng_name,
                packed,
                nistrng.SP800_22R1A_BATTERY,
                check_eligibility=True
            )
            if result and result[0] is not None:
                res, extra = result
                return res.score
        except Exception as e:
            print(f"测试 {test_name} 执行失败: {e}")

        return 0.0

    def get_test_names(self) -> List[str]:
        """获取所有测试名称"""
        return self.TEST_NAMES.copy()


# 为了向后兼容，创建别名
NISTTestSuite = NISTTestSuiteNistrng
