from Adafruit_CCS811 import Adafruit_CCS811
import csv
from collections import deque
import os

ccs = Adafruit_CCS811()

ts = deque(maxlen=86400)
CO2 = deque(maxlen=86400)
TVOC = deque(maxlen=86400)

def update_data:
    ccs.readData()
    # ts.append(time.strftime("%H:%M:%S"))
    # CO2.append(ccs.geteCO2())
    # TVOC.append(ccs.getTVOC())

    with open(f"csvfiles/{time.strftime('%Y%m%d')}_ccsdata.csv","a") as f:
        csvwriter = csv.DictWriter(f, fieldnames=fieldnames)

        ts = time.strftime("%H:%M:%S")
        CO2 = ccs.geteCO2()
        TVOC = ccs.getTVOC()

        info = {
            "Timestamp": ts
            "Co2": CO2
            "Tvoc": TVOC
        }

        csvwriter.writerow(info)
        # print(ts, CO2, TVOC)
        #TODO: Create delete function for old CSVs
    time.sleep(1)