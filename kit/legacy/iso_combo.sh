KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
S="1 2 3 4 5 6"; N=1000
c(){ STRATS=unified TAG=_c_$1 UW=$2 legacy/run_iso.sh $N "$S"; }
c esc 1,0,0,0; c escval 1,0,1,0; c escvalnear 1,0,1,1; c escboundval 1,1,1,0
echo ISOCOMBODONE
