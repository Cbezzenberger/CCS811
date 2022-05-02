from datetime import datetime, timedelta 
import time
from numpy import nan
import adafruit_ccs811
from multiprocessing import Process
import csv
import os
import board
import busio
import sys
import schedule
#TODO: Switch from csv-based to tinydb in-memory storage.

i2c_bus = busio.I2C(board.SCL, board.SDA)
ccs = adafruit_ccs811.CCS811(i2c_bus)

fieldnames = ["Timestamp", "Co2", "Tvoc"]

IOerror_counter = 0

def update_ccsdata():
    global IOerror_counter #Could not find a workaround for using global without rewriting large parts of the logic.
    try:
        if ccs.eco2 < 7500 and ccs.tvoc < 7500: #Sometimes, sensor is returning crazy-high numbers, this should catch it and return NAN in those cases.
            #TODO: Add a check to see if the sensor is actually working.
            return {
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Co2": ccs.eco2,
                "Tvoc": ccs.tvoc}
            IOerror_counter = 0 #reset IOError counter after successful sensor readout.
        else:
            return {
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Co2": nan,
                "Tvoc": nan}
    except (IOError, RuntimeError): #Seems to just happen sometimes, currently just returning NAN until it is resolved.
        if IOerror_counter > 5:
            sys.exit()
        else:
            return {
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Co2": nan,
                "Tvoc": nan}
            increase_IOerror_counter(IOerror_counter)

def write_csvfile(update_frq = 5): #Update frequency in seconds. This will create a new csvfile entry according to the set frequency.
    if not os.path.exists("csvfiles"):
        os.mkdir("csvfiles", mode=0o777)

    while True:
        csvpath = f"csvfiles/{datetime.utcnow().strftime('%d')}_ccsdata.csv"

        if not os.path.exists(csvpath):
            with open(csvpath, "w")as csv_file:
                csv.DictWriter(csv_file, fieldnames=fieldnames).writeheader()

        with open(csvpath, "a") as csv_file:
            csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)

            info = update_ccsdata()

            csvwriter.writerow(info)

        time.sleep(update_frq)

def delete_old_csv(): #Scheduled function delete the csv file from the next day's date at 23:55.
    schedule.every().day.at("23:55").do(_delete_old_csv)
    while True:
        schedule.run_pending()
        time.sleep(60)

def _delete_old_csv():
    tmrw = datetime.today() + timedelta(days=1)
    try:
        os.remove(os.path.abspath(f"csvfiles/{tmrw.strftime('%d')}_ccsdata.csv"))
    except FileNotFoundError:
        pass #File creation is handled in write_csvfile function.

#TODO:Not sure if this is the most efficient implementation.
if __name__ == '__main__':
    p1 = Process(target=delete_old_csv)
    p1.start()
    p2 = Process(target=write_csvfile)
    p2.start()
    p1.join()
    p2.join()
