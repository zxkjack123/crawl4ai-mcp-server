#!/usr/bin/env python3
"""Mock HTTP server for healthcheck.sh integration tests.

Responds to /health (GET) and /read_url (POST) with configurable behaviour
controlled by the first command-line argument:

  healthy    → /health returns 200, /read_url returns valid content
  health_down → /health returns 500
  read_error → /read_url returns {"error": "..."} (no "content" key)
  read_empty → /read_url returns {} (no "content" key)

Prints the actual port on the first line of stdout, then serves forever.
"""

import json
import sys
import http.server
import socketserver


MODE = sys.argv[1] if len(sys.argv) > 1 else "healthy"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if MODE == "health_down":
            self.send_response(500)
            self.end_headers()
            return
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/read_url":
            if MODE == "read_error":
                body = json.dumps({"error": "crawl failed"}).encode()
            elif MODE == "read_empty":
                body = json.dumps({}).encode()
            else:
                body = json.dumps({
                    "url": "https://example.com",
                    "content": "# Example Domain\nHello world",
                    "format": "markdown",
                }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


httpd = socketserver.TCPServer(("127.0.0.1", 0), Handler)
actual_port = httpd.server_address[1]
print(actual_port, flush=True)
httpd.serve_forever()
