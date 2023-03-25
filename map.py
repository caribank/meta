import geopandas as gpd
import pandas as pd

df = pd.read_csv("raw/cariban_language_list.csv", keep_default_na=False)

df = df[df["Latitude"] != ""]
df = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude)
)  # convert to a geodataframe
# df.drop(columns=["Sampled"], inplace=True)
df["Alive"] = df["Alive"].replace({"y": "yes", "n": "no"})

df = df.set_crs("epsg:4326")
m = df.explore(
    marker_kwds=dict(radius=3.5), style_kwds=dict(fillOpacity=1), zoom_start=5
)

m.save(f"map.html")
