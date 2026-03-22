import os
import json
import cgi
import io
import urllib.request
import urllib.error

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Content-Type": "application/json",
}

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&detect_language=true&punctuate=true"

def handler(request):
    if request.method == "OPTIONS":
        return Response("", headers=HEADERS)
    api_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not api_key:
        return Response(json.dumps({"error": "DEEPGRAM_API_KEY not set"}), status=500, headers=HEADERS)
    try:
        audio = request.files.get("audio")
        audio_bytes = audio.read()
        audio_ctype = audio.content_type or "audio/webm"
    except Exception as e:
        return Response(json.dumps({"error": f"No audio: {e}"}), status=400, headers=HEADERS)
    try:
        req = urllib.request.Request(
            DEEPGRAM_URL, data=audio_bytes,
            headers={"Authorization": f"Token {api_key}", "Content-Type": audio_ctype},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            dg = json.loads(resp.read())
        transcript = dg.get("results",{}).get("channels",[{}])[0].get("alternatives",[{}])[0].get("transcript","")
        detected = dg.get("results",{}).get("channels",[{}])[0].get("detected_language","unknown")
        return Response(json.dumps({"text": transcript, "language": detected}), headers=HEADERS)
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, headers=HEADERS)
