import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from _db import get_record_by_id, delete_record


def _parse_id(path: str, query: str) -> str:
    qs = urllib.parse.parse_qs(query)
    if "id" in qs:
        return qs["id"][0]
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2:
        return parts[-1]
    return None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_GET(self):
        rid = _parse_id(self.path, self._query())
        if not rid:
            self._json({"error": "id required"}, 400); return
        rec = get_record_by_id(rid)
        if rec:
            self._json(rec)
        else:
            self._json({"error": "Record not found"}, 404)

    def do_DELETE(self):
        rid = _parse_id(self.path, self._query())
        if not rid:
            self._json({"error": "id required"}, 400); return
        ok = delete_record(rid)
        if ok:
            self._json({"status": "deleted"})
        else:
            self._json({"error": "Record not found"}, 404)

    def _query(self):
        return self.path.split("?", 1)[1] if "?" in self.path else ""

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