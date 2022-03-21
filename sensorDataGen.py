import multiprocessing
from Adafruit_CCS811 import Adafruit_CCS811
from multiprocessing import Process
import csv
import time
import os
import sys
import schedule

ccs = Adafruit_CCS811()

fieldnames = ["Timestamp", "Co2", "Tvoc"]
IOerror_counter = 0

def update_ccsdata():
    ccs.readData()
    if ccs.geteCO2() < 7500 and ccs.getTVOC() < 7500:
        return {
            "Timestamp": time.strftime("%H:%M:%S"),
            "Co2": ccs.geteCO2(),
            "Tvoc": ccs.getTVOC()}
    else:
        return {
            "Timestamp": time.strftime("%H:%M:%S"),
            "Co2": 0,
            "Tvoc": 0}

def write_csvfile(update_frq = 5): #define update frequency in seconds. This will create a new csvfile etry according to the set frequency.
    if not os.path.exists("csvfiles"): #Create subdirectory for csvfiles if it does not exist.
        os.mkdir("csvfiles", mode=0o777)

    while True:
        csvpath = f"csvfiles/{time.strftime('%d')}_ccsdata.csv"
        # csvpath = f"csvfiles/{time.strftime('%d%H')}_ccsdata.csv" #uncomment for more detailed data in additional csvfiles, created per hour.

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
    csvlist = os.listdir("csvfiles")
    if len(csvlist) > 27:
        oldestfile = min(csvlist, key=os.path.getctime)
        os.remove(os.path.abspath(oldestfile))

#TODO:Not sure if this is the most efficient implementation.
if __name__ == '__main__':
    p1 = multiprocessing.Process(target=delete_old_csv)
    p1.start()
    p2 = multiprocessing.Process(target=write_csvfile)
    p2.start()
    p1.join()
    p2.join()