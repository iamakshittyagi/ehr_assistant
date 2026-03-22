import os
import json
import urllib.request
import urllib.error

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert medical AI assistant. Extract structured EHR data from the transcript.
- Return ONLY valid JSON, no explanation, no markdown, no backticks
- All output must be in English
- symptoms MUST be an array of strings
- treatment MUST be an array of strings
Return EXACTLY this JSON shape:
{"patient_name":"","age":"","gender":"","doctor_name":"","diagnosis":"","symptoms":[],"treatment":[],"followup":"","prakriti":"","notes":""}"""

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Content-Type": "application/json",
}

def normalize(data):
    def clean(v): return str(v).strip() if v else ""
    def lst(v):
        if isinstance(v, list): return [str(i).strip() for i in v if i]
        if isinstance(v, str): return [x.strip() for x in v.split(",") if x.strip()]
        return []
    return {
        "patient_name": clean(data.get("patient_name")),
        "age": clean(data.get("age")),
        "gender": clean(data.get("gender")),
        "doctor_name": clean(data.get("doctor_name")),
        "diagnosis": clean(data.get("diagnosis")),
        "symptoms": lst(data.get("symptoms")),
        "treatment": lst(data.get("treatment")),
        "followup": clean(data.get("followup")),
        "prakriti": clean(data.get("prakriti")),
        "notes": clean(data.get("notes")),
    }

def compute_confidence(data):
    fields = ["patient_name","age","gender","diagnosis","symptoms","treatment"]
    return round(sum(1 for f in fields if data.get(f)) / len(fields), 2)

def handler(request):
    if request.method == "OPTIONS":
        return Response("", headers=HEADERS)

    try:
        body = request.json()
    except Exception:
        return Response(json.dumps({"error": "Invalid JSON"}), status=400, headers=HEADERS)

    transcript = (body.get("transcript") or "").strip()
    if not transcript:
        return Response(json.dumps({"error": "No transcript"}), status=400, headers=HEADERS)

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return Response(json.dumps({"error": "GROQ_API_KEY not set"}), status=500, headers=HEADERS)

    payload = json.dumps({
        "model": MODEL,
        "temperature": 0.1,
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Transcript:\n{transcript}"}
        ],
        "response_format": {"type": "json_object"}
    }).encode()

    req = urllib.request.Request(
        GROQ_URL, data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        raw = result["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()
        data = normalize(json.loads(raw))
        data["confidence"] = compute_confidence(data)
        return Response(json.dumps(data), headers=HEADERS)
    except urllib.error.HTTPError as e:
        return Response(json.dumps({"error": f"Groq {e.code}: {e.read().decode()}"}), status=500, headers=HEADERS)
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, headers=HEADERS)
