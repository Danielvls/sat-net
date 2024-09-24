import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import json
from src.utils.counter import Counter
from scipy.ndimage import gaussian_filter
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

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

    def plot_satellite_usage_heatmap(self, bins=100, sigma=10):
        lats = [sat['latitude'] for sat in self.satellite_positions]
        lons = [sat['longitude'] for sat in self.satellite_positions]
        weights = [self.satellite_usage.get(sat['id'], 0) for sat in self.satellite_positions]

        heatmap, xedges, yedges = np.histogram2d(
            lats, lons, bins=bins, range=[[-90, 90], [-180, 180]], weights=weights
        )
        heatmap_smooth = gaussian_filter(heatmap, sigma=sigma)

        plt.figure(figsize=(15, 10), dpi=300)
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(cfeature.OCEAN.with_scale('50m'), zorder=0, facecolor='lightblue')
        ax.add_feature(cfeature.LAND.with_scale('50m'), zorder=0, facecolor='beige')
        ax.coastlines(resolution='50m')
        ax.add_feature(cfeature.BORDERS.with_scale('50m'))

        extent = [-180, 180, -90, 90]
        plt.imshow(
            heatmap_smooth,
            cmap='coolwarm',
            alpha=0.6,
            origin='lower',
            extent=extent,
            transform=ccrs.PlateCarree()
        )

        # 绘制卫星点
        ax.scatter(
            lons, lats, color='black', edgecolor='white', s=100, zorder=5, marker='o', label='Satellites',
            transform=ccrs.PlateCarree()
        )

        # 使用卫星的实际 ID 作为标签
        for sat in self.satellite_positions:
            lon = sat['longitude']
            lat = sat['latitude']
            sat_id = sat['id']
            ax.text(lon + 2, lat + 2, sat_id, color='black', fontsize=9, transform=ccrs.PlateCarree())

        # 添加地面站
        facility_data = [
            ("Facility1", 28.62, -80.62, 10.0),  # 美国佛罗里达州
            ("Facility2", 34.30, 108.95, 400.0),  # 中国西安卫星测控中心
            ("Facility3", -23.80, 133.89, 600.0),  # 澳大利亚艾丽斯泉地面站
            ("Facility4", 47.83, 11.14, 600.0)  # 德国魏尔海姆跟踪站
        ]

        # 提取地面站的经纬度
        facility_lats = [facility[1] for facility in facility_data]
        facility_lons = [facility[2] for facility in facility_data]

        # 使用三角形标出地面站
        ax.scatter(
            facility_lons, facility_lats, color='red', s=150, marker='^', label='Facilities',
            transform=ccrs.PlateCarree()
        )

        # 设置经纬度刻度
        ax.set_xticks(np.arange(-180, 181, 60), crs=ccrs.PlateCarree())
        ax.set_yticks(np.arange(-90, 91, 30), crs=ccrs.PlateCarree())

        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())

        # 添加颜色条
        plt.colorbar(label="Satellite Usage")

        # 添加图例
        ax.legend(loc='upper right')
        plt.title("Satellite Usage Heatmap with Facilities")
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
