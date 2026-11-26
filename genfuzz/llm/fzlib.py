"""공통 도구: 코드 경로(edge) 얻기, crash 위치 분류, 16진수 파싱."""
import os, re, subprocess, tempfile, shutil

ENV = dict(os.environ, AFL_SKIP_BIN_CHECK="1", AFL_QUIET="1")


def edge_maps(binary, d):
    """폴더 d 안의 파일마다 밟은 edge 집합을 돌려준다. {파일이름: set}.
    afl-showmap -i/-o 폴더 모드로 한 번에 돌려서 파일마다 프로그램을 새로 띄우는 것보다 훨씬 빠르다."""
    out = tempfile.mkdtemp(prefix="smap_")
    try:
        subprocess.run(["afl-showmap", "-q", "-i", d, "-o", out, "-t", "2000", "--", binary, "@@"],
                       capture_output=True, env=ENV)
        res = {}
        for n in os.listdir(out):
            try:
                if n.startswith("README"): continue
                res[n] = {int(ln.split(":")[0]) for ln in open(os.path.join(out, n)) if ":" in ln}
            except OSError:
                pass
        return res
    finally:
        shutil.rmtree(out, ignore_errors=True)


def bug_of(tri, path):
    """crash 입력을 분류용 바이너리에 넣어 '신호 + 맨 위 함수'를 돌려준다. crash가 아니면 None."""
    try:
        p = subprocess.run([tri, path], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return "timeout"
    m = re.search(rb"\[CRASH ([^\]]+)\]", p.stderr)
    if m:
        return " ".join(m.group(1).decode().split()[:2])
    return f"sig{p.returncode}" if p.returncode < 0 else None


def parse_hex(line):
    """LLM이 쓴 한 줄에서 16진수 입력을 꺼낸다. 형식이 안 맞으면 None."""
    s = re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", line)            # '1.' '-' 같은 목록 기호
    s = re.sub(r"(?i)^\s*input\s*\d*\s*[:：]", "", s)
    s = re.sub(r"0x|\\x|[\s,:\-`\"'_]", "", s)
    if not s or len(s) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", s):
        return None
    b = bytes.fromhex(s)
    return b if 1 <= len(b) <= 4096 else None
