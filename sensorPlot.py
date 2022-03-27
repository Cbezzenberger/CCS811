from datetime import datetime
import pandas as pd
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import matplotlib.dates as md
import matplotlib.ticker as tkr

cm = 1/2.54 #centimeters to inches conversion
fig, ax = plt.subplots(figsize = (2.38*cm,4.88*cm), dpi = 130) #current display is 250×122@2.13".
    #Trying to get to exact pixels for later conversion to ePaper.
# fig, ax = plt.subplots()
Ts, Co2 = [],[]
ln, = plt.plot([], [], 'r-')
ln2, = plt.plot([], [], 'k--')
plt.grid(which = 'both', axis='y', color = 'k', linestyle = ':', linewidth = '0.5')

def plot_init():
    ax.set_ylim(0,4000)
    ax.yaxis.set_major_formatter(tkr.FuncFormatter(lambda y,pos: f"{int(y/1000)}k"))
    return ln, ln2

def plot_update(frame):
    current_day = datetime.utcnow().strftime("%d")
    sensor_data = pd.read_csv(f"csvfiles/{current_day}_ccsdata.csv", parse_dates=['Timestamp'])

    Ts = sensor_data['Timestamp'][-240:]
    Co2 = sensor_data['Co2'][-240:]
    Tvoc = sensor_data['Tvoc'][-240:]

    if frame == 0: #workaround for a bug in pyplot where axis updates don't work with blitting enabled
        fig.canvas.resize_event()
        
    ax.set_ylim(0,Co2.max()+500)
    ax.set_xlim(Ts.min(), Ts.max())
    ln.set_data(Ts, Co2)
    ln2.set_data(Ts, Tvoc)
    xformatter = md.DateFormatter('%H:%M')
    xlocator = md.MinuteLocator(byminute = [0,15,30,45], interval = 1)
    ax.xaxis.set_major_locator(xlocator)
    ax.xaxis.set_major_formatter(xformatter)
    fig.autofmt_xdate()

    plt.savefig('fig.png', bbox_inches = 'tight')

    return ln, ln2

ani = FuncAnimation(fig, plot_update, interval = 5000, init_func = plot_init, blit = True, repeat = False)
plt.show()