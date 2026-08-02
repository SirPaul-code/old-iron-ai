# Optimize this host using Old Iron AI

You are operating an evidence-first inference optimization programme on hardware that may already provide a production service. Read `AGENTS.md`, `README.md`, `docs/article.md`, `docs/results.md` and the scripts before making changes.

The user will provide the llama.cpp binary, model path and workload objective. Do not copy the reference DL380p settings blindly.

## Required workflow

1. **Audit read-only.** Run `scripts/audit-host.sh` and record CPU model, sockets, cores, NUMA nodes and distances, memory per node, GPU model/VRAM/PCIe link, kernel, automatic NUMA balancing, THP state, currently running model processes and service health. Do not print secrets.
2. **Establish the objective.** Classify the target as interactive decode, cold repository ingestion, long-context overnight research, or concurrent serving. State which metrics will decide the winner.
3. **Record the exact runtime.** Save the llama.cpp binary hash/build identity and its `--help` output. Use only flags supported by that binary.
4. **Protect production.** Capture the current unit definition, effective command line, health result and kernel settings. Create and test a rollback. Use an unused loopback port for candidates. Never stop or replace production without explicit approval.
5. **Create a staged matrix.** Begin with a baseline. On multi-socket hosts test actual page placement, no-mmap/mmap if supported, conservative worker geometries, and memory policies appropriate to the topology. Test batch and micro-batch only after the loading path is stable. Add KV/cache experiments only when the target workload requires them.
6. **Measure phases separately.** Record cold process load, cold prompt-prefill, cached turns and decode. Preserve input hashes, effective arguments, cache state, raw llama.cpp timings, wall time, output hash and placement evidence.
7. **Fail locally.** OOM, unsupported flags, startup failures, timeouts and invalid output reject the current arm; they do not abort the complete programme unless production safety is affected.
8. **Validate the winner.** Repeat across at least two independent cold process loads. Report minimum, median, mean, maximum, coefficient of variation and correctness evidence. Do not promote a one-sample screen.
9. **Explain causality carefully.** Separate direct measurement, derived values and interpretation. Preserve negative results. Do not attribute a gain to a custom patch when its control won.
10. **Stop before deployment.** Present the proposed command, evidence, expected benefit, limitations and exact rollback. Wait for explicit approval.

## Final report format

```text
Objective:
Reference hardware/runtime:
Baseline:
Candidate matrix:
Rejected arms and reasons:
Validated winner:
  load time:
  cold prefill tok/s:
  decode tok/s:
  cached-turn latency:
  context length:
  samples / cold loads:
  CV:
  correctness:
Why it likely worked:
What remains uncertain:
Files changed:
Proposed production command:
Rollback command:
```

Treat the reference repository as a methodology and evidence source, not a promise that its exact flags are optimal elsewhere.
