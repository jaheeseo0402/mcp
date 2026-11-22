"""LLM 입력 자동 생성: 서버 폴더를 읽어 프롬프트를 자동으로 만들고 LLM API를 불러 경로 입력 풀을 받는다.
사람이 값을 직접 쓰지 않는다. 환경변수: ANTHROPIC_API_KEY (필수), LLM_MODEL (기본 claude-sonnet-5-5), LLM_STUB=1 (배관 시험용, 실제 호출 없음)
level: blind = 폴더 정보 없음 / tree = 서버 폴더 구조 + 바로 옆 폴더 이름(제안 모델이 읽는 정보와 같은 범위)"""
import os, json, re, urllib.request

def tree_text(root, limit=200):
    out = []
    for d, ds, fs in os.walk(root):
        ds[:] = sorted(x for x in ds if x != ".git")
        for n in sorted(fs) + ds:
            out.append(os.path.relpath(os.path.join(d, n), root))
        if len(out) > limit: break
    return "\n".join(out[:limit])

def build_prompt(root, parent, level, tools):
    t = "\n".join(f"- {x['name']}({', '.join((x.get('inputSchema') or {}).get('properties', {}).keys())}): {(x.get('description') or '')[:120]}" for x in tools)
    base = ("You are generating test inputs for fuzzing an MCP filesystem server. The server must refuse any path outside its single allowed directory. "
            "Output ONLY a JSON array of 80 strings to be used as values of path-like arguments (path, source, destination). "
            "Mix: path-traversal attempts, boundary values (empty, very long, nonexistent), valid paths, and near-valid paths.\n\nTools:\n" + t + "\n")
    if level == "tree":
        names = sorted(n for n in os.listdir(parent) if os.path.join(parent, n) != root)
        base += (f"\nThe allowed directory is {root}\nIts contents (relative paths):\n{tree_text(root)}\n"
                 f"Its sibling directories (names only): {', '.join(names)}\n")
    else:
        base += "\nYou do not know where the allowed directory is or what it contains.\n"
    return base

def parse(text):
    m = re.search(r"\[.*\]", text, re.S)
    arr = json.loads(m.group(0))
    return [x for x in arr if isinstance(x, str)]

def call_gemini(prompt):
    key = os.environ["GEMINI_API_KEY"]; model = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}", body, {"content-type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"])

def call_llm(prompt):
    if os.environ.get("GEMINI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"): return call_gemini(prompt)
    if os.environ.get("LLM_STUB"):
        return json.dumps(["sample.txt", "../x", ""])
    key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({"model": os.environ.get("LLM_MODEL", "claude-sonnet-5-5"), "max_tokens": 4000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com") + "/v1/messages", body,
                                 {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return "".join(b.get("text", "") for b in r["content"])

def generate(root, parent, level, tools, save_to):
    """프롬프트와 응답을 save_to에 저장(재현·검토용)하고 경로 풀을 돌려준다"""
    prompt = build_prompt(root, parent, level, tools)
    raw = call_llm(prompt)
    pool = parse(raw)
    json.dump({"level": level, "model": os.environ.get("LLM_MODEL", "(provider default)"), "prompt": prompt, "raw": raw, "paths": pool},
              open(save_to, "w"), ensure_ascii=False, indent=1)
    return pool


# ---- 수동 붙여넣기 방식(API 없이): 프롬프트를 출력 -> 아무 LLM 채팅창에 붙여넣기 -> 응답을 고치지 말고 파일로 저장 ----
SIBLINGS = ["other_a", "other_b", "sandbox_secret"]   # 실험 폴더 구성(afl_fuzz.py가 만드는 것과 같음)
def manual_prompt(level, tools):
    """실행 경로가 아닌 고정 가짜 경로(/data/sandbox)로 프롬프트를 만든다. 응답의 /data/sandbox, /data는 실행 때 실제 경로로 바뀐다."""
    import tempfile, shutil
    d = tempfile.mkdtemp(); root = os.path.join(d, "data", "sandbox")
    shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_orig"), root)
    for n in SIBLINGS: os.makedirs(os.path.join(d, "data", n), exist_ok=True)
    p = build_prompt(root, os.path.join(d, "data"), level, tools).replace(root, "/data/sandbox")
    shutil.rmtree(d); return p

def load_raw(path, root, parent):
    return [p.replace("/data/sandbox", root).replace("/data", parent) for p in parse(open(path, encoding="utf-8").read())]

if __name__ == "__main__":
    import sys
    # 사용: python3 llm_gen.py prompt blind|tree   -> 프롬프트 출력
    TOOLS = [{"name": n, "inputSchema": {"properties": {k: {} for k in ks}}, "description": ""} for n, ks in
             [("read_file", ["path"]), ("write_file", ["path", "content"]), ("edit_file", ["path"]), ("list_directory", ["path"]), ("get_file_info", ["path"]),
              ("create_directory", ["path"]), ("move_file", ["source", "destination"]), ("search_files", ["path", "pattern"]), ("directory_tree", ["path"])]]
    print(manual_prompt(sys.argv[2], TOOLS))
