import time
import pandas as pd
import os
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates

# Ts = deque(maxlen=360)
# Co2 = deque(maxlen=360)
# Tvoc = deque(maxlen=360)

def animate_sensor_data(i):
    current_day = time.strftime("%d")
    sensor_data = pd.read_csv(f"csvfiles/{current_day}_ccsdata.csv", parse_dates=True)
    
    # Ts.append(time.strptime(sensor_data["Timestamp"].iat[-1], "%H:%M:%S"))
    # Co2.append(sensor_data["Co2"].iat[-1])
    # Tvoc.append(sensor_data["Tvoc"].iat[-1])

    Ts = sensor_data['Timestamp'][-360:]
    Co2 = sensor_data['Co2'][-360:]
    Tvoc = sensor_data['Tvoc'][-360:]

    plt.cla()

    plt.plot(Ts, Co2, label = "eCO2")
    plt.plot(Ts, Tvoc, label = "TVOC")

    plt.legend(loc = 'upper left')
    plt.tight_layout()

ani = animation.FuncAnimation(plt.gcf(), animate_sensor_data, interval = 5000)

plt.show()