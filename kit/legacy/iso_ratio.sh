KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
S="1 2 3 4 5 6"; N=1000
r(){ STRATS=unified TAG=_r_$1 UW=$2 legacy/run_iso.sh $N "$S"; }
r eq 1,1,1,1; r esc50 3,1,1,1; r esc11 1,3,3,3; r bnd50 1,3,1,1; r val50 1,1,3,1; r near50 1,1,1,3
echo ISORATIODONE
