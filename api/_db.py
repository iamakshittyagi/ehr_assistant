import os
import json
import uuid
from datetime import datetime

try:
    from upstash_redis import Redis
    _redis = Redis(
        url=os.environ["KV_REST_API_URL"],
        token=os.environ["KV_REST_API_TOKEN"],
    )
except Exception:
    _redis = None

RECORDS_INDEX = "ehr:index"
RECORD_PREFIX = "ehr:rec:"


def _r():
    if _redis is None:
        raise RuntimeError("Redis not configured. Set KV_REST_API_URL and KV_REST_API_TOKEN.")
    return _redis


def save_record(data: dict) -> str:
    rid = str(uuid.uuid4())
    now = datetime.utcnow()
    data["id"]         = rid
    data["date"]       = now.strftime("%Y-%m-%d")
    data["created_at"] = now.isoformat()
    _r().set(RECORD_PREFIX + rid, json.dumps(data))
    _r().zadd(RECORDS_INDEX, {rid: now.timestamp()})
    return rid


def get_all_records(limit: int = 200) -> list:
    ids = _r().zrange(RECORDS_INDEX, 0, limit - 1, rev=True)
    records = []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for rid in ids:
        raw = _r().get(RECORD_PREFIX + rid)
        if raw:
            rec = json.loads(raw) if isinstance(raw, str) else raw
            rec["is_today"] = rec.get("date") == today
            records.append(rec)
    return records


def get_record_by_id(rid: str):
    raw = _r().get(RECORD_PREFIX + rid)
    if not raw:
        return None
    return json.loads(raw) if isinstance(raw, str) else raw


def delete_record(rid: str) -> bool:
    deleted = _r().delete(RECORD_PREFIX + rid)
    _r().zrem(RECORDS_INDEX, rid)
    return deleted > 0


def search_records(query: str) -> list:
    query = query.lower()
    all_recs = get_all_records(500)
    return [
        r for r in all_recs
        if query in (r.get("patient_name") or "").lower()
        or query in (r.get("diagnosis") or "").lower()
    ]