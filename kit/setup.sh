#!/bin/bash
# 처음 한 번만: bash setup.sh   (WSL2 Ubuntu 기준)
set -e
cd "$(dirname "$0")"
echo "[1/4] 필수 패키지 확인"
command -v node >/dev/null || { echo "node 없음 -> 아래 두 줄 실행 후 다시:"; echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"; echo "  sudo apt-get install -y nodejs"; exit 1; }
sudo apt-get install -y python3 python3-venv python3-pip >/dev/null
echo "[2/4] 옛 버전 filesystem 서버"
npm install --silent
echo "[3/4] 다른 서버 (agent-infra, adpharm-ro)"
(cd srv && npm install --silent)
echo "[4/4] 파이썬 환경 + mcp-fuzzer 0.7.0"
python3 -m venv venv
./venv/bin/pip install -q "mcp-fuzzer==0.7.0" scipy
echo "완료. 다음: bash quick_test.sh"
