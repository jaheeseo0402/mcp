import sys,json,os,shutil,hashlib,itertools,time
sys.path.insert(0,'/tmp/claude-0/-home-claude/861682e7-01ca-5830-8b5e-2318d47f2212/scratchpad/tk')
from mcpc import Client
S='/tmp/claude-0/-home-claude/861682e7-01ca-5830-8b5e-2318d47f2212/scratchpad/tk'
W='/tmp/pre/w'; R=W+'/a'
cmds={'old':['node',S+'/node_modules/mcp-server-filesystem/dist/index.js',R],
'agent':['node',S+'/srv/node_modules/@agent-infra/mcp-server-filesystem/dist/index.cjs','--allowed-directories',R]}
def reset(sym):
    shutil.rmtree(W,ignore_errors=True); os.makedirs(R+'/d'); os.makedirs(W+'/a_evil'); os.makedirs(W+'/o')
    open(R+'/f.txt','w').write('inside'); open(R+'/d/g.txt','w').write('inside2')
    open(W+'/secret.txt','w').write('SECRET'); open(W+'/a_evil/s.txt','w').write('SECRET'); open(W+'/o/s.txt','w').write('SECRET')
    if sym: os.symlink(W+'/o',R+'/ln')
def snap():
    out={}
    for dp,dn,fn in os.walk(W):
        if dp==R or dp.startswith(R+'/'): continue
        for n in fn+dn:
            p=os.path.join(dp,n)
            if p==R or p.startswith(R+'/'): continue
            try: out[p]=hashlib.md5(open(p,'rb').read()).hexdigest() if os.path.isfile(p) else 'D'
            except Exception: out[p]='?'
    return out
IN=['f.txt','d/g.txt','d','new.txt','d/new.txt']
ESC=['../secret.txt','../o/s.txt','../a_evil/s.txt','../new_out.txt','../o/new.txt','../a_evil/new.txt','../newdir']
LN=['ln/s.txt','ln/new.txt']
def P(x): return R+'/'+x
def actions(sym):
    paths=IN+ESC+(LN if sym else [])
    A=[]
    for p in paths:
        for form in ('rel','abs'):
            pp=P(p)
            A+= [('read_file',{'path':pp}),('write_file',{'path':pp,'content':'X'}),('list_directory',{'path':pp}),
                 ('create_directory',{'path':pp}),('get_file_info',{'path':pp}),('edit_file',{'path':pp,'edits':[{'oldText':'inside','newText':'PWN'}]})]
            break
    # abs outside forms
    for ap in [W+'/secret.txt',W+'/a_evil/s.txt',W+'/a_evil/new.txt']:
        A+=[('read_file',{'path':ap}),('write_file',{'path':ap,'content':'X'})]
    for s in IN[:3]+(['ln/s.txt'] if sym else []):
        for d in IN[3:]+ESC[3:]+(['ln/new.txt'] if sym else []):
            A.append(('move_file',{'source':P(s),'destination':P(d)}))
    for s in ESC[:3]:
        for d in IN[3:]: A.append(('move_file',{'source':P(s),'destination':P(d)}))
    return A
def run(cl,seq):
    resp=[]; leak=False
    for t,a in seq:
        r=cl.req('tools/call',{'name':t,'arguments':a}); s=json.dumps(r)
        if 'SECRET' in s and 'error' not in r and not r.get('result',{}).get('isError'): leak=True
        resp.append(r)
    return leak
def viol(cl,seq,sym):
    reset(sym); b=snap(); leak=run(cl,seq); a=snap()
    return leak or a!=b
for srv in sys.argv[1:]:
  for sym in (False,True):
    reset(sym); cl=Client(cmds[srv]); A=actions(sym)
    single={}
    for i,x in enumerate(A): single[i]=viol(cl,[x],sym)
    sv=[i for i in single if single[i]]
    # pairs: only pairs where neither alone violates
    found=[]; n=0
    safe=[i for i in single if not single[i]]
    # restrict first-call to state-changing tools, second to all
    mut=[i for i in safe if A[i][0] in('write_file','create_directory','move_file','edit_file')]
    t0=time.time()
    for i in mut:
        for j in safe:
            n+=1
            if viol(cl,[A[i],A[j]],sym): found.append((A[i],A[j]))
    print(srv,'sym' if sym else 'nosym','actions',len(A),'single-violating',len(sv),'pairs tested',n,'pair-only violations',len(found),round(time.time()-t0),'s',flush=True)
    for f in found[:15]: print('  ',json.dumps(f).replace(W,'W'))
    cl.close()
