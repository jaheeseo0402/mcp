"""공통 AFL식 퍼저 틀 (대상 서버: Node.js MCP 서버, 피드백: V8 코드 커버리지)
    시드 큐 -> (큐에서 하나 선택) -> 전략별 변이 -> 서버 호출 -> 새 커버리지면 큐에 추가
세 조건은 '변이 전략'만 다르고 나머지(초기 시드, 큐, 피드백, 호출 수)는 모두 같다."""
import os, sys, json, time, random, argparse, asyncio, select, urllib.parse, subprocess
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
from mcpc import Client
from common import PATH_HINTS
import hashlib, secrets

ap = argparse.ArgumentParser()
ap.add_argument("--strategy", required=True, choices=["random", "mcpfuzzer", "ours", "llm", "info"])
ap.add_argument("--info-level", type=int, default=3, choices=[0, 1, 2, 3, 4], help="info 전략: 알고 있는 서버 정보 수준 (0 없음 / 1 허용 폴더 경로만 / 2 +폴더 내부 구조 / 3 +이웃 폴더 이름 / 4 +이웃 폴더 안 파일 이름)")
ap.add_argument("--info-gen", default="four", choices=["four", "rand"], help="four = 4종류(경로 이탈·경계값·유효·준유효 각 25%) / rand = 같은 정보로 이름을 무작위 조합만 함(대조)")
ap.add_argument("--pool", default="", help="llm 전략: 미리 만든 입력 풀(JSON)")
ap.add_argument("--server", required=True, choices=["old", "agent", "adro"])
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--per-tool", type=int, default=1000)
ap.add_argument("--out", required=True)
ap.add_argument("--no-cov", action="store_true")
ap.add_argument("--variant", default="full", choices=["full","allstr","nameonly","noconst"])
ap.add_argument("--seedmode", default="generic", choices=["generic", "real"])
A = ap.parse_args()

rng = random.Random(A.seed)
RUN = os.path.abspath(A.out); os.makedirs(RUN, exist_ok=True)
ROOT = os.path.join(RUN, "iso", "sandbox"); PARENT = os.path.dirname(ROOT)
if os.path.exists(PARENT): subprocess.run(["rm", "-rf", PARENT])
os.makedirs(PARENT); subprocess.run(["cp", "-a", os.path.join(KIT, "base_orig"), ROOT])
for d in ("sandbox_secret", "other_a", "other_b"): os.makedirs(os.path.join(PARENT, d))
# --- 보안 오라클용 준비: 허용 폴더 밖 파일에 실행마다 다른 난수 토큰을 심는다 ---
TOKENS = {"sandbox_secret/secret.txt": "TOP_SECRET_OUTSIDE\nTOK_" + secrets.token_hex(8) + "\n",
          "other_a/data.txt": "TOK_" + secrets.token_hex(8) + "\n"}
for rel, tk in TOKENS.items(): open(os.path.join(PARENT, rel), "w").write(tk)
TOKVALS = [l for tk in TOKENS.values() for l in tk.split() if l.startswith("TOK_")]
OUT_NAMES = ("secret.txt", "data.txt")  # 허용 폴더 밖에만 있는 파일 이름 (목록 노출 판정용)
def fp_outside():
    """허용 폴더(ROOT) 밖 파일시스템의 지문. 호출 전후를 비교해 실제 생성·변경·삭제를 잡는다."""
    out = {}
    for dp, dn, fn in os.walk(PARENT):
        if os.path.abspath(dp) == os.path.abspath(ROOT): dn[:] = []; continue
        dn[:] = [d for d in dn if os.path.abspath(os.path.join(dp, d)) != os.path.abspath(ROOT)]
        rel = os.path.relpath(dp, PARENT); out[rel + "/"] = "d"
        for f in fn:
            fpth = os.path.join(dp, f)
            try: out[os.path.join(rel, f)] = hashlib.sha1(open(fpth, "rb").read()).hexdigest()
            except OSError: out[os.path.join(rel, f)] = "?"
    return out

SRV = {"old": (["node", KIT + "/node_modules/mcp-server-filesystem/dist/index.js", ROOT]),
       "agent": (["node", KIT + "/srv/node_modules/@agent-infra/mcp-server-filesystem/dist/index.cjs", "--allowed-directories", ROOT]),
       "adro": (["node", KIT + "/srv/node_modules/@adpharm/mcp-server-filesystem-ro/dist/index.js", ROOT])}[A.server]
COV = None if A.no_cov else os.path.join(RUN, "cov.txt")
if COV and os.path.exists(COV): os.remove(COV)
def start():
    return Client(SRV, env={"NODE_OPTIONS": "--require " + os.path.join(KIT, "covpre.cjs"), "COV_FILE": COV} if COV else {}, cov=COV)
cli = start(); cli.cov_new()
tools = cli.req("tools/list")["result"]["tools"]; cli.cov_new()

# ---------------- 공통 부품 ----------------
def ptype(spec):
    t = spec.get("type")
    if isinstance(t, list): t = next((x for x in t if x != "null"), "string")
    if t is None: t = "object" if "properties" in spec else "string"
    return t
def is_pathlike(name, spec):
    return any(h in name.lower() for h in PATH_HINTS) or "path" in str(spec.get("description", "")).lower()
def seed_val(spec, name):  # 초기 시드: 세 조건 공통, 스키마에 맞는 평범한 값 (서버 폴더 정보 사용 안 함)
    if not isinstance(spec, dict): return "x"
    if "enum" in spec: return spec["enum"][0]
    t = ptype(spec)
    if t == "string":
        if is_pathlike(name, spec): return os.path.join(ROOT, "sample.txt") if A.seedmode == "real" else "sample.txt"
        return "hello"
    if t in ("integer", "number"): return 1
    if t == "boolean": return True
    if t == "array": return [seed_val(spec.get("items", {}), name)]
    if t == "object":
        props = spec.get("properties", {}); req = set(spec.get("required", []))
        return {k: seed_val(v, k) for k, v in props.items() if k in req}
    return "x"
INTERESTING_INT = [-128, -1, 0, 1, 16, 32, 64, 100, 127, 128, 255, 256, 512, 1000, 1024, 4096, 32767, 32768, 65535, 65536, 2**31 - 1]
INTERESTING_CH = ["\x00", "\x01", "\x7f", "\x80", "\xff"]
def mut_str(v, other=None):  # AFL havoc: 비트 반전, 특수값, 삽입, 삭제, 복제, 덮어쓰기, 교차
    b = list(v); op = rng.randint(0, 6)
    if op == 0 and b: i = rng.randrange(len(b)); b[i] = chr(ord(b[i]) ^ (1 << rng.randint(0, 7)))
    elif op == 1 and b: b[rng.randrange(len(b))] = rng.choice(INTERESTING_CH)
    elif op == 2: b.insert(rng.randint(0, len(b)), chr(rng.randint(0, 255)))
    elif op == 3 and b: i = rng.randrange(len(b)); del b[i:i + rng.randint(1, 4)]
    elif op == 4 and b: i = rng.randrange(len(b)); j = min(len(b), i + rng.randint(1, 8)); b[i:i] = b[i:j]
    elif op == 5 and b:
        i = rng.randrange(len(b)); j = min(len(b), i + rng.randint(1, 4)); b[i:j] = [chr(rng.randint(0, 255)) for _ in range(j - i)]
    elif op == 6 and isinstance(other, str) and other:
        cut = rng.randint(0, len(b)); b = b[:cut] + list(other[rng.randint(0, len(other) - 1):])
    return "".join(b)[:4200]
def havoc(v, other=None):
    if isinstance(v, bool): return not v
    if isinstance(v, str): return mut_str(v, other)
    if isinstance(v, (int, float)):
        return v + rng.choice([-1, 1]) * rng.randint(1, 35) if rng.random() < 0.5 else rng.choice(INTERESTING_INT)
    if isinstance(v, list):
        if not v: return v
        w = list(v); i = rng.randrange(len(w)); w[i] = havoc(w[i]); return w
    if isinstance(v, dict):
        w = dict(v)
        if w: k = rng.choice(list(w)); w[k] = havoc(w[k])
        return w
    return v

# ---------------- 전략별 변이 (여기만 다르다) ----------------
class Random:
    name = "random"
    def begin_call(self, tool): pass
    def field(self, k, spec, cur, other): return havoc(cur, other if isinstance(other, str) else None)

class McpFuzzer:  # mcp-fuzzer 0.7.0의 입력 생성(필드 이름 -> 공격 사전)을 그대로 호출해 값을 가져온다. 재사용(35%)은 havoc.
    name = "mcpfuzzer"
    def __init__(self):
        from mcp_fuzzer.fuzz_engine.mutators.strategies import ToolStrategies
        self.TS = ToolStrategies; self.loop = asyncio.new_event_loop(); self.cur = {}
    def begin_call(self, tool):
        try: self.cur = self.loop.run_until_complete(self.TS.fuzz_tool_arguments(tool, phase="aggressive")) or {}
        except Exception: self.cur = {}
    def field(self, k, spec, cur, other):
        if rng.random() < 0.35 or k not in self.cur: return havoc(cur, other if isinstance(other, str) else None)
        return self.cur[k]

class Ours:  # 경로형 필드는 서버 폴더를 읽어 만든 4종류(각 25%)에서 다시 뽑는다. 나머지 필드는 havoc.
    name = "ours"
    def __init__(self):
        self.inside = []
        for d, ds, fs in os.walk(ROOT):
            ds[:] = [x for x in ds if x != ".git"]
            for n in fs + ds: self.inside.append(os.path.relpath(os.path.join(d, n), ROOT))
            if len(self.inside) > 200: break
        self.inside = self.inside or ["notes.txt"]
        self.outside = [n for n in os.listdir(PARENT) if os.path.join(PARENT, n) != ROOT] or ["x"]
    def valid(self): return os.path.join(ROOT, rng.choice(self.inside))
    def near(self):
        if A.variant == "noconst": return self.valid()
        base = rng.choice(self.inside); d, n = os.path.split(base); stem, ext = os.path.splitext(n)
        v = [base, os.path.join(d, stem + ".bak"), base + "~", os.path.join(d, n.upper()), "./" + base,
             os.path.join(d, stem[:-1] + ext), os.path.join(d, stem + "_v2" + ext), os.path.join("subdir", n)]
        return os.path.join(ROOT, rng.choice(v))
    def escape(self):
        k = rng.randint(1, 6); name = rng.choice(self.outside)
        if A.variant == "noconst": return rng.choice(["../" * k + name, os.path.join(PARENT, name)])
        return rng.choice(["../" * k + name, os.path.join(ROOT, "../" * k + name), os.path.join(PARENT, name), "..\\" * k + name,
                           urllib.parse.quote("../" * k, safe="") + name, "....//" * k + name, ROOT + "_sibling/" + name, self.valid() + "\x00.txt"])
    def boundary(self):
        if A.variant == "noconst": return rng.choice(["", ROOT])
        return rng.choice(["", ".", "/", ROOT, ROOT + "/", " ", "a" * 255, "a" * 4096, os.path.join(ROOT, "no_such_dir", "deep", "x.txt"), self.valid() + "/"])
    def begin_call(self, tool): pass
    def pl(self, k, spec):
        if A.variant == "allstr": return True  # 규칙 없음: 모든 문자열 필드에 적용
        if A.variant == "nameonly": return any(h in k.lower() for h in PATH_HINTS)  # 설명 문구 판단 제거
        return is_pathlike(k, spec)
    def field(self, k, spec, cur, other):
        if isinstance(spec, dict) and ptype(spec) == "string" and self.pl(k, spec):
            return rng.choice([self.escape, self.boundary, self.valid, self.near])()
        return havoc(cur, other if isinstance(other, str) else None)

class Info:  # 정보 수준(0~4)과 생성 방식(four/rand)을 따로 바꾸는 통제 실험용. 나머지 필드는 havoc.
    name = "info"
    GUESS_OUT = ["etc", "tmp", "backup", "data", "private", "home"]  # 서버 구조를 모를 때 쓰는 일반적인 추측 이름(고정, 실험 전에 정함)
    def __init__(self):
        L = A.info_level; self.L = L; self.gen = A.info_gen
        self.root = ROOT if L >= 1 else None; self.par = PARENT if L >= 1 else None
        self.inside = ["sample.txt"]
        if L >= 2:
            self.inside = []
            for d, ds, fs in os.walk(ROOT):
                ds[:] = [x for x in ds if x != ".git"]
                for n in fs + ds: self.inside.append(os.path.relpath(os.path.join(d, n), ROOT))
                if len(self.inside) > 200: break
            self.inside = self.inside or ["notes.txt"]
        self.outside = list(self.GUESS_OUT)
        if L >= 3:
            self.outside = [n for n in os.listdir(PARENT) if os.path.join(PARENT, n) != ROOT] or ["x"]
        if L >= 4:
            more = []
            for n in list(self.outside):
                full = os.path.join(PARENT, n)
                if os.path.isdir(full):
                    for d, ds, fs in os.walk(full):
                        for f in fs: more.append(os.path.relpath(os.path.join(d, f), PARENT))
            self.outside = self.outside + more
        self.known = self.inside + self.outside
        self.prefixes = [""] + ["../", "../../"] + ([self.root + "/", self.par + "/"] if self.root else [])
    def j(self, rel): return os.path.join(self.root, rel) if self.root else rel
    def valid(self): return self.j(rng.choice(self.inside))
    def near(self):
        base = rng.choice(self.inside); d, n = os.path.split(base); stem, ext = os.path.splitext(n)
        v = [base, os.path.join(d, stem + ".bak"), base + "~", os.path.join(d, n.upper()), "./" + base,
             os.path.join(d, stem[:-1] + ext), os.path.join(d, stem + "_v2" + ext), os.path.join("subdir", n)]
        return self.j(rng.choice(v))
    def escape(self):
        k = rng.randint(1, 6); name = rng.choice(self.outside); c = ["../" * k + name, "..\\" * k + name,
            urllib.parse.quote("../" * k, safe="") + name, "....//" * k + name, self.valid() + "\x00.txt"]
        if self.root: c += [os.path.join(ROOT, "../" * k + name), os.path.join(PARENT, name), ROOT + "_sibling/" + name]
        return rng.choice(c)
    def boundary(self):
        c = ["", ".", "/", " ", "a" * 255, "a" * 4096, self.j("no_such_dir/deep/x.txt"), self.valid() + "/"]
        if self.root: c += [ROOT, ROOT + "/"]
        return rng.choice(c)
    def rand(self): return rng.choice(self.prefixes) + rng.choice(self.known)
    def begin_call(self, tool): pass
    def field(self, k, spec, cur, other):
        if isinstance(spec, dict) and ptype(spec) == "string" and is_pathlike(k, spec):
            return self.rand() if self.gen == "rand" else rng.choice([self.escape, self.boundary, self.valid, self.near])()
        return havoc(cur, other if isinstance(other, str) else None)

class LLM:  # LLM이 미리 만들어 둔 경로 입력 풀(1회 생성, 고정)에서 경로형 필드를 뽑는다. 나머지 필드는 havoc.
    name = "llm"
    def __init__(self):
        if A.pool.startswith("auto:"):  # 자동 생성: 폴더를 읽어 LLM을 호출 (llm_gen.py)
            import llm_gen
            P = llm_gen.generate(ROOT, PARENT, A.pool[5:], tools, os.path.join(RUN, "llm_pool.json"))
        elif A.pool.startswith("raw:"):  # LLM 채팅창 응답을 그대로 저장한 파일
            import llm_gen
            P = llm_gen.load_raw(A.pool[4:], ROOT, PARENT)
        else:
            P = json.load(open(A.pool))["paths"]
        self.pool = [p.replace("{ROOT}", ROOT).replace("{PARENT}", PARENT).replace("{ROOTNAME}", os.path.basename(ROOT)) for p in P]
    def begin_call(self, tool): pass
    def field(self, k, spec, cur, other):
        if isinstance(spec, dict) and ptype(spec) == "string" and is_pathlike(k, spec): return rng.choice(self.pool)
        return havoc(cur, other if isinstance(other, str) else None)

strat = {"random": Random, "mcpfuzzer": McpFuzzer, "ours": Ours, "llm": LLM, "info": Info}[A.strategy]()

# ---------------- 메인 루프 ----------------
log = open(os.path.join(RUN, "calls.jsonl"), "w")
queue = {}; nc = 0; t0 = time.time(); FP = fp_outside()
for tool in tools:
    nm = tool["name"]; sch = tool.get("inputSchema") or {}; props = sch.get("properties", {}); req = set(sch.get("required", []))
    queue[nm] = [{k: seed_val(v, k) for k, v in props.items() if k in req}]
    for _ in range(A.per_tool):
        base = rng.choice(queue[nm]); other = rng.choice(queue[nm])
        args = json.loads(json.dumps(base)); keys = list(props.keys()) or list(args.keys())
        strat.begin_call(tool)
        for _ in range(2 ** rng.randint(1, 3)):
            if not keys: break
            k = rng.choice(keys); spec = props.get(k, {})
            cur = args[k] if k in args else seed_val(spec, k)
            args[k] = strat.field(k, spec, cur, other.get(k))
        try:
            r = cli.req("tools/call", {"name": nm, "arguments": args})
        except Exception:
            r = {"error": {"message": "client error"}}
        new = cli.cov_new()
        if "error" in r and r["error"].get("message") == "server closed": cli.close(); cli = start(); cli.cov_new(); cli.req("tools/list"); cli.cov_new()
        res = r.get("result") or {}
        txt = json.dumps(r["error"]) if r.get("error") else " ".join(x.get("text", "") for x in (res.get("content") or []) if isinstance(x, dict))
        iserr = bool(r.get("error")) or bool(res.get("isError"))
        # --- 보안 오라클: 응답 문구가 아니라 실제 파일시스템 상태로 판정 ---
        viol = []; eff = []
        fp2 = fp_outside()
        if fp2 != FP:
            viol.append("mutate"); eff = sorted(k for k in set(fp2) | set(FP) if fp2.get(k) != FP.get(k))[:4]; FP = fp2
        if not iserr:
            if any(t in txt for t in TOKVALS): viol.append("leak")
            argtxt = json.dumps(args)
            if any(n in txt and n not in argtxt for n in OUT_NAMES): viol.append("list")
        log.write(json.dumps({"tool": nm, "args": args, "txt": txt[:300], "err": iserr, "new": new, "viol": viol, "eff": eff}) + "\n")
        if new > 0 and len(queue[nm]) < 400: queue[nm].append(json.loads(json.dumps(args)))
        nc += 1
log.close(); cli.close()
total = 0
if COV and os.path.exists(COV):
    ls = open(COV).read().splitlines(); total = json.loads(ls[-1])["total"] if ls else 0
json.dump({"calls": nc, "cov_total": total, "secs": round(time.time() - t0, 1), "queue": {k: len(v) for k, v in queue.items()}}, open(os.path.join(RUN, "summary.json"), "w"))
print("done", A.strategy, A.server, A.seed, nc, total, round(time.time() - t0))
