"""
集成测试
测试模块间的协作和数据流
"""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import CISChipRandomnessTest
from utils.data_loader import DataLoader
from utils.report_generator import ReportGenerator


@pytest.mark.integration
class TestIntegration:
    """集成测试"""

    def test_single_file_test(self, sample_bin_file):
        """单文件测试应返回完整结果"""
        tester = CISChipRandomnessTest(significance_level=0.01)
        result = tester.run_single_file_test(sample_bin_file)

        # 验证结果结构
        assert 'file' in result
        assert 'total_bits' in result
        assert 'segment_count' in result
        assert 'nist_results' in result
        assert 'gbt_results' in result
        assert 'nist_pass_rate' in result
        assert 'gbt_pass_rate' in result
        assert 'overall_pass_rate' in result

        # 验证NIST结果
        assert len(result['nist_results']) == 15
        assert all(0 <= v <= 1 for v in result['nist_results'].values())

        # 验证GB/T结果
        assert len(result['gbt_results']) == 4
        assert all(0 <= v <= 1 for v in result['gbt_results'].values())

        # 验证通过率
        assert 0 <= result['nist_pass_rate'] <= 1
        assert 0 <= result['gbt_pass_rate'] <= 1
        assert 0 <= result['overall_pass_rate'] <= 1

    def test_directory_test(self, sample_data_dir):
        """目录测试应返回汇总结果"""
        tester = CISChipRandomnessTest(significance_level=0.01)
        result = tester.run_directory_test(sample_data_dir)

        # 验证结果结构
        assert 'file_count' in result
        assert 'total_bits' in result
        assert 'nist_results' in result
        assert 'gbt_results' in result

        # 验证文件数量
        assert result['file_count'] == 3

    def test_report_generation_text(self, sample_bin_file, output_dir):
        """文本报告应成功生成"""
        tester = CISChipRandomnessTest(significance_level=0.01)
        result = tester.run_single_file_test(sample_bin_file)

        if 'error' not in result:
            report_gen = ReportGenerator(output_dir)
            filepath = report_gen.generate_text_report(result)

            assert os.path.exists(filepath)
            assert filepath.endswith('.txt')

            # 验证报告内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'CIS芯片TRNG随机性测试报告' in content
                assert 'NIST SP 800-22' in content

    def test_report_generation_html(self, sample_bin_file, output_dir):
        """HTML报告应成功生成"""
        tester = CISChipRandomnessTest(significance_level=0.01)
        result = tester.run_single_file_test(sample_bin_file)

        if 'error' not in result:
            report_gen = ReportGenerator(output_dir)
            filepath = report_gen.generate_html_report(result)

            assert os.path.exists(filepath)
            assert filepath.endswith('.html')

            # 验证报告内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'CIS芯片TRNG随机性测试报告' in content

    def test_report_generation_json(self, sample_bin_file, output_dir):
        """JSON报告应成功生成"""
        tester = CISChipRandomnessTest(significance_level=0.01)
        result = tester.run_single_file_test(sample_bin_file)

        if 'error' not in result:
            report_gen = ReportGenerator(output_dir)
            filepath = report_gen.generate_json_report(result)

            assert os.path.exists(filepath)
            assert filepath.endswith('.json')

    def test_data_loader_integration(self, sample_bin_file):
        """数据加载器应与测试套件正确集成"""
        loader = DataLoader()
        bits = loader.load_from_file(sample_bin_file)

        # 验证数据
        valid, msg = loader.validate_sequence(bits, min_length=1000)
        assert valid

        # 获取信息
        info = loader.get_sequence_info(bits)
        assert info['length'] > 0

    @pytest.mark.slow
    def test_random_data_should_have_results(self, sample_bin_file):
        """真随机数据应返回有效结果"""
        tester = CISChipRandomnessTest(significance_level=0.01)
        result = tester.run_single_file_test(sample_bin_file)

        # 应该有结果而不是错误
        assert 'error' not in result, f"测试出错: {result.get('error')}"

        # 应该有NIST和GB/T结果
        assert 'nist_results' in result
        assert 'gbt_results' in result
        assert len(result['nist_results']) == 15
        assert len(result['gbt_results']) == 4
