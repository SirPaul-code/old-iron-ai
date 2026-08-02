#!/usr/bin/env python3
import argparse, json, statistics
from collections import defaultdict
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--input',required=True)
p.add_argument('--output',required=True)
a=p.parse_args()
rows=[]
for line in Path(a.input).read_text().splitlines():
    try: rows.append(json.loads(line))
    except json.JSONDecodeError: pass
by=defaultdict(list)
for row in rows:
    if row.get('status')=='ok' and row.get('timings',{}).get('prompt_per_second'):
        by[row['arm']].append(row)
summary=[]
for arm, values in by.items():
    pp=[float(v['timings']['prompt_per_second']) for v in values]
    gp=[float(v['timings'].get('predicted_per_second',0)) for v in values if v['timings'].get('predicted_per_second')]
    mean=statistics.mean(pp)
    summary.append({
        'arm':arm,
        'samples':len(pp),
        'prompt_tok_s_median':statistics.median(pp),
        'prompt_tok_s_min':min(pp),
        'prompt_tok_s_max':max(pp),
        'prompt_cv':statistics.pstdev(pp)/mean if len(pp)>1 and mean else 0,
        'generation_tok_s_median':statistics.median(gp) if gp else None,
    })
summary.sort(key=lambda x:x['prompt_tok_s_median'],reverse=True)
out={'winner':summary[0] if summary else None,'arms':summary,'failed_rows':sum(1 for r in rows if r.get('status')!='ok')}
Path(a.output).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
