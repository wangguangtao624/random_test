#!/usr/bin/env python3
"""
测试运行脚本
一键运行所有自动化测试
"""

import os
import sys
import subprocess


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("CIS芯片TRNG随机性测试平台 - 自动化测试")
    print("=" * 70)
    print()

    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 检查pytest是否安装
    try:
        import pytest
        print(f"[OK] pytest {pytest.__version__} 已安装")
    except ImportError:
        print("[ERROR] pytest 未安装，正在安装...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest'], check=True)
        print("[OK] pytest 安装完成")

    print()
    print("-" * 70)
    print("运行测试...")
    print("-" * 70)
    print()

    # 运行pytest
    args = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '-x',  # 遇到失败停止
    ]

    result = subprocess.run(args, capture_output=False)

    print()
    print("=" * 70)

    if result.returncode == 0:
        print("[SUCCESS] 所有测试通过!")
    else:
        print(f"[FAIL] 测试失败 (返回码: {result.returncode})")

    print("=" * 70)

    return result.returncode


def run_unit_tests_only():
    """只运行单元测试"""
    print("运行单元测试...")
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    args = [
        sys.executable, '-m', 'pytest',
        'tests/test_nist_algorithm.py',
        'tests/test_gbt_algorithm.py',
        'tests/test_data_loader.py',
        'tests/test_statistics.py',
        '-v',
        '--tb=short'
    ]

    return subprocess.run(args).returncode


def run_integration_tests_only():
    """只运行集成测试"""
    print("运行集成测试...")
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    args = [
        sys.executable, '-m', 'pytest',
        'tests/test_integration.py',
        '-v',
        '--tb=short'
    ]

    return subprocess.run(args).returncode


def run_e2e_tests_only():
    """只运行端到端测试"""
    print("运行端到端测试...")
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    args = [
        sys.executable, '-m', 'pytest',
        'tests/test_e2e.py',
        '-v',
        '--tb=short'
    ]

    return subprocess.run(args).returncode


def run_with_coverage():
    """运行测试并生成覆盖率报告"""
    print("运行测试并生成覆盖率报告...")
    print()

    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(script_dir)

    # 检查pytest-cov是否安装
    try:
        import pytest_cov
    except ImportError:
        print("安装 pytest-cov...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest-cov'], check=True)

    args = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--cov=core',
        '--cov=utils',
        '--cov-report=html',
        '--cov-report=term'
    ]

    return subprocess.run(args).returncode


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == '--unit':
            sys.exit(run_unit_tests_only())
        elif command == '--integration':
            sys.exit(run_integration_tests_only())
        elif command == '--e2e':
            sys.exit(run_e2e_tests_only())
        elif command == '--coverage':
            sys.exit(run_with_coverage())
        elif command == '--help':
            print("用法: python run_tests.py [选项]")
            print()
            print("选项:")
            print("  (无参数)      运行所有测试")
            print("  --unit        只运行单元测试")
            print("  --integration 只运行集成测试")
            print("  --e2e         只运行端到端测试")
            print("  --coverage    运行测试并生成覆盖率报告")
            print("  --help        显示此帮助信息")
        else:
            print(f"未知命令: {command}")
            print("使用 --help 查看帮助")
            sys.exit(1)
    else:
        sys.exit(run_tests())
