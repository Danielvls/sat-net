import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Get the current file path and locate the project root directory
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]

# File paths
file_path_city = project_root / 'data' / 'worldcities.csv'
file_path_internet = project_root / 'data' / 'world_internet_user_origin.csv'

# Load city data with geographic info and internet usage data
city_data = pd.read_csv(file_path_city)
internet_data = pd.read_csv(file_path_internet, encoding='ISO-8859-1')

# Extract relevant columns: city, country, population, latitude, and longitude
city_country_population = city_data[['city', 'country', 'population', 'lat', 'lng']].copy()

# Extract internet usage information: country and internet usage percentage
internet_usage = internet_data[['Country', '% of Population']].copy()

# Rename columns by creating new DataFrames, avoiding in-place operations
internet_usage = internet_usage.rename(columns={'% of Population': 'InternetUsagePercentage'})
city_country_population = city_country_population.rename(columns={'city': 'City', 'country': 'Country', 'population': 'Population', 'lat': 'Latitude', 'lng': 'Longitude'})

# Merge city population data with internet usage data on 'Country'
merged_data = pd.merge(city_country_population, internet_usage, on='Country', how='left')

# Remove countries with missing Internet Usage data and create a new DataFrame to avoid SettingWithCopyWarning
cleaned_data = merged_data.dropna(subset=['InternetUsagePercentage']).copy()

# Add a new column for the number of internet users using .loc[] to avoid SettingWithCopyWarning
cleaned_data['InternetUsers'] = cleaned_data['Population'] * (cleaned_data['InternetUsagePercentage'] / 100)

# Display the merged data
print(merged_data.columns)

# Re-run the merging process
city_country_population = city_data[['city', 'country', 'population', 'lat', 'lng']].copy()
internet_usage = internet_data[['Country', '% of Population']].copy()

# Apply logarithmic scaling to InternetUsers to enhance color contrast
cleaned_data['LogInternetUsers'] = np.log1p(cleaned_data['InternetUsers'])  # log1p is used to handle zeros

# Plot cities based on their latitude and longitude, colored by Internet Users
plt.figure(figsize=(10, 6))

# Scatter plot with color based on the number of Internet Users
scatter = plt.scatter(
    cleaned_data['Longitude'],
    cleaned_data['Latitude'],
    c=cleaned_data['LogInternetUsers'],  # Using log-scaled InternetUsers for better color contrast
    cmap='coolwarm',  # You can try 'viridis', 'inferno', etc.
    s=cleaned_data['Population'] / 1e6,  # Scale marker size by population
    alpha=0.6
)

# Add a colorbar to indicate the number of Internet Users
cbar = plt.colorbar(scatter)
cbar.set_label('Number of Internet Users')

# Add labels and title
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('City Locations Colored by Number of Internet Users and Sized by Population')

# Show the plot
plt.show()