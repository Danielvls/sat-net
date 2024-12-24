import numpy as np
from scipy.integrate import quad
from scipy.special import i0  # 修正的第一类零阶贝塞尔函数
import math


# 定义被积函数
def integrand(theta_T, sigma, phi):
    """
    计算积分中的被积函数值。

    参数:
        theta_T: 当前积分变量
        sigma: 标准偏差
        phi: 偏置角度

    返回:
        被积函数的值
    """
    # 指数项
    exponent = -(theta_T + 53.58 * phi ** 2) / (107.16 * sigma ** 2)

    # 贝塞尔函数输入
    bessel_input = (theta_T * phi) / (7.32 * sigma ** 2)

    # 避免指数项 underflow
    if exponent < -700:
        return 0

    # 计算被积函数值
    return np.exp(exponent) * i0(bessel_input)
    # return np.exp(exponent)


# 参数设置
sigma = 3e-6  # 标准偏差 (3 μrad -> rad)
phi = 2e-6  # 偏置角度 (2 μrad -> rad)

# 积分上下限：从 1 μrad 到有限的 100 μrad，避免无穷大问题
lower_limit = 3e-6  # 1 μrad
upper_limit = 100e-6  # 100 μrad

# 执行积分
try:
    P_outage, error = quad(integrand, lower_limit, upper_limit, args=(sigma, phi))
    print(f"P_outage 结果: {P_outage:.5e}")
    print(f"积分误差: {error:.2e}")
except Exception as e:
    print("计算过程中出现错误:", e)
