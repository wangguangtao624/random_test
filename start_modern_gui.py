#!/usr/bin/env python3
"""
启动CIS芯片TRNG随机性测试平台 - 现代化UI
"""

import sys
import os

# 添加random_test_suite目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, "random_test_suite"))

# 切换工作目录到random_test_suite
os.chdir(os.path.join(script_dir, "random_test_suite"))

# 导入并运行GUI
from gui_modern import main

if __name__ == "__main__":
    main()
