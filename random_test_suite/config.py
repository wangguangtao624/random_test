"""
配置文件 - CIS芯片TRNG随机性测试套件
"""

# 显著性水平
SIGNIFICANCE_LEVEL = 0.01

# 测试数据要求
MIN_SEQUENCE_LENGTH = 1000000  # 最小序列长度 (1Mbit)
MIN_SEQUENCE_COUNT = 1000      # 最小序列组数

# 通过标准
MIN_PASS_RATE = 0.98           # 最低通过率 98%

# NIST SP 800-22 测试参数
NIST_PARAMS = {
    'frequency_within_block': {
        'block_size': 128  # 块大小M
    },
    'longest_run_of_ones': {
        'block_size': 128  # 块大小M
    },
    'binary_matrix_rank': {
        'matrix_size': 32  # 矩阵大小Q×Q
    },
    'non_overlapping_template': {
        'template_length': 9  # 模板长度m
    },
    'overlapping_template': {
        'template_length': 9  # 模板长度m
    },
    'maurers_universal': {
        'block_size': 7  # 块大小L
    },
    'linear_complexity': {
        'block_size': 500  # 块大小M
    },
    'serial': {
        'pattern_length': 16  # 模式长度m
    },
    'approximate_entropy': {
        'pattern_length': 10  # 模式长度m
    }
}

# GB/T 32915-2016 测试参数
GBT_PARAMS = {
    'poker_test': {
        'block_sizes': [4, 8]  # 分组长度m
    },
    'autocorrelation': {
        'max_shift': 100  # 最大位移量
    },
    'binary_derivative': {
        'max_levels': 10  # 最大推导级数
    }
}

# 报告配置
REPORT_CONFIG = {
    'generate_text': True,
    'generate_html': True,
    'generate_json': True,
    'include_charts': True
}
