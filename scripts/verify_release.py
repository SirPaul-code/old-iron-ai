#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def close(actual: float, expected: float, tolerance: float = 1e-6):
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f'{actual} != {expected}')


# Every committed JSON file must parse.
for path in ROOT.rglob('*.json'):
    json.loads(path.read_text())

# The original prompt text was not part of the public handoff. Verify the
# published fingerprints and provenance statement instead of fabricating data.
manifest = load('benchmarks/prompts/manifest.json')
assert manifest['publication_status'] == 'fingerprints-only'
assert manifest['benchmark_input_tokens'] == 8663
assert len(manifest['artifacts']) == 3
for artifact in manifest['artifacts']:
    assert re.fullmatch(r'[0-9a-f]{64}', artifact['sha256'])
assert (ROOT / 'benchmarks/prompts/README.md').is_file()

raw = load('evidence/v8/RESULTS_SUMMARY.json')
close(raw['final_validation']['median_prompt_tok_s'], 176.09250719268482)
assert raw['final_validation']['samples'] == 6
assert raw['final_validation']['cv'] < 0.01

study = load('data/study-summary.json')
close(study['headline']['speedup'], 176.09250719268482 / 38.721014)
assert 4.54 < study['headline']['speedup'] < 4.56

readme = (ROOT / 'README.md').read_text()
assert 'prompt-prefill' in readme
assert '15–16 tok/s' in readme
assert 'fingerprints-only' in readme

bad = re.compile(r'\b(TODO|FIXME|TBD)\b|coming soon|<repository-url>', re.I)
for path in ROOT.rglob('*'):
    if (
        not path.is_file()
        or '.git' in path.parts
        or '__pycache__' in path.parts
        or path.resolve() == Path(__file__).resolve()
    ):
        continue
    text = path.read_text(errors='ignore')
    assert not bad.search(text), f'unfinished marker in {path}'
    assert '192.168.1.235' not in text
    assert '/srv/ai/config/client.env' not in text

for markdown in ROOT.rglob('*.md'):
    for target in re.findall(r'\[[^]]*\]\(([^)]+)\)', markdown.read_text(errors='ignore')):
        if target.startswith(('http://', 'https://', '#', 'mailto:')):
            continue
        clean = target.split('#', 1)[0]
        if clean and not (markdown.parent / clean).resolve().exists():
            raise AssertionError(f'broken link in {markdown}: {target}')

print('RESULT=RELEASE_VERIFIED')
