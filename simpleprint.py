from collections import deque
from Adafruit_CCS811 import Adafruit_CCS811
import time
import sys

sensordata = deque(maxlen=1000)
ccs = Adafruit_CCS811()

while True:
    try:
        ccs.readData()
        print(f"Time: {time.strftime('%H:%M:%S')}\nCO2: {ccs.geteCO2()}\nTVOC: {ccs.getTVOC()}\n")
    except IOError:
        print("ioError, exiting...\n")
    except KeyboardInterrupt:
        sys.exit()
        print("User interrupt. Exiting...\n")
    except Exception as e:
        print(e)
    sensordata.append()