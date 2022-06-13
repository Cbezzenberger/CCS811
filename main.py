from time import time
import sensorDataGen
import sensorPlotEpaper
import printToEpaper
from time import sleep

sleep(1)
sensorDataGen.main()
sleep(5)
sensorPlotEpaper.main()
sleep(5)
printToEpaper.main()
print("Running")