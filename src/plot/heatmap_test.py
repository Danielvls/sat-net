import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from matplotlib import ticker
from matplotlib.colors import LogNorm

# 创建地图
fig, ax = plt.subplots(figsize=(10, 6))

# 设置地图投影
m = Basemap(projection='cyl', resolution='c', ax=ax)
m.drawcoastlines()

# 绘制一些示例数据（这里使用随机数据代替原始图像数据）
lons = np.linspace(-180, 180, 360)
lats = np.linspace(-90, 90, 180)
lon, lat = np.meshgrid(lons, lats)
data = np.random.rand(180, 360) * 1e6

# 绘制数据，使用 logarithmic normalization 来模拟您的 colorbar
pcm = m.pcolormesh(lon, lat, data, norm=LogNorm(), cmap='hot')

# 添加 colorbar 并设置为科学计数法
cb = m.colorbar(pcm, location='right', pad="5%")
cb.ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
cb.ax.yaxis.get_offset_text().set_position((1.1, 0))

# 设置纬度刻度，确保包括90°
ax.set_yticks(np.arange(-90, 91, 30))
ax.set_yticklabels([f'{lat}°N' if lat > 0 else (f'{-lat}°S' if lat < 0 else '0°') for lat in np.arange(-90, 91, 30)])

plt.show()
