# SPDX-License-Identifier: GPL-3.0-only
import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from PIL import Image

from main import display_due
from printToEpaper import image_buffers
from sensorDataGen import SensorReader, append_reading, csv_path, recent_readings
from sensorPlotEpaper import RED, draw_dashboard


class ImageTests(unittest.TestCase):
    def test_display_buffers_use_full_128_by_250_frame(self):
        image = Image.new("RGB", (250, 128), "white")
        image.putpixel((0, 0), RED)
        image.putpixel((249, 127), (0, 0, 0))
        red, black = image_buffers(image)
        self.assertEqual((len(red), len(black)), (4000, 4000))
        self.assertEqual(red[3999] & 1, 1)
        self.assertEqual(black[3999] & 1, 0)
        self.assertEqual(black[0] & 128, 0)

    def test_dashboard_handles_no_and_one_reading(self):
        self.assertEqual(draw_dashboard([]).size, (250, 128))
        now = datetime.now(timezone.utc)
        self.assertEqual(draw_dashboard([(now, 600, 30)]).size, (250, 128))

    def test_line_and_bars_remain_distinct_for_related_readings(self):
        now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        readings = [(now - timedelta(minutes=30), 400, 0),
                    (now - timedelta(minutes=15), 700, 100), (now, 400, 0)]
        image = draw_dashboard(readings, now=now)
        self.assertEqual(image.getpixel((123, 42)), RED)
        self.assertEqual(image.getpixel((123, 70)), (0, 0, 0))

    def test_fixed_time_axis_uses_timestamps_and_fits_visible_area(self):
        now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        readings = [(now - timedelta(minutes=40), 2000, 1000),
                    (now - timedelta(minutes=30), 400, 0),
                    (now - timedelta(minutes=25), 700, 30)]
        image = draw_dashboard(readings, now=now)
        self.assertEqual(image.getpixel((61, 42)), RED)
        self.assertTrue(all(image.getpixel((x, y)) == (255, 255, 255)
                            for x in range(250) for y in range(122, 128)))

    def test_co2_axis_uses_visible_peak_plus_100_with_400_bottom(self):
        now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        readings = [(now - timedelta(minutes=40), 3000, 100),
                    (now - timedelta(minutes=30), 400, 0),
                    (now - timedelta(minutes=15), 750, 0)]
        image = draw_dashboard(readings, now=now)
        self.assertEqual(image.getpixel((123, 40)), RED)
        self.assertEqual(image.getpixel((123, 32)), (255, 255, 255))

    def test_single_spike_does_not_change_chart_or_axis_scale(self):
        now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        baseline = [(now - timedelta(seconds=40 - 10 * index), 500, 20)
                    for index in range(5)]
        spiky = baseline.copy()
        spiky[2] = (spiky[2][0], 2500, 900)
        self.assertEqual(draw_dashboard(spiky, now=now).tobytes(),
                         draw_dashboard(baseline, now=now).tobytes())

    def test_sustained_rise_remains_visible(self):
        now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        baseline = [(now - timedelta(seconds=40 - 10 * index), 500, 20)
                    for index in range(5)]
        risen = baseline[:2] + [(stamp, 800, 150) for stamp, _, _ in baseline[2:]]
        self.assertNotEqual(draw_dashboard(risen, now=now).tobytes(),
                            draw_dashboard(baseline, now=now).tobytes())


class DataTests(unittest.TestCase):
    def test_failed_display_retries_before_night_interval(self):
        self.assertFalse(display_due(59, None, 60, 900))
        self.assertTrue(display_due(60, None, 60, 900))
        self.assertFalse(display_due(61, 60, None, 900))

    def test_csv_headers_dates_and_retention(self):
        now = datetime.now(timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            old = csv_path(directory, now - timedelta(days=9))
            old.write_text("old\n")
            append_reading(directory, (now, 500, 10))
            append_reading(directory, (now, 510, 11))
            self.assertFalse(old.exists())
            with csv_path(directory, now).open(newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], ["Timestamp", "Co2", "Tvoc"])
            self.assertEqual([row[1] for row in recent_readings(directory)], [500, 510])

    def test_sensor_retries_after_io_error(self):
        class BrokenSensor:
            data_ready = True

            @property
            def eco2(self):
                raise OSError("temporary I2C failure")

        reader = SensorReader()
        reader.sensor = BrokenSensor()
        self.assertIsNone(reader.read())
        self.assertIsNotNone(reader.sensor)
        reader.next_attempt = 0
        self.assertIsNone(reader.read())
        self.assertIsNotNone(reader.sensor)
        reader.next_attempt = 0
        self.assertIsNone(reader.read())
        self.assertIsNone(reader.sensor)


if __name__ == "__main__":
    unittest.main()
