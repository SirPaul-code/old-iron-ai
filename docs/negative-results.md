# Negative results

Performance research is not reproducible if only winners are published.

## `MLOCK_ONFAULT`

Two early runs produced approximately 6.19 and 28.19 tok/s. Deferred page population moved expensive faults into the critical request path and created unstable performance. The branch was rejected.

## Process-wide socket affinity

Pinning the complete process to one socket did not explain the primary bottleneck. Some affinity combinations reduced throughput because GPU-facing work, CPU-side MoE work and memory traffic did not share the same ideal placement.

## More CPU workers

Under the same V5 mmap stage, `threads=16, threads-batch=32` reached only 24.865 tok/s, compared with 38.770 for `8/32`. More logical workers increased coordination and cross-socket traffic.

## THP as the final explanation

A one-load no-mmap/THP-never probe reached approximately 102.26 tok/s. Later evidence did not establish THP as a stable causal winner, so V7 retained the original THP mode. The observation is preserved but not used as the headline explanation.

## Explicit in-engine NUMA allocator

The V8 prototype introduced explicit CPU buffer classes for the two NUMA nodes. It was a real implementation experiment, but its candidates did not beat global process interleave. The published result does not claim that this patch caused the gain.

## AVX1 Q8 prefetch

Several prefetch variants were screened for the Sandy Bridge AVX1 path. The AVX control remained selected. No custom Q8 kernel is credited with the final result.

## Alternative MoE placement

A layer-wise MoE placement prototype was tested. The control remained selected. Increasing `n-cpu-moe` from 45 to 46 also regressed to approximately 100.803 tok/s in the runtime screen.

## Oversized or undersized micro-batches

- Batch 4096 / micro-batch 512 remained near 102.466 tok/s.
- Micro-batch 256 fell to 60.432 tok/s.
- Micro-batch 1024 reached 174.483 tok/s and was selected for repeated validation.

The result demonstrates why batch parameters cannot be inferred from available RAM alone.
