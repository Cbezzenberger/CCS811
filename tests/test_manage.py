# SPDX-License-Identifier: GPL-3.0-only
import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from manage import create_server
from settings import load_settings


class ManagementSecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.server = create_server(self.directory.name, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()
        self.directory.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def form(self, token):
        return urlencode({"csrf_token": token, "sample_seconds": "15",
                          "day_refresh_minutes": "2", "night_refresh_minutes": "12",
                          "night_start": "23:00", "night_end": "07:00"})

    def test_loopback_host_and_csrf_are_required(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.assertEqual(self.request("GET", "/", headers={"Host": "evil.example"})[0], 403)
        status, page = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(self.server.csrf_token, page)
        form = self.form(self.server.csrf_token)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.assertEqual(self.request("POST", "/settings", self.form("bad"), headers)[0], 403)
        headers["Origin"] = self.origin
        self.assertEqual(self.request("POST", "/settings", self.form("bad"), headers)[0], 403)
        self.assertFalse((Path(self.directory.name) / "settings.json").exists())

    def test_form_from_before_restart_explains_expiry(self):
        old_token = self.server.csrf_token
        self.server.csrf_token = "replacement-token"
        status, page = self.request("POST", "/settings", self.form(old_token),
                                    {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 403)
        self.assertIn("expired after a restart", page)
        self.assertIn("replacement-token", page)

    def test_valid_post_saves_settings_and_invalid_values_do_not(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Origin": "null"}
        status, _ = self.request("POST", "/settings", self.form(self.server.csrf_token), headers)
        self.assertEqual(status, 303)
        path = Path(self.directory.name) / "settings.json"
        self.assertEqual(load_settings(path).night_refresh_minutes, 12)
        invalid = self.form(self.server.csrf_token).replace("sample_seconds=15", "sample_seconds=1")
        self.assertEqual(self.request("POST", "/settings", invalid, headers)[0], 400)
        self.assertEqual(load_settings(path).sample_seconds, 15)


if __name__ == "__main__":
    unittest.main()
