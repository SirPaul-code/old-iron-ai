#!/usr/bin/env python3
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--matrix',required=True);p.add_argument('--help-file',required=True);a=p.parse_args()
m=json.loads(Path(a.matrix).read_text());h=Path(a.help_file).read_text(errors='replace')
assert isinstance(m.get('candidates'),list) and m['candidates'],'matrix has no candidates'
seen=set(); unsupported=[]
for arm in m['candidates']:
    name=arm.get('name'); assert name and name not in seen,f'invalid/duplicate arm {name!r}'; seen.add(name)
    argv=m.get('base_args',[])+arm.get('args',[])
    flags=[x for x in argv if isinstance(x,str) and x.startswith('--')]
    for flag in flags:
        if flag not in h: unsupported.append((name,flag))
if unsupported:
    for arm,flag in unsupported: print(f'ERROR_UNSUPPORTED arm={arm} flag={flag}')
    raise SystemExit(1)
print(f'CANDIDATES={len(m["candidates"])} RESULT=MATRIX_VALID')
