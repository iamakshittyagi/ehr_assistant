import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from _db import search_records


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_GET(self):
        qs = {}
        if "?" in self.path:
            qs = urllib.parse.parse_qs(self.path.split("?", 1)[1])
        query = (qs.get("q") or [""])[0].strip()
        if not query:
            self._json([]); return
        try:
            results = search_records(query)
            self._json(results)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Content-Type", "application/json")

    def _json(self, obj, status=200):
        self._cors()
        self.send_response(status)
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, *_): pass