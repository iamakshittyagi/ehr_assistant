import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL    = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert medical AI assistant. Extract structured EHR data from the transcript.
- Return ONLY valid JSON, no explanation, no markdown, no backticks
- All output must be in English
- symptoms MUST be an array of strings
- treatment MUST be an array of strings
Return EXACTLY this JSON shape:
{"patient_name":"","age":"","gender":"","doctor_name":"","diagnosis":"","symptoms":[],"treatment":[],"followup":"","prakriti":"","notes":""}"""


def compute_confidence(data):
    fields = ["patient_name","age","gender","diagnosis","symptoms","treatment"]
    return round(sum(1 for f in fields if data.get(f)) / len(fields), 2)

def normalize(data):
    def clean(v): return str(v).strip() if v else ""
    def lst(v):
        if isinstance(v, list): return [str(i).strip() for i in v if i]
        if isinstance(v, str): return [x.strip() for x in v.split(",") if x.strip()]
        return []
    return {
        "patient_name": clean(data.get("patient_name")),
        "age":          clean(data.get("age")),
        "gender":       clean(data.get("gender")),
        "doctor_name":  clean(data.get("doctor_name")),
        "diagnosis":    clean(data.get("diagnosis")),
        "symptoms":     lst(data.get("symptoms")),
        "treatment":    lst(data.get("treatment")),
        "followup":     clean(data.get("followup")),
        "prakriti":     clean(data.get("prakriti")),
        "notes":        clean(data.get("notes")),
    }

def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner = lines[1:] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).rstrip("`").strip()
    return text


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_POST(self):
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            self._json({"error": "GROQ_API_KEY not set"}, 500); return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._json({"error": "Invalid JSON body"}, 400); return

        transcript = (body.get("transcript") or "").strip()
        if not transcript:
            self._json({"error": "No transcript provided"}, 400); return

        payload = json.dumps({
            "model": MODEL,
            "temperature": 0.1,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Transcript:\n{transcript}"}
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
            raw  = strip_fences(result["choices"][0]["message"]["content"])
            data = normalize(json.loads(raw))
            data["confidence"] = compute_confidence(data)
            self._json(data)
        except urllib.error.HTTPError as e:
            self._json({"error": f"Groq {e.code}: {e.read().decode()}"}, 500)
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