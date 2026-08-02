# Reproduction guide

The reference V8 flags are not universal defaults. Reproduce the method, then test the hypotheses appropriate to the target host.

## 1. Clone and verify

```bash
git clone https://github.com/SirPaul-code/old-iron-ai.git
cd old-iron-ai
python3 benchmarks/prompts/materialize.py
make verify
```

The repository does not distribute model weights or a llama.cpp binary.

## 2. Prepare an isolated candidate

```bash
cp config/host.env.example config/host.env
chmod 600 config/host.env
```

Edit the binary, model path and an unused loopback port. Do not commit `config/host.env`.

## 3. Audit read-only

```bash
./scripts/audit-host.sh results/host-audit.json
/path/to/llama-server --help > results/llama-help.txt 2>&1
sha256sum /path/to/llama-server > results/llama-server.sha256
```

Capture the currently running production command and health result separately. Do not stop it.

## 4. Generate and review the matrix

```bash
python3 benchmarks/tools/generate_matrix.py \
  --audit results/host-audit.json \
  --llama-help results/llama-help.txt \
  --output results/matrix.json

python3 benchmarks/tools/validate_matrix.py \
  --matrix results/matrix.json \
  --help-file results/llama-help.txt
```

Remove irrelevant candidates and review memory requirements. On a single-socket host, NUMA placement arms should not be generated. On a system where no-mmap or research flags are unsupported, they must not be invented.

## 5. Preflight

```bash
./scripts/preflight.sh config/host.env
```

Preflight requires a loopback candidate address, a free port, readable model and executable binary.

## 6. Run detached and resumably

```bash
./scripts/control.sh start \
  --env config/host.env \
  --matrix results/matrix.json \
  --run-dir results/run-001

./scripts/control.sh status --run-dir results/run-001
./scripts/control.sh pause  --run-dir results/run-001
./scripts/control.sh resume --run-dir results/run-001
./scripts/control.sh abort  --run-dir results/run-001
```

The suite starts a candidate process group, waits for health, records the exact command, captures page placement and GPU state, executes the fixed corpus and restores NUMA-balancing/THP settings after every arm. OOM and unsupported candidates are recorded locally.

## 7. Analyze

```bash
python3 benchmarks/tools/analyze_runs.py \
  --input results/run-001/results.jsonl \
  --output results/run-001/summary.json
```

A discovery winner is not final. Repeat it across at least two independent cold process loads and preserve prompt order, cache policy and correctness hashes.

## 8. Inspect placement manually

```bash
numastat -p <pid>
python3 scripts/summarize_numa_maps.py --pid <pid>
tr '\0' ' ' < /proc/<pid>/cmdline; echo
```

Capture after server readiness and after the request.

## 9. Deployment boundary

The repository does not replace production automatically. Before deployment, report:

- baseline and validated winner;
- model load, cold prefill, decode and cached-turn results;
- context length and KV placement;
- exact command and changed files;
- output/correctness evidence;
- production health check;
- exact rollback command.

Deployment requires explicit approval from the operator.
