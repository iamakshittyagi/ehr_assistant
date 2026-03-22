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
    query = (request.args.get("q") or "").strip().lower()
    if not query:
        return Response(json.dumps([]), headers=HEADERS)
    try:
        r = get_redis()
        ids = r.zrange("ehr:index", 0, 499, rev=True)
        results = []
        for rid in ids:
            raw = r.get(f"ehr:rec:{rid}")
            if raw:
                rec = json.loads(raw) if isinstance(raw, str) else raw
                if query in (rec.get("patient_name") or "").lower() or \
                   query in (rec.get("diagnosis") or "").lower():
                    results.append(rec)
        return Response(json.dumps(results), headers=HEADERS)
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, headers=HEADERS)
