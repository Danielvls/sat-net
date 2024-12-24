import numpy as np
import matplotlib.pyplot as plt
from scipy.special import i0


# 定义莱斯分布的概率密度函数
def rice_distribution(x, nu, sigma):
    """
    计算莱斯分布的概率密度函数。

    参数:
        x: 随机变量的幅度 (数组)
        nu: 非中心参数 (均值参数)
        sigma: 标准偏差 (噪声强度)
    返回:
        莱斯分布的 PDF 值
    """
    return (x / sigma ** 2) * np.exp(- (x ** 2 + nu ** 2) / (2 * sigma ** 2)) * i0((x * nu) / sigma ** 2)


# 参数设置
sigma = 2  # 标准偏差，方差为4时 sigma = sqrt(4) = 2
nu = 3  # 非中心参数（可调整）

# 定义随机变量 x 的取值范围
x_values = np.linspace(0, 15, 1000)

# 计算莱斯分布的 PDF
pdf_values = rice_distribution(x_values, nu, sigma)

# 绘制莱斯分布的图像
plt.figure(figsize=(8, 6))
plt.plot(x_values, pdf_values, label=rf"Rice Distribution ($\sigma = {sigma}$, $\nu = {nu}$)", color="blue")
plt.xlabel("x (Amplitude)", fontsize=12)
plt.ylabel("Probability Density", fontsize=12)
plt.title("Rice Distribution with Variance = 4", fontsize=14)
plt.grid(True)
plt.legend()
plt.show()
