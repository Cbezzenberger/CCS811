#First clone geeekpi/epaper
import time
from Epaper import *
from PIL import Image
import sys

def print2epaper(imgfile):
    fnf_counter = 0 #FileNotFound counter
    X_PIXEL = 128
    Y_PIXEL = 250

    try:
        e = Epaper(X_PIXEL, Y_PIXEL)
        f = Image.open(imgfile)
        fnf_counter = 0
        f = f.rotate(angle=90, expand=True)

        rBuf = [0] * 4000
        bBuf = [0] * 4000

        f = f.convert('RGB')
        data = f.load()
        for y in range(250):
            for x in range(128):
                if data[x,y] == (237,28,36): #IndexError: image index out of range TODO: Probably resize image to correct resolution.
                    index = int(16 * y + (15 - (x - 7) / 8))
                    tmp = rBuf[index]
                    rBuf[index] = tmp | (1 << (x % 8))
                elif data[x,y] == (255,255,255):
                    index = int(16 * y + (15 - (x - 7) / 8))
                    tmp = bBuf[index]
                    bBuf[index] = tmp | (1 << (x % 8))

        e.flash_red(buf = rBuf)
        e.flash_black(buf=bBuf)
        e.update()


    except FileNotFoundError:
        if fnf_counter <= 5:
            time.sleep(2)
            print(f"No png file found to print to epaper display. Retrying {fnf_counter}")
            fnf_counter += 1
        elif fnf_counter > 5:
            sys.exit("No png file found to print to epaper display. Exiting...\n")

while True:
    print2epaper("fig.png")
    time.sleep(30)
