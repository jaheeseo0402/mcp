"""3번 실험: 구조정보 단계(L0~L3)별로 LLM에게 테스트 입력을 만들게 한다.
사용:
  python3 gen_llm.py prompts                      # prompts/L0~L3.txt 를 만든다(무료 채팅창에 붙여넣기용)
  python3 gen_llm.py ollama qwen2.5:3b 5 [L2,L3]  # 로컬 Ollama로 단계마다 5번 호출(단계 지정 가능) -> raw/ 에 응답 저장 -> 입력 파일로 변환
  python3 gen_llm.py parse chat-<이름>            # 채팅창 응답을 raw/chat-<이름>_L0_1.txt 처럼 저장한 뒤 변환
결과: in/<태그>/<단계>/f00001 ... (바이너리 입력 파일), in/<태그>/stats.csv (형식 통과율)
"""
import glob, json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fzlib import parse_hex

HERE = os.path.dirname(os.path.abspath(__file__))
EXIF = os.path.join(HERE, "..", "exif")
N_PER_QUERY = 10

TASK = ("Generate {n} different test input files for the program. Try to make inputs that reach many different "
        "code paths of its parser, including unusual or malformed ones that may trigger bugs.\n"
        "Output format (strict): exactly one input per line, written as `INPUT: ` followed by the file bytes as a "
        "hexadecimal string without spaces (for example `INPUT: 0a1b2c3d`). Each input must be at most 150 bytes. "
        "Every line must be different from all the other lines (change field values, lengths, counts, offsets, tags or order), "
        "and must not be an exact copy of any example given above. Do not write anything else.")

INFO = {
    "L0": "You are testing a program. You know nothing about what the program does or which file format it reads.",
    "L1": ("You are testing a program that reads image files in JPEG format. "
           "A JPEG file starts with the bytes FF D8 FF E1."),
    "L2": ("You are testing a program that reads the EXIF metadata of JPEG files. "
           "A JPEG file starts with the bytes FF D8 FF E1. Structure of the file:\n"
           "- FF D8 (start of image), then FF E1 (APP1 marker), then a 2-byte big-endian length of the APP1 segment.\n"
           "- Then the 6 bytes `Exif\\0\\0` = 45 78 69 66 00 00.\n"
           "- Then a TIFF header: byte order `II` (49 49, little endian) or `MM` (4D 4D, big endian), then 2A 00 (or 00 2A), "
           "then a 4-byte offset to the first IFD (usually 8).\n"
           "- An IFD is: 2-byte entry count, then entries of 12 bytes each, then a 4-byte offset to the next IFD (0 = none).\n"
           "- An entry is: tag (2 bytes), type (2 bytes, 1..12: byte, ascii, short, long, rational, ...), "
           "count (4 bytes), value or offset to the value (4 bytes; values longer than 4 bytes are stored elsewhere and "
           "this field is an offset from the TIFF header).\n"
           "- Common tags: 010F Make, 0110 Model, 0112 Orientation, 011A XResolution, 0131 Software, "
           "8769 Exif IFD pointer, 8825 GPS IFD pointer, 927C MakerNote.\n"
           "- The file ends with FF D9."),
}


def sample_hex():
    return open(os.path.join(EXIF, "seeds", "L3", "v0"), "rb").read().hex()


def build_prompt(L, n=N_PER_QUERY):
    info = INFO["L2" if L == "L3" else L]
    if L == "L3":
        info += f"\n\nHere is one valid example file (hex): {sample_hex()}"
    return info + "\n\n" + TASK.format(n=n)


def write_prompts():
    os.makedirs(os.path.join(HERE, "prompts"), exist_ok=True)
    for L in ("L0", "L1", "L2", "L3"):
        open(os.path.join(HERE, "prompts", f"{L}.txt"), "w").write(build_prompt(L) + "\n")
    print("prompts/L0~L3.txt 작성 완료")


def ask_ollama(model, prompt, seed):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 1.0, "top_p": 0.95, "num_predict": 2000, "seed": seed}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", body, {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=1800).read())["response"]


def parse(tag):
    """raw/<tag>_<단계>_<번호>.txt 를 읽어 in/<tag>/<단계>/ 에 입력 파일을 만든다. 같은 바이트는 한 번만."""
    rows = []
    for L in ("L0", "L1", "L2", "L3"):
        files = sorted(glob.glob(os.path.join(HERE, "raw", f"{tag}_{L}_*.txt")))
        if not files:
            continue
        outd = os.path.join(HERE, "in", tag, L)
        os.makedirs(outd, exist_ok=True)
        for old in glob.glob(os.path.join(outd, "f*")):
            os.remove(old)
        seen, lines, bad = set(), 0, 0
        for fn in files:
            for ln in open(fn, errors="replace"):
                if not re.match(r"\s*(\d+[.)]\s*)?(?i:input)", ln):
                    continue
                lines += 1
                b = parse_hex(ln)
                if b is None:
                    bad += 1
                elif b not in seen:
                    seen.add(b)
                    open(os.path.join(outd, f"f{len(seen):05d}"), "wb").write(b)
        rows.append((L, len(files), lines, bad, len(seen)))
        print(f"{L}: 응답 {len(files)}개, INPUT 줄 {lines}, 형식 오류 {bad}, 서로 다른 입력 {len(seen)}")
    with open(os.path.join(HERE, "in", tag, "stats.csv"), "w") as f:
        f.write("level,responses,input_lines,bad_hex,unique_inputs\n")
        for r in rows:
            f.write(",".join(map(str, r)) + "\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prompts":
        write_prompts()
    elif cmd == "ollama":
        model, reps = sys.argv[2], int(sys.argv[3])
        tag = "ollama-" + re.sub(r"[^A-Za-z0-9.]+", "-", model)
        os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
        levels = sys.argv[4].split(",") if len(sys.argv) > 4 else ["L0", "L1", "L2", "L3"]
        for L in levels:
            for k in range(1, reps + 1):
                fn = os.path.join(HERE, "raw", f"{tag}_{L}_{k}.txt")
                if os.path.exists(fn):
                    continue
                t0 = time.time(); print(f"{L} #{k} 요청 중...", flush=True)
                resp = ask_ollama(model, build_prompt(L), seed=k)
                if not resp.strip():
                    print("  빈 응답: 저장하지 않음"); continue
                open(fn, "w").write(resp)
                print(f"  완료 ({time.time() - t0:.0f}초)", flush=True)
        parse(tag)
    elif cmd == "parse":
        parse(sys.argv[2])
    else:
        print(__doc__)
