import os
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler

try:
    from upstash_redis import Redis
    _redis = Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])
except Exception:
    _redis = None

def _r():
    if _redis is None:
        raise RuntimeError("Redis not configured")
    return _redis

def get_all_records(limit=200):
    ids = _r().zrange("ehr:index", 0, limit - 1, rev=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    records = []
    for rid in ids:
        raw = _r().get(f"ehr:rec:{rid}")
        if raw:
            rec = json.loads(raw) if isinstance(raw, str) else raw
            rec["is_today"] = rec.get("date") == today
            records.append(rec)
    return records


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_GET(self):
        try:
            self._json(get_all_records())
        except Exception as e:
            self._json({"error": str(e)}, 500)

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