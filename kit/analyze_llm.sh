#!/bin/bash
# LLM 풀 조건 결과 표 (서버별: llmblind / llmtree). 제안·Random·mcp-fuzzer는 analyze.sh(runs/)와 비교
cd "$(dirname "$0")"
RUNS=runs_llm ./venv/bin/python - <<'PY'
import afl_an as a
for srv in ("old","agent","adro"):
    for st in ("llmblind","llmtree","llmtreeq"):
        D=a.collect(srv,st)
        if not D: continue
        print(f"== {srv} {st} (시드 {len(D)})")
        for met in ("out","pairs","ok","cov"):
            m,h=a.ci([r[met] for r in D]); print(f"  {met:5s} {m:.1f}±{h:.1f}")
PY
