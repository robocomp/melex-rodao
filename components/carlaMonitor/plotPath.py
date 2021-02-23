import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import matplotlib.pyplot as plt
import yaml

df = pd.read_csv('/home/robocomp/robocomp/components/melex-rodao/files/results/test_210223_1256/gnss.csv',
                 delimiter=';', skiprows=0, low_memory=False)

geometry = [Point(xy) for xy in zip(df['Longitude'], df['Latitude'])]
gdf = GeoDataFrame(df, geometry=geometry)
fig, ax1 = plt.subplots(figsize=(10, 6))

# this is a simple map that goes with geopandas
roads = gpd.read_file('/home/robolab/robocomp/components/melex-rodao/files/campus/roads.geojson')
roads.plot(ax=ax1)
buildings = gpd.read_file('/home/robolab/robocomp/components/melex-rodao/files/campus/buildings.geojson')
buildings.plot(ax=ax1, color='darkslateblue')

gdf.plot(ax=ax1, marker='.', color='red', markersize=1);

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

gdf2.plot(ax=ax1, marker='o', color='y', markersize=15);
plt.show()
