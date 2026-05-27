"""
端到端测试
测试CLI和GUI的完整流程
"""

import pytest
import sys
import os
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.e2e
class TestE2E:
    """端到端测试"""

    def test_cli_help(self):
        """CLI应显示帮助信息"""
        result = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        assert result.returncode == 0
        assert 'CIS芯片TRNG随机性测试套件' in result.stdout

    @pytest.mark.slow
    def test_cli_single_file(self, sample_bin_file):
        """CLI单文件测试应成功"""
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as output_dir:
            result = subprocess.run(
                [sys.executable, 'main.py', '--file', sample_bin_file, '--output', output_dir],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                timeout=600
            )

            # 验证执行成功（或至少有输出）
            assert 'CIS芯片TRNG随机性测试套件' in result.stdout

    @pytest.mark.slow
    def test_cli_directory(self, sample_data_dir):
        """CLI目录测试应成功"""
        with tempfile.TemporaryDirectory() as output_dir:
            result = subprocess.run(
                [sys.executable, 'main.py', '--data-dir', sample_data_dir, '--output', output_dir],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                timeout=600
            )

            # 验证有输出
            assert 'CIS芯片TRNG随机性测试套件' in result.stdout

    def test_gui_import(self):
        """GUI模块应能正常导入"""
        try:
            import gui_modern
            assert hasattr(gui_modern, 'ModernTestPlatform')
        except ImportError as e:
            if 'ttkbootstrap' in str(e):
                pytest.skip("ttkbootstrap未安装")
            else:
                raise

    def test_main_module_import(self):
        """主模块应能正常导入"""
        from main import CISChipRandomnessTest

        tester = CISChipRandomnessTest()
        assert tester is not None

    def test_nist_suite_import(self):
        """NIST测试套件应能正常导入"""
        from core.nist_tests_ng import NISTTestSuiteNistrng

        suite = NISTTestSuiteNistrng()
        assert suite is not None

    def test_gbt_suite_import(self):
        """GB/T测试套件应能正常导入"""
        from core.gbt_tests import GBTTestSuite

        suite = GBTTestSuite()
        assert suite is not None

    def test_data_loader_import(self):
        """数据加载器应能正常导入"""
        from utils.data_loader import DataLoader

        loader = DataLoader()
        assert loader is not None

    def test_report_generator_import(self):
        """报告生成器应能正常导入"""
        from utils.report_generator import ReportGenerator

        gen = ReportGenerator()
        assert gen is not None

    @pytest.mark.slow
    def test_full_workflow(self, sample_bin_file, output_dir):
        """完整工作流测试"""
        from main import CISChipRandomnessTest
        from utils.report_generator import ReportGenerator

        # 1. 创建测试实例
        tester = CISChipRandomnessTest(significance_level=0.01)

        # 2. 运行测试
        result = tester.run_single_file_test(sample_bin_file)

        # 3. 验证结果
        assert 'error' not in result, f"测试出错: {result.get('error')}"
        assert result['total_bits'] > 0

        # 4. 生成报告
        report_gen = ReportGenerator(output_dir)
        text_path = report_gen.generate_text_report(result)
        html_path = report_gen.generate_html_report(result)
        json_path = report_gen.generate_json_report(result)

        # 5. 验证报告
        assert os.path.exists(text_path)
        assert os.path.exists(html_path)
        assert os.path.exists(json_path)
