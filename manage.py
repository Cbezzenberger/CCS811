# SPDX-License-Identifier: GPL-3.0-only
"""Loopback-only settings page, intended for access through SSH forwarding."""

import html
import logging
import os
import secrets
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from sensorDataGen import recent_readings
from settings import FIELDS, Settings, load_settings, save_settings


LOG = logging.getLogger(__name__)
DATA_DIR = Path(os.environ.get("COIMAGER_DATA_DIR", Path(__file__).resolve().parent / "csvfiles"))
PORT = 8765


class SettingsHandler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        LOG.info("HTTP %s", format_string % args)

    def _trusted_host(self):
        return (self.client_address[0] == "127.0.0.1"
                and self.headers.get_all("Host") == [f"127.0.0.1:{self.server.server_port}"])

    def _respond(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def _page(self, error="", status=200):
        settings = load_settings(self.server.settings_path)
        local_now = datetime.now().astimezone()
        interval = settings.display_interval_seconds(local_now.time()) // 60
        recent = recent_readings(self.server.data_dir, limit=1)
        if recent:
            timestamp, co2, tvoc = recent[-1]
            sample = (f"Last sample: {co2} ppm eCO2 · {tvoc} ppb TVOC · "
                      f"{timestamp.astimezone():%Y-%m-%d %H:%M:%S}")
        else:
            sample = "Waiting for the first sensor reading"
        error_html = f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
        values = {name: html.escape(str(getattr(settings, name)), quote=True) for name in FIELDS}
        token = html.escape(self.server.csrf_token, quote=True)
        page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>eCO2 imager settings</title>
<style>
body{{font:16px system-ui,sans-serif;margin:0;background:#f5f5f2;color:#192323}}
main{{max-width:560px;margin:2rem auto;padding:1.5rem;background:white;border:1px solid #ddd;border-radius:10px}}
h1{{font-size:1.5rem;margin-top:0}}p{{line-height:1.5}}fieldset{{border:1px solid #ccc;border-radius:6px;margin:1rem 0;padding:1rem}}
legend{{font-weight:700}}label{{display:block;margin:.8rem 0 .3rem}}input{{font:inherit;padding:.5rem;width:100%;box-sizing:border-box}}
button{{font:inherit;background:#193b3b;color:white;border:0;border-radius:5px;padding:.7rem 1.2rem;cursor:pointer}}
.muted{{color:#475757}}.error{{color:#9b1b1b;font-weight:700}}
</style></head><body><main>
<h1>eCO2 imager settings</h1>
<p class="muted">{html.escape(sample)}</p>
<p>Current display refresh: every {interval} minute{'s' if interval != 1 else ''}.
Local time: {local_now:%H:%M} {html.escape(local_now.tzname() or '')}.</p>
{error_html}
<form action="/settings" method="post">
<input type="hidden" name="csrf_token" value="{token}">
<fieldset><legend>Sampling and display</legend>
<label for="sample_seconds">Sensor sample interval (seconds)</label>
<input id="sample_seconds" name="sample_seconds" type="number" min="5" max="60" required value="{values['sample_seconds']}">
<label for="day_refresh_minutes">Day display refresh (minutes)</label>
<input id="day_refresh_minutes" name="day_refresh_minutes" type="number" min="1" max="60" required value="{values['day_refresh_minutes']}">
<label for="night_refresh_minutes">Night display refresh (minutes)</label>
<input id="night_refresh_minutes" name="night_refresh_minutes" type="number" min="1" max="120" required value="{values['night_refresh_minutes']}">
</fieldset>
<fieldset><legend>Night window</legend>
<p class="muted">Uses the Pi's local time. A window can cross midnight.</p>
<label for="night_start">Starts at</label><input id="night_start" name="night_start" type="time" required value="{values['night_start']}">
<label for="night_end">Ends at</label><input id="night_end" name="night_end" type="time" required value="{values['night_end']}">
</fieldset><button type="submit">Save settings</button></form>
</main></body></html>"""
        self._respond(status, page)

    def do_GET(self):
        if not self._trusted_host():
            self._respond(403, "Forbidden")
        elif self.path != "/":
            self._respond(404, "Not found")
        else:
            self._page()

    def do_POST(self):
        if not self._trusted_host():
            LOG.warning("Rejected settings POST: unexpected Host or peer")
            self._respond(403, "Forbidden")
            return
        if self.path != "/settings":
            self._respond(404, "Not found")
            return
        length = self.headers.get("Content-Length", "")
        if not length.isdecimal() or int(length) > 4096:
            self._respond(413, "Invalid request size")
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/x-www-form-urlencoded":
            self._respond(415, "Unsupported content type")
            return
        try:
            form = parse_qs(self.rfile.read(int(length)).decode("utf-8"),
                            keep_blank_values=True, strict_parsing=True, max_num_fields=6)
            if set(form) != set(FIELDS) | {"csrf_token"} or any(len(values) != 1 for values in form.values()):
                raise ValueError("All timing fields are required")
            if not secrets.compare_digest(form["csrf_token"][0], self.server.csrf_token):
                LOG.warning("Rejected settings POST: invalid form token")
                self._page("This form expired after a restart. Reload the page and try again.", status=403)
                return
            settings = Settings.from_values({name: form[name][0] for name in FIELDS})
            save_settings(self.server.settings_path, settings)
        except (UnicodeDecodeError, ValueError) as error:
            self._page(str(error), status=400)
            return
        except OSError:
            LOG.exception("Could not save settings")
            self._respond(500, "Could not save settings")
            return
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()


def create_server(data_dir=DATA_DIR, port=PORT):
    server = HTTPServer(("127.0.0.1", port), SettingsHandler)
    server.data_dir = Path(data_dir)
    server.settings_path = server.data_dir / "settings.json"
    server.csrf_token = secrets.token_urlsafe(32)
    return server


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with create_server() as server:
        LOG.info("Settings page listening on 127.0.0.1:%s", server.server_port)
        server.serve_forever()


if __name__ == "__main__":
    main()
