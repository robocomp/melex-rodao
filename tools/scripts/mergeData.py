import os
from datetime import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
dir = '/home/robocomp/robocomp/components/melex-rodao/files/results/test_210225_1650/'

df1 = pd.read_csv(os.path.join(dir, 'carlaMonitor_gnss.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

df2 = pd.read_csv(os.path.join(dir, 'carlaMonitor_imu.csv'),
                  delimiter=';', skiprows=0, low_memory=False)

df3 = pd.read_csv(os.path.join(dir, 'carlaBridge_fps.csv'),
                  delimiter=';', skiprows=0, low_memory=False)


# df3 = pd.merge_asof(df1, df2,on='Time')
df_Result = pd.merge_ordered(df1, df2, on='Time', fill_method="ffill")
df_Result = pd.merge_ordered(df_Result,df3 , on='Time', fill_method="ffill")
# df3['Time'] = df3['Time'].apply(lambda x: datetime.timestamp(x))
print(df_Result)
df_Result.to_csv(os.path.join(dir, 'dataMerged.csv'))


