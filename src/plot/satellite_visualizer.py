import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import json
from src.utils.counter import Counter
# from scipy.ndimage import gaussian_filter
from scipy.stats import gaussian_kde
from scipy.ndimage import gaussian_filter
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter, MaxNLocator
import re
import numpy as np
from src.utils.sim_config import num_orbit_planes, num_sat_per_plane
import seaborn as sns
import geopandas as gpd
import pandas as pd
import cartopy.crs as ccrs
import matplotlib.colors as mcolors


class SatelliteVisualizer:
    def __init__(self, satellite_usage=None):
        self.counter = Counter()
        if satellite_usage is None:
            self.satellite_usage = self.counter.get_node_usage()  # 从 Counter 获取卫星使用情况
        else:
            self.satellite_usage = satellite_usage  # 或者使用传入的 satellite_usage
        print("satellite_usage:", self.satellite_usage)
        self.satellite_positions = self._get_all_satellite_positions()

    def _get_all_satellite_positions(self):
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[2]
        graph_path = project_root / 'graphs'

        satellite_positions = {}
        graph_files = list(graph_path.glob('graph0.json'))
        if not graph_files:
            raise FileNotFoundError(f"在路径 {graph_path} 下未找到 'graph*.json' 文件。")
        for graph_file in graph_files:
            satellite_coords = self._load_satellite_data(graph_file)
            for sat in satellite_coords:
                satellite_positions[sat['id']] = sat  # 使用卫星 ID 去重
        print("satellite_positions:", satellite_positions)
        return list(satellite_positions.values())

    @staticmethod
    def _load_satellite_data(graph_file_path):
        with open(graph_file_path, 'r') as f:
            satellite_data = json.load(f)
        satellite_coords = []
        for node in satellite_data['nodes']:
            if 'latitude' in node and 'longitude' in node:
                satellite_coords.append({
                    'id': node['id'],
                    'latitude': node['latitude'],
                    'longitude': node['longitude']
                })
        return satellite_coords

    def plot_satellite_usage_heatmap(self,  bins=100, sigma=5):
        lats = [sat['latitude'] for sat in self.satellite_positions]
        lons = [sat['longitude'] for sat in self.satellite_positions]
        weights = [self.satellite_usage.get(sat['id'], 0) for sat in self.satellite_positions]

        heatmap, xedges, yedges = np.histogram2d(
            lats, lons, bins=bins, range=[[-90, 90], [-180, 180]], weights=weights
        )
        heatmap_smooth = gaussian_filter(heatmap, sigma=sigma)

        plt.figure(figsize=(15, 10), dpi=300)
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.OCEAN.with_scale('50m'), zorder=0, facecolor='lightgrey')
        ax.add_feature(cfeature.LAND.with_scale('50m'), zorder=0, facecolor='lightgrey')
        ax.coastlines(resolution='50m')
        ax.add_feature(cfeature.BORDERS.with_scale('50m'))

        extent = [-180, 180, -90, 90]
        plt.imshow(
            heatmap_smooth,
            cmap='afmhot',
            alpha=0.7,
            origin='lower',
            extent=extent,
            transform=ccrs.PlateCarree()
        )


        ax.scatter(
            lons, lats, color='black', edgecolor='white', s=100, zorder=5, marker='o', label='Satellites',
            transform=ccrs.PlateCarree()
        )

        # Iteration of orbits and satellite serial numbers
        for orbit_num in range(1, num_orbit_planes + 1):
            satellites_in_orbit = {}
            for sat in self.satellite_positions:
                sat_id = sat['id']
                num = int(re.search(r'\d+', sat_id).group())
                current_orbit_num = num // 100 if num >= 100 else num // 10
                sequence_num = num % 100 if num >= 100 else num % 10

                if current_orbit_num == orbit_num:
                    satellites_in_orbit[sequence_num] = sat

            # start 1
            seq_nums = sorted(satellites_in_orbit.keys())

            for i in range(num_sat_per_plane):
                # get next satellite
                current_seq = seq_nums[i]
                current_sat = satellites_in_orbit[current_seq]
                next_seq = seq_nums[(i + 1) % num_sat_per_plane]
                next_sat = satellites_in_orbit[next_seq]

                current_lon = current_sat['longitude']
                current_lat = current_sat['latitude']
                next_lon = next_sat['longitude']
                next_lat = next_sat['latitude']

                # calculate 2d distance
                distance = np.sqrt((next_lon - current_lon) ** 2 + (next_lat - current_lat) ** 2)

                # if the distance is too large, use the previous satellite
                if distance > 50:
                    prev_seq = seq_nums[i - 1] if i > 1 else seq_nums[-1]
                    prev_sat = satellites_in_orbit[prev_seq]

                    next_lon = current_lon - (prev_sat['longitude'] - current_lon)
                    next_lat = current_lat - (prev_sat['latitude'] - current_lat)

                # 计算箭头的终点，保持定长
                arrow_length = 10  # 定义箭头长度
                direction_lon = next_lon - current_lon
                direction_lat = next_lat - current_lat
                length = np.sqrt(direction_lon ** 2 + direction_lat ** 2)

                if length > 0:
                    unit_lon = direction_lon / length
                    unit_lat = direction_lat / length
                    arrow_end_lon = current_lon + unit_lon * arrow_length
                    arrow_end_lat = current_lat + unit_lat * arrow_length
                else:
                    arrow_end_lon = current_lon
                    arrow_end_lat = current_lat

                # 绘制箭头
                ax.annotate(
                    '',
                    xy=(arrow_end_lon, arrow_end_lat),
                    xytext=(current_lon, current_lat),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
                    transform=ccrs.PlateCarree()
                )

                ax.text(current_lon + 2, current_lat + 2, current_sat['id'], color='black', fontsize=9,
                        transform=ccrs.PlateCarree())

        # 添加地面站
        facility_data = [
            ("Facility1", 28.62, -80.62, 10.0),
            ("Facility2", 34.30, 108.95, 400.0),
            ("Facility3", -23.80, 133.89, 600.0),
            ("Facility4", 47.83, 11.14, 600.0)
        ]

        facility_lats = [facility[1] for facility in facility_data]
        facility_lons = [facility[2] for facility in facility_data]

        ax.scatter(
            facility_lons, facility_lats, color='red', s=150, marker='^', label='Facilities',
            transform=ccrs.PlateCarree()
        )

        ax.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
        ax.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())

        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())

        plt.colorbar(label="Satellite Usage", fraction=0.03, pad=0.04, aspect=15)
        ax.legend(loc='upper right')
        # plt.title("Satellite Usage Heatmap with Facilities")
        plt.savefig('satellite_usage_heatmap.png', dpi=600, bbox_inches='tight')
        plt.show()

    def plot_user_heatmap(self):
        # Create a figure
        fig, ax = plt.subplots(figsize=(15, 10), dpi=300, subplot_kw={'projection': ccrs.PlateCarree()})

        # Configure the background
        ax.add_feature(cfeature.OCEAN.with_scale('50m'), zorder=0)
        ax.add_feature(cfeature.LAND.with_scale('50m'), zorder=0)
        ax.coastlines(resolution='50m')
        ax.add_feature(cfeature.BORDERS.with_scale('50m'))

        # Get user points
        user_points = self.counter.get_user_points()

        # Extract latitude and longitude from user points
        user_lons = [point[0] for point in user_points]
        user_lats = [point[1] for point in user_points]
        df = pd.DataFrame({'lon': user_lons, 'lat': user_lats})

        # Create a DataFrame
        gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(df.lon, df.lat)
        )

        # Plot KDE
        # 使用Kernel Density Estimation (KDE) plot来绘制地理空间点的密度图
        norm = mcolors.PowerNorm(gamma=1)
        sns.kdeplot(
            x=gdf.geometry.x,  # 提供点的x坐标（经度）
            y=gdf.geometry.y,  # 提供点的y坐标（纬度）
            alpha=0.7,
            cmap='coolwarm',  # 使用从冷到暖的颜色映射以表示密度的变化
            fill=True,  # 使用 fill 代替 shade，填充整个分布区域以提高可读性
            ax=ax,  # 在指定的子图轴上绘制
            # thresh=0,  # 使用 thresh 代替 shade_lowest，设定密度阈值，低于该阈值的区域将不被绘制
            bw_method=0.3,  # 指定带宽调整因子，较小的值产生更细致的密度估计
            levels=50,  # 设定等高线的级别数量，表示密度的不同层次
            cbar=True,  # 显示颜色条以指示密度的变化
            cbar_kws={
                'label': 'Density',
                'orientation': 'horizontal',
                'shrink': 0.8,
                'extend': 'both'  # 扩展颜色条，使其包括超出数据范围的部分

            },
            norm=norm
        )

        # Mark user points
        ax.scatter(
            user_lons, user_lats,
            color='black', s=10, marker='o', label='User Points', transform=ccrs.PlateCarree()
        )

        # Add facilities
        facility_data = [
            ("Facility1", 28.62, -80.62, 10.0),
            ("Facility2", 34.30, 108.95, 400.0),
            ("Facility3", -23.80, 133.89, 600.0),
            ("Facility4", 47.83, 11.14, 600.0)
        ]
        facility_lats = [facility[1] for facility in facility_data]
        facility_lons = [facility[2] for facility in facility_data]

        ax.scatter(
            facility_lons, facility_lats, color='red', s=150, marker='^', label='Facilities',
            transform=ccrs.PlateCarree()
        )

        # Add ticks using MaxNLocator for better handling
        # ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both'))
        # ax.yaxis.set_major_locator(MaxNLocator(integer=True, prune='both'))

        ax.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
        ax.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())

        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.tick_params(labelbottom=True, labelleft=True)
        # ax.gridlines(draw_labels=False, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')

        ax.legend(loc='upper right')
        plt.savefig('world_user_heatmap.png', dpi=1000, bbox_inches='tight')
        plt.show()

if __name__ == '__main__':
    satellite_usage = {
        'Sat11': 10,
        'Sat12': 15,
        'Sat13': 8,
        'Sat14': 20,
        'Sat21': 5,
        'Sat22': 12,
    }
    visualizer = SatelliteVisualizer(satellite_usage)
    visualizer.plot_satellite_usage_heatmap()
