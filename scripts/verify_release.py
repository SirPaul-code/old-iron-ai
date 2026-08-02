#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text())
def close(a,b,tol=1e-6):
    if not math.isclose(a,b,rel_tol=tol,abs_tol=tol): raise AssertionError(f'{a} != {b}')
for path in ROOT.rglob('*.json'): json.loads(path.read_text())
# Materialize and verify the exact fixed corpus.
exec(compile((ROOT/'benchmarks/prompts/materialize.py').read_text(),str(ROOT/'benchmarks/prompts/materialize.py'),'exec'),{'__file__':str(ROOT/'benchmarks/prompts/materialize.py'),'__name__':'__main__'})
for line in (ROOT/'benchmarks/prompts/SHA256SUMS').read_text().splitlines():
    digest,name=line.split(None,1)
    actual=hashlib.sha256((ROOT/'benchmarks/prompts'/name.strip()).read_bytes()).hexdigest()
    assert digest==actual,(name,digest,actual)
raw=load('evidence/v8/RESULTS_SUMMARY.json')
close(raw['final_validation']['median_prompt_tok_s'],176.09250719268482)
assert raw['final_validation']['samples']==6
study=load('data/study-summary.json')
close(study['headline']['speedup'],176.09250719268482/38.721014)
assert 4.54 < study['headline']['speedup'] < 4.56
readme=(ROOT/'README.md').read_text()
assert 'prompt-prefill' in readme and '15–16 tok/s' in readme
bad=re.compile(r'\b(TODO|FIXME|TBD)\b|coming soon|<repository-url>',re.I)
for path in ROOT.rglob('*'):
    if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts or path.resolve()==Path(__file__).resolve(): continue
    text=path.read_text(errors='ignore')
    assert not bad.search(text),f'unfinished marker in {path}'
    assert '192.168.1.235' not in text
    assert '/srv/ai/config/client.env' not in text
for md in ROOT.rglob('*.md'):
    for target in re.findall(r'\[[^]]*\]\(([^)]+)\)',md.read_text(errors='ignore')):
        if target.startswith(('http://','https://','#','mailto:')): continue
        clean=target.split('#',1)[0]
        if clean and not (md.parent/clean).resolve().exists(): raise AssertionError(f'broken link in {md}: {target}')
print('RESULT=RELEASE_VERIFIED')
