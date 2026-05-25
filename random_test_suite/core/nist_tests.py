"""
NIST SP 800-22 统计测试套件实现
实现全部15项统计测试
"""

import numpy as np
from scipy import stats
from typing import List, Tuple, Dict
import math


class NISTTestSuite:
    """NIST SP 800-22 统计测试套件"""

    def __init__(self, significance_level: float = 0.01):
        self.alpha = significance_level
        self.test_names = [
            'frequency_monobit',
            'frequency_within_block',
            'runs',
            'longest_run_of_ones',
            'binary_matrix_rank',
            'dft_spectral',
            'non_overlapping_template',
            'overlapping_template',
            'maurers_universal',
            'linear_complexity',
            'serial',
            'approximate_entropy',
            'cumulative_sums',
            'random_excursions',
            'random_excursions_variant'
        ]

    def run_all_tests(self, sequence: List[int]) -> Dict[str, float]:
        """
        执行所有15项测试

        Args:
            sequence: 比特序列 (list of 0/1)

        Returns:
            Dict: 测试名称 -> P-value
        """
        results = {}

        # 确保序列长度足够
        n = len(sequence)
        if n < 100:
            raise ValueError(f"序列长度不足: {n} < 100")

        # 转换为numpy数组提高效率
        bits = np.array(sequence, dtype=np.int8)

        # 执行各项测试
        results['frequency_monobit'] = self.frequency_monobit_test(bits)
        results['frequency_within_block'] = self.frequency_within_block_test(bits)
        results['runs'] = self.runs_test(bits)
        results['longest_run_of_ones'] = self.longest_run_of_ones_test(bits)
        results['binary_matrix_rank'] = self.binary_matrix_rank_test(bits)
        results['dft_spectral'] = self.dft_spectral_test(bits)
        results['non_overlapping_template'] = self.non_overlapping_template_test(bits)
        results['overlapping_template'] = self.overlapping_template_test(bits)
        results['maurers_universal'] = self.maurers_universal_test(bits)
        results['linear_complexity'] = self.linear_complexity_test(bits)

        # serial_test返回Tuple，取第一个值
        serial_result = self.serial_test(bits)
        if isinstance(serial_result, tuple):
            results['serial'] = serial_result[0]
        else:
            results['serial'] = serial_result

        results['approximate_entropy'] = self.approximate_entropy_test(bits)

        # cumulative_sums_test返回Tuple，取最小值
        cusum_result = self.cumulative_sums_test(bits)
        if isinstance(cusum_result, tuple):
            results['cumulative_sums'] = min(cusum_result)
        else:
            results['cumulative_sums'] = cusum_result

        # random_excursions_test返回Dict，取最小值
        re_result = self.random_excursions_test(bits)
        if isinstance(re_result, dict):
            results['random_excursions'] = min(re_result.values())
        else:
            results['random_excursions'] = re_result

        # random_excursions_variant_test返回Dict，取最小值
        rev_result = self.random_excursions_variant_test(bits)
        if isinstance(rev_result, dict):
            results['random_excursions_variant'] = min(rev_result.values())
        else:
            results['random_excursions_variant'] = rev_result

        return results

    def frequency_monobit_test(self, bits: np.ndarray) -> float:
        """
        测试1: 频率测试（单比特）
        检测整个序列中0和1的比例是否接近相等
        """
        n = len(bits)

        # 将0映射为-1，1映射为+1
        S = 2 * bits - 1
        S = np.sum(S)

        # 计算统计量
        s_obs = abs(S) / math.sqrt(n)

        # 计算P-value
        p_value = math.erfc(s_obs / math.sqrt(2))

        return p_value

    def frequency_within_block_test(self, bits: np.ndarray, M: int = 128) -> float:
        """
        测试2: 块内频率测试
        检测固定长度块内0和1的比例是否均匀
        """
        n = len(bits)
        N = n // M  # 块的数量

        if N < 1:
            return 0.0

        # 计算每块中1的比例
        proportions = []
        for i in range(N):
            block = bits[i*M:(i+1)*M]
            proportions.append(np.sum(block) / M)

        # 计算卡方统计量
        chi_squared = 4 * M * sum((p - 0.5)**2 for p in proportions)

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, N)

        return p_value

    def runs_test(self, bits: np.ndarray) -> float:
        """
        测试3: 游程测试
        检测序列中游程的数量是否符合随机预期
        """
        n = len(bits)

        # 计算1的比例
        pi = np.sum(bits) / n

        # 如果比例偏离太大，直接返回0
        if abs(pi - 0.5) >= 2 / math.sqrt(n):
            return 0.0

        # 计算观测的游程数
        V = 1
        for i in range(1, n):
            if bits[i] != bits[i-1]:
                V += 1

        # 计算统计量
        p = pi
        q = 1 - p
        p_value = math.erfc(abs(V - 2*n*p*q) / (2*math.sqrt(2*n)*p*q))

        return p_value

    def longest_run_of_ones_test(self, bits: np.ndarray, M: int = 128) -> float:
        """
        测试4: 块内最长游程测试
        检测块内最长连续1的长度分布是否随机
        """
        n = len(bits)
        N = n // M

        if N < 1:
            return 0.0

        # 定义最长游程的区间
        if M == 8:
            K = 3
            pi = [0.2148, 0.3672, 0.2305, 0.1875]
            boundaries = [1, 2, 3, 4]
        elif M == 128:
            K = 5
            pi = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
            boundaries = [4, 5, 6, 7, 8, 9]
        else:
            K = 5
            pi = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
            boundaries = [4, 5, 6, 7, 8, 9]

        # 统计各区间最长游程的频数
        counts = [0] * (K + 1)
        for i in range(N):
            block = bits[i*M:(i+1)*M]
            max_run = 0
            current_run = 0

            for bit in block:
                if bit == 1:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 0

            # 归类到区间
            for j in range(K + 1):
                if j == 0 and max_run <= boundaries[0]:
                    counts[j] += 1
                    break
                elif j == K and max_run >= boundaries[K]:
                    counts[j] += 1
                    break
                elif j > 0 and boundaries[j-1] < max_run <= boundaries[j]:
                    counts[j] += 1
                    break

        # 计算卡方统计量
        chi_squared = 0
        for i in range(K + 1):
            expected = N * pi[i]
            chi_squared += (counts[i] - expected)**2 / expected

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, K)

        return p_value

    def binary_matrix_rank_test(self, bits: np.ndarray, Q: int = 32) -> float:
        """
        测试5: 二元矩阵秩测试
        检测序列中二元矩阵的秩分布，发现线性依赖关系
        """
        n = len(bits)
        N = n // (Q * Q)

        if N < 1:
            return 0.0

        # 统计满秩、满秩-1和其他的矩阵数
        FM = 0  # 满秩
        FM1 = 0  # 满秩-1
        other = 0

        for i in range(N):
            # 构造Q×Q矩阵
            matrix = bits[i*Q*Q:(i+1)*Q*Q].reshape(Q, Q)

            # 计算秩（在GF(2)上）
            rank = self._gf2_rank(matrix)

            if rank == Q:
                FM += 1
            elif rank == Q - 1:
                FM1 += 1
            else:
                other += 1

        # 计算期望概率
        p1 = 1.0
        for i in range(Q):
            p1 *= (1 - 2**(i-Q))

        p2 = p1 * (1 - 2**(-Q)) * (1 - 2**(-Q+1))
        p3 = 1 - p1 - p2

        # 计算卡方统计量
        chi_squared = ((FM - N*p1)**2 / (N*p1) +
                      (FM1 - N*p2)**2 / (N*p2) +
                      (other - N*p3)**2 / (N*p3))

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, 2)

        return p_value

    def _gf2_rank(self, matrix: np.ndarray) -> int:
        """计算GF(2)上的矩阵秩"""
        m, n = matrix.shape
        rank = 0

        for col in range(n):
            # 找到主元
            pivot = None
            for row in range(rank, m):
                if matrix[row, col] == 1:
                    pivot = row
                    break

            if pivot is None:
                continue

            # 交换行
            matrix[[rank, pivot]] = matrix[[pivot, rank]]

            # 消元
            for row in range(m):
                if row != rank and matrix[row, col] == 1:
                    matrix[row] = (matrix[row] + matrix[rank]) % 2

            rank += 1

        return rank

    def dft_spectral_test(self, bits: np.ndarray) -> float:
        """
        测试6: 离散傅里叶变换（频谱）测试
        检测序列中的周期性特征
        """
        n = len(bits)

        # 将0映射为-1，1映射为+1
        X = 2 * bits - 1

        # 执行FFT
        fft_result = np.fft.fft(X)

        # 计算幅度谱
        magnitudes = np.abs(fft_result[:n//2])

        # 计算阈值
        T = math.sqrt(math.log(1/0.05) * n)

        # 统计超过阈值的峰值数量
        N0 = 0.95 * n / 2
        N1 = np.sum(magnitudes < T)

        # 计算统计量
        d = (N1 - N0) / math.sqrt(n * 0.95 * 0.05 / 4)

        # 计算P-value
        p_value = math.erfc(abs(d) / math.sqrt(2))

        return p_value

    def non_overlapping_template_test(self, bits: np.ndarray, m: int = 9) -> float:
        """
        测试7: 非重叠模板匹配测试
        检测特定二元模板的出现频率
        """
        n = len(bits)

        # 使用模板 B = 100000000 (m=9)
        template = np.array([1] + [0]*(m-1), dtype=np.int8)

        # 统计非重叠匹配次数
        count = 0
        i = 0
        while i <= n - m:
            if np.array_equal(bits[i:i+m], template):
                count += 1
                i += m
            else:
                i += 1

        # 计算期望值和方差
        N = n // m
        mu = (N - m + 1) / 2**m
        sigma2 = N * (1/2**m - (2*m-1)/2**(2*m))

        if sigma2 <= 0:
            return 0.0

        # 计算统计量
        chi_squared = (count - mu)**2 / sigma2

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, 1)

        return p_value

    def overlapping_template_test(self, bits: np.ndarray, m: int = 9) -> float:
        """
        测试8: 重叠模板匹配测试
        检测重叠模式的出现频率
        """
        n = len(bits)

        # 使用模板 B = 111111111 (m=9)
        template = np.ones(m, dtype=np.int8)

        # 统计重叠匹配次数
        count = 0
        for i in range(n - m + 1):
            if np.array_equal(bits[i:i+m], template):
                count += 1

        # 计算期望值
        mu = (n - m + 1) / 2**m

        # 使用泊松近似
        if mu < 5:
            # 使用精确分布
            p_value = 1 - stats.poisson.cdf(count, mu)
        else:
            # 使用正态近似
            z = (count - mu) / math.sqrt(mu)
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))

        return p_value

    def maurers_universal_test(self, bits: np.ndarray, L: int = 7, Q: int = 1280) -> float:
        """
        测试9: Maurer通用统计测试
        检测序列是否可以被显著压缩
        """
        n = len(bits)

        # 检查序列长度
        if n < (Q + 1) * L:
            return 0.0

        K = n // L - Q

        # 初始化表
        table = {}

        # 初始化阶段
        for i in range(Q):
            block = tuple(bits[i*L:(i+1)*L])
            table[block] = i + 1

        # 测试阶段
        sum_val = 0
        for i in range(Q, Q + K):
            block = tuple(bits[i*L:(i+1)*L])
            if block in table:
                sum_val += math.log2(i + 1 - table[block])
            else:
                sum_val += math.log2(i + 1)
            table[block] = i + 1

        # 计算统计量
        fn = sum_val / K

        # 期望值和方差（预计算的表）
        expected = [0, 0, 0, 0, 0, 0, 0, 5.2177052, 6.1962507, 7.1836656,
                    8.1764248, 9.1723243, 10.170032, 11.168765, 12.168070,
                    13.167693, 14.167488, 15.167379]
        variance = [0, 0, 0, 0, 0, 0, 0, 2.954, 3.125, 3.238,
                   3.311, 3.356, 3.384, 3.401, 3.410, 3.416, 3.419, 3.421]

        if L < 6 or L > 16:
            return 0.0

        # 计算统计量
        c = 0.7 - 0.8/L + (4 + 32/L) * K**(-3/L) / 15
        sigma = c * math.sqrt(variance[L] / K)

        z = (fn - expected[L]) / sigma

        # 计算P-value
        p_value = math.erfc(abs(z) / math.sqrt(2))

        return p_value

    def linear_complexity_test(self, bits: np.ndarray, M: int = 500) -> float:
        """
        测试10: 线性复杂度测试
        检测序列是否可由较短的线性反馈移位寄存器生成
        """
        n = len(bits)
        N = n // M

        if N < 1:
            return 0.0

        # 计算每块的线性复杂度
        complexities = []
        for i in range(N):
            block = bits[i*M:(i+1)*M]
            lc = self._berlekamp_massey(block)
            complexities.append(lc)

        # 计算期望值
        mu = M / 2 + (9 + (-1)**(M+1)) / 18

        # 计算卡方统计量
        chi_squared = 0
        for lc in complexities:
            T = (-1)**M * (lc - mu) + 2/9
            chi_squared += T * T

        chi_squared *= 9 / M

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, N)

        return p_value

    def _berlekamp_massey(self, sequence: np.ndarray) -> int:
        """Berlekamp-Massey算法计算线性复杂度"""
        n = len(sequence)

        # 初始化
        C = np.zeros(n, dtype=np.int8)
        B = np.zeros(n, dtype=np.int8)
        C[0] = 1
        B[0] = 1

        L = 0
        m = 1
        b = 1

        for i in range(n):
            # 计算差异
            d = sequence[i]
            for j in range(1, L + 1):
                d ^= C[j] & sequence[i - j]

            if d == 0:
                m += 1
            else:
                T = C.copy()

                # 更新C
                for j in range(i - m + 1):
                    if B[j] == 1:
                        C[j + m] ^= 1

                if 2 * L <= i:
                    L = i + 1 - L
                    B = T
                    b = d
                    m = 1
                else:
                    m += 1

        return L

    def serial_test(self, bits: np.ndarray, m: int = 16) -> Tuple[float, float, float]:
        """
        测试11: 序列测试
        检测所有可能的m位模式的出现频率是否均匀

        Returns:
            Tuple: (P-value_1, P-value_2, P-value_delta)
        """
        n = len(bits)

        # 扩展序列以处理循环
        extended = np.concatenate([bits, bits[:m-1]])

        # 统计所有m位模式的出现次数
        counts = {}
        for i in range(n):
            pattern = tuple(extended[i:i+m])
            counts[pattern] = counts.get(pattern, 0) + 1

        # 计算卡方统计量
        expected = n / 2**m
        chi2_m = sum((count - expected)**2 for count in counts.values()) / expected

        # 计算m-1位模式
        counts_m1 = {}
        for i in range(n):
            pattern = tuple(extended[i:i+m-1])
            counts_m1[pattern] = counts_m1.get(pattern, 0) + 1

        expected_m1 = n / 2**(m-1)
        chi2_m1 = sum((count - expected_m1)**2 for count in counts_m1.values()) / expected_m1

        # 计算m-2位模式
        counts_m2 = {}
        for i in range(n):
            pattern = tuple(extended[i:i+m-2])
            counts_m2[pattern] = counts_m2.get(pattern, 0) + 1

        expected_m2 = n / 2**(m-2)
        chi2_m2 = sum((count - expected_m2)**2 for count in counts_m2.values()) / expected_m2

        # 计算P-value
        p1 = 1 - stats.chi2.cdf(chi2_m, 2**m - 1)
        p2 = 1 - stats.chi2.cdf(chi2_m1, 2**(m-1) - 1)
        p3 = 1 - stats.chi2.cdf(chi2_m - chi2_m1, 2**(m-1))

        return p1, p2, p3

    def approximate_entropy_test(self, bits: np.ndarray, m: int = 10) -> float:
        """
        测试12: 近似熵测试
        检测序列的熵值是否符合随机预期
        """
        n = len(bits)

        def count_patterns(pattern_length):
            """统计指定长度模式的出现次数"""
            counts = {}
            extended = np.concatenate([bits, bits[:pattern_length-1]])

            for i in range(n):
                pattern = tuple(extended[i:i+pattern_length])
                counts[pattern] = counts.get(pattern, 0) + 1

            return counts

        # 统计m位和m+1位模式
        counts_m = count_patterns(m)
        counts_m1 = count_patterns(m + 1)

        # 计算近似熵
        def calc_phi(counts):
            total = sum(counts.values())
            phi = 0
            for count in counts.values():
                if count > 0:
                    p = count / total
                    phi += p * math.log(p)
            return phi

        phi_m = calc_phi(counts_m)
        phi_m1 = calc_phi(counts_m1)

        apen = phi_m - phi_m1

        # 计算卡方统计量
        chi_squared = 2 * n * (math.log(2) - apen)

        # 计算P-value
        p_value = 1 - stats.chi2.cdf(chi_squared, 2**m)

        return p_value

    def cumulative_sums_test(self, bits: np.ndarray) -> Tuple[float, float]:
        """
        测试13: 累积和测试
        检测序列中偏移的最大累积和是否异常

        Returns:
            Tuple: (P-value_forward, P-value_backward)
        """
        n = len(bits)

        # 将0映射为-1，1映射为+1
        S = 2 * bits - 1

        # 计算累积和
        cumulative = np.cumsum(S)

        # 正向最大累积和
        z_forward = np.max(np.abs(cumulative))

        # 反向最大累积和
        z_backward = np.max(np.abs(np.cumsum(S[::-1])))

        # 计算P-value（使用正态近似）
        def calc_pvalue(z):
            # 使用经验公式
            p = 0
            for k in range(-int(n/z) - 1, int(n/z) + 2):
                term1 = stats.norm.cdf((4*k+1)*z/math.sqrt(n))
                term2 = stats.norm.cdf((4*k-1)*z/math.sqrt(n))
                p += term1 - term2
            return min(max(p, 0), 1)

        p_forward = calc_pvalue(z_forward)
        p_backward = calc_pvalue(z_backward)

        return p_forward, p_backward

    def random_excursions_test(self, bits: np.ndarray) -> Dict[int, float]:
        """
        测试14: 随机游程测试
        检测循环随机游程中各状态的访问次数

        Returns:
            Dict: 状态 -> P-value
        """
        n = len(bits)

        # 将0映射为-1，1映射为+1
        X = 2 * bits - 1

        # 计算累积和（添加0作为起点）
        cumulative = np.concatenate([[0], np.cumsum(X)])

        # 找到循环（返回0的时刻）
        cycles = []
        cycle_start = 0

        for i in range(1, len(cumulative)):
            if cumulative[i] == 0:
                if i > cycle_start + 1:
                    cycles.append(cumulative[cycle_start:i+1])
                cycle_start = i

        # 如果没有完整的循环
        if len(cycles) < 1:
            return {state: 1.0 for state in range(-4, 5) if state != 0}

        # 统计各状态的访问次数
        states = [-4, -3, -2, -1, 1, 2, 3, 4]
        visit_counts = {state: 0 for state in states}

        for cycle in cycles:
            for state in states:
                visit_counts[state] += np.sum(cycle == state)

        # 计算期望值
        pi = {
            -4: 0.0278, -3: 0.0625, -2: 0.1250, -1: 0.2500,
            1: 0.2500, 2: 0.1250, 3: 0.0625, 4: 0.0278
        }

        # 计算卡方统计量
        J = len(cycles)
        p_values = {}

        for state in states:
            expected = J * pi[state]
            if expected > 0:
                chi_squared = (visit_counts[state] - expected)**2 / expected
                p_values[state] = 1 - stats.chi2.cdf(chi_squared, 1)
            else:
                p_values[state] = 1.0

        # 返回最小的P-value
        return min(p_values.values())

    def random_excursions_variant_test(self, bits: np.ndarray) -> Dict[int, float]:
        """
        测试15: 随机游程变体测试
        检测随机游程中特定状态的访问次数

        Returns:
            Dict: 状态 -> P-value
        """
        n = len(bits)

        # 将0映射为-1，1映射为+1
        X = 2 * bits - 1

        # 计算累积和
        cumulative = np.concatenate([[0], np.cumsum(X)])

        # 统计各状态的访问次数
        states = list(range(-9, 10))
        states.remove(0)

        visit_counts = {}
        for state in states:
            visit_counts[state] = np.sum(cumulative == state)

        # 计算P-value
        p_values = {}
        for state in states:
            # 使用正态近似
            expected = 2 * (abs(state) + 1)  # 简化的期望值
            z = (visit_counts[state] - expected) / math.sqrt(expected)
            p_values[state] = 2 * (1 - stats.norm.cdf(abs(z)))

        # 返回最小的P-value
        return min(p_values.values())
