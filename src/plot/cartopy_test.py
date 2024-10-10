import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import cartopy.crs as ccrs
import seaborn as sns

# 创建示例数据
np.random.seed(0)
n_points = 100
lon = np.random.uniform(-100, -70, n_points)
lat = np.random.uniform(20, 50, n_points)
df = pd.DataFrame({'lon': lon, 'lat': lat})
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))

# 设置绘图
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})

# 使用seaborn的kdeplot绘制KDE
sns.kdeplot(x=gdf.geometry.x, y=gdf.geometry.y, cmap='Reds', fill=True, ax=ax)

# 添加背景地图
ctx.add_basemap(ax, crs=ccrs.PlateCarree())

# 设置坐标轴
ax.set_title('KDE Plot Example with PlateCarree Projection')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

plt.show()
