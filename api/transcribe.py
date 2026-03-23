import os
import json
import io
import re
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&detect_language=true&punctuate=true"

def parse_multipart(body: bytes, content_type: str):
    """
    Minimal multipart/form-data parser that doesn't rely on the
    deprecated/removed `cgi` module (dropped in Python 3.13).
    Returns (audio_bytes, audio_content_type) or raises ValueError.
    """
    m = re.search(r'boundary=([^\s;]+)', content_type)
    if not m:
        raise ValueError("No boundary in Content-Type")
    boundary = m.group(1).strip('"').encode()

    # Split on --boundary
    delimiter = b"--" + boundary
    parts = body.split(delimiter)

    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        # Separate headers from body (blank line = \r\n\r\n)
        if b"\r\n\r\n" not in part:
            continue
        headers_raw, data = part.split(b"\r\n\r\n", 1)
        # Strip trailing --\r\n (last boundary marker)
        data = data.rstrip(b"\r\n--")

        headers_text = headers_raw.decode(errors="replace")
        if 'name="audio"' not in headers_text:
            continue

        # Extract Content-Type of the part if present
        ct_match = re.search(r'Content-Type:\s*(\S+)', headers_text, re.IGNORECASE)
        part_ctype = ct_match.group(1).strip() if ct_match else "audio/webm"
        return data, part_ctype

    raise ValueError("No 'audio' field found in multipart body")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        api_key = os.environ.get("DEEPGRAM_API_KEY", "")
        if not api_key:
            self._ok({"error": "DEEPGRAM_API_KEY not set"}); return

        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)

        try:
            audio_bytes, audio_ctype = parse_multipart(raw_body, content_type)
        except Exception as e:
            self._ok({"error": "No audio: " + str(e)}); return

        try:
            req = urllib.request.Request(
                DEEPGRAM_URL,
                data=audio_bytes,
                headers={
                    "Authorization": "Token " + api_key,
                    "Content-Type": audio_ctype,
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
            self._ok({"text": transcript, "language": detected})
        except urllib.error.HTTPError as e:
            self._ok({"error": "Deepgram " + str(e.code) + ": " + e.read().decode()})
        except Exception as e:
            self._ok({"error": str(e)})

    def _ok(self, obj):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, *a): pass