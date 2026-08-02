# Engine V8 adaptive master report

Status: **complete**

Selected candidate: V3-derived binary, global interleave wrapper, inherited explicit CPU-buffer policy, batch/micro-batch 2048/1024, 45 CPU-resident MoE layers, 8/32 workers and no-mmap loading.

Final validation: median **176.092507 tok/s**, range **173.411371–176.921991**, CV **0.685%**, six samples across two independent cold process loads, **1.686474x** over the V7 median.

The explicit NUMA buffer, AVX1 and MoE placement experiments were screened but did not become the selected winner.
