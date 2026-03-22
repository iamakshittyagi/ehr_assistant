import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

def get_redis():
    from upstash_redis import Redis
    return Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])

def get_record(rid):
    raw = get_redis().get(f"ehr:rec:{rid}")
    if not raw: return None
    return json.loads(raw) if isinstance(raw, str) else raw

def delete_record(rid):
    r = get_redis()
    deleted = r.delete(f"ehr:rec:{rid}")
    r.zrem("ehr:index", rid)
    return deleted > 0

def parse_id(path, query):
    qs = urllib.parse.parse_qs(query)
    if "id" in qs: return qs["id"][0]
    parts = [p for p in path.split("/") if p]
    return parts[-1] if len(parts) >= 2 else None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()
    def do_GET(self):
        rid = parse_id(self.path, self._query())
        if not rid: self._json({"error": "id required"}, 400); return
        rec = get_record(rid)
        self._json(rec) if rec else self._json({"error": "Not found"}, 404)
    def do_DELETE(self):
        rid = parse_id(self.path, self._query())
        if not rid: self._json({"error": "id required"}, 400); return
        ok = delete_record(rid)
        self._json({"status": "deleted"}) if ok else self._json({"error": "Not found"}, 404)
    def _query(self):
        return self.path.split("?", 1)[1] if "?" in self.path else ""
    def _cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Content-Type", "application/json")
    def _json(self, obj, status=200):
        self._cors()
        self.send_response(status)
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
    def log_message(self, *_): pass
