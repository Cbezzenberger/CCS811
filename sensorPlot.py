import time
import pandas as pd
# import glob
import os
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation

Ts = deque(maxlen=360)
Co2 = deque(maxlen=360)
Tvoc = deque(maxlen=360)

def animate_sensor_data(i):
    current_day = time.strftime("%d")
    sensor_data = pd.read_csv(f"csvfiles/{current_day}_ccsdata.csv")
    
    Ts.append(time.strptime(sensor_data["Timestamp"].iat[-1], "%H:%M:%S"))
    Co2.append(sensor_data["Co2"].iat[-1])
    Tvoc.append(sensor_data["Tvoc"].iat[-1])

    plt.cla()

    plt.plot(Ts, Co2, label = "eCO2")
    plt.plot(Ts, Tvoc, label = "TVOC")

    plt.legend(loc = 'upper left')
    plt.tight_layout()

ani = animation.FuncAnimation(plt.gcf(), animate_sensor_data, interval = 5000)

plt.show()

# def get_file_ctime(fp):
#     return os.path.getctime(fp)
# file_list = glob.glob("csvfiles/*")
# file_list.sort(key = get_file_ctime)

# #get 3600 second entries from last and second to last file
# file_currenth = file_list[:0]
# file_lasth = file_list[:-1]

# sensordata1h = deque(maxlen=3600)
# while True:
#     if file_currenth = 
#     with open(file_currenth, "r") as f:
#         with open(file_lasth, "r") as lf:
#             sensordata1h = 
# %%
