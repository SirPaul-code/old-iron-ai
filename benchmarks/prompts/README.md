# Benchmark prompt provenance

The V8 research handoff preserved the SHA-256 fingerprints of three prompt artifacts and reported an 8,663-token controlled input. It did not include the original prompt text in the final public release material.

This directory therefore publishes only `manifest.json`. The repository deliberately does not generate replacement prompts, because synthetic text would not reproduce the measured workload and would create a false impression of exact reproducibility.

The published performance values remain auditable against the normalized result tables and V8 evidence files. Re-running the exact corpus requires the original prompt artifacts whose hashes are listed in the manifest. New users can still apply the benchmark methodology to their own fixed corpus, but their results must be reported as a new experiment rather than a reproduction of the original token stream.
