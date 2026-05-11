#!/usr/bin/env python3
"""Tiny HTTP forward proxy for Polymarket CLOB — Render (US/Oregon), zero deps."""
import os
import json
import http.client
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

TARGET_HOST = "clob.polymarket.com"
TARGET_SCHEME = "https"
PORT = int(os.environ.get("PORT", 10000))


class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._forward("GET")

    def do_POST(self):
        self._forward("POST")

    def do_DELETE(self):
        self._forward("DELETE")

    def do_PUT(self):
        self._forward("PUT")

    def do_OPTIONS(self):
        self._forward("OPTIONS")

    def _forward(self, method):
        # Parse path; default to /
        path = self.path if self.path else "/"

        conn = http.client.HTTPSConnection(TARGET_HOST, timeout=45)
        try:
            body = None
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                body = self.rfile.read(content_length)

            # Build headers, strip hop-by-hop
            hdrs = {}
            for key, value in self.headers.items():
                kl = key.lower()
                if kl not in ("host", "content-length", "connection"):
                    hdrs[key] = value

            conn.request(method, path, body=body, headers=hdrs)
            resp = conn.getresponse()

            self.send_response(resp.status)
            for key, value in resp.getheaders():
                kl = key.lower()
                if kl not in ("transfer-encoding", "connection"):
                    self.send_header(key, value)

            # Read full body
            body_bytes = resp.read()
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)

        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"proxy error: {e}".encode())
        finally:
            conn.close()

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}", flush=True)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Proxy :{PORT} -> https://{TARGET_HOST}", flush=True)
    server.serve_forever()