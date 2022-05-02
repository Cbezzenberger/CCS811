#First clone geeekpi/epaper
from time import sleep
from Epaper import *
from PIL import Image
import sys

def print_to_epaper(imgfile):
    file_not_found_counter = 0 #FileNotFound counter
    X_PIXEL = 128
    Y_PIXEL = 250

    while True: 
        try:
            e = Epaper(X_PIXEL, Y_PIXEL)
            with Image.open(imgfile) as f:
                file_not_found_counter = 0
                f = f.rotate(angle=90, expand=True)

                rBuf = [0] * 4000
                bBuf = [0] * 4000

                f = f.convert('RGB')
                data = f.load()

            for y in range(250): #This piece of code is directly taken from the geeekpi demo.py file
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
            sleep(5)

        except FileNotFoundError:
            if file_not_found_counter <= 5:
                sleep(2)
                print(f"No png file found to print to epaper display. Retrying {file_not_found_counter}")
                file_not_found_counter += 1
            elif file_not_found_counter > 5:
                sys.exit("No png file found to print to epaper display. Exiting...\n")

if __name__ == '__main__':
    print_to_epaper()