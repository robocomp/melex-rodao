import os

import pandas as pd
from math import sin, cos, sqrt, atan2, radians

from matplotlib import pyplot as plt
import matplotlib
from sklearn import preprocessing

matplotlib.use('TkAgg')

directory = '/home/robocomp/robocomp/components/melex-rodao/files/results/'
dir = max([os.path.join(directory, d) for d in os.listdir(directory)], key=os.path.getmtime)
print(dir)


# dir = '/home/robocomp/robocomp/components/melex-rodao/files/results/prueba'


def getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2):
    R = 6373.0  # Radius of the earth in km
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    rLat1 = radians(lat1)
    rLat2 = radians(lat2)
    a = sin(dLat / 2) * sin(dLat / 2) + cos(rLat1) * cos(rLat2) * sin(dLon / 2) * sin(dLon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    d = R * c *1000 # Distance in m
    return d


def calc_velocity(dist_km, time_start, time_end):
    """Return 0 if time_start == time_end, avoid dividing by 0"""
    # if dist_km == 0:
    #     return 0

    dt = (time_end - time_start).total_seconds()
    if dt == 0:
        return 0

    return dist_km /dt if time_end > time_start else 0


df = pd.read_csv(os.path.join(dir, 'carlaBridge_gnss.csv'),
                 delimiter=';', skiprows=0, low_memory=False)

df['Time'] = pd.to_datetime(df['Time'], unit='s')

df['prevLat'] = df['Latitude'].shift(1)
df['prevLon'] = df['Longitude'].shift(1)
df['prevTime'] = df['Time'].shift(1)


df.to_csv('velocity.csv')

# create a new column for distance
df['dist_km'] = df.apply(
    lambda row: getDistanceFromLatLonInKm(
        lat1=row['Latitude'],
        lon1=row['Longitude'],
        lat2=row['prevLat'],
        lon2=row['prevLon']
    ),
    axis=1
)

# create a new column for velocity km/s
df['velocity'] = df.apply(
    lambda row: calc_velocity(
        dist_km=row['dist_km'],
        time_start=row['prevTime'],
        time_end=row['Time']
    ),
    axis=1
)

#To km/h
df['velocity'] = df['velocity'].apply(lambda x: x * 3.6)

df['prom_velocity'] = df['velocity'].rolling(5).mean()

fig, [ax0, ax1] = plt.subplots(2)
ax0.plot(df['Time'], df['prom_velocity'], c='purple')
plt.xlabel("Tiempo ")
plt.ylabel("Velocidad (Km/h)")

df2 = pd.read_csv(os.path.join(dir, 'carlaBridge_velocity.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

df2['Time'] = pd.to_datetime(df2['Time'], unit='s')

ax1.plot(df2['Time'], df2['Velocity'], c='turquoise')
plt.xlabel("Tiempo ")
plt.ylabel("Velocidad Carla (Km/h)")

# ax1.xlabel("Tiempo ")
# ax1.ylabel("Velocidad (Km/h)")
plt.show()
