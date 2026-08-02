import csv,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(['python3','materialize.py'],cwd=ROOT/'benchmarks/prompts',check=True)

    def test_required_files(self):
        for path in ['README.md','docs/article.md','docs/results.md','CLAIM_LEDGER.md','evidence/v8/RESULTS_SUMMARY.json','prompts/optimize-my-host.md']:
            self.assertTrue((ROOT/path).is_file(),path)

    def test_v8_final(self):
        data=json.loads((ROOT/'evidence/v8/RESULTS_SUMMARY.json').read_text())['final_validation']
        self.assertAlmostEqual(data['median_prompt_tok_s'],176.09250719268482)
        self.assertEqual(data['samples'],6)
        self.assertLess(data['cv'],0.01)

    def test_v6_pair(self):
        with (ROOT/'data/v6-load-path.csv').open() as stream: rows=list(csv.DictReader(stream))
        mmap=sorted(float(r['prompt_tok_s']) for r in rows if r['load'] in ('mmap-a','mmap-b'))
        no_mmap=sorted(float(r['prompt_tok_s']) for r in rows if r['load'] in ('no-mmap-a','no-mmap-b'))
        mm=(mmap[2]+mmap[3])/2
        nn=(no_mmap[2]+no_mmap[3])/2
        self.assertAlmostEqual(mm,38.72101397838546)
        self.assertAlmostEqual(nn,93.13375297984027)
        self.assertGreater(nn/mm,2.40)

    def test_prompt_hashes(self):
        result=subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=ROOT/'benchmarks/prompts',capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_numa_parser(self):
        import importlib.util
        path=ROOT/'scripts/summarize_numa_maps.py'
        spec=importlib.util.spec_from_file_location('numa_summary',path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result=module.summarize('x N0=10 N1=5\ny N0=5\n')
        self.assertEqual(result['total_pages'],20)
        self.assertAlmostEqual(result['nodes']['0']['percent'],75.0)

if __name__=='__main__': unittest.main()
