# CIS芯片TRNG随机性测试套件

## 简介

本工具集成了 NIST SP 800-22 和 GB/T 32915-2016 两个标准的全部测试项，用于验证CIS芯片真随机数生成器(TRNG)的输出质量。

## 测试覆盖

### NIST SP 800-22 (15项)
1. Frequency (Monobit) Test - 单比特频数检测
2. Frequency Test within a Block - 块内频数检测
3. Runs Test - 游程检测
4. Test for Longest Run of Ones - 块内最长游程检测
5. Binary Matrix Rank Test - 二元矩阵秩检测
6. Discrete Fourier Transform Test - 离散傅里叶检测
7. Non-overlapping Template Matching Test - 非重叠模板匹配检测
8. Overlapping Template Matching Test - 重叠模板匹配检测
9. Maurer's Universal Statistical Test - Maurer通用统计检测
10. Linear Complexity Test - 线性复杂度检测
11. Serial Test - 序列检测
12. Approximate Entropy Test - 近似熵检测
13. Cumulative Sums Test - 累加和检测
14. Random Excursions Test - 随机游动检测
15. Random Excursions Variant Test - 随机游动变体检测

### GB/T 32915-2016 补充测试 (3项)
16. Poker Test - 扑克检测
17. Autocorrelation Test - 自相关检测
18. Binary Derivative Test - 二元推导检测

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 或者直接安装
pip install numpy scipy matplotlib
```

## 使用方法

### 1. 准备测试数据

将TRNG输出的二进制数据文件放入 `data/` 目录。

数据格式要求：
- 二进制文件(.bin)或文本文件(.txt)
- 每个文件包含至少 1,000,000 比特
- 建议准备 1000 个文件用于统计分析

### 2. 运行测试

```bash
# 运行完整测试
python main.py --data-dir ./data --output ./reports

# 运行单个文件测试
python main.py --file data/sample.bin --output ./reports

# 指定测试项
python main.py --data-dir ./data --tests nist,gbt
```

### 3. 查看报告

测试完成后，在 `reports/` 目录下会生成：
- `report_YYYYMMDD_HHMMSS.txt` - 文本报告
- `report_YYYYMMDD_HHMMSS.html` - HTML报告（含图表）
- `results_YYYYMMDD_HHMMSS.json` - 详细结果数据

## 项目结构

```
random_test_suite/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖列表
├── README.md              # 本文件
├── config.py              # 配置文件
├── core/                  # 核心测试模块
│   ├── __init__.py
│   ├── nist_tests.py      # NIST SP 800-22 测试实现
│   ├── gbt_tests.py       # GB/T 32915-2016 补充测试
│   └── statistics.py      # 统计分析函数
├── utils/                 # 工具模块
│   ├── __init__.py
│   ├── data_loader.py     # 数据加载器
│   └── report_generator.py # 报告生成器
├── tests/                 # 测试用例
├── data/                  # 测试数据目录
└── reports/               # 测试报告目录
```

## 通过标准

| 指标 | 要求 |
|------|------|
| 单项测试P-value | ≥ 0.01 |
| 总体通过率 | ≥ 98% |
| 测试序列长度 | ≥ 1Mbit/组 |
| 测试序列组数 | ≥ 1000组 |
| 显著性水平 | α = 0.01 |

## 许可证

MIT License
