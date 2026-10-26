#!/usr/bin/env python3
"""
DINGO Ephemeral Gateway Node Cloud Relay
Receives internal VPC announcements from regional gateway nodes on 10.129.0.2:5150
and forwards them over the Pritunl mesh to active vehicle edge hubs (van01 / van02).
"""
import urllib.request
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

EDGE_HUBS = [
    "http://192.168.219.16:5150",
    "http://192.168.219.18:5150"
]

class RelayHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        path = self.path
        
        print(f"[RELAY] Received {path} from {self.client_address[0]}: {body[:100]}", flush=True)
        results = {}
        for hub in EDGE_HUBS:
            try:
                target_url = f"{hub}{path}"
                req = urllib.request.Request(
                    target_url,
                    data=body,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    results[hub] = resp.status
                    print(f"[RELAY] Forwarded to {target_url}: HTTP {resp.status}", flush=True)
            except Exception as e:
                results[hub] = str(e)
                print(f"[RELAY] Failed to forward to {target_url}: {e}", flush=True)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": True, "relayed": True, "targets": results}).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"ok","service":"dingo-gateway-relay"}')

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = HTTPServer(('10.129.0.2', 5150), RelayHandler)
    server.serve_forever()
