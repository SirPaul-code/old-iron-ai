# Methodology

## Metric definitions

**Cold process load** means a newly started llama.cpp server process. **Cold prompt-prefill** means prompt-cache reuse is disabled for the measured request. **Decode** is the generated-token phase and is reported separately. **Agentic fixture** is a multi-turn request shape with prefix-cache reuse; it is not interchangeable with the one-token cold-prefill benchmark.

The core corpus contains three byte-identical 8.7k-token-class fixtures. `benchmarks/prompts/materialize.py` reconstructs the exact files and verifies their committed SHA-256 values. Most characterization requests generated one token so elapsed time was dominated by prompt evaluation.

## Placement verification

A process wrapper is an intention, not evidence. Controlled stages checked:

- `/proc/<pid>/numa_maps` for per-node page counts and mapping type;
- `numastat -p <pid>` for process-level node distribution;
- `/proc/<pid>/status` for RSS and locked memory;
- placement after readiness and again after the request.

Automatic NUMA balancing, THP enabled mode and THP defrag mode were saved before the arm and restored afterward.

## Cold-load structure

Discovery screens could use one or two samples but could not become a final claim. Causal validation used reversed prompt order and independent process loads. V8 final validation used six samples over two cold process loads. Coefficient of variation was population standard deviation divided by mean.

## Correctness

Prompts A/B/C generated deterministic one-token outputs with identical hashes across both final loads. This is a narrow regression check, not a model-quality test.

## Telemetry

The study combined llama.cpp timing fields with GPU utilization, CPU IPC, IMC traffic, memory bandwidth and physical page placement. Telemetry supports the host-pipeline explanation but is not presented as proof of every microarchitectural mechanism.

## Selection rule

A final candidate had to start successfully, produce the expected output hashes, survive independent cold loads and improve the target workload. OOM, unsupported flags or startup failure invalidated that arm rather than the entire programme. Differences below roughly 3% were not treated as meaningful without additional repetitions.
