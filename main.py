#! /usr/bin/env python3

from time import time
import sensorDataGen
import sensorPlotEpaper
import printToEpaper
from time import sleep
from multiprocessing import Process

#Create individual processes for each of the functions sensorDataGen.main(), sensorPlotEpaper.main(), and printToEpaper.main()

def main():
    p1 = Process(target=sensorDataGen.main)
    p1.start()
    p2 = Process(target=sensorPlotEpaper.main)
    p2.start()
    p3 = Process(target=printToEpaper.main)
    p3.start()
    p1.join()
    p2.join()
    p3.join()

if __name__ == "__main__":
    main()