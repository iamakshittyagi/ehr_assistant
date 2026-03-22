import os
import json
import uuid
from datetime import datetime

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Content-Type": "application/json",
}

def get_redis():
    from upstash_redis import Redis
    return Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])

def handler(request):
    if request.method == "OPTIONS":
        return Response("", headers=HEADERS)
    try:
        data = request.json()
    except Exception:
        return Response(json.dumps({"error": "Invalid JSON"}), status=400, headers=HEADERS)
    if not isinstance(data, dict) or not data.get("patient_name", "").strip():
        return Response(json.dumps({"error": "patient_name required"}), status=400, headers=HEADERS)
    for field in ("symptoms", "treatment"):
        v = data.get(field)
        if isinstance(v, list):
            data[field] = "; ".join(v)
    try:
        r = get_redis()
        rid = str(uuid.uuid4())
        now = datetime.utcnow()
        data["id"] = rid
        data["date"] = now.strftime("%Y-%m-%d")
        data["created_at"] = now.isoformat()
        r.set(f"ehr:rec:{rid}", json.dumps(data))
        r.zadd("ehr:index", {rid: now.timestamp()})
        return Response(json.dumps({"status": "saved", "id": rid}), headers=HEADERS)
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, headers=HEADERS)
