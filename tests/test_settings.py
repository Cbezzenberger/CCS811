# SPDX-License-Identifier: GPL-3.0-only
import json
import tempfile
import unittest
from datetime import time
from pathlib import Path

from settings import Settings, load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_night_window_crosses_midnight(self):
        settings = Settings()
        self.assertEqual(settings.display_interval_seconds(time(21, 59)), 60)
        self.assertEqual(settings.display_interval_seconds(time(22, 0)), 600)
        self.assertEqual(settings.display_interval_seconds(time(7, 59)), 600)
        self.assertEqual(settings.display_interval_seconds(time(8, 0)), 60)

    def test_validated_settings_round_trip(self):
        values = {"sample_seconds": "15", "day_refresh_minutes": "2",
                  "night_refresh_minutes": "12", "night_start": "23:30", "night_end": "06:30"}
        settings = Settings.from_values(values)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            save_settings(path, settings)
            self.assertEqual(load_settings(path), settings)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_invalid_values_are_rejected(self):
        values = {"sample_seconds": "1", "day_refresh_minutes": "2",
                  "night_refresh_minutes": "12", "night_start": "22:00", "night_end": "08:00"}
        with self.assertRaises(ValueError):
            Settings.from_values(values)
        values["sample_seconds"] = "10"
        values["night_end"] = "22:00"
        with self.assertRaises(ValueError):
            Settings.from_values(values)

    def test_invalid_file_keeps_previous_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({"sample_seconds": 0}))
            previous = Settings(sample_seconds=15)
            self.assertEqual(load_settings(path, previous), previous)


if __name__ == "__main__":
    unittest.main()
