"""
统计函数单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.statistics import (
    calculate_pass_rate,
    calculate_uniformity,
    analyze_p_value_distribution,
    calculate_confidence_interval,
    check_randomness_quality,
    generate_summary_statistics
)


class TestStatistics:
    """统计函数测试"""

    def test_calculate_pass_rate_all_pass(self):
        """全部通过时通过率应为1.0"""
        p_values = [0.05, 0.03, 0.02, 0.1, 0.5]
        rate = calculate_pass_rate(p_values, threshold=0.01)

        assert rate == 1.0

    def test_calculate_pass_rate_all_fail(self):
        """全部失败时通过率应为0.0"""
        p_values = [0.001, 0.005, 0.0001, 0.008]
        rate = calculate_pass_rate(p_values, threshold=0.01)

        assert rate == 0.0

    def test_calculate_pass_rate_partial(self):
        """部分通过时通过率应正确"""
        p_values = [0.05, 0.005, 0.02, 0.008]
        rate = calculate_pass_rate(p_values, threshold=0.01)

        assert abs(rate - 0.5) < 0.001

    def test_calculate_pass_rate_empty(self):
        """空列表应返回0.0"""
        rate = calculate_pass_rate([], threshold=0.01)

        assert rate == 0.0

    def test_calculate_uniformity(self):
        """均匀性检验应返回卡方统计量和P-value"""
        p_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
        chi_sq, p_value = calculate_uniformity(p_values, bins=10)

        assert chi_sq >= 0
        assert 0 <= p_value <= 1

    def test_calculate_uniformity_empty(self):
        """空列表应返回(0.0, 0.0)"""
        chi_sq, p_value = calculate_uniformity([])

        assert chi_sq == 0.0
        assert p_value == 0.0

    def test_analyze_p_value_distribution(self):
        """P-value分布分析应返回统计指标"""
        p_values = [0.1 * i for i in range(1, 11)]
        analysis = analyze_p_value_distribution(p_values)

        assert 'mean' in analysis
        assert 'std' in analysis
        assert 'min' in analysis
        assert 'max' in analysis
        assert 'median' in analysis

        assert analysis['min'] == 0.1
        assert analysis['max'] == 1.0

    def test_analyze_p_value_distribution_empty(self):
        """空列表应返回空字典"""
        analysis = analyze_p_value_distribution([])

        assert analysis == {}

    def test_calculate_confidence_interval(self):
        """置信区间应正确计算"""
        lower, upper = calculate_confidence_interval(0.95, 100, confidence=0.99)

        assert 0 <= lower <= 1
        assert 0 <= upper <= 1
        assert lower < upper

    def test_calculate_confidence_interval_zero_n(self):
        """样本数为0时应返回(0, 0)"""
        lower, upper = calculate_confidence_interval(0.95, 0)

        assert lower == 0.0
        assert upper == 0.0

    def test_check_randomness_quality_pass(self):
        """通过的测试应标记为PASS"""
        results = {
            'test1': 0.05,
            'test2': 0.1,
            'test3': 0.02
        }
        evaluations = check_randomness_quality(results, threshold=0.01)

        assert all(v == "PASS" for v in evaluations.values())

    def test_check_randomness_quality_fail(self):
        """失败的测试应标记为FAIL"""
        results = {
            'test1': 0.005,
            'test2': 0.001,
            'test3': 0.008
        }
        evaluations = check_randomness_quality(results, threshold=0.01)

        assert all(v == "FAIL" for v in evaluations.values())

    def test_generate_summary_statistics(self):
        """汇总统计应正确生成"""
        all_results = [
            {'test1': 0.05, 'test2': 0.1},
            {'test1': 0.03, 'test2': 0.02},
            {'test1': 0.08, 'test2': 0.15}
        ]
        summary = generate_summary_statistics(all_results)

        assert 'test1' in summary
        assert 'test2' in summary
        assert 'pass_rate' in summary['test1']
        assert 'mean_p_value' in summary['test1']

    def test_generate_summary_statistics_empty(self):
        """空列表应返回空字典"""
        summary = generate_summary_statistics([])

        assert summary == {}
