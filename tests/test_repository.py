import csv
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_required_files(self):
        required = [
            'README.md',
            'docs/article.md',
            'docs/results.md',
            'CLAIM_LEDGER.md',
            'evidence/v8/RESULTS_SUMMARY.json',
            'prompts/optimize-my-host.md',
            'benchmarks/prompts/manifest.json',
            'benchmarks/prompts/README.md',
        ]
        for path in required:
            self.assertTrue((ROOT / path).is_file(), path)

    def test_v8_final(self):
        data = json.loads((ROOT / 'evidence/v8/RESULTS_SUMMARY.json').read_text())['final_validation']
        self.assertAlmostEqual(data['median_prompt_tok_s'], 176.09250719268482)
        self.assertEqual(data['samples'], 6)
        self.assertLess(data['cv'], 0.01)

    def test_v6_pair(self):
        with (ROOT / 'data/v6-load-path.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        mmap = sorted(float(row['prompt_tok_s']) for row in rows if row['load'] in ('mmap-a', 'mmap-b'))
        no_mmap = sorted(float(row['prompt_tok_s']) for row in rows if row['load'] in ('no-mmap-a', 'no-mmap-b'))
        mmap_median = (mmap[2] + mmap[3]) / 2
        no_mmap_median = (no_mmap[2] + no_mmap[3]) / 2
        self.assertAlmostEqual(mmap_median, 38.72101397838546)
        self.assertAlmostEqual(no_mmap_median, 93.13375297984027)
        self.assertGreater(no_mmap_median / mmap_median, 2.40)

    def test_prompt_fingerprint_manifest(self):
        manifest = json.loads((ROOT / 'benchmarks/prompts/manifest.json').read_text())
        self.assertEqual(manifest['publication_status'], 'fingerprints-only')
        self.assertEqual(manifest['benchmark_input_tokens'], 8663)
        self.assertEqual(len(manifest['artifacts']), 3)
        names = [artifact['name'] for artifact in manifest['artifacts']]
        self.assertEqual(names, ['prompt-A.txt', 'prompt-B.txt', 'prompt-C.txt'])
        for artifact in manifest['artifacts']:
            self.assertRegex(artifact['sha256'], re.compile(r'^[0-9a-f]{64}$'))

    def test_numa_parser(self):
        path = ROOT / 'scripts/summarize_numa_maps.py'
        spec = importlib.util.spec_from_file_location('numa_summary', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.summarize('x N0=10 N1=5\ny N0=5\n')
        self.assertEqual(result['total_pages'], 20)
        self.assertAlmostEqual(result['nodes']['0']['percent'], 75.0)


if __name__ == '__main__':
    unittest.main()
