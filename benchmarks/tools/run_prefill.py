#!/usr/bin/env python3
import argparse, hashlib, json, os, time, urllib.request
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--base-url',required=True); p.add_argument('--prompt',action='append',required=True)
p.add_argument('--repeats',type=int,default=1); p.add_argument('--n-predict',type=int,default=1)
p.add_argument('--timeout',type=int,default=7200); p.add_argument('--output',required=True)
p.add_argument('--arm',required=True); p.add_argument('--api-key-env',default='API_KEY')
a=p.parse_args()
headers={'Content-Type':'application/json'}
key=os.environ.get(a.api_key_env,'')
if key: headers['Authorization']='Bearer '+key
out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
for prompt_path in a.prompt:
    text=Path(prompt_path).read_text(errors='replace')
    sha=hashlib.sha256(text.encode()).hexdigest()
    for repeat in range(1,a.repeats+1):
        payload={'prompt':text,'n_predict':a.n_predict,'temperature':0,'seed':42,'stream':False,'cache_prompt':False}
        req=urllib.request.Request(a.base_url.rstrip('/')+'/completion',data=json.dumps(payload).encode(),headers=headers,method='POST')
        started=time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=a.timeout) as r: result=json.loads(r.read().decode())
            row={'status':'ok','arm':a.arm,'prompt_file':Path(prompt_path).name,'prompt_sha256':sha,'repeat':repeat,'wall_s':time.monotonic()-started,'timings':result.get('timings',{}),'tokens_cached':result.get('tokens_cached'),'tokens_evaluated':result.get('tokens_evaluated'),'content_sha256':hashlib.sha256(result.get('content','').encode()).hexdigest()}
        except Exception as e:
            row={'status':'request_failed','arm':a.arm,'prompt_file':Path(prompt_path).name,'prompt_sha256':sha,'repeat':repeat,'wall_s':time.monotonic()-started,'error':str(e)}
        with out.open('a') as f: f.write(json.dumps(row,sort_keys=True)+'\n')
        print(json.dumps(row))
