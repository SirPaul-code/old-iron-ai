#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,re,signal,subprocess,time,urllib.request
from pathlib import Path
stop_requested=False
def on_signal(signum,frame):
    global stop_requested; stop_requested=True
signal.signal(signal.SIGTERM,on_signal); signal.signal(signal.SIGINT,on_signal)
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--matrix',required=True);p.add_argument('--run-dir',required=True);a=p.parse_args()
run=Path(a.run_dir);run.mkdir(parents=True,exist_ok=True)
def env_file(path):
    out={}
    for raw in Path(path).read_text().splitlines():
        line=raw.strip()
        if line and not line.startswith('#') and '=' in line:
            k,v=line.split('=',1);out[k]=v.strip().strip('"').strip("'")
    return out
cfg=env_file(a.env);matrix=json.loads(Path(a.matrix).read_text())
for k in ('LLAMA_SERVER_BIN','MODEL_PATH','CANDIDATE_HOST','CANDIDATE_PORT','STARTUP_TIMEOUT','REQUEST_TIMEOUT'):
    if not cfg.get(k): raise SystemExit(f'missing {k}')
def expand(v):
    if not isinstance(v,str): return v
    for k,x in cfg.items(): v=v.replace('${'+k+'}',x)
    return v
def atomic(path,obj):
    t=path.with_suffix(path.suffix+'.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(path)
def state(**kw):
    cur={}
    try:cur=json.loads((run/'state.json').read_text())
    except Exception:pass
    cur.update(kw);cur['updated_at']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());atomic(run/'state.json',cur)
def completed():
    try:return set(json.loads((run/'completed.json').read_text()))
    except Exception:return set()
def mark(name):atomic(run/'completed.json',sorted(completed()|{name}))
def health():
    try:
        with urllib.request.urlopen(f"http://{cfg['CANDIDATE_HOST']}:{cfg['CANDIDATE_PORT']}/health",timeout=3) as r:d=json.loads(r.read().decode())
        return d.get('status') in ('ok','ready') or d.get('healthy') is True
    except Exception:return False
def stop(proc):
    if proc is None:return
    try:os.killpg(proc.pid,signal.SIGTERM)
    except Exception:pass
    for _ in range(30):
        if proc.poll() is not None:return
        time.sleep(1)
    try:os.killpg(proc.pid,signal.SIGKILL)
    except Exception:pass
def read(path):
    try:
        x=Path(path).read_text().strip();m=re.search(r'\[([^]]+)\]',x);return m.group(1) if m else x
    except Exception:return None
def write(path,value):Path(path).write_text(str(value))
orig={'numa_balancing':read('/proc/sys/kernel/numa_balancing'),'thp_enabled':read('/sys/kernel/mm/transparent_hugepage/enabled'),'thp_defrag':read('/sys/kernel/mm/transparent_hugepage/defrag')};atomic(run/'original-kernel-settings.json',orig)
def restore():
    for k,path in [('numa_balancing','/proc/sys/kernel/numa_balancing'),('thp_enabled','/sys/kernel/mm/transparent_hugepage/enabled'),('thp_defrag','/sys/kernel/mm/transparent_hugepage/defrag')]:
        if orig.get(k) is not None:
            try:write(path,orig[k])
            except Exception:pass
def apply(arm):
    s=arm.get('kernel',{})
    if 'numa_balancing' in s:write('/proc/sys/kernel/numa_balancing',s['numa_balancing'])
    if 'thp_enabled' in s:write('/sys/kernel/mm/transparent_hugepage/enabled',s['thp_enabled'])
    if 'thp_defrag' in s:write('/sys/kernel/mm/transparent_hugepage/defrag',s['thp_defrag'])
def capture(adir,pid,label):
    commands={'numastat':['numastat','-p',str(pid)],'nvidia_smi':['nvidia-smi','--query-gpu=timestamp,name,utilization.gpu,memory.used,power.draw','--format=csv,noheader,nounits']}
    for name,cmd in commands.items():
        try:r=subprocess.run(cmd,text=True,capture_output=True,timeout=30);(adir/f'{label}-{name}.txt').write_text(r.stdout+('\nSTDERR:\n'+r.stderr if r.stderr else ''))
        except Exception as e:(adir/f'{label}-{name}.txt').write_text(str(e)+'\n')
    for source,name in [(f'/proc/{pid}/numa_maps','numa_maps'),(f'/proc/{pid}/status','status'),(f'/proc/{pid}/cmdline','cmdline')]:
        try:
            data=Path(source).read_bytes();(adir/f'{label}-{name}.txt').write_bytes(data.replace(b'\0',b' ') if name=='cmdline' else data)
        except Exception as e:(adir/f'{label}-{name}.txt').write_text(str(e)+'\n')
root=Path('/opt/old-iron-ai');root=root if root.exists() else Path(__file__).resolve().parents[2]
prompts=[str(x) for x in sorted((root/'benchmarks/prompts').glob('prompt-*.txt'))]
result_file=run/'results.jsonl';done=completed();proc=None;log=None
try:
  for idx,arm in enumerate(matrix['candidates'],1):
    name=arm['name']
    if name in done:continue
    if stop_requested or (run/'PAUSE_REQUESTED').exists():state(state='PAUSED',current_arm=name);(run/'RESULT').write_text('INTERRUPTED\n');raise SystemExit(0)
    if (run/'ABORT_REQUESTED').exists():state(state='ABORTED',current_arm=name);(run/'RESULT').write_text('FAIL\n');raise SystemExit(1)
    adir=run/'arms'/name;adir.mkdir(parents=True,exist_ok=True);apply(arm)
    prefix=[expand(x) for x in arm.get('numactl_prefix',matrix.get('numactl_prefix',[]))]
    command=prefix+[cfg['LLAMA_SERVER_BIN'],'--model',cfg['MODEL_PATH']]+[expand(x) for x in matrix.get('base_args',[])]+[expand(x) for x in arm.get('args',[])]
    atomic(adir/'command.json',{'argv':command,'kernel':arm.get('kernel',{}),'stage':arm.get('stage')})
    state(state='STARTING',current_arm=name,index=idx,total=len(matrix['candidates']))
    log=(adir/'server.log').open('wb');proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,**cfg})
    deadline=time.time()+int(cfg['STARTUP_TIMEOUT']);ready=False
    while time.time()<deadline and not stop_requested:
        if proc.poll() is not None:break
        if health():ready=True;break
        time.sleep(2)
    if stop_requested or (run/'PAUSE_REQUESTED').exists():
        stop(proc);log.close();proc=None;state(state='PAUSED',current_arm=name);(run/'RESULT').write_text('INTERRUPTED\n');raise SystemExit(0)
    if not ready:
        stop(proc);log.close();proc=None;detail=(adir/'server.log').read_text(errors='replace')[-8000:];status='startup_oom' if re.search(r'out of memory|cudaMalloc failed|failed to allocate',detail,re.I) else 'startup_failed'
        with result_file.open('a') as f:f.write(json.dumps({'status':status,'arm':name,'stage':arm.get('stage'),'detail':detail})+'\n')
        mark(name);done.add(name);restore();continue
    capture(adir,proc.pid,'ready');state(state='RUNNING',current_arm=name,index=idx,total=len(matrix['candidates']))
    cmd=['python3',str(root/'benchmarks/tools/run_prefill.py'),'--base-url',f"http://{cfg['CANDIDATE_HOST']}:{cfg['CANDIDATE_PORT']}",'--output',str(result_file),'--arm',name,'--n-predict',cfg.get('N_PREDICT','1'),'--timeout',cfg['REQUEST_TIMEOUT']]
    for prompt in prompts:cmd+=['--prompt',prompt]
    subprocess.run(cmd,env={**os.environ,**cfg},check=False);capture(adir,proc.pid,'after')
    stop(proc);log.close();proc=None;mark(name);done.add(name);restore()
  ok_rows=0
  if result_file.exists():
    for line in result_file.read_text().splitlines():
      try:
        if json.loads(line).get('status')=='ok': ok_rows+=1
      except Exception: pass
  if ok_rows == 0:
    state(state='FAILED',completed=len(done),reason='NO_SUCCESSFUL_MEASUREMENTS');(run/'RESULT').write_text('FAIL\n');raise SystemExit(1)
  state(state='COMPLETE',completed=len(done),successful_measurements=ok_rows);(run/'RESULT').write_text('PASS\n')
except BaseException:
  if not (run/'RESULT').exists():(run/'RESULT').write_text('FAIL\n')
  raise
finally:
  stop(proc)
  if log and not log.closed:log.close()
  restore()
