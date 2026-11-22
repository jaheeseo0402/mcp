KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
S="1 2 3 4 5 6"; N=1000
for p in 10 20 30 40 50 60 70; do
 q=$(python3 -c "print(round((100-$p)/3/100,4))"); e=$(python3 -c "print($p/100)")
 STRATS=unified TAG=_sw$p UW=$e,$q,$q,$q legacy/run_iso.sh $N "$S"
done
echo SWEEPDONE
