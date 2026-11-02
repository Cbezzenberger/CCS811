# SPDX-License-Identifier: GPL-3.0-only
"""Validated, persistent timing settings shared by the imager and its UI."""

import json
import logging
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


LOG = logging.getLogger(__name__)
FIELDS = ("sample_seconds", "day_refresh_minutes", "night_refresh_minutes",
          "night_start", "night_end", "eco2_warning_ppm")


@dataclass(frozen=True)
class Settings:
    sample_seconds: int = 10
    day_refresh_minutes: int = 1
    night_refresh_minutes: int = 10
    night_start: str = "22:00"
    night_end: str = "08:00"
    eco2_warning_ppm: int = 1000

    @classmethod
    def from_values(cls, values):
        if set(values) != set(FIELDS):
            raise ValueError("All settings fields are required")
        numbers = {}
        for name, minimum, maximum in (("sample_seconds", 5, 60),
                                       ("day_refresh_minutes", 1, 60),
                                       ("night_refresh_minutes", 1, 120),
                                       ("eco2_warning_ppm", 401, 8192)):
            value = values[name]
            if type(value) is str and value.isdecimal():
                value = int(value)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be between {minimum} and {maximum}")
            numbers[name] = value
        times = {}
        for name in ("night_start", "night_end"):
            value = values[name]
            if not isinstance(value, str) or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value):
                raise ValueError(f"{name} must be in 24-hour HH:MM format")
            times[name] = value
        if times["night_start"] == times["night_end"]:
            raise ValueError("Night start and end must differ")
        return cls(**numbers, **times)

    def is_night(self, local_time):
        current = local_time.strftime("%H:%M")
        if self.night_start < self.night_end:
            return self.night_start <= current < self.night_end
        return current >= self.night_start or current < self.night_end

    def display_interval_seconds(self, local_time):
        minutes = self.night_refresh_minutes if self.is_night(local_time) else self.day_refresh_minutes
        return minutes * 60


def load_settings(path, fallback=None):
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as stream:
            values = json.load(stream)
            # Preserve timing choices saved before the warning setting existed.
            if isinstance(values, dict) and set(values) == set(FIELDS) - {"eco2_warning_ppm"}:
                values["eco2_warning_ppm"] = Settings().eco2_warning_ppm
            return Settings.from_values(values)
    except FileNotFoundError:
        return fallback or Settings()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        LOG.warning("Invalid settings at %s; keeping previous values", path, exc_info=True)
        return fallback or Settings()


def save_settings(path, settings):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".settings-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(asdict(settings), stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
