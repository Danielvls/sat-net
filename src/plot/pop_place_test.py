import pandas as pd
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.ticker as mticker  # Added for custom gridline locators
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.stats import gaussian_kde  # Import Gaussian KDE for density estimation
from matplotlib.ticker import ScalarFormatter

# Get the current file path and locate the project root directory
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]

# File paths
file_path_city = project_root / 'data' / 'worldcities.csv'
file_path_internet = project_root / 'data' / 'world_internet_user_origin.csv'

# Load city data with geographic information and internet usage data
city_data = pd.read_csv(file_path_city)
internet_data = pd.read_csv(file_path_internet, encoding='ISO-8859-1')

# Extract relevant columns: city, country, population, latitude, and longitude
city_country_population = city_data[['city', 'country', 'population', 'lat', 'lng']].copy()

# Extract internet usage information: country and internet usage percentage
internet_usage = internet_data[['Country', '% of Population']].copy()

# Rename columns for clarity
internet_usage = internet_usage.rename(columns={'% of Population': 'InternetUsagePercentage'})
city_country_population = city_country_population.rename(
    columns={
        'city': 'City',
        'country': 'Country',
        'population': 'Population',
        'lat': 'Latitude',
        'lng': 'Longitude'
    }
)

# Merge city population data with internet usage data
merged_data = pd.merge(city_country_population, internet_usage, on='Country', how='left')

# Drop rows with NaN values in Population or InternetUsagePercentage
cleaned_data = merged_data.dropna(subset=['Population', 'InternetUsagePercentage']).copy()

# Add a new column for the number of internet users
cleaned_data['InternetUsers'] = cleaned_data['Population'] * (cleaned_data['InternetUsagePercentage'] / 100)

# Optionally apply logarithmic transformation to InternetUsers
# To avoid log(0), add a small constant, e.g., 1
# cleaned_data['LogInternetUsers'] = np.log(cleaned_data['InternetUsers'] + 1)
# weights = cleaned_data['LogInternetUsers']

# Prepare data for Kernel Density Estimation (KDE)
positions = np.vstack([cleaned_data['Longitude'], cleaned_data['Latitude']])
weights = cleaned_data['InternetUsers']  # Using the original InternetUsers

# Increase KDE bandwidth parameter to expand heat zones
kde = gaussian_kde(positions, weights=weights, bw_method=0.1)

# Create grid coordinates for evaluation, adjust resolution
grid_size = 200  # Adjust as needed to balance speed and detail
lon_grid = np.linspace(-180, 180, grid_size*2)
lat_grid = np.linspace(-90, 90, grid_size)


lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
grid_positions = np.vstack([lon_mesh.ravel(), lat_mesh.ravel()])

# Evaluate KDE on the grid
density = kde(grid_positions).reshape(lon_mesh.shape)

# Mask zero densities and normalize
density_masked = np.ma.masked_where(density == 0, density)
vmax = density_masked.max() / 3  # Reduce vmax to enhance low-density areas
norm = colors.Normalize(vmax=vmax)

# Set up the map projection and create a figure
fig = plt.figure(figsize=(15, 10))
ax = plt.axes(projection=ccrs.Robinson())

# Add map features with higher resolution (50m)
ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='lightgray')
ax.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='lightgray')
ax.add_feature(cfeature.COASTLINE.with_scale('50m'))
ax.add_feature(cfeature.BORDERS.with_scale('50m'), linestyle=':')

# Ensure the map extent is set correctly to [-180, 180] and [-90, 90]
ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())

# Plot the heatmap using imshow
img = ax.imshow(
    density_masked,
    extent=[-180, 180, -90, 90],
    cmap='afmhot',
    alpha=0.7,
    origin='lower',
    norm=norm,
    transform=ccrs.PlateCarree(),
    zorder=1
)

# img = ax.pcolormesh(
#     lon_mesh, lat_mesh, density_masked,
#     cmap='hot', alpha=0.8,
#     transform=ccrs.PlateCarree(),  # 使用 PlateCarree 进行经纬度数据的转换
#     shading='auto'
# )

# Add scatter plot of cities (dots only)
ax.scatter(
    cleaned_data['Longitude'],
    cleaned_data['Latitude'],
    s=1,  # Set fixed size for smaller points
    color='black',
    alpha=0.2,
    marker='.',  # Use dot marker
    transform=ccrs.PlateCarree(),
    label='Cities',
    zorder=2
)

# Add a colorbar on the right side of the image
cbar = plt.colorbar(img, ax=ax, orientation='vertical', pad=0.02, fraction=0.05, aspect=10)
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((0, 0))  # 强制使用科学计数法
cbar.ax.yaxis.set_major_formatter(formatter)

# cbar.ax.yaxis.get_offset_text().set_position((1.1, 0))  # 调整偏移文本位置

# cbar.set_label('Estimated Number of Internet Users')

# Add gridlines and labels
gl = ax.gridlines(
    draw_labels=True,
    linewidth=0.5,
    color='gray',
    alpha=0.5,
    linestyle='--'
)

gl.top_labels = False  # 关闭顶部的经度标签
gl.right_labels = False  # 关闭右侧的纬度标签

# Set the title
# ax.set_title('Global Internet Users Heatmap with City Locations')

# Add legend
plt.legend(loc='lower left')

# Show the plot
plt.show()
plt.savefig('heatmap_with_city_locations_afmhot.png', dpi=300)