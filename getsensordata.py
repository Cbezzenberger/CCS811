import time
from Adafruit_CCS811 import Adafruit_CCS811

ccs = Adafruit_CCS811()
sens_dict = {}

def update_values():
    try:
        ccs.readData()
        return time.strftime("%H:%M:%S") , ccs.geteCO2(), ccs.getTVOC()
    except IOError:
        print("Connection error")
    except KeyboardInterrupt:
        print("Exiting...\n")

# while True:
#     ts, Co2, TVOC = update_values()
#     print(ts, Co2, TVOC)
#     sens_dict[ts] = (Co2, TVOC)
#     if len(sens_dict) > 3619: #one hour and 20 seconds of historic data. all additional data is deleted. TODO: Add automatic csv file creation for each day.
#         del sens_dict[-20:]
#     time.sleep(1)