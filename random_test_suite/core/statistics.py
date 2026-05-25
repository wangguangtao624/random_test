"""
统计分析函数
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple
import math


def calculate_pass_rate(p_values: List[float], threshold: float = 0.01) -> float:
    """
    计算通过率

    Args:
        p_values: P-value列表
        threshold: 显著性水平阈值

    Returns:
        float: 通过率 (0-1)
    """
    if not p_values:
        return 0.0

    pass_count = sum(1 for p in p_values if p >= threshold)
    return pass_count / len(p_values)


def calculate_uniformity(p_values: List[float], bins: int = 10) -> Tuple[float, float]:
    """
    检验P-value分布的均匀性

    Args:
        p_values: P-value列表
        bins: 分箱数量

    Returns:
        Tuple: (卡方统计量, P-value)
    """
    if not p_values:
        return 0.0, 0.0

    # 计算直方图
    observed, bin_edges = np.histogram(p_values, bins=bins, range=(0, 1))

    # 期望频数（均匀分布）
    expected = len(p_values) / bins

    # 计算卡方统计量
    chi_squared = np.sum((observed - expected)**2 / expected)

    # 计算P-value
    p_value = 1 - stats.chi2.cdf(chi_squared, bins - 1)

    return chi_squared, p_value


def analyze_p_value_distribution(p_values: List[float]) -> Dict[str, float]:
    """
    分析P-value分布的统计特性

    Args:
        p_values: P-value列表

    Returns:
        Dict: 统计指标
    """
    if not p_values:
        return {}

    p_array = np.array(p_values)

    results = {
        'mean': np.mean(p_array),
        'std': np.std(p_array),
        'min': np.min(p_array),
        'max': np.max(p_array),
        'median': np.median(p_array),
        'q25': np.percentile(p_array, 25),
        'q75': np.percentile(p_array, 75),
        'skewness': stats.skew(p_array),
        'kurtosis': stats.kurtosis(p_array)
    }

    # 计算均匀性检验
    chi_squared, uniformity_p = calculate_uniformity(p_values)
    results['uniformity_chi_squared'] = chi_squared
    results['uniformity_p_value'] = uniformity_p

    return results


def calculate_confidence_interval(pass_rate: float, n: int, confidence: float = 0.99) -> Tuple[float, float]:
    """
    计算通过率的置信区间

    Args:
        pass_rate: 通过率
        n: 样本数量
        confidence: 置信水平

    Returns:
        Tuple: (下限, 上限)
    """
    if n <= 0:
        return 0.0, 0.0

    # 使用正态近似
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    se = math.sqrt(pass_rate * (1 - pass_rate) / n)

    lower = pass_rate - z * se
    upper = pass_rate + z * se

    # 限制在[0, 1]范围内
    lower = max(0, lower)
    upper = min(1, upper)

    return lower, upper


def check_randomness_quality(results: Dict[str, float], threshold: float = 0.01) -> Dict[str, str]:
    """
    评估随机数质量

    Args:
        results: 测试结果 {测试名: P-value}
        threshold: 显著性水平阈值

    Returns:
        Dict: 评估结果 {测试名: 评估结论}
    """
    evaluations = {}

    for test_name, p_value in results.items():
        if p_value >= threshold:
            evaluations[test_name] = "PASS"
        else:
            evaluations[test_name] = "FAIL"

    return evaluations


def generate_summary_statistics(all_results: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    生成汇总统计

    Args:
        all_results: 所有测试结果列表

    Returns:
        Dict: 汇总统计
    """
    if not all_results:
        return {}

    # 获取所有测试名称
    test_names = list(all_results[0].keys())

    summary = {}
    for test_name in test_names:
        p_values = [r[test_name] for r in all_results if test_name in r]

        if p_values:
            pass_rate = calculate_pass_rate(p_values)
            analysis = analyze_p_value_distribution(p_values)

            summary[test_name] = {
                'pass_rate': pass_rate,
                'mean_p_value': analysis.get('mean', 0),
                'std_p_value': analysis.get('std', 0),
                'min_p_value': analysis.get('min', 0),
                'max_p_value': analysis.get('max', 0),
                'uniformity_p_value': analysis.get('uniformity_p_value', 0)
            }

    return summary
