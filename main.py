#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Single-process CCS811 logger and e-paper dashboard."""

import logging
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from statistics import median

from printToEpaper import create_display, display_image
from sensorDataGen import SensorReader, append_reading, recent_readings
from sensorPlotEpaper import draw_dashboard, draw_warning
from settings import Settings, load_settings


LOG = logging.getLogger(__name__)
DATA_DIR = Path(os.environ.get("COIMAGER_DATA_DIR", Path(__file__).resolve().parent / "csvfiles"))
SETTINGS_PATH = DATA_DIR / "settings.json"
ALERT_PAGE_SECONDS = 120


def display_due(started, last_display, retry_at, interval):
    if retry_at is not None:
        return started >= retry_at
    return last_display is None or started - last_display >= interval


def next_page(alert, last_page):
    return "warning" if alert and last_page != "warning" else "graph"


def eco2_alert(history, threshold, conditioning_seconds=0):
    """Require two nearby high samples so a lone spike cannot trigger the panel."""
    if conditioning_seconds > 0:
        return False
    recent = list(history)[-3:]
    last_break = 0
    for index, (earlier, later) in enumerate(zip(recent, recent[1:])):
        gap = (later[0] - earlier[0]).total_seconds()
        if gap < 0 or gap > 180:
            last_break = index + 1
    recent = recent[last_break:]
    if len(recent) < 2:
        return False
    if len(recent) == 2:
        return all(row[1] >= threshold for row in recent)
    return median(row[1] for row in recent) >= threshold


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    reader = SensorReader()
    display = None
    last_display = None
    retry_display_at = None
    history = deque(recent_readings(DATA_DIR, limit=360), maxlen=360)
    settings = Settings()
    current_alert = False
    displayed_alert = False
    last_page = None

    while True:
        started = time.monotonic()
        settings = load_settings(SETTINGS_PATH, settings)
        reading = reader.read()
        if reading is not None:
            history.append(reading)
            try:
                append_reading(DATA_DIR, reading)
            except OSError:
                LOG.exception("Could not save sensor reading")

        conditioning_seconds = reader.conditioning_remaining()
        if conditioning_seconds > 0:
            current_alert = False
        elif reading is not None:
            current_alert = eco2_alert(history, settings.eco2_warning_ppm, conditioning_seconds)
        interval = (ALERT_PAGE_SECONDS if current_alert else
                    settings.display_interval_seconds(datetime.now().time()))
        if (display_due(started, last_display, retry_display_at, interval) or
                (retry_display_at is None and current_alert != displayed_alert)):
            try:
                if display is None:
                    display = create_display()
                page = next_page(current_alert, last_page)
                if page == "warning":
                    co2 = round(median(row[1] for row in list(history)[-3:]))
                    image = draw_warning(co2)
                else:
                    image = draw_dashboard(history, reading, conditioning_seconds)
                display_image(display, image)
                LOG.info("Display updated (%s) with %d readings", page, len(history))
                last_display = started
                displayed_alert = current_alert
                last_page = page
                retry_display_at = None
            except (ImportError, OSError, RuntimeError, ValueError, IndexError):
                LOG.exception("Display update failed; will retry")
                if display is not None:
                    display.spi.close()
                display = None
                retry_display_at = time.monotonic() + 60

        time.sleep(max(0, settings.sample_seconds - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
