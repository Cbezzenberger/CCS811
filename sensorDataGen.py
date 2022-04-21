from datetime import datetime, timedelta 
import time
#Could probably be shrunk by just using the time module.
import adafruit_ccs811
from multiprocessing import Process
import csv
import os
import board
import busio
import sys
import schedule
#TODO: Switch from csv-based to tinydb in-memory storage. https://www.opensourceforu.com/2017/05/three-python-databases-pickledb-tinydb-zodb/
#from tinydb.storages import MemoryStorage 

i2c_bus = busio.I2C(board.SCL, board.SDA)
ccs = adafruit_ccs811.CCS811(i2c_bus)

fieldnames = ["Timestamp", "Co2", "Tvoc"]
IOerror_counter = 0

#db = TinyDB(storage=MemoryStorage)

def update_ccsdata():
    if ccs.eco2() < 7500 and ccs.tvoc() < 7500:
        return {
            "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Co2": ccs.eco2(),
            "Tvoc": ccs.tvoc()}
    else:
        return {
            "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Co2": 0,
            "Tvoc": 0}

def write_csvfile(update_frq = 5): #define update frequency in seconds. This will create a new csvfile etry according to the set frequency.
    if not os.path.exists("csvfiles"): #Create subdirectory for csvfiles if it does not exist.
        os.mkdir("csvfiles", mode=0o777)

    while True:
        csvpath = f"csvfiles/{datetime.utcnow().strftime('%d')}_ccsdata.csv"

        if not os.path.exists(csvpath):
            with open(csvpath, "w")as csv_file:
                csv.DictWriter(csv_file, fieldnames=fieldnames).writeheader()

        try:
            with open(csvpath, "a") as csv_file:
                csvwriter = csv.DictWriter(csv_file, fieldnames=fieldnames)

                info = update_ccsdata()

                csvwriter.writerow(info)
                #TODO: Create delete function for old CSVs
                # csvfiles = [i for i in os.listdir("./csvfiles") if os.path.isfile(os.path.join("csvfiles, f"))]
                IOerror_counter = 0 #reset IOError counter after successful write attempt.
            time.sleep(update_frq)

        except IOError: #Seems to just happen occasionally
            if IOerror_counter > 3:
                sys.exit()
            else:
                time.sleep(10)
                IOerror_counter += 1
                
#Function to delete the oldest CSVfile, once there are more than 27 csvfiles in the folder.
#TODO:Section should be updated, finding and deleting a specific date offset file instead of just the oldest.


def delete_old_csv(): #Thanks @RightmireM
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