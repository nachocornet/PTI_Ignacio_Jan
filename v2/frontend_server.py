#!/usr/bin/env python3
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from settings import SETTINGS


ALLOWED_PATHS = {
    "/frontend.html": "frontend.html",
    "/frontend.variables.js": "frontend.variables.js",
}


class FrontendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/frontend.html")
            self.end_headers()
            return

        filename = ALLOWED_PATHS.get(self.path)
        if not filename or not os.path.exists(filename):
            self.send_error(404, "Not found")
            return

        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

        with open(filename, "rb") as f:
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
    print(f"Frontend server on http://{SETTINGS.app_host}:{SETTINGS.frontend_port}/frontend.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
