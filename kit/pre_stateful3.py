import sys,random,json
sys.argv=[sys.argv[0]]
exec(open('pre.py').read().split("for srv in sys.argv[1:]:")[0])
random.seed(1)
for srv in ('old','agent'):
  for sym in (False,True):
    reset(sym); cl=Client(cmds[srv]); A=actions(sym)
    sv=[i for i,x in enumerate(A) if viol(cl,[x],sym)]
    if not sym: print(srv,'single:',sorted(set((A[i][0],json.dumps(A[i][1]).replace(W,'W')[:70]) for i in sv))[:12])
    safe=[i for i in range(len(A)) if i not in sv]; f=0; ex=None
    for _ in range(15000):
        s=[A[random.choice(safe)] for _ in range(3)]
        # skip if any single call part violates (already safe) ; test seq
        if viol(cl,s,sym): f+=1; ex=ex or s
    print(srv,'sym' if sym else 'nosym','3-seq random 15000 -> violations',f, json.dumps(ex).replace(W,'W') if ex else '')
    cl.close()
