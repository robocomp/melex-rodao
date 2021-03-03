import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

directory = '/home/robocomp/robocomp/components/melex-rodao/files/results/'
dir = max([os.path.join(directory, d) for d in os.listdir(directory)], key=os.path.getmtime)

df3 = pd.read_csv(os.path.join(dir, 'carlaBridge_fps.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

df3 = df3[df3['FPS'] != 0]  # Remove columns with FPS 0 --- bridge not working yet
df3['Time'] = df3['Time'].apply(lambda x: datetime.fromtimestamp(x))
plt.plot(df3['Time'], df3['FPS'], c='purple')
plt.xlabel("Tiempo ")
plt.ylabel("FPS")
plt.show()

