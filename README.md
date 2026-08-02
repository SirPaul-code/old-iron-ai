# Old Iron AI

**Topology-aware llama.cpp benchmarking for memory-rich, multi-socket servers with limited GPU VRAM.**

Old Iron AI documents a controlled optimization study on a 2012 HP ProLiant DL380p Gen8 with two Intel Xeon E5-2660 CPUs, 173 GiB DDR3 and one RTX 3080 10 GiB. The reference workload was an approximately 85 GiB Qwen3-Coder-Next Q8_0 GGUF model, so host memory placement and bandwidth were part of the inference hot path.

The project began with a crude end-to-end smoke test that needed roughly eight minutes to return a one-line `OK`. That observation is only the origin story: it mixed model loading, prompt processing, runtime overhead and output generation. The publishable study starts with a fixed workload and measures those stages separately.

## Headline result

| Stage | Cold prompt-prefill | Approx. time for 8.7k input tokens |
|---|---:|---:|
| Controlled mmap baseline | 38.721 tok/s | 224.3 s |
| Paired no-mmap | 93.134 tok/s | 93.3 s |
| V7 validated profile | 104.415 tok/s | 83.2 s |
| V8 final validation | **176.093 tok/s** | **49.3 s** |

That is approximately **4.55x higher cold prompt-prefill throughput** on the same host, GPU, model family and fixed workload. It is not a claim that generated-token speed or the complete agent became 4.55x faster. Recorded generation stayed around 15–16 tok/s in the V8 agentic fixture.

V8 was validated across six samples from two independent cold process loads. The range was 173.411–176.922 tok/s with a coefficient of variation of 0.69%.

## What actually changed

| Experiment | Result | Supported conclusion |
|---|---:|---|
| Model pages on NUMA node 1 vs node 0 | 31.30 vs 48.74 tok/s | Physical page placement changed throughput by 55.7% under the V3 load path. |
| `threads=8, threads-batch=32` vs `16/32` | 38.770 vs 24.865 tok/s | More CPU workers could create harmful synchronization and cross-socket traffic. |
| Paired mmap vs no-mmap | 38.721 vs 93.134 tok/s | The loading/allocation path was the largest validated V1–V7 change. |
| Local node bandwidth vs concurrent nodes | 19.515 / 19.685 vs 39.185 GiB/s | Both memory controllers could contribute when the policy and load path matched. |
| V8 `ubatch=1024` vs `ubatch=256` | 174.483 vs 60.432 tok/s | Micro-batch geometry caused the final large V8 step. |
| Explicit allocator, AVX1 and MoE placement prototypes | Controls remained selected | These research branches did not cause the published result. |

The GPU was not replaced and the model was not changed. The result came from fixing the host pipeline feeding the GPU: deterministic placement experiments, no-mmap loading, interleaving across both memory controllers, a stable worker geometry and a larger physical micro-batch.

## Final selected benchmark profile

```text
process policy       numactl --interleave=0,1
llama.cpp NUMA mode  --numa distribute
load path            --load-mode none
context               one 32k slot for the controlled V8 profile
batch / micro-batch  --batch-size 2048 --ubatch-size 1024
CPU workers          --threads 8 --threads-batch 32
MoE split            --n-cpu-moe 45
GPU offload          --gpu-layers auto
KV cache             Q8 K and Q8 V in the recorded profile
prompt cache         disabled for cold-prefill validation
```

These values are a reproducible hypothesis set for similar systems, not universal defaults.

## Why it worked

The 85 GiB model could not fit in 10 GiB of VRAM, so ordinary DDR3 was part of the inference hot path. The server is two NUMA domains connected by QPI rather than one flat pool of cores and RAM. V3 showed that physical page placement alone could change throughput by more than half. V6 then showed that placement did not rescue the mmap path: paired no-mmap loads were about 2.4x faster and loaded the model in roughly 475 seconds instead of roughly 1,386 seconds.

The V7 profile raised recorded GPU utilization from 38.49% to 97.45% while CPU IPC rose from 0.446 to 1.852. Concurrent memory testing reached 39.185 GiB/s, approximately the sum of the two local controllers. The evidence supports a host-pipeline explanation: the original runtime did not feed the GPU continuously; no-mmap plus an interleaved policy allowed more useful host and GPU work to overlap.

V8 exposed another large control after the loading path was corrected. A 1024-token micro-batch reached 174.483 tok/s in screening, while 256 reached 60.432 tok/s. The final six-sample validation then reached 176.093 tok/s.

## Repository map

```text
benchmarks/tools/          candidate generation, execution and analysis
benchmarks/prompts/        fingerprints-only prompt provenance manifest
config/                    safe host configuration template
data/                      normalized V3–V8 measurements
evidence/v8/               final selected candidate and correctness evidence
docs/                      article, methodology, results and limitations
prompts/                    autonomous-agent entry point
scripts/                    audit, preflight, control and release verification
tests/                      repository consistency tests
CLAIM_LEDGER.md             public claim-to-evidence map
```

## Quick start on another host

Start with the read-only audit and capture the exact CLI supported by the installed binary:

```bash
./scripts/audit-host.sh results/host-audit.json
/path/to/llama-server --help > results/llama-help.txt 2>&1
python3 benchmarks/tools/generate_matrix.py \
  --audit results/host-audit.json \
  --llama-help results/llama-help.txt \
  --output results/matrix.json
```

Review the generated matrix. The runner uses an isolated loopback port, records effective arguments, treats OOM and unsupported candidates as local failures, captures NUMA placement and restores kernel settings after each arm. It does not replace an existing production service automatically.

The agent-oriented entry point is [`prompts/optimize-my-host.md`](prompts/optimize-my-host.md). Agent safety and evidence rules are in [`AGENTS.md`](AGENTS.md).

## Negative results preserved

- `MLOCK_ONFAULT` produced 6.19 and 28.19 tok/s and moved page-fault cost into the critical path.
- Process affinity did not explain the primary ceiling and sometimes reduced throughput.
- `threads=16, threads-batch=32` regressed to 24.865 tok/s.
- A one-load `THP=never` result was promising, but later work did not establish it as the causal winner.
- The explicit in-engine NUMA allocator, AVX1 prefetch variants and MoE placement prototype did not beat their controls.

## Evidence boundary

Committed CSV and JSON files preserve the reported values used by public claims. Where only a normalized research handoff was available, the repository labels it as normalized evidence rather than pretending it is the original raw log.

The final public handoff preserved three SHA-256 prompt fingerprints and the reported 8,663-token input, but not the original prompt text. The repository therefore publishes a `fingerprints-only` manifest and does not fabricate replacement prompts. Exact token-stream reproduction requires the original artifacts matching those hashes. The complete ordered source patch series for a bit-identical research-binary rebuild was also not available, so exact source reconstruction is not claimed.

## Scope

This is a single-host systems study focused on cold prompt-prefill, selected cached turns, memory placement and runtime geometry. It is not a model-quality evaluation, multi-user serving benchmark, wall-power/TCO study or comparison against modern AI appliances. Long-context V9 work is deliberately separate because it exposed a different bottleneck.

Run the repository verification with:

```bash
make verify
```

## License

MIT. See [`LICENSE`](LICENSE).
