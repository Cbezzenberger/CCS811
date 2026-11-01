#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Single-process CCS811 logger and e-paper dashboard."""

import logging
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path

from printToEpaper import create_display, display_image
from sensorDataGen import SensorReader, append_reading, recent_readings
from sensorPlotEpaper import draw_dashboard
from settings import Settings, load_settings


LOG = logging.getLogger(__name__)
DATA_DIR = Path(os.environ.get("COIMAGER_DATA_DIR", Path(__file__).resolve().parent / "csvfiles"))
SETTINGS_PATH = DATA_DIR / "settings.json"


def display_due(started, last_display, retry_at, interval):
    if retry_at is not None:
        return started >= retry_at
    return last_display is None or started - last_display >= interval


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    reader = SensorReader()
    display = None
    last_display = None
    retry_display_at = None
    history = deque(recent_readings(DATA_DIR, limit=360), maxlen=360)
    settings = Settings()

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

        interval = settings.display_interval_seconds(datetime.now().time())
        if display_due(started, last_display, retry_display_at, interval):
            try:
                if display is None:
                    display = create_display()
                image = draw_dashboard(history, reading, reader.conditioning_remaining())
                display_image(display, image)
                LOG.info("Display updated with %d readings", len(history))
                last_display = started
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
