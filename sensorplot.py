import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime as dt

# threading.Timer(1,#Function)  ##creates a second thread to process a function and keeps going after the function is executed and the timer is done

def animate(i):
    plt.cla()
    plt.plot(ts, CO2, label = "Co2")
    plt.xlabel("Time")
    plt.ylabel("Co2 in ppM")
    plt.legend()
    plt.grid(True)
    plt.show()

ani = FuncAnimation(plt.gcf(), animate, 1000)

# def update_graph():
#     temp = getsensordata.update_values()
#     ts.append(temp[0])
#     CO2.append(temp[1])
#     TVOC.append(temp[2])