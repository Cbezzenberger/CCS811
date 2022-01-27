from Adafruit_CCS811 import Adafruit_CCS811
import csv
import time
# from collections import deque
import os
import sys

ccs = Adafruit_CCS811()

fieldnames = ["Timestamp", "Co2", "Tvoc"]
IOerror_counter = []

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

        try:
            with open(csvpath, "a") as csv_file:
                csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)

                info = update_ccsdata()

                csvwriter.writerow(info)
                #TODO: Create delete function for old CSVs
                IOerror_counter = 0 #reset IOError counter after successful write attempt.
            time.sleep(1)

        except IOError: #Seems to just happen occasionally
            if IOerror_counter > 3:
                sys.exit()
            else:
                time.sleep(10)
                IOerror_counter += 1
                
write_csvfile()