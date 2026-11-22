KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
for r in a b; do TAG=_iso$r STRATS=unified legacy/run_iso.sh 1000 "1 2 3 4 5 6"; done; echo ISODONE
