#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--audit',required=True)
p.add_argument('--llama-help',required=True)
p.add_argument('--output',required=True)
a=p.parse_args()
audit=json.loads(Path(a.audit).read_text())
help_text=Path(a.llama_help).read_text(errors='replace')
raw=audit.get('commands',audit.get('raw',{}))
lscpu=raw.get('lscpu',{}).get('stdout','')
def field(name,default):
    m=re.search(rf'^{re.escape(name)}:\s*(.+)$',lscpu,re.M)
    return m.group(1).strip() if m else default
sockets=int(field('Socket(s)','1'))
logical=int(field('CPU(s)','1'))
cores_socket=int(field('Core(s) per socket',str(max(1,logical//max(1,sockets)))))
def supported(flag): return flag in help_text
base=['--alias','${MODEL_ALIAS}','--ctx-size','${CTX_SIZE}','--n-predict','${N_PREDICT}','--host','${CANDIDATE_HOST}','--port','${CANDIDATE_PORT}','--parallel','1','--metrics','--perf']
if supported('--numa'): base += ['--numa','distribute']
policies=[('inherit',[])]
if sockets>1 and shutil.which('numactl'):
    policies += [('preferred0',['numactl','--preferred=0']),('preferred1',['numactl','--preferred=1']),('interleave',['numactl','--interleave=0,1'])]
load_modes=['mmap','none'] if supported('--load-mode') else ['default']
base_threads=max(1,cores_socket)
batch_threads=min(logical,32)
candidates=[]
def add(stage,name,prefix,args):
    candidates.append({'stage':stage,'name':name,'numactl_prefix':prefix,'args':[str(x) for x in args],'kernel':{'numa_balancing':0}})
for mode in load_modes:
    for pname,prefix in policies:
        args=['--threads',base_threads,'--threads-batch',batch_threads]
        if supported('--load-mode'): args += ['--load-mode',mode]
        if supported('--batch-size'): args += ['--batch-size',2048]
        if supported('--ubatch-size'): args += ['--ubatch-size',512]
        add('load-and-placement',f'{pname}-{mode}',prefix,args)
for t,tb in sorted(set([(base_threads,batch_threads),(min(logical,base_threads*2),batch_threads),(base_threads,max(base_threads,16))])):
    args=['--threads',t,'--threads-batch',tb]
    if supported('--load-mode'): args += ['--load-mode','none']
    if supported('--batch-size'): args += ['--batch-size',2048]
    if supported('--ubatch-size'): args += ['--ubatch-size',512]
    add('threads',f't{t}-tb{tb}',policies[-1][1] if sockets>1 else [],args)
if supported('--ubatch-size'):
    for ub in [256,512,1024]:
        args=['--threads',base_threads,'--threads-batch',batch_threads,'--batch-size',2048,'--ubatch-size',ub]
        if supported('--load-mode'): args += ['--load-mode','none']
        add('micro-batch',f'ubatch-{ub}',policies[-1][1] if sockets>1 else [],args)
out={'schema':1,'name':'adaptive-staged-screen','generated_from':{'sockets':sockets,'logical_cpus':logical,'cores_per_socket':cores_socket},'base_args':base,'candidates':candidates}
Path(a.output).write_text(json.dumps(out,indent=2)+'\n')
print(f'WROTE={a.output} CANDIDATES={len(candidates)}')
