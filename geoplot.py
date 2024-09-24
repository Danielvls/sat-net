# Import Libraries
import pandas as pd
import geopandas
import folium
import geodatasets
import matplotlib.pyplot as plt

df1 = pd.read_csv("volcano_data_2010.csv")

# Keep only relevant columns
df = df1.loc[:, ("Year", "Name", "Country", "Latitude", "Longitude", "Type")]
df.info()

# Create point geometries
geometry = geopandas.points_from_xy(df.Longitude, df.Latitude)
geo_df = geopandas.GeoDataFrame(
    df[["Year", "Name", "Country", "Latitude", "Longitude", "Type"]], geometry=geometry
)

geo_df.head()

world = geopandas.read_file(geodatasets.get_path("naturalearth.land"))
df.Type.unique()

fig, ax = plt.subplots(figsize=(24, 18))
world.plot(ax=ax, alpha=0.4, color="grey")
geo_df.plot(column="Type", ax=ax, legend=True)
plt.title("Volcanoes")

plt.show()
