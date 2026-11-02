# SPDX-License-Identifier: GPL-3.0-only
import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFont

from main import ALERT_PAGE_SECONDS, display_due, eco2_alert, next_page
from printToEpaper import image_buffers
from sensorDataGen import SensorReader, append_reading, csv_path, recent_readings
from sensorPlotEpaper import RED, draw_dashboard, draw_warning


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

    def test_warning_uses_white_placard_and_legible_palette(self):
        image = draw_warning(1200)
        self.assertEqual(image.size, (250, 128))
        self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(image.getpixel((17, 16)), RED)
        self.assertEqual(image.getpixel((221, 99)), RED)
        self.assertTrue(any(image.getpixel((x, y)) == RED
                            for x in range(60, 190) for y in range(29, 55)))
        self.assertTrue(any(image.getpixel((x, y)) == (0, 0, 0)
                            for x in range(30, 220) for y in range(58, 88)))
        self.assertEqual({image.getpixel((x, y)) for x in range(250) for y in range(128)},
                         {RED, (0, 0, 0), (255, 255, 255)})

    def test_warning_labels_keep_every_glyph_pixel(self):
        image = draw_warning(1200)
        labels = (("CAUTION", 29, 3, RED),
                  ("AIR QUALITY ESTIMATE", 58, 1, (0, 0, 0)),
                  ("1200 ppm eCO2", 69, 1, (0, 0, 0)),
                  ("CHECK VENTILATION", 80, 1, (0, 0, 0)),
                  ("eCO2 HIGH", 92, 3, RED))
        for text, top, scale, color in labels:
            with self.subTest(text=text):
                reference = Image.new("1", (300, 32))
                ImageDraw.Draw(reference).text((8, 8), text, fill=1,
                                               font=ImageFont.load_default())
                bounds = reference.getbbox()
                width = (bounds[2] - bounds[0]) * scale
                height = (bounds[3] - bounds[1]) * scale
                left = (250 - width) // 2
                expected = sum(reference.getpixel((x, y))
                               for x in range(300) for y in range(32)) * scale * scale
                actual = sum(image.getpixel((x, y)) == color
                             for x in range(left, left + width)
                             for y in range(top, top + height))
                self.assertEqual(actual, expected)


class DataTests(unittest.TestCase):
    def test_warning_alternates_with_graph_on_short_interval(self):
        self.assertEqual(next_page(True, "graph"), "warning")
        self.assertEqual(next_page(True, "warning"), "graph")
        self.assertEqual(next_page(False, "warning"), "graph")
        self.assertFalse(display_due(ALERT_PAGE_SECONDS - 1, 0, None, ALERT_PAGE_SECONDS))
        self.assertTrue(display_due(ALERT_PAGE_SECONDS, 0, None, ALERT_PAGE_SECONDS))

    def test_warning_requires_sustained_eco2_and_waits_for_warmup(self):
        now = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
        readings = [(now - timedelta(seconds=20), 500, 0),
                    (now - timedelta(seconds=10), 1500, 50), (now, 500, 0)]
        self.assertFalse(eco2_alert(readings, 1000))
        readings[-1] = (now, 1200, 50)
        self.assertTrue(eco2_alert(readings, 1000))
        self.assertFalse(eco2_alert(readings, 1000, conditioning_seconds=1))
        self.assertTrue(eco2_alert(readings, 1100))
        self.assertFalse(eco2_alert(readings, 1300))
        self.assertFalse(eco2_alert(readings[:2], 1000))
        self.assertTrue(eco2_alert(readings[1:], 1000))

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
