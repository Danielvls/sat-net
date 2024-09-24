import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from scipy.ndimage import gaussian_filter
# 导入Cartopy专门提供的经纬度的Formatter
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

# 卫星数据及其随机权重
satellites = [
    {"latitude": 5.989706585538288, "longitude": 169.04144363879965, "id": "Sat11", "weight": np.random.uniform(0.1, 1.0)},
    {"latitude": 38.83193495956897, "longitude": 169.04154764878922, "id": "Sat12", "weight": np.random.uniform(0.1, 1.0)},
    {"latitude": 11.45617480600666, "longitude": -160.9472200601379, "id": "Sat21", "weight": np.random.uniform(0.1, 1.0)},
    {"latitude": 71.50331976126108, "longitude": 169.0418722022911, "id": "Sat13", "weight": np.random.uniform(0.1, 1.0)},
    {"latitude": 44.27470970649282, "longitude": -160.90377354501797, "id": "Sat22", "weight": np.random.uniform(0.1, 1.0)},
    {"latitude": 75.9300137339148, "longitude": -10.95916479862613, "id": "Sat14", "weight": np.random.uniform(0.1, 1.0)}
]

# 提取经纬度和权重数据
lats = [sat['latitude'] for sat in satellites]
lons = [sat['longitude'] for sat in satellites]
weights = [sat['weight'] for sat in satellites]

# 创建更精细的热力图网格
lon_grid = np.linspace(-180, 180, 720)  # 将经度网格数量增加到720个（每0.5度一个点）
lat_grid = np.linspace(-90, 90, 360)    # 将纬度网格数量增加到360个（每0.5度一个点）
heatmap, xedges, yedges = np.histogram2d(lats, lons, bins=[lat_grid, lon_grid], weights=weights)

# 应用不同纬度和经度方向的高斯模糊，使经度模糊是纬度模糊的两倍
heatmap_smooth = gaussian_filter(heatmap, sigma=(2, 8))  # 纬度模糊为1，经度模糊为2


# 创建 PlateCarree 投影地图
fig = plt.figure(figsize=(15, 10), dpi=300)  # 15x10 英寸的图像，300 DPI 高分辨率
ax = plt.axes(projection=ccrs.PlateCarree())

# 添加50m分辨率的地理特征
ax.coastlines(resolution='50m')  # 使用50m分辨率的海岸线
ax.add_feature(cfeature.BORDERS.with_scale('50m'))  # 添加50m分辨率的国界线
ax.add_feature(cfeature.OCEAN.with_scale('50m'))  # 添加50m分辨率的海洋
ax.add_feature(cfeature.LAND.with_scale('50m'))  # 添加50m分辨率的陆地

# 绘制热力图
extent = [-180, 180, -90, 90]
plt.imshow(heatmap_smooth.T, extent=extent, cmap='YlOrRd', alpha=0.7, transform=ccrs.PlateCarree())

# 设置大刻度和小刻度
tick_proj = ccrs.PlateCarree()
ax.set_xticks(np.arange(-180, 180 + 60, 60), crs=tick_proj)
ax.set_xticks(np.arange(-180, 180 + 30, 30), minor=True, crs=tick_proj)
ax.set_yticks(np.arange(-90, 90 + 30, 30), crs=tick_proj)
ax.set_yticks(np.arange(-90, 90 + 15, 15), minor=True, crs=tick_proj)

# 利用Formatter格式化刻度标签
ax.xaxis.set_major_formatter(LongitudeFormatter())
ax.yaxis.set_major_formatter(LatitudeFormatter())

# 显示地图
plt.title("50m")
plt.show()
