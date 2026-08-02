# Agent-oriented optimization workflow

The repository is designed so a coding agent can apply the methodology without requiring the operator to understand every NUMA or llama.cpp flag first. The agent remains constrained by an evidence and safety contract.

## Contract

The agent must begin read-only, discover the exact binary and supported flags, save production state without printing secrets, create a rollback before writes, use an isolated candidate port and require explicit approval before deployment.

## Decision sequence

1. Identify the real workload: interactive decode, large cold prefill, long-context generation or multi-user throughput.
2. Audit sockets, local memory, GPU attachment, VRAM, PCIe link and current kernel state.
3. Measure a fixed baseline rather than guessing from specifications.
4. Select only experiments relevant to the detected topology and supported flags.
5. Run staged screens rather than an unbounded Cartesian product.
6. Validate the winner across cold loads and compare correctness hashes.
7. Restore production and report exactly what changed.

## Expected report

The report must contain baseline and winner prefill, decode, load time, context length, cache state, page placement, effective flags, failed arms, correctness evidence, changed files and the exact rollback command. A candidate that improves prefill but materially damages decode or long-context behaviour must not be described as the best agent configuration.

Use [`../prompts/optimize-my-host.md`](../prompts/optimize-my-host.md) as the entry point.
