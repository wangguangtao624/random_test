"""
GB/T 32915-2016 算法单元测试
验证扑克检测、自相关检测、二元推导检测
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gbt_tests import GBTTestSuite


@pytest.mark.gbt
class TestGBTAlgorithm:
    """GB/T测试算法验证"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.suite = GBTTestSuite(significance_level=0.01)

    def test_all_zeros_should_fail(self, all_zeros):
        """全0序列应该测试失败"""
        results = self.suite.run_all_tests(all_zeros)

        # 扑克检测应该失败
        assert results['poker_test_m4'] < 0.01, "全0序列应导致扑克检测失败"

    def test_all_ones_should_fail(self, all_ones):
        """全1序列应该测试失败"""
        results = self.suite.run_all_tests(all_ones)

        # 扑克检测应该失败
        assert results['poker_test_m4'] < 0.01, "全1序列应导致扑克检测失败"

    def test_random_should_pass(self, random_bits):
        """真随机序列应该通过测试"""
        results = self.suite.run_all_tests(random_bits)

        # 至少2项测试应该通过
        pass_count = sum(1 for p in results.values() if p >= 0.01)
        assert pass_count >= 2, f"真随机序列应至少通过2项测试，实际通过{pass_count}项"

    def test_returns_4_tests(self, random_bits):
        """应返回4项测试结果"""
        results = self.suite.run_all_tests(random_bits)
        assert len(results) == 4, f"应返回4项测试结果，实际{len(results)}项"

    def test_p_values_in_range(self, random_bits):
        """P-value应在[0, 1]范围内"""
        results = self.suite.run_all_tests(random_bits)

        for name, p_value in results.items():
            assert 0 <= p_value <= 1, f"测试 {name} 的P-value={p_value} 超出[0,1]范围"

    def test_test_names_correct(self, random_bits):
        """测试名称应正确"""
        expected_names = [
            'poker_test_m4',
            'poker_test_m8',
            'autocorrelation_test',
            'binary_derivative_test'
        ]

        results = self.suite.run_all_tests(random_bits)
        actual_names = set(results.keys())
        expected_set = set(expected_names)

        assert actual_names == expected_set, f"测试名称不匹配。缺少: {expected_set - actual_names}, 多余: {actual_names - expected_set}"

    def test_periodic_should_fail(self, periodic_bits):
        """周期序列应该测试失败"""
        results = self.suite.run_all_tests(periodic_bits)

        # 至少1项测试应该失败
        fail_count = sum(1 for p in results.values() if p < 0.01)
        assert fail_count >= 1, "周期序列应导致至少1项测试失败"

    def test_poker_test_m4(self, random_bits):
        """扑克检测m=4应正常工作"""
        results = self.suite.run_all_tests(random_bits)
        assert 'poker_test_m4' in results
        assert 0 <= results['poker_test_m4'] <= 1

    def test_poker_test_m8(self, random_bits):
        """扑克检测m=8应正常工作"""
        results = self.suite.run_all_tests(random_bits)
        assert 'poker_test_m8' in results
        assert 0 <= results['poker_test_m8'] <= 1

    def test_autocorrelation_test(self, random_bits):
        """自相关检测应正常工作"""
        results = self.suite.run_all_tests(random_bits)
        assert 'autocorrelation_test' in results
        assert 0 <= results['autocorrelation_test'] <= 1

    def test_binary_derivative_test(self, random_bits):
        """二元推导检测应正常工作"""
        results = self.suite.run_all_tests(random_bits)
        assert 'binary_derivative_test' in results
        assert 0 <= results['binary_derivative_test'] <= 1
