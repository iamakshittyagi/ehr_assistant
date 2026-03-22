import os
import json

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
    rid = request.args.get("id", "").strip()
    if not rid:
        return Response(json.dumps({"error": "id required"}), status=400, headers=HEADERS)
    try:
        r = get_redis()
        if request.method == "DELETE":
            r.delete(f"ehr:rec:{rid}")
            r.zrem("ehr:index", rid)
            return Response(json.dumps({"status": "deleted"}), headers=HEADERS)
        raw = r.get(f"ehr:rec:{rid}")
        if not raw:
            return Response(json.dumps({"error": "Not found"}), status=404, headers=HEADERS)
        rec = json.loads(raw) if isinstance(raw, str) else raw
        return Response(json.dumps(rec), headers=HEADERS)
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, headers=HEADERS)
