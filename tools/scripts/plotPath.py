import os

import numpy as np
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import matplotlib.pyplot as plt
import yaml
import matplotlib


def set_color(value):
    if value == np.nan:
        value = 0
    if value < 5:
        color = 'greenyellow'
    elif value < 10:
        color = 'yellow'
    elif value < 15:
        color = 'gold'
    elif value < 20:
        color = 'darkorange'
    elif value >= 20:
        color = 'red'
    return color


matplotlib.use('TkAgg')

# Read last directory
directory = '/home/robocomp/robocomp/components/melex-rodao/files/results/'
dir = max([os.path.join(directory, d) for d in os.listdir(directory)], key=os.path.getmtime)

# Read gnss file
df = pd.read_csv(os.path.join(dir, 'carlaBridge_gnss.csv'),
                 delimiter=';', skiprows=0, low_memory=False)

# Read velocity file generated with velocity.py script
df2 = pd.read_csv(os.path.join(dir, 'velocity.csv'),
                  delimiter=';', skiprows=0, low_memory=False)
# Merge dataframes
df_merge_result = pd.merge_ordered(df, df2, on='Time', fill_method="ffill")

# Create column color depending of the velocity
df['Color'] = df_merge_result['prom_velocity'].apply(lambda value: set_color(value))

# Create geodataframe to plot latitude and loingitude
geometry = [Point(xy) for xy in zip(df['Longitude'], df['Latitude'])]
gdf = GeoDataFrame(df, geometry=geometry)

fig, ax1 = plt.subplots(figsize=(10, 6))
gdf.plot(ax=ax1, marker='o', color=gdf['Color'], markersize=8);

# Read roads map
roads = gpd.read_file('/home/robolab/robocomp/components/melex-rodao/files/campus/roads.geojson')
roads.plot(ax=ax1)
# Buildings map
buildings = gpd.read_file('/home/robolab/robocomp/components/melex-rodao/files/campus/buildings.geojson')
buildings.plot(ax=ax1, color='darkslateblue')

# Read and plot cameras location
yaml_file = open('/home/robocomp/robocomp/components/melex-rodao/etc/cameras.yml')
pose_cameras_dict = yaml.load(yaml_file)

cam_lat = []
cam_lon = []
for pose in pose_cameras_dict.values():
    cam_lat.append(pose['latitude'])
    cam_lon.append(pose['longitude'])

df2 = pd.DataFrame({'Latitude': cam_lat, 'Longitude': cam_lon})
geometry2 = [Point(xy) for xy in zip(cam_lon, cam_lat)]
gdf2 = GeoDataFrame(df2, geometry=geometry2)

gdf2.plot(ax=ax1, marker='o', color='y', markersize=20);

plt.show()
