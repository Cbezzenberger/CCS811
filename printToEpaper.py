#First clone geeekpi/epaper
from cmath import exp
from time import sleep
from Epaper import *
from PIL import Image, UnidentifiedImageError
import sys
from copy import deepcopy

def print_to_epaper(imgfile, frequency=30):
    file_error_counter = 0 #FileNotFound or unidentified image error counter
    X_PIXEL = 128
    Y_PIXEL = 250

    while True: 
        try:
            e = Epaper(X_PIXEL, Y_PIXEL)

            #This causes an OSError: "too many open files" due to a bug in the PIL library. See Stackoverflow question #29234413. Workaround below.
            # with Image.open(imgfile) as f:
            #     file_error_counter = 0
            #     f = f.rotate(angle=90, expand=True)

            #     rBuf = [0] * 4000
            #     bBuf = [0] * 4000

            #     f = f.convert('RGB')
            #     data = f.load() 

            imgfile = deepcopy(Image.open(imgfile))
            file_error_counter = 0
            imgfile = imgfile.rotate(angle=90, expand=True)

            rBuf = [0] * 4000
            bBuf = [0] * 4000
            
            imgfile = imgfile.convert('RGB')

            for y in range(250): #This piece of code is directly taken from the geeekpi demo.py file
                for x in range(128):
                    if data[x,y] == (237,28,36):
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
            sleep(frequency)

        except (FileNotFoundError, UnidentifiedImageError):
            if file_error_counter <= 5:
                sleep(2)
                print(f"No png file found to print to epaper display or unidentified image error. Retrying {file_error_counter}")
                file_error_counter += 1
            elif file_error_counter > 5:
                sys.exit("No png file found to print to epaper display or unidentified image error. Exiting...\n")

def main():
    print_to_epaper("fig.png")

if __name__ == '__main__':
    main()
