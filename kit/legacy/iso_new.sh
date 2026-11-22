KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
S="1 2 3 4 5 6"; N=1000
WRAP=mcp_wrap5.py STRATS=unified TAG=_ada ADAPT=1 legacy/run_iso.sh $N "$S"
# 단계 나누기: 앞 5000번 / 뒤 5000번
WRAP=mcp_wrap5.py STRATS=unified TAG=_ph1 PHASEA=0,0.333,0.333,0.333 PHASE_AT=5000 UW=0.7,0.1,0.1,0.1 legacy/run_iso.sh $N "$S"
WRAP=mcp_wrap5.py STRATS=unified TAG=_ph2 PHASEA=0.7,0.1,0.1,0.1 PHASE_AT=5000 UW=0,0.333,0.333,0.333 legacy/run_iso.sh $N "$S"
echo NEWDONE
