# SPDX-License-Identifier: GPL-3.0-only
"""Read the CCS811 and keep a small, dated CSV history."""

import csv
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


LOG = logging.getLogger(__name__)
FIELDS = ("Timestamp", "Co2", "Tvoc")
CONDITIONING_SECONDS = 20 * 60


class SensorReader:
    def __init__(self):
        self.sensor = None
        self.next_attempt = 0.0
        self.consecutive_errors = 0
        self.started_at = None

    def conditioning_remaining(self):
        if self.started_at is None:
            return CONDITIONING_SECONDS
        return max(0, CONDITIONING_SECONDS - (time.monotonic() - self.started_at))

    def read(self):
        if time.monotonic() < self.next_attempt:
            return None
        try:
            if self.sensor is None:
                import adafruit_ccs811
                import board
                import busio

                self.sensor = adafruit_ccs811.CCS811(busio.I2C(board.SCL, board.SDA))
                self.started_at = time.monotonic()
                self.consecutive_errors = 0
            if not self.sensor.data_ready:
                return None
            co2 = self.sensor.eco2
            tvoc = self.sensor.tvoc
            if not 400 <= co2 <= 8192 or not 0 <= tvoc <= 1187:
                LOG.warning("Discarding out-of-range CCS811 reading: eCO2=%s, TVOC=%s", co2, tvoc)
                return None
            self.consecutive_errors = 0
            return (datetime.now(timezone.utc), co2, tvoc)
        except (OSError, RuntimeError, ValueError):
            self.consecutive_errors += 1
            if self.consecutive_errors >= 3:
                LOG.exception("CCS811 failed three times; reconnecting in 30 seconds")
                self.sensor = None
                self.started_at = None
                self.next_attempt = time.monotonic() + 30
            else:
                LOG.exception("CCS811 read failed; retrying in 10 seconds")
                self.next_attempt = time.monotonic() + 10
            return None


def csv_path(data_dir, day):
    return Path(data_dir) / f"{day:%Y-%m-%d}_ccsdata.csv"


def append_reading(data_dir, reading):
    timestamp, co2, tvoc = reading
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = csv_path(data_dir, timestamp)
    with path.open("a", newline="") as stream:
        writer = csv.writer(stream)
        if stream.tell() == 0:
            writer.writerow(FIELDS)
        writer.writerow((timestamp.isoformat(), co2, tvoc))

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=7)
    for old_path in data_dir.glob("????-??-??_ccsdata.csv"):
        try:
            if datetime.strptime(old_path.name[:10], "%Y-%m-%d").date() < cutoff:
                old_path.unlink()
        except (ValueError, OSError):
            LOG.warning("Could not clean up %s", old_path, exc_info=True)


def recent_readings(data_dir, limit=120):
    today = datetime.now(timezone.utc)
    readings = []
    for day in (today - timedelta(days=1), today):
        path = csv_path(data_dir, day)
        try:
            with path.open(newline="") as stream:
                for row in csv.DictReader(stream):
                    try:
                        readings.append((datetime.fromisoformat(row["Timestamp"].replace("Z", "+00:00")),
                                         int(row["Co2"]), int(row["Tvoc"])))
                    except (KeyError, TypeError, ValueError):
                        continue
        except FileNotFoundError:
            continue
        except OSError:
            LOG.warning("Could not read %s", path, exc_info=True)
    return readings[-limit:]
