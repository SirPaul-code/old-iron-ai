# Results: V1–V8

## Reading the numbers

The main metric is cold prompt-prefill throughput. It measures how quickly the model processes a complete uncached input before generation. Decode is reported separately. The first informal eight-minute `OK` smoke test is not compared numerically with the controlled corpus because it included startup and agent-harness overhead.

## Milestones

| Stage | Configuration or question | Result | Interpretation |
|---|---|---:|---|
| V2 | `MLOCK_ONFAULT` | 6.19 and 28.19 tok/s | Deferred faults were unstable and moved work into the request path. |
| V3 | preferred node 1 | median 31.30 tok/s | Remote/less favourable page placement. |
| V3 | preferred node 0 | median 48.74 tok/s | 55.7% faster than node 1 under this load path. |
| V3 | interleave | 32.04–48.25 tok/s | Unstable before the loading path was corrected. |
| V4 | stable mmap characterization | approximately 38.63 tok/s | Affinity and balancing were not the primary ceiling. |
| V5 | mmap, threads 8 / batch threads 32 | 38.770 tok/s | Stable controlled thread policy. |
| V5 | mmap, threads 16 / batch threads 32 | 24.865 tok/s | More workers regressed performance. |
| V5 | no-mmap screen | 101.044 tok/s | First large indication that load path dominated. |
| V5 | no-mmap validation | 94.201 tok/s | Repeated validation of the direction. |
| V6 | paired mmap | median 38.721 tok/s | Controlled causal baseline. |
| V6 | paired no-mmap | median 93.134 tok/s | Approximately 2.405x over paired mmap. |
| V7 | no-mmap + interleave + 8/32 | median 104.415 tok/s | Validated pre-final host pipeline. |
| V8 | ubatch 1024 screen | 174.483 tok/s | Decisive runtime-geometry screen. |
| V8 | final validation | median 176.093 tok/s | Six samples, two cold loads, CV 0.69%. |

## V3: physical page placement

| Policy | Sample | Node 0 | Node 1 | Prompt tok/s | Prompt seconds |
|---|---|---:|---:|---:|---:|
| preferred:0 | A | 100.0% | 0.0% | 48.4947 | 179.10 |
| preferred:0 | B | 100.0% | 0.0% | 48.9855 | 177.86 |
| preferred:1 | A | 3.3% | 96.7% | 31.2129 | 278.17 |
| preferred:1 | B | 3.3% | 96.7% | 31.3911 | 277.20 |
| interleave:0,1 | A | 50.0% | 50.0% | 48.2455 | 180.04 |
| interleave:0,1 | B | 50.0% | 50.0% | 32.0423 | 271.62 |

The node-0 versus node-1 result established that page placement was causal. The unstable interleave result established that policy alone was not sufficient under the original mmap path.

## V4–V5: balancing, affinity and workers

Disabling automatic NUMA balancing reduced uncontrolled migration but did not create the final throughput increase. Process-wide socket affinity did not reliably help. The strongest thread comparison under the same stage was:

| Threads | Batch threads | Median prompt tok/s |
|---:|---:|---:|
| 8 | 32 | 38.770 |
| 8 | 16 | 38.523 |
| 16 | 16 | 38.113 |
| 16 | 32 | 24.865 |

The result demonstrates why logical CPU count should not be copied directly into every worker pool on an old dual-socket machine.

## V6: paired loading-path programme

Six samples across two cold process loads were collected for each principal mode.

| Mode | Median prompt tok/s | Typical cold load | Relative throughput |
|---|---:|---:|---:|
| mmap | 38.721 | approximately 1,386 s | 1.000x |
| no-mmap | 93.134 | approximately 475 s | 2.405x |

Controls:

- A loader-policy mmap arm remained near 25.16 tok/s.
- A no-mmap/no-repack arm remained near 92.92 tok/s.
- A one-load no-mmap/THP-never arm reached approximately 102.26 tok/s, but later evidence did not establish THP as the final causal winner.

The full samples are in `data/v6-load-path.csv`.

## V7: hardware mechanism evidence

The validated V7 median was 104.41462680727065 tok/s over six samples and two cold loads.

| Metric | mmap baseline | V7 profile |
|---|---:|---:|
| GPU utilization | 38.49% | 97.45% |
| CPU IPC | 0.446 | 1.852 |
| IMC read bandwidth | 5.690 GiB/s | 7.547 GiB/s |
| Cache-miss percentage | 21.10% | 21.74% |

Memory triad measurements:

| Placement | GiB/s |
|---|---:|
| Node 0 local | 19.515 |
| Node 1 local | 19.685 |
| Concurrent aggregate | 39.185 |
| Remote paths | approximately 10–11 |

The near-additive concurrent result supports using both memory controllers after correcting the loading path.

## V8: selection and validation

Runtime screen:

| Arm | Prompt tok/s |
|---|---:|
| runtime-ub1024 | 174.483 |
| runtime-b4096-ub512 | 102.466 |
| runtime-v7 | 102.286 |
| runtime-cpu-moe46 | 100.803 |
| runtime-ub256 | 60.432 |

The explicit allocator, AVX1 prefetch and alternative MoE placement research branches did not beat their controls.

Final candidate:

```text
numactl --interleave=0,1
--numa distribute
--load-mode none
--batch-size 2048
--ubatch-size 1024
--threads 8
--threads-batch 32
--n-cpu-moe 45
--gpu-layers auto
--parallel 1
```

Final validation:

| Statistic | Value |
|---|---:|
| Samples | 6 |
| Independent cold loads | 2 |
| Minimum | 173.411 tok/s |
| Median | 176.093 tok/s |
| Mean | 175.675 tok/s |
| Maximum | 176.922 tok/s |
| CV | 0.69% |
| Gain versus V7 | 1.686x |
| Gain versus paired mmap baseline | approximately 4.55x |

For an approximately 8,686-token input, the isolated prefill stage is approximately 224.3 seconds at the paired mmap baseline and 49.3 seconds at the V8 median.

## Agentic fixture

The narrow three-turn fixture generated 32 tokens per turn and reused the prefix on the short follow-ups.

| Profile | First-turn wall time | Cached follow-ups | Recorded decode |
|---|---:|---:|---:|
| V7 baseline | 87.949 s | approximately 2.7 s | approximately 15–16 tok/s |
| V8 candidate | 52.938 s | approximately 2.7 s | approximately 15–16 tok/s |

This fixture shows a practical first-turn improvement but does not make the cold-prefill headline an end-to-end agent speed claim.

## Correctness

The final cold-load validation used deterministic one-token outputs. Prompt A/B/C output hashes were identical across both final process loads. This is a narrow regression check, not a general quality evaluation.
