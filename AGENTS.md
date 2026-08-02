# Agent contract

This repository may be used on a host that already serves inference. The following rules are binding.

1. Begin with a read-only audit and save the current service, process command line, health endpoint and kernel settings without printing credentials.
2. Determine the exact installed llama.cpp binary identity and supported flags. Never assume the reference host's CLI applies.
3. Ask which workload matters: interactive decode, cold repository ingestion, long-context overnight work or concurrent throughput.
4. Create an isolated loopback candidate port and a tested rollback before the first write.
5. Benchmark model load, cold prefill, cached turns and decode separately.
6. Verify actual NUMA page placement instead of trusting `numactl` alone.
7. Treat OOM, unsupported flags, startup failure and invalid output as candidate-local failures.
8. Restore kernel settings and stop the candidate after every arm, including interruption.
9. Do not call a one-sample screen a validated winner.
10. Do not deploy automatically. Present the evidence and require explicit user approval.
11. Do not read, copy or commit API keys, private target data, model weights or unrelated server files.
12. Preserve negative results and distinguish direct measurement, derived values and interpretation.
