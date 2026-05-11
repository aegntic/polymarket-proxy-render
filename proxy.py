#!/usr/bin/env python3
"""Tiny HTTP forward proxy for Polymarket CLOB — Render (US/Oregon)."""
import os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx

TARGET = "https://clob.polymarket.com"
PORT = int(os.environ.get("PORT", 10000))

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self): self._forward("GET")
    def do_POST(self): self._forward("POST")
    def do_DELETE(self): self._forward("DELETE")
    
    def _forward(self, method):
        target_url = TARGET + self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        headers = {}
        for key, value in self.headers.items():
            if key.lower() not in ("host", "content-length", "connection"):
                headers[key] = value
        
        try:
            client = httpx.Client(timeout=45, follow_redirects=False)
            if method == "GET":
                resp = client.get(target_url, headers=headers)
            elif method == "POST":
                resp = client.post(target_url, content=body, headers=headers)
            else:
                resp = client.request(method, target_url, content=body, headers=headers)
            
            self.send_response(resp.status_code)
            for key, value in resp.headers.items():
                if key.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(resp.content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f'proxy error: {e}'.encode())
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}", flush=True)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Proxy :{PORT} -> {TARGET}", flush=True)
    server.serve_forever()
