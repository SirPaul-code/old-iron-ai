# Old Iron AI

**Topology-aware llama.cpp benchmarking for memory-rich, multi-socket servers with limited GPU VRAM.**

This project documents how a dusty 2012 HP DL380p Gen8 with two Xeon E5-2660 processors, 173 GiB of DDR3 and one RTX 3080 10 GiB became a practical local inference host for long coding, research and authorized security tasks.

The first crude end-to-end smoke test took roughly eight minutes to return a one-line `OK`. That observation is part of the origin story, not part of the controlled benchmark. The measured study begins with a fixed prompt corpus and separates model loading, cold prompt-prefill, cached turns and output generation.

## TL;DR

- Reference workload: Qwen3-Coder-Next Q8_0 GGUF, approximately 85 GiB, with most weights resident in system memory.
- Controlled mmap-oriented baseline: **38.721 prompt-prefill tokens/s**.
- Final V8 median: **176.093 prompt-prefill tokens/s**.
- Same host, GPU, model family and fixed corpus: **approximately 4.55x higher cold-prefill throughput**.
- V8 validation: **six samples across two independent cold process loads**, range **173.411–176.922 tok/s**, CV **0.69%**.
- Recorded output generation remained around **15–16 tok/s**. The 176 tok/s result is not decode speed.
- In a separate three-turn agentic fixture, the first 8.7k-token turn fell from **87.949 s** on the V7 baseline to **52.938 s** on V8; the short cached follow-up turns remained around **2.7 s**.

The final result did not come from a new tensor engine or a custom AVX kernel. It came mainly from correcting the model-loading path, using both NUMA memory controllers, avoiding an unfavorable thread geometry and selecting a much larger micro-batch for prompt processing.

## Reference result

| Stage | Prompt-prefill | Approx. time for 8.7k tokens | What the stage established |
|---|---:|---:|---|
| Paired mmap baseline | 38.721 tok/s | 224.3 s | Reproducible controlled baseline |
| Paired no-mmap | 93.134 tok/s | 93.3 s | Load path was the first major bottleneck |
| V7 validated baseline | 104.415 tok/s | 83.2 s | no-mmap + interleave + stable thread policy |
| V8 final validation | **176.093 tok/s** | **49.3 s** | batch 2048 / micro-batch 1024 on the corrected pipeline |

The derived prompt times describe the isolated cold-prefill stage of the fixed benchmark. The separate agentic fixture above includes request overhead and 32 generated tokens.

## What changed, and what each change proved

| Experiment | Result | Supported conclusion |
|---|---:|---|
| V3 model pages on node 1 vs node 0 | 31.30 vs 48.74 tok/s | Physical placement alone changed throughput by 55.7% under that load path. |
| V4 automatic NUMA balancing on vs off | Similar steady-state speed; fewer pathological runs with it off | Disabling balancing improved determinism more than raw throughput. |
| V5 `threads=8, threads-batch=32` vs `16/32` | 38.770 vs 24.865 tok/s | More CPU workers could reduce throughput through synchronization and cross-socket traffic. |
| V6 paired mmap vs no-mmap | 38.721 vs 93.134 tok/s | The loading/allocation path was the largest validated V1–V7 change. |
| V7 interleave across both sockets | 104.415 tok/s; 39.185 GiB/s concurrent memory triad | Both memory controllers could contribute when the allocation path and process policy matched. |
| V8 micro-batch screen | ubatch 1024: 174.483; ubatch 256: 60.432 tok/s | Runtime geometry, especially micro-batch size, caused the final V8 step. |
| V8 explicit allocator, AVX1 and MoE placement prototypes | Controls remained the selected candidates | These research branches did not cause the final published result. |

## Final selected profile

The controlled V8 candidate used this shape:

```text
process policy       numactl --interleave=0,1
llama.cpp NUMA mode  --numa distribute
load path            --load-mode none          # no-mmap
context slots        one 32k slot in the benchmark profile
batch / micro-batch  --batch-size 2048 --ubatch-size 1024
CPU workers          --threads 8 --threads-batch 32
MoE split            --n-cpu-moe 45
GPU offload          --gpu-layers auto
KV cache             Q8 K and Q8 V in the recorded profile
prompt cache          disabled for cold-prefill validation
```

The public data also preserves the screening arms that lost. The winning numbers are specific to this host, build, model quantization and corpus; they are a hypothesis set for another machine, not a universal configuration.

## Why it worked

The 85 GiB model could not fit in 10 GiB of VRAM, so host memory was part of the inference hot path. This server is two NUMA domains connected by QPI rather than one flat pool of cores and RAM. V3 showed that where pages physically landed could change prompt throughput by more than half. V6 then showed that even near-perfect node-0 placement did not rescue the mmap path: paired no-mmap loads were about 2.4x faster and loaded the model in roughly 475 seconds instead of roughly 1,386 seconds.

The V7 profile moved GPU utilization from 38.49% in the mmap baseline to 97.45%, while CPU IPC rose from 0.446 to 1.852. Concurrent local memory tests measured 19.515 GiB/s on node 0, 19.685 GiB/s on node 1 and 39.185 GiB/s when both controllers worked at the same time. The evidence therefore supports a host-pipeline explanation: the original runtime did not feed the GPU continuously; no-mmap plus an interleaved policy made more useful host and GPU work overlap.

V8 did not replace that finding. It exposed another large control knob after the loading path was fixed. A 1024-token micro-batch reached 174.483 tok/s in screening, while 256 reached 60.432 and batch 4096 / micro-batch 512 remained near 102.466. The final six-sample validation then reached 176.093 tok/s.

Read the full analysis in [`docs/article.md`](docs/article.md) and every reported arm in [`docs/results.md`](docs/results.md).

## What did not work

- `MLOCK_ONFAULT` produced 6.19 and 28.19 tok/s and was rejected because the deferred page-fault cost moved into the critical path.
- Process-wide affinity did not explain the main ceiling and sometimes made the system slower.
- `threads=16, threads-batch=32` fell to 24.865 tok/s in the V5 matrix.
- A one-load `THP=never` probe reached 102.259 tok/s, but the later ABBA programme did not establish THP as a reliable causal winner; V7 retained the original THP mode.
- The explicit in-engine NUMA allocator prototype was real but did not beat global interleave.
- AVX1 Q8 prefetch variants and the layer-wise MoE placement prototype did not beat their controls.

See [`docs/negative-results.md`](docs/negative-results.md).

## Use the methodology on another host

The repository includes a read-only hardware audit, a staged matrix generator, a resumable local candidate runner and a strict agent contract. The intended entry point is [`prompts/optimize-my-host.md`](prompts/optimize-my-host.md).

```bash
./scripts/audit-host.sh
/path/to/llama-server --help > llama-help.txt 2>&1
python3 benchmarks/tools/generate_matrix.py \
  --audit results/latest/host-audit.json \
  --llama-help llama-help.txt \
  --output matrix.json
```

Review the matrix before running it. The workflow launches candidates on a loopback port, records effective arguments and output hashes, captures page placement, restores kernel settings after every arm, and treats OOM or unsupported candidates as local failures. It does not stop or replace an existing production service automatically.

Detailed instructions: [`docs/reproduction.md`](docs/reproduction.md). Exact runtime controls and placement verification: [`docs/flags-and-memory-policy.md`](docs/flags-and-memory-policy.md).

## Evidence and source boundary

The exact result summary, selected candidate, agentic fixture and correctness hashes are committed under [`evidence/v8/`](evidence/v8/). The experimental V8 patch is preserved under [`experiments/`](experiments/) because it is part of the audit trail, not because it won.

The validated binary recorded a local research identity `39b0456b4addaa2058566ed6c993dcd71ed024f1`. That identity is provenance, not a public GitHub ref. The research handoff also records public upstream base `fb92d8f1873c96ec63f9c59721d58a55bf46d441` and expected reconstructed tree `69250916f0566620e4034fff3c9b5b89fd35bfc8`. This release does not claim a bit-identical public rebuild because the complete ordered patch series was not present in the final public handoff. See [`docs/source-provenance.md`](docs/source-provenance.md).

## Scope and limitations

This is a single-host systems study. It measures cold prompt-prefill, selected cached turns and a narrow deterministic output fixture. It is not a model-quality evaluation, a multi-user throughput result, a wall-power/TCO study or a comparison against modern AI appliances. No complete long-context result is included in this release.

## Repository map

```text
data/                       normalized V1–V8 measurements
evidence/v8/                final machine-readable V8 evidence
experiments/                non-winning research prototype patch
benchmarks/prompts/         fixed corpus and SHA-256 hashes
benchmarks/tools/           matrix generation and local candidate runner
scripts/                    read-only host audit and verification
prompts/                    agent-oriented optimization entry point
docs/article.md             publication-style technical article
docs/results.md             complete reported tables and stage interpretation
CLAIM_LEDGER.md              claim-to-evidence map
docs/evidence-audit.md        resolution of stage and source discrepancies
```

Run `make verify` to validate JSON, prompt hashes, derived ratios, shell syntax, Python syntax and the public-claim ledger.
