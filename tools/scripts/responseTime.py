import os
from datetime import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib

matplotlib.use('TkAgg')

directory = '/home/robocomp/robocomp/components/melex-rodao/files/results/'
dir = max([os.path.join(directory, d) for d in os.listdir(directory)], key=os.path.getmtime)

df1 = pd.read_csv(os.path.join(dir, 'carlaRemoteControl_communication.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

df2 = pd.read_csv(os.path.join(dir, 'carlaBridge_response.csv'),
                  delimiter=';', skiprows=0, low_memory=False)


# df3 = pd.merge_asof(df1, df2,on='Time')
df4 = pd.merge_ordered(df1, df2, on='Time', fill_method="ffill")
#
df4['TotalTime'] = df4['CommunicationTime'] + df4['ServerResponseTime']

df4.to_csv(os.path.join(dir, 'responsetime.csv'))

std = df4['TotalTime'].std()
mean = df4['TotalTime'].mean()
#
print(f'Media {mean}   Desviación {std}')
df4['Time'] = pd.to_datetime(df4['Time'], unit='s')

plt.plot(df4['Time'],df4['TotalTime'], c='turquoise')
# df4['Time'] = df4['Time'].apply(lambda x: datetime.fromtimestamp(x))
plt.xlabel("Tiempo ")
plt.ylabel("Response")
plt.show()

