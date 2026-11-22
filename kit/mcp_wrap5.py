import os, sys, json, time, random, urllib.parse
from mcp_fuzzer.fuzz_engine.mutators.strategies.registry import strategy_registry
from mcp_fuzzer.__main__ import run

STRATEGY = os.environ.get("STRATEGY", "random")
ROOT = os.path.realpath(os.environ["ROOT"])
PARENT = os.path.dirname(ROOT)
GEN_LOG = os.environ.get("GEN_LOG")
rng = random.Random(int(os.environ.get("SEED", "1")))
PATH_HINTS = ("path", "file", "dir", "folder", "source", "destination", "target")
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-./ "

# ---- 탐색 단계: 허용 폴더 안/밖 이웃을 읽는다 ----
CANARY = os.path.join(PARENT, "canary_outside.txt")
if not os.path.exists(CANARY):
    with open(CANARY, "w") as f:
        f.write("CANARY_OUTSIDE_MARKER")
inside = []
for d, ds, fs in os.walk(ROOT):
    ds[:] = [x for x in ds if x != '.git']
    for n in fs + ds:
        inside.append(os.path.relpath(os.path.join(d, n), ROOT))
    if len(inside) > 200:
        break
inside = inside or ["notes.txt"]
if os.environ.get("INCLUDE_ROOT") == "1":
    inside.append("")
outside = [n for n in os.listdir(PARENT) if os.path.join(PARENT, n) != ROOT] or ["x"]

cats = []
ADA_NEW = {'escape':0,'boundary':0,'valid':0,'near_miss':0}
ADA_N = {'escape':0,'boundary':0,'valid':0,'near_miss':0}
ADA_EPS = 0.2
ADA_SEEN = set()
ADA_LASTCAT = [None]
counter = [0]
LAST = [None]

def rand_str(n):
    return "".join(rng.choice(CHARS) for _ in range(n))

def random_any():
    k = rng.randint(0, 6)
    if k == 0: return rand_str(rng.randint(0, 200))
    if k == 1: return rng.randint(-10**9, 10**9)
    if k == 2: return rng.random() < 0.5
    if k == 3: return None
    if k == 4: return [rand_str(5), rng.randint(0, 100), None]
    if k == 5: return {"a": rand_str(5), "b": rng.randint(0, 10)}
    return rand_str(1000)

def ptype(spec):
    t = spec.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if t is None:
        t = "object" if "properties" in spec else "string"
    return t

def is_pathlike(name, spec):
    return any(h in name.lower() for h in PATH_HINTS) or "path" in str(spec.get("description", "")).lower()

def valid_path():
    return os.path.join(ROOT, rng.choice(inside))

def near_miss_path():
    base = rng.choice(inside)
    if base == "":
        return ROOT
    d, n = os.path.split(base)
    stem, ext = os.path.splitext(n)
    v = [base, os.path.join(d, stem + ".bak"), base + "~", os.path.join(d, n.upper()),
         "./" + base, os.path.join(d, stem[:-1] + ext), os.path.join(d, stem + "_v2" + ext),
         os.path.join("subdir", n)]
    return os.path.join(ROOT, rng.choice(v))

def escape_path():
    k = rng.randint(1, 6)
    name = rng.choice(outside)
    forms = ["../" * k + name, os.path.join(ROOT, "../" * k + name), os.path.join(PARENT, name),
             "..\\" * k + name, urllib.parse.quote("../" * k, safe="") + name,
             "....//" * k + name, ROOT + "_sibling/" + name, valid_path() + "\x00.txt"]
    G = {"rel": [0, 1, 3, 5], "abs": [2], "sib": [6], "enc": [4, 7]}
    drop = set(i for g in os.environ.get("EDROP", "").split(",") if g in G for i in G[g])
    return rng.choice([f for i, f in enumerate(forms) if i not in drop])

def boundary_path():
    return rng.choice(["", ".", "/", ROOT, ROOT + "/", " ", "a" * 255, "a" * 4096,
                       os.path.join(ROOT, "no_such_dir", "deep", "x.txt"), valid_path() + "/"])

def path_value(mode):
    if mode == "semantic":
        cats.append("near_miss"); return near_miss_path()
    W = [("escape", 0.35, escape_path), ("boundary", 0.35, boundary_path), ("valid", 0.30, valid_path)]
    if mode == "unified":
        uw = [float(x) for x in os.environ.get("UW", "1,1,1,1").split(",")]  # 비율 가중치: 탈출,경계,정상,근접오답
        if os.environ.get("PHASEA") and counter[0] < int(os.environ.get("PHASE_AT", "5000")):
            uw = [float(x) for x in os.environ["PHASEA"].split(",")]
        if os.environ.get("ADAPT") == "1":
            nm_ = ["escape", "boundary", "valid", "near_miss"]
            uw = [(1.0 + ADA_NEW[k]) / (1.0 + ADA_N[k]) + ADA_EPS for k in nm_]
        W = [("escape", uw[0], escape_path), ("boundary", uw[1], boundary_path), ("valid", uw[2], valid_path), ("near_miss", uw[3], near_miss_path)]
    ab = os.environ.get("ABL", "").split(",")
    W = [w for w in W if w[0] not in ab]
    r = rng.random() * sum(w[1] for w in W)
    for nm, wt, fn in W:
        r -= wt
        if r < 0:
            cats.append(nm); return fn()
    cats.append(W[-1][0]); return W[-1][2]()

try:
    from mcp_fuzzer.fuzz_engine.mutators.strategies import interesting_values as _iv
    HYB_STR = [x for n in ("SQL_INJECTION","NOSQL_INJECTION","XSS_PAYLOADS","PATH_TRAVERSAL","COMMAND_INJECTION","SSRF_PAYLOADS","UNICODE_TRICKS","ENCODING_BYPASS","BOUNDARY_STRINGS") for x in getattr(_iv, n, []) if isinstance(x, str)]
    HYB_INT = [x for n in ("BOUNDARY_INTS_SMALL","BOUNDARY_INTS_MEDIUM","OVERFLOW_INTS") for x in getattr(_iv, n, []) if isinstance(x, int) and not isinstance(x, bool)]
except Exception as _e:
    HYB_STR, HYB_INT = [""], [0]
try:
    HYB_REAL = [x for v in _iv.REALISTIC_SAMPLES.values() for x in v if isinstance(x, str)]
except Exception:
    HYB_REAL = ["John"]
def gen(spec, name, mode):
    if not isinstance(spec, dict): return "x"
    if "enum" in spec: return rng.choice(spec["enum"])
    t = ptype(spec)
    if t == "string":
        if is_pathlike(name, spec): return path_value(mode)
        if mode == "semantic": return rng.choice(["hello world", "notes", "*.txt", "name"])
        if mode == "hybridr" and rng.random() < 0.5: return rng.choice(HYB_REAL)
        if mode in ("hybrid", "hybridr"): return rng.choice(HYB_STR)
        return rng.choice(["", " ", "*", "[", "\x00", "x" * rng.randint(2, 5000)])
    if t in ("integer", "number"):
        if mode in ("hybrid", "hybridr"): return rng.choice(HYB_INT)
        return rng.choice([1, 2, 5, 10]) if mode == "semantic" else rng.choice([0, -1, 1, 2**31 - 1, 2**53])
    if t == "boolean": return rng.random() < 0.5
    if t == "array":
        n = 1 if mode == "semantic" else rng.randint(1, 2)
        return [gen(spec.get("items", {}), name, mode) for _ in range(n)]
    if t == "object":
        props = spec.get("properties", {}); req = set(spec.get("required", []))
        return {k: gen(v, k, mode) for k, v in props.items() if k in req or rng.random() < 0.5}
    return "x"


# ---------------- AFL-style: seed corpus + havoc mutation + feedback ----------------
INTERESTING_INT = [-128, -1, 0, 1, 16, 32, 64, 100, 127, 128, 255, 256, 512, 1000, 1024, 4096, 32767, 32768, 65535, 65536, 2**31 - 1]
INTERESTING_CH = ["\x00", "\x01", "\x7f", "\x80", "\xff"]
corpus = {}
seen_sig = {}
def seed_val(spec, name, real):
    if not isinstance(spec, dict): return "x"
    if "enum" in spec: return spec["enum"][0]
    t = ptype(spec)
    if t == "string":
        if is_pathlike(name, spec): return valid_path() if real else "sample.txt"
        return "hello"
    if t in ("integer", "number"): return 1
    if t == "boolean": return True
    if t == "array": return [seed_val(spec.get("items", {}), name, real)]
    if t == "object":
        props = spec.get("properties", {}); req = set(spec.get("required", []))
        return {k: seed_val(v, k, real) for k, v in props.items() if k in req}
    return "x"
def mut_str(v, other=None):
    b = list(v)
    op = rng.randint(0, 6)
    if op == 0 and b:
        i = rng.randrange(len(b)); b[i] = chr(ord(b[i]) ^ (1 << rng.randint(0, 7)))
    elif op == 1 and b:
        b[rng.randrange(len(b))] = rng.choice(INTERESTING_CH)
    elif op == 2:
        b.insert(rng.randint(0, len(b)), chr(rng.randint(0, 255)))
    elif op == 3 and b:
        i = rng.randrange(len(b)); del b[i:i + rng.randint(1, 4)]
    elif op == 4 and b:
        i = rng.randrange(len(b)); j = min(len(b), i + rng.randint(1, 8)); b[i:i] = b[i:j]
    elif op == 5 and b:
        i = rng.randrange(len(b)); j = min(len(b), i + rng.randint(1, 4))
        b[i:j] = [chr(rng.randint(0, 255)) for _ in range(j - i)]
    elif op == 6 and isinstance(other, str) and other:
        cut = rng.randint(0, len(b)); b = b[:cut] + list(other[rng.randint(0, len(other)-1):])
    return "".join(b)[:4200]
def mut_val(v, other=None):
    if isinstance(v, bool): return not v
    if isinstance(v, str): return mut_str(v, other)
    if isinstance(v, (int, float)):
        r = rng.random()
        if r < 0.5: return v + rng.choice([-1, 1]) * rng.randint(1, 35)
        return rng.choice(INTERESTING_INT)
    if isinstance(v, list):
        if not v: return v
        w = list(v); i = rng.randrange(len(w)); w[i] = mut_val(w[i]); return w
    if isinstance(v, dict):
        w = dict(v)
        if w:
            k = rng.choice(list(w)); w[k] = mut_val(w[k])
        return w
    return v
AFLS = ("afl", "aflg", "afl_random", "afl_mcpfuzzer", "afl_ours")
NSEED = 8
async def mf_seed(tool):
    from mcp_fuzzer.fuzz_engine.mutators.strategies import ToolStrategies as _TS
    saved = dict(strategy_registry._tool); strategy_registry._tool.clear()
    try:
        return await _TS.fuzz_tool_arguments(tool, phase="aggressive")
    finally:
        strategy_registry._tool.update(saved)
async def make_seed(tool, props, req):
    if STRATEGY == "afl_random":
        return {k: random_any() for k in req}
    if STRATEGY == "afl_mcpfuzzer":
        return await mf_seed(tool)
    return {k: gen(v, k, "unified") for k, v in props.items() if k in req}
async def afl_generate(tool, real):
    name = tool.get("name"); schema = tool.get("inputSchema") or {}
    props = schema.get("properties", {}); req = set(schema.get("required", []))
    if name not in corpus:
        if STRATEGY in ("afl_random", "afl_mcpfuzzer", "afl_ours"):
            corpus[name] = [await make_seed(tool, props, req) for _ in range(NSEED)]
        else:
            corpus[name] = [{k: seed_val(v, k, real) for k, v in props.items() if k in req}]
    base = rng.choice(corpus[name]); other = rng.choice(corpus[name])
    args = json.loads(json.dumps(base))
    keys = list(props.keys()) or list(args.keys())
    for _ in range(2 ** rng.randint(1, 3)):
        if not keys: break
        k = rng.choice(keys)
        if k in args: args[k] = mut_val(args[k], other.get(k) if isinstance(other.get(k), str) else None)
        elif rng.random() < 0.5: args[k] = seed_val(props.get(k, {}), k, real)
    return args

async def generate(tool):
    del cats[:]
    schema = tool.get("inputSchema") or {}
    props = schema.get("properties", {}); req = set(schema.get("required", []))
    args = {}
    if STRATEGY in AFLS:
        args = await afl_generate(tool, STRATEGY == "afl")
        props = {}
    for k, v in props.items():
        if STRATEGY == "random":
            if rng.random() < 0.7: args[k] = random_any()
        elif k in req or rng.random() < 0.5:
            args[k] = gen(v, k, STRATEGY)
    counter[0] += 1
    ADA_LASTCAT[0] = [c for c in cats if c in ADA_N]
    LAST[0] = (tool.get("name"), args)
    if GEN_LOG:
        with open(GEN_LOG, "a") as f:
            f.write(json.dumps({"i": counter[0], "t": time.time(), "strategy": STRATEGY,
                                "tool": tool.get("name"), "args": args, "cats": list(cats)}) + "\n")
    return args

if STRATEGY != "mcpfuzzer":
    for ph in ("aggressive", "realistic"):
        strategy_registry.register_tool(ph, generate)
from mcp_fuzzer.fuzz_engine.mutators.tool_mutator import ToolMutator

if STRATEGY in AFLS or os.environ.get("ADAPT") == "1":
    import re as _re
    from mcp_fuzzer.client import tool_client_execution as _tce
    from mcp_fuzzer.fuzz_engine.mutators import tool_mutator as _tm
    def _fine(resp):
        try:
            c = resp.get("content") or []
            t = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            t = _re.sub(r"/[^\s'\"]+", "<P>", t); t = _re.sub(r"\d+", "<N>", t)
            return ("E:" if resp.get("isError") else "OK:") + t[:60]
        except Exception:
            return "unk"
    _tce.response_shape_signature = _fine
    _orig = _tm.ToolMutator.record_feedback
    def _rf(self, tool_name, args, **kw):
        sig = kw.get("response_signature")
        if os.environ.get("ADAPT") == "1" and sig is not None:
            new_ = (tool_name, sig) not in ADA_SEEN
            ADA_SEEN.add((tool_name, sig))
            for c_ in (ADA_LASTCAT[0] or []):
                ADA_N[c_] += 1
                if new_: ADA_NEW[c_] += 1
        if sig is not None and tool_name in corpus:
            st = seen_sig.setdefault(tool_name, set())
            if sig not in st:
                st.add(sig); corpus[tool_name].append(json.loads(json.dumps(args)))
        return _orig(self, tool_name, args, **kw)
    _tm.ToolMutator.record_feedback = _rf
if os.environ.get('RESEED', '0') == '0':
    ToolMutator._seed_ratio_for_phase = staticmethod(lambda phase: 0.0)
sys.exit(run())
