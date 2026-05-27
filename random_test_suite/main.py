#!/usr/bin/env python3
"""
CIS芯片TRNG随机性测试主程序
集成 NIST SP 800-22 和 GB/T 32915-2016 全部测试项
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nist_tests_ng import NISTTestSuiteNistrng as NISTTestSuite
from core.gbt_tests import GBTTestSuite
from core.statistics import calculate_pass_rate, generate_summary_statistics
from utils.data_loader import DataLoader
from utils.report_generator import ReportGenerator


class CISChipRandomnessTest:
    """CIS芯片TRNG随机性测试套件"""

    def __init__(self, significance_level: float = 0.01):
        self.alpha = significance_level
        self.nist_suite = NISTTestSuite(significance_level)
        self.gbt_suite = GBTTestSuite(significance_level)
        self.data_loader = DataLoader()

    def run_single_file_test(self, filepath: str) -> Dict[str, Any]:
        """
        对单个文件运行完整测试

        Args:
            filepath: 数据文件路径

        Returns:
            Dict: 测试结果
        """
        print(f"\n正在处理文件: {filepath}")

        # 加载数据
        bits = self.data_loader.load_from_file(filepath)
        info = self.data_loader.get_sequence_info(bits)

        print(f"  序列长度: {info['length']:,} 比特")
        print(f"  1的比例: {info['ones_ratio']:.4f}")

        # 验证序列
        valid, msg = self.data_loader.validate_sequence(bits)
        if not valid:
            print(f"  警告: {msg}")
            return {'error': msg}

        # 分割序列为多个片段
        segments = self.data_loader.split_sequence(bits, segment_length=1000000)
        print(f"  分割为 {len(segments)} 个测试片段")

        # 运行测试
        nist_results = []
        gbt_results = []

        for i, segment in enumerate(segments):
            print(f"  测试片段 {i+1}/{len(segments)}...", end='\r')

            # NIST测试
            try:
                nist_result = self.nist_suite.run_all_tests(segment)
                nist_results.append(nist_result)
            except Exception as e:
                print(f"\n  NIST测试错误: {e}")

            # GB/T测试
            try:
                gbt_result = self.gbt_suite.run_all_tests(segment)
                gbt_results.append(gbt_result)
            except Exception as e:
                print(f"\n  GB/T测试错误: {e}")

        print()

        # 计算通过率
        nist_pass_rates = self._calculate_pass_rates(nist_results)
        gbt_pass_rates = self._calculate_pass_rates(gbt_results)

        # 计算总体通过率
        nist_overall = sum(nist_pass_rates.values()) / len(nist_pass_rates) if nist_pass_rates else 0
        gbt_overall = sum(gbt_pass_rates.values()) / len(gbt_pass_rates) if gbt_pass_rates else 0
        overall = (nist_overall * 15 + gbt_overall * 3) / 18

        return {
            'file': os.path.basename(filepath),
            'file_count': 1,
            'total_bits': info['length'],
            'segment_count': len(segments),
            'significance_level': self.alpha,
            'nist_results': nist_pass_rates,
            'gbt_results': gbt_pass_rates,
            'nist_pass_rate': nist_overall,
            'gbt_pass_rate': gbt_overall,
            'overall_pass_rate': overall
        }

    def run_directory_test(self, directory: str, pattern: str = '*') -> Dict[str, Any]:
        """
        对目录中的所有文件运行测试

        Args:
            directory: 数据目录
            pattern: 文件匹配模式

        Returns:
            Dict: 测试结果
        """
        print(f"\n正在扫描目录: {directory}")

        # 获取所有文件
        files = []
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.data_loader.supported_extensions:
                    files.append(filepath)

        if not files:
            print("未找到支持的数据文件")
            return {'error': '未找到数据文件'}

        print(f"找到 {len(files)} 个数据文件")

        # 运行测试
        all_results = []
        total_bits = 0

        for i, filepath in enumerate(files):
            print(f"\n处理文件 {i+1}/{len(files)}: {os.path.basename(filepath)}")

            result = self.run_single_file_test(filepath)
            if 'error' not in result:
                all_results.append(result)
                total_bits += result['total_bits']

        # 汇总结果
        summary = self._aggregate_results(all_results)
        summary['file_count'] = len(all_results)
        summary['total_bits'] = total_bits

        return summary

    def _calculate_pass_rates(self, results_list: List[Dict[str, float]]) -> Dict[str, float]:
        """计算各项测试的通过率"""
        if not results_list:
            return {}

        # 获取所有测试名称
        test_names = list(results_list[0].keys())

        pass_rates = {}
        for test_name in test_names:
            p_values = [r.get(test_name, 0) for r in results_list if test_name in r]
            if p_values:
                pass_rates[test_name] = calculate_pass_rate(p_values, self.alpha)

        return pass_rates

    def _aggregate_results(self, results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """汇总多个文件的测试结果"""
        if not results_list:
            return {}

        # 汇总NIST结果
        nist_aggregated = {}
        for result in results_list:
            for test_name, pass_rate in result.get('nist_results', {}).items():
                if test_name not in nist_aggregated:
                    nist_aggregated[test_name] = []
                nist_aggregated[test_name].append(pass_rate)

        nist_pass_rates = {}
        for test_name, rates in nist_aggregated.items():
            nist_pass_rates[test_name] = sum(rates) / len(rates)

        # 汇总GB/T结果
        gbt_aggregated = {}
        for result in results_list:
            for test_name, pass_rate in result.get('gbt_results', {}).items():
                if test_name not in gbt_aggregated:
                    gbt_aggregated[test_name] = []
                gbt_aggregated[test_name].append(pass_rate)

        gbt_pass_rates = {}
        for test_name, rates in gbt_aggregated.items():
            gbt_pass_rates[test_name] = sum(rates) / len(rates)

        # 计算总体通过率
        nist_overall = sum(nist_pass_rates.values()) / len(nist_pass_rates) if nist_pass_rates else 0
        gbt_overall = sum(gbt_pass_rates.values()) / len(gbt_pass_rates) if gbt_pass_rates else 0
        overall = (nist_overall * 15 + gbt_overall * 3) / 18

        return {
            'significance_level': self.alpha,
            'nist_results': nist_pass_rates,
            'gbt_results': gbt_pass_rates,
            'nist_pass_rate': nist_overall,
            'gbt_pass_rate': gbt_overall,
            'overall_pass_rate': overall
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='CIS芯片TRNG随机性测试套件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试单个文件
  python main.py --file data/sample.bin

  # 测试整个目录
  python main.py --data-dir ./data

  # 指定输出目录
  python main.py --data-dir ./data --output ./reports

  # 生成HTML报告
  python main.py --data-dir ./data --format html
        """
    )

    parser.add_argument('--file', '-f', help='单个数据文件路径')
    parser.add_argument('--data-dir', '-d', help='数据目录路径')
    parser.add_argument('--output', '-o', default='./reports', help='输出目录 (默认: ./reports)')
    parser.add_argument('--format', choices=['text', 'html', 'all'], default='all',
                       help='报告格式 (默认: all)')
    parser.add_argument('--alpha', type=float, default=0.01,
                       help='显著性水平 (默认: 0.01)')
    parser.add_argument('--pattern', default='*', help='文件匹配模式 (默认: *)')

    args = parser.parse_args()

    # 验证参数
    if not args.file and not args.data_dir:
        parser.error("请指定 --file 或 --data-dir 参数")

    if args.file and args.data_dir:
        parser.error("不能同时指定 --file 和 --data-dir")

    # 创建测试套件
    tester = CISChipRandomnessTest(significance_level=args.alpha)

    # 运行测试
    print("=" * 60)
    print("CIS芯片TRNG随机性测试套件")
    print("=" * 60)
    print(f"显著性水平: α = {args.alpha}")
    print(f"通过标准: P-value ≥ {args.alpha}")
    print()

    if args.file:
        results = tester.run_single_file_test(args.file)
    else:
        results = tester.run_directory_test(args.data_dir, args.pattern)

    # 生成报告
    if 'error' not in results:
        print("\n" + "=" * 60)
        print("生成测试报告")
        print("=" * 60)

        report_gen = ReportGenerator(args.output)

        if args.format in ['text', 'all']:
            text_path = report_gen.generate_text_report(results)
            print(f"文本报告: {text_path}")

        if args.format in ['html', 'all']:
            html_path = report_gen.generate_html_report(results)
            print(f"HTML报告: {html_path}")

        json_path = report_gen.generate_json_report(results)
        print(f"JSON结果: {json_path}")

        # 打印摘要
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        print(f"总体通过率: {results['overall_pass_rate']*100:.2f}%")
        print(f"NIST通过率: {results['nist_pass_rate']*100:.2f}%")
        print(f"GB/T通过率: {results['gbt_pass_rate']*100:.2f}%")

        if results['overall_pass_rate'] >= 0.98:
            print("\n[OK] 测试通过！TRNG输出满足随机性要求。")
        else:
            print("\n[FAIL] 测试未通过。建议检查TRNG设计。")

    else:
        print(f"\n错误: {results['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
