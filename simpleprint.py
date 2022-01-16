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
        time.sleep(1)
    except IOError:
        print("ioError, exiting...\n")
    except KeyboardInterrupt:
        print("User interrupt. Exiting...\n")
        sys.exit()
    except Exception as e:
        print(e)