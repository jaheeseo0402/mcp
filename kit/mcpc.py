import subprocess, json, os, time
class Client:
    def __init__(self, cmd, env=None, cov=None):
        self.cov = cov; self.covn = 0
        e = dict(os.environ); e.update(env or {})
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=e, text=True, bufsize=1)
        self.id = 0
        self.req("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "afl", "version": "1"}})
        self.note("notifications/initialized")
    def _send(self, m): self.p.stdin.write(json.dumps(m) + "\n"); self.p.stdin.flush()
    def note(self, method, params=None): self._send({"jsonrpc": "2.0", "method": method, **({"params": params} if params else {})})
    def req(self, method, params=None):
        self.id += 1; i = self.id
        self._send({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}})
        while True:
            line = self.p.stdout.readline()
            if not line: return {"error": {"message": "server closed"}}
            try: m = json.loads(line)
            except Exception: continue
            if m.get("id") == i: return m
    def cov_new(self):
        """호출 직후 preload가 쓴 마지막 줄에서 '새 구간 수'를 읽는다"""
        if not self.cov: return 0
        for _ in range(200):
            try:
                with open(self.cov) as f: lines = f.read().splitlines()
            except FileNotFoundError: lines = []
            if len(lines) > self.covn:
                new = sum(json.loads(l)["n"] for l in lines[self.covn:]); self.covn = len(lines); return new
            time.sleep(0.005)
        return 0
    def close(self):
        try: self.p.terminate()
        except Exception: pass
