"""
报告生成器
生成文本和HTML格式的测试报告
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np


class ReportGenerator:
    """报告生成器"""

    def __init__(self, output_dir: str = './reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_text_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        生成文本报告

        Args:
            results: 测试结果
            filename: 输出文件名

        Returns:
            str: 报告内容
        """
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filepath = os.path.join(self.output_dir, filename)

        lines = []
        lines.append("=" * 80)
        lines.append("CIS芯片TRNG随机性测试报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 测试概览
        lines.append("一、测试概览")
        lines.append("-" * 80)
        lines.append(f"测试数据文件数量: {results.get('file_count', 0)}")
        lines.append(f"测试序列总长度: {results.get('total_bits', 0):,} 比特")
        lines.append(f"显著性水平: α = {results.get('significance_level', 0.01)}")
        lines.append(f"通过标准: P-value ≥ {results.get('significance_level', 0.01)}")
        lines.append("")

        # NIST测试结果
        lines.append("二、NIST SP 800-22 测试结果 (15项)")
        lines.append("-" * 80)
        lines.append(f"{'测试项':<45} {'通过率':>10} {'状态':>8}")
        lines.append("-" * 80)

        nist_results = results.get('nist_results', {})
        for test_name, pass_rate in nist_results.items():
            status = "PASS" if pass_rate >= 0.98 else "FAIL"
            lines.append(f"{test_name:<45} {pass_rate*100:>9.2f}% {status:>8}")

        lines.append("-" * 80)
        nist_pass_rate = results.get('nist_pass_rate', 0)
        lines.append(f"{'NIST总体通过率':<45} {nist_pass_rate*100:>9.2f}%")
        lines.append("")

        # GB/T测试结果
        lines.append("三、GB/T 32915-2016 补充测试结果 (3项)")
        lines.append("-" * 80)
        lines.append(f"{'测试项':<45} {'通过率':>10} {'状态':>8}")
        lines.append("-" * 80)

        gbt_results = results.get('gbt_results', {})
        for test_name, pass_rate in gbt_results.items():
            status = "PASS" if pass_rate >= 0.98 else "FAIL"
            lines.append(f"{test_name:<45} {pass_rate*100:>9.2f}% {status:>8}")

        lines.append("-" * 80)
        gbt_pass_rate = results.get('gbt_pass_rate', 0)
        lines.append(f"{'GB/T总体通过率':<45} {gbt_pass_rate*100:>9.2f}%")
        lines.append("")

        # 总体结论
        lines.append("四、总体结论")
        lines.append("-" * 80)
        overall_pass_rate = results.get('overall_pass_rate', 0)
        overall_status = "通过" if overall_pass_rate >= 0.98 else "未通过"

        lines.append(f"总体通过率: {overall_pass_rate*100:.2f}%")
        lines.append(f"测试结论: {overall_status}")

        if overall_status == "通过":
            lines.append("")
            lines.append("该CIS芯片的TRNG输出满足 NIST SP 800-22 和 GB/T 32915-2016 的随机性要求。")
        else:
            lines.append("")
            lines.append("该CIS芯片的TRNG输出未能满足随机性要求，建议检查硬件设计。")

        lines.append("")
        lines.append("=" * 80)

        # 写入文件
        report_content = "\n".join(lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return filepath

    def generate_html_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        生成HTML报告

        Args:
            results: 测试结果
            filename: 输出文件名

        Returns:
            str: 报告文件路径
        """
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        filepath = os.path.join(self.output_dir, filename)

        # 生成图表
        chart_paths = self._generate_charts(results)

        html_content = self._build_html(results, chart_paths)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filepath

    def _generate_charts(self, results: Dict[str, Any]) -> Dict[str, str]:
        """生成图表"""
        chart_paths = {}

        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 图表1: NIST测试通过率
            nist_results = results.get('nist_results', {})
            if nist_results:
                fig, ax = plt.subplots(figsize=(12, 6))

                test_names = list(nist_results.keys())
                pass_rates = list(nist_results.values())

                colors = ['green' if r >= 0.98 else 'red' for r in pass_rates]
                bars = ax.bar(range(len(test_names)), pass_rates, color=colors)

                ax.set_xlabel('测试项')
                ax.set_ylabel('通过率')
                ax.set_title('NIST SP 800-22 测试通过率')
                ax.set_xticks(range(len(test_names)))
                ax.set_xticklabels(test_names, rotation=45, ha='right')
                ax.axhline(y=0.98, color='r', linestyle='--', label='98%阈值')
                ax.legend()

                plt.tight_layout()
                chart_path = os.path.join(self.output_dir, 'nist_pass_rates.png')
                plt.savefig(chart_path, dpi=150)
                plt.close()
                chart_paths['nist_pass_rates'] = chart_path

            # 图表2: GB/T测试通过率
            gbt_results = results.get('gbt_results', {})
            if gbt_results:
                fig, ax = plt.subplots(figsize=(8, 6))

                test_names = list(gbt_results.keys())
                pass_rates = list(gbt_results.values())

                colors = ['green' if r >= 0.98 else 'red' for r in pass_rates]
                bars = ax.bar(range(len(test_names)), pass_rates, color=colors)

                ax.set_xlabel('测试项')
                ax.set_ylabel('通过率')
                ax.set_title('GB/T 32915-2016 补充测试通过率')
                ax.set_xticks(range(len(test_names)))
                ax.set_xticklabels(test_names, rotation=45, ha='right')
                ax.axhline(y=0.98, color='r', linestyle='--', label='98%阈值')
                ax.legend()

                plt.tight_layout()
                chart_path = os.path.join(self.output_dir, 'gbt_pass_rates.png')
                plt.savefig(chart_path, dpi=150)
                plt.close()
                chart_paths['gbt_pass_rates'] = chart_path

            # 图表3: 总体通过率饼图
            overall_pass_rate = results.get('overall_pass_rate', 0)
            fig, ax = plt.subplots(figsize=(6, 6))

            labels = ['通过', '未通过']
            sizes = [overall_pass_rate, 1 - overall_pass_rate]
            colors = ['green', 'red']

            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('总体测试通过率')

            chart_path = os.path.join(self.output_dir, 'overall_pass_rate.png')
            plt.savefig(chart_path, dpi=150)
            plt.close()
            chart_paths['overall_pass_rate'] = chart_path

        except Exception as e:
            print(f"警告: 生成图表时出错: {e}")

        return chart_paths

    def _build_html(self, results: Dict[str, Any], chart_paths: Dict[str, str]) -> str:
        """构建HTML内容"""
        overall_pass_rate = results.get('overall_pass_rate', 0)
        overall_status = "通过" if overall_pass_rate >= 0.98 else "未通过"

        nist_results = results.get('nist_results', {})
        gbt_results = results.get('gbt_results', {})

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CIS芯片TRNG随机性测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #007bff;
            border-left: 4px solid #007bff;
            padding-left: 10px;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .pass {{
            color: green;
            font-weight: bold;
        }}
        .fail {{
            color: red;
            font-weight: bold;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .chart {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart img {{
            max-width: 100%;
            height: auto;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CIS芯片TRNG随机性测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>一、测试概览</h2>
        <div class="summary">
            <p><strong>测试数据文件数量:</strong> {results.get('file_count', 0)}</p>
            <p><strong>测试序列总长度:</strong> {results.get('total_bits', 0):,} 比特</p>
            <p><strong>显著性水平:</strong> α = {results.get('significance_level', 0.01)}</p>
            <p><strong>通过标准:</strong> P-value ≥ {results.get('significance_level', 0.01)}</p>
        </div>

        <h2>二、NIST SP 800-22 测试结果 (15项)</h2>
        <table>
            <thead>
                <tr>
                    <th>测试项</th>
                    <th>通过率</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""

        for test_name, pass_rate in nist_results.items():
            status_class = "pass" if pass_rate >= 0.98 else "fail"
            status_text = "PASS" if pass_rate >= 0.98 else "FAIL"
            html += f"""
                <tr>
                    <td>{test_name}</td>
                    <td>{pass_rate*100:.2f}%</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>
        <p><strong>NIST总体通过率:</strong> {results.get('nist_pass_rate', 0)*100:.2f}%</p>

        <h2>三、GB/T 32915-2016 补充测试结果 (3项)</h2>
        <table>
            <thead>
                <tr>
                    <th>测试项</th>
                    <th>通过率</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""

        for test_name, pass_rate in gbt_results.items():
            status_class = "pass" if pass_rate >= 0.98 else "fail"
            status_text = "PASS" if pass_rate >= 0.98 else "FAIL"
            html += f"""
                <tr>
                    <td>{test_name}</td>
                    <td>{pass_rate*100:.2f}%</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>
        <p><strong>GB/T总体通过率:</strong> {results.get('gbt_pass_rate', 0)*100:.2f}%</p>

        <h2>四、图表分析</h2>
        <div class="chart">
"""

        for chart_name, chart_path in chart_paths.items():
            # 使用相对路径
            rel_path = os.path.relpath(chart_path, self.output_dir)
            html += f'            <img src="{rel_path}" alt="{chart_name}">\n'

        html += f"""
        </div>

        <h2>五、总体结论</h2>
        <div class="summary">
            <p><strong>总体通过率:</strong> {overall_pass_rate*100:.2f}%</p>
            <p><strong>测试结论:</strong> <span class="{'pass' if overall_status == '通过' else 'fail'}">{overall_status}</span></p>
"""

        if overall_status == "通过":
            html += """
            <p>该CIS芯片的TRNG输出满足 NIST SP 800-22 和 GB/T 32915-2016 的随机性要求。</p>
"""
        else:
            html += """
            <p>该CIS芯片的TRNG输出未能满足随机性要求，建议检查硬件设计。</p>
"""

        html += """
        </div>

        <div class="footer">
            <p>本报告由CIS芯片TRNG随机性测试套件自动生成</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def generate_json_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        生成JSON格式的详细结果

        Args:
            results: 测试结果
            filename: 输出文件名

        Returns:
            str: JSON文件路径
        """
        if filename is None:
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = os.path.join(self.output_dir, filename)

        # 添加元数据
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'tool_version': '1.0.0'
            },
            'results': results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return filepath
