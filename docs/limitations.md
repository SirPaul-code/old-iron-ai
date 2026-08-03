# Limitations and non-claims

- The results apply to one server, one DIMM population, one GPU, one model quantization and one `llama.cpp` research snapshot.
- The headline 176.093 tok/s result is cold prompt-prefill. It is the strongest repeated controlled result, not generated-token speed and not a claim that the complete agent became 4.55x faster.
- V8 was nevertheless useful as a complete local inference profile for its intended workload: the recorded agentic fixture retained approximately 15–16 generated tok/s and short cached follow-up turns around 2.7 seconds.
- The reference service used one slot. This is not a concurrent multi-user result.
- The output-hash fixture checks narrow deterministic consistency, not model quality.
- The agentic fixture is deliberately narrow and is not a coding-quality benchmark.
- V7 telemetry supports a host-pipeline interpretation but does not prove every low-level mechanism independently.
- V8 runtime screens used one sample per arm before final validation. Final six-sample statistics apply only to the selected winner.
- The exact V8 flags are not universal defaults. Different CPUs, DIMM populations, GPUs, models, quantizations and context targets can select different winners.
- The original prompt text was not present in the final public handoff. The repository publishes its SHA-256 fingerprints and reported token count rather than fabricating replacement prompts.
- The complete ordered source patch series was not present in the public handoff, so the repository does not claim a bit-identical reconstruction of the research binary.
- No complete V9 study is included. V9 is mentioned only as the next research direction for longer OpenCode sessions, context growth, KV-cache behaviour, MoE placement, generation and agent-runtime interaction.
- No V9 code or unvalidated V9 benchmark result is published in this V8 release.
- No complete wall-power measurement exists, so this release makes no TCO, carbon or energy-efficiency claim.
- No comparison is made against current Macs, data-center GPUs or integrated AI appliances.
