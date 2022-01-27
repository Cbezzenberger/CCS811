from Adafruit_CCS811 import Adafruit_CCS811
import csv
import time
# from collections import deque
import os
from sys import exit

ccs = Adafruit_CCS811()

fieldnames = ["Timestamp", "Co2", "Tvoc"]
Error_counter = []

def update_ccsdata():
    ccs.readData()
    return {
        "Timestamp": time.strftime("%H:%M:%S"),
        "Co2": ccs.geteCO2(),
        "Tvoc": ccs.getTVOC()
        }

def write_csvfile():
    if not os.path.exists("csvfiles"):
        os.mkdir("csvfiles", mode=0o777)

    while True:
        csvpath = f"csvfiles/{time.strftime('%H')}_ccsdata.csv"
        if not os.path.exists(csvpath):
            with open(csvpath, "w")as csv_file:
                csv.DictWriter(csv_file, fieldnames=fieldnames).writeheader()
        with open(csvpath, "a") as csv_file:
            csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)

            info = update_ccsdata()

            csvwriter.writerow(info)
            # print(ts, CO2, TVOC)
            #TODO: Create delete function for old CSVs
        time.sleep(1)
    
write_csvfile()