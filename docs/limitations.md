# Limitations and non-claims

- The results apply to one server, one DIMM population, one GPU, one model quantization and one llama.cpp research snapshot.
- The headline 176.093 tok/s is cold prompt-prefill. It is not generated-token speed and not complete autonomous-agent throughput.
- The reference service used one slot. This is not a concurrent multi-user result.
- The output-hash fixture checks narrow deterministic consistency, not model quality.
- The agentic fixture generated a short repeated output; it is not a coding benchmark.
- V7 telemetry supports a host-pipeline interpretation but does not prove every low-level mechanism independently.
- V8 runtime screens used one sample per arm before final validation. Final six-sample statistics apply only to the selected winner.
- No complete long-context study is included. Performance at tens or hundreds of thousands of context tokens can have different bottlenecks.
- No complete wall-power measurement exists, so this release makes no TCO, carbon or energy-efficiency claim.
- No comparison is made against current Macs, data-center GPUs or integrated AI appliances.
- The experimental patch is preserved for audit but is not claimed to reconstruct the exact binary by itself.
