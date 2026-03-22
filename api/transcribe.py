import os
import json
import cgi
import io
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

DEEPGRAM_URL = (
    "https://api.deepgram.com/v1/listen"
    "?model=nova-2"
    "&smart_format=true"
    "&detect_language=true"
    "&punctuate=true"
)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_POST(self):
        api_key = os.environ.get("DEEPGRAM_API_KEY", "")
        if not api_key:
            self._json({"error": "DEEPGRAM_API_KEY not set"}, 500); return

        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE":   content_type,
            "CONTENT_LENGTH": str(length),
        }
        try:
            form = cgi.FieldStorage(
                fp=io.BytesIO(raw_body),
                environ=environ,
                keep_blank_values=True,
            )
            audio_field = form["audio"]
            audio_bytes = audio_field.file.read()
            audio_ctype = audio_field.type or "audio/webm"
        except Exception as e:
            self._json({"error": f"Could not parse audio: {e}"}, 400); return

        try:
            req = urllib.request.Request(
                DEEPGRAM_URL,
                data=audio_bytes,
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type":  audio_ctype,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                dg = json.loads(resp.read())

            transcript = (
                dg.get("results", {})
                  .get("channels", [{}])[0]
                  .get("alternatives", [{}])[0]
                  .get("transcript", "")
            )
            detected = (
                dg.get("results", {})
                  .get("channels", [{}])[0]
                  .get("detected_language", "unknown")
            )
            self._json({"text": transcript, "language": detected})

        except urllib.error.HTTPError as e:
            self._json({"error": f"Deepgram error {e.code}: {e.read().decode()}"}, 500)
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