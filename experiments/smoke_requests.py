import threading, http.server, json
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        b = json.dumps({"ua": self.headers.get("User-Agent", ""), "path": self.path}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.send_header("Set-Cookie", "k=v")
        self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
s = http.server.HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
import requests
from requests.adapters import HTTPAdapter
u = f"http://127.0.0.1:{s.server_port}"
ses = requests.Session(); ses.mount("http://", HTTPAdapter(max_retries=3))
r = ses.get(u + "/a?x=1", timeout=5, headers={"X": "1"})
assert r.status_code == 200 and r.json()["path"] == "/a?x=1" and ses.cookies.get("k") == "v"
r2 = requests.get(u + "/b", stream=True, timeout=5); assert b"".join(r2.iter_content(8))
assert requests.post(u + "/c", data={"a": 1}, timeout=5).status_code in (200, 501)
try: requests.get("http://127.0.0.1:1/", timeout=1)
except requests.exceptions.ConnectionError: pass
print("OK")
