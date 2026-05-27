"""
NIST SP 800-22 算法单元测试
验证nistrng集成的正确性
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nist_tests_ng import NISTTestSuiteNistrng


@pytest.mark.nist
class TestNISTAlgorithm:
    """NIST测试算法验证"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.suite = NISTTestSuiteNistrng(significance_level=0.01)

    def test_all_zeros_should_fail(self, all_zeros):
        """全0序列应该大部分测试失败"""
        results = self.suite.run_all_tests(all_zeros)

        # 频率相关测试应该失败
        assert results['frequency_monobit'] < 0.01, "全0序列应导致频率测试失败"
        assert results['frequency_within_block'] < 0.01, "全0序列应导致块内频率测试失败"

        # 至少50%的测试应该失败
        fail_count = sum(1 for p in results.values() if p < 0.01)
        assert fail_count >= len(results) * 0.5, f"全0序列应导致大部分测试失败，实际失败{fail_count}项"

    def test_all_ones_should_fail(self, all_ones):
        """全1序列应该大部分测试失败"""
        results = self.suite.run_all_tests(all_ones)

        # 频率相关测试应该失败
        assert results['frequency_monobit'] < 0.01, "全1序列应导致频率测试失败"

        # 至少50%的测试应该失败
        fail_count = sum(1 for p in results.values() if p < 0.01)
        assert fail_count >= len(results) * 0.5, f"全1序列应导致大部分测试失败，实际失败{fail_count}项"

    def test_alternating_should_fail(self, alternating_bits):
        """交替序列应该部分测试失败"""
        results = self.suite.run_all_tests(alternating_bits)

        # 游程测试应该失败（游程长度固定为1）
        assert results['runs'] < 0.01, "交替序列应导致游程测试失败"

    def test_biased_should_fail_frequency(self, biased_bits):
        """有偏序列应该导致频率测试失败"""
        results = self.suite.run_all_tests(biased_bits)

        # 频率测试应该失败
        assert results['frequency_monobit'] < 0.01, "有偏序列应导致频率测试失败"

    @pytest.mark.slow
    def test_random_should_have_some_pass(self, random_bits_large):
        """真随机序列应有部分测试通过（NIST要求至少1项）"""
        results = self.suite.run_all_tests(random_bits_large)

        # 至少1项测试应该通过
        pass_count = sum(1 for p in results.values() if p >= 0.01)

        assert pass_count >= 1, f"真随机序列应至少通过1项测试，实际通过{pass_count}项"

    def test_returns_15_tests(self, random_bits):
        """应返回15项测试结果"""
        results = self.suite.run_all_tests(random_bits)
        assert len(results) == 15, f"应返回15项测试结果，实际{len(results)}项"

    def test_p_values_in_range(self, random_bits):
        """P-value应在[0, 1]范围内"""
        results = self.suite.run_all_tests(random_bits)

        for name, p_value in results.items():
            assert 0 <= p_value <= 1, f"测试 {name} 的P-value={p_value} 超出[0,1]范围"

    def test_test_names_correct(self, random_bits):
        """测试名称应正确映射"""
        expected_names = [
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

        results = self.suite.run_all_tests(random_bits)
        actual_names = set(results.keys())
        expected_set = set(expected_names)

        assert actual_names == expected_set, f"测试名称不匹配。缺少: {expected_set - actual_names}, 多余: {actual_names - expected_set}"

    def test_invalid_sequence_raises_error(self):
        """短序列应抛出错误"""
        short_sequence = [0, 1, 0] * 10  # 只有30位

        with pytest.raises(ValueError):
            self.suite.run_all_tests(short_sequence)
