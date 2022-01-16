import dash
import getsensordata
from plotly
from collections import deque

ts = deque(maxlen=3600)
CO2 = deque(maxlen=3600)
TVOC = deque(maxlen=3600)





def update_graph():
    temp = getsensordata.update_values()
    ts.append(temp[0])
    CO2.append(temp[1])
    TVOC.append(temp[2])