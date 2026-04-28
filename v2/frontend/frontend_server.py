#!/usr/bin/env python3
import mimetypes
import os
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.settings import SETTINGS


FRONTEND_DIR = Path(__file__).resolve().parent


ALLOWED_PATHS = {
    "/frontend_portal.html": "frontend_portal.html",
    "/issuer_dashboard.html": "issuer_dashboard.html",
    "/verifier_dashboard.html": "verifier_dashboard.html",
    "/frontend.variables.js": "frontend.variables.js",
}


class FrontendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/frontend_portal.html")
            self.end_headers()
            return

        filename = ALLOWED_PATHS.get(self.path)
        if not filename:
            self.send_error(404, "Not found")
            return

        file_path = FRONTEND_DIR / filename
        if not file_path.exists():
            self.send_error(404, "Not found")
            return

        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


def main() -> None:
    server = HTTPServer((SETTINGS.app_host, SETTINGS.frontend_port), FrontendHandler)
    print(f"Frontend server on http://{SETTINGS.app_host}:{SETTINGS.frontend_port}/frontend_portal.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
