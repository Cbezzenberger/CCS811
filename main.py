#! /usr/bin/env python3

import sensorDataGen
import sensorPlotEpaper
import printToEpaper
from time import sleep
from multiprocessing import Process

def main():
    p1 = Process(target=sensorDataGen.main)
    p1.start()
    sleep(10)
    p2 = Process(target=sensorPlotEpaper.main)
    p2.start()
    sleep(10)
    p3 = Process(target=printToEpaper.main)
    p3.start()
    p1.join()
    p2.join()
    p3.join()

if __name__ == "__main__":
    main()
