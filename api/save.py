import os
import json
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._ok({"error": str(e)}); return

        if not data.get("patient_name", "").strip():
            self._ok({"error": "patient_name required"}); return

        try:
            import upstash_redis
            self._ok({"debug": "upstash imported ok"})
        except ImportError as e:
            self._ok({"error": "import failed: " + str(e)})
        except Exception as e:
            self._ok({"error": "other error: " + str(e), "type": type(e).__name__})

    def _cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Content-Type", "application/json")

    def _ok(self, obj, status=200):
        self._cors()
        self.send_response(status)
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, *a): pass
