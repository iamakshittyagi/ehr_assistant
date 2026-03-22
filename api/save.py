import os
import json
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        try:
            from upstash_redis import Redis
            self.wfile.write(b'{"status":"upstash ok"}')
        except Exception as e:
            self.wfile.write(json.dumps({"error":str(e)}).encode())
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a):pass
