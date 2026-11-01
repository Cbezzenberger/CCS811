# SPDX-License-Identifier: GPL-3.0-only
"""Draw a compact two-color chart without loading matplotlib on a Pi Zero."""

from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont


RED = (237, 28, 36)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WIDTH, HEIGHT = 250, 128
WINDOW_MINUTES = 30


def draw_dashboard(history, latest=None, conditioning_seconds=0, now=None):
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    current = latest or (history[-1] if history else None)
    if current is None:
        draw.text((8, 12), "Waiting for CCS811 data", fill=BLACK, font=font)
        return image

    _, co2, tvoc = current
    draw.text((5, 3), f"eCO2 {co2} ppm", fill=RED, font=font)
    draw.text((131, 3), f"TVOC {tvoc} ppb", fill=BLACK, font=font)
    if conditioning_seconds > 0:
        minutes = int((conditioning_seconds + 59) // 60)
        draw.text((107, 16), f"WARM {minutes}m", fill=BLACK, font=font)

    left, top, right, bottom = 29, 23, 218, 98
    middle = (top + bottom) // 2
    draw.line((left, top, left, bottom), fill=RED)
    draw.line((right, top, right, bottom), fill=BLACK)
    draw.line((left, bottom, right, bottom), fill=BLACK)
    for x, label in ((left, "-30m"), ((left + right) // 2, "-15m"), (right, "now")):
        draw.line((x, bottom, x, bottom + 4), fill=BLACK)
        label_width = draw.textbbox((0, 0), label, font=font)[2]
        draw.text((x - label_width // 2, 107), label, fill=BLACK, font=font)

    end = now or datetime.now().astimezone()
    start = end - timedelta(minutes=WINDOW_MINUTES)
    visible = [row for row in history if start <= row[0] <= end]
    if not visible:
        return image

    co2_min = 400
    co2_max = max(600, ((max(row[1] for row in visible) + 149) // 100) * 100)
    tvoc_max = max(50, ((max(row[2] for row in visible) + 69) // 50) * 50)
    for y, label in ((top, co2_max), (middle, (co2_min + co2_max) // 2), (bottom - 8, co2_min)):
        draw.text((0, y), str(label), fill=RED, font=font)
    for y, label in ((top, tvoc_max), (middle, tvoc_max // 2), (bottom - 8, 0)):
        draw.text((222, y), str(label), fill=BLACK, font=font)

    def x_at(timestamp):
        return left + round((timestamp - start).total_seconds() * (right - left) /
                            (WINDOW_MINUTES * 60))

    # Spaced bars remain legible when samples arrive faster than the pixel grid.
    bars = {}
    for timestamp, _, value in visible:
        bucket = (x_at(timestamp) - left) // 4
        x = min(right - 1, left + bucket * 4 + 2)
        y = bottom - round(value * (bottom - top) / tvoc_max)
        bars[x] = min(y, bars.get(x, bottom))
    for x, y in bars.items():
        draw.line((x, min(y, bottom - 2), x, bottom - 1), fill=BLACK)

    line = [(x_at(row[0]), bottom - round((row[1] - co2_min) * (bottom - top) /
                                                (co2_max - co2_min))) for row in visible]
    for first, second in zip(line, line[1:]):
        if second[0] - first[0] <= 20:  # Leave a gap when samples are missing for over three minutes.
            draw.line((first, second), fill=RED, width=2)
    for point in line:
        draw.point(point, fill=RED)
    return image
