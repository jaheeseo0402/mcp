KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
S="1 2 3 4 5 6"; N=1000
STRATS="random structure unified afl_random afl_mcpfuzzer afl_ours afl" legacy/run_iso.sh $N "$S"
STRATS=mcpfuzzer legacy/run_iso.sh $N "$S"
STRATS=mcpfuzzer TAG=_reseed RESEED=1 legacy/run_iso.sh $N "$S"
for a in escape boundary valid near_miss; do STRATS=unified TAG=_no_$a ABL=$a legacy/run_iso.sh $N "$S"; done
for g in rel abs sib enc; do STRATS=unified TAG=_noesc_$g EDROP=$g legacy/run_iso.sh $N "$S"; done
echo ISOALLDONE
