# SPDX-License-Identifier: GPL-3.0-only
"""Convert a 250 x 128 RGB image to the GeeekPi Epaper buffers.

Buffer conversion adapted from geeekpi/epaper/eink2.13_demo.py (GPL-3.0).
"""

import time

from PIL import Image

from sensorPlotEpaper import RED, WIDTH, HEIGHT


def image_buffers(image):
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(f"Expected {WIDTH}x{HEIGHT} image, got {image.size}")
    rotated = image.convert("RGB").transpose(Image.Transpose.ROTATE_90)
    pixels = rotated.load()
    red = [0] * 4000
    black = [0] * 4000
    for y in range(250):
        for x in range(128):
            color = pixels[x, y]
            index = 16 * y + (15 - x // 8)
            bit = 1 << (x % 8)
            if color == RED:
                red[index] |= bit
            elif color == (255, 255, 255):
                black[index] |= bit
    return red, black


def display_image(display, image):
    red, black = image_buffers(image)
    display.flash_red(buf=red)
    display.flash_black(buf=black)
    display.update()


def create_display():
    """Give the upstream driver's unbounded BUSY wait a timeout."""
    import RPi.GPIO as GPIO
    from Epaper import Epaper

    class TimedEpaper(Epaper):
        def wait(self):
            deadline = time.monotonic() + 30
            while GPIO.input(self.BUSY_PIN) != GPIO.LOW:
                if time.monotonic() >= deadline:
                    raise TimeoutError("E-paper BUSY pin stayed high for 30 seconds")
                time.sleep(0.1)

    display = TimedEpaper.__new__(TimedEpaper)
    try:
        display.__init__(128, 250)
    except Exception:
        if hasattr(display, "spi"):
            display.spi.close()
        raise
    return display
