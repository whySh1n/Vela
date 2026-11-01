"""Desktop Vela: a local page on 127.0.0.1, opened in the browser."""

from __future__ import annotations

import json
import os
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import library
import radio

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "desk_web")
FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/library":
            self._send(200, json.dumps(library.load()))
            return
        if parsed.path == "/api/search":
            query = urllib.parse.parse_qs(parsed.query)
            def one(key):
                values = query.get(key) or [""]
                return values[0][:80]
            try:
                stations = radio.search(one("name"), one("tag"), one("country"))
            except RuntimeError as exc:
                self._send(200, json.dumps({"ok": False, "stations": [], "message": str(exc)}))
                return
            self._send(200, json.dumps({"ok": True, "stations": stations, "message": ""}))
            return
        item = FILES.get(parsed.path)
        if not item:
            self._send(404, "Not found", "text/plain; charset=utf-8")
            return
        name, content_type = item
        try:
            with open(os.path.join(ROOT, name), "rb") as handle:
                payload = handle.read()
        except OSError:
            self._send(404, "Not found", "text/plain; charset=utf-8")
            return
        self._send(200, payload, content_type)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/library":
            self._send(404, json.dumps({"ok": False}))
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 256_000:
            self._send(400, json.dumps({"ok": False, "message": "Bad library"}))
            return
        try:
            raw = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, ValueError):
            self._send(400, json.dumps({"ok": False, "message": "Bad library"}))
            return
        if not isinstance(raw, dict):
            self._send(400, json.dumps({"ok": False}))
            return
        saved = library.save(
            {
                "favorites": raw.get("favorites") or [],
                "custom": raw.get("custom") or [],
                "volume": raw.get("volume", 82),
            }
        )
        self._send(200, json.dumps({"ok": True, **saved}))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    print(f"Vela desk is on {url}")
    print("Leave this running. Ctrl-C closes the desk.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
