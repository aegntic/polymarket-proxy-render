#!/usr/bin/env python3
"""
Tiny HTTP forward proxy for Polymarket CLOB — bypasses AU geoblock.
Deploy on Render.com free tier (US/Oregon region).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import ssl
import os
import sys

TARGET = "https://clob.polymarket.com"
PORT = int(os.environ.get("PORT", 10000))

ssl_ctx = ssl.create_default_context()


class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._forward("GET")

    def do_POST(self):
        self._forward("POST")

    def do_DELETE(self):
        self._forward("DELETE")

    def _forward(self, method):
        target_url = TARGET + self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(target_url, data=body, method=method)

        for key, value in self.headers.items():
            if key.lower() not in ("host", "content-length", "connection"):
                req.add_header(key, value)

        try:
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=45) as resp:
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f'{{"error":"{e}"}}'.encode())

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}", flush=True)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Proxy on :{PORT} → {TARGET}", flush=True)
    server.serve_forever()
