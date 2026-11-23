"""퍼저(afl_fuzz.py)와 분석기(afl_an.py)가 공유하는 경로 필드 판별 기준 (한 곳에서만 정의)."""
PATH_HINTS = ("path", "file", "dir", "folder", "source", "destination", "target")
def is_path_name(name):
    return any(h in str(name).lower() for h in PATH_HINTS)
