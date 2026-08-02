# Experimental source patch

`v8-numa-avx1-prototype.patch` preserves the combined research changes available in the public handoff, including explicit Linux NUMA CPU buffer types and AVX1 prefetch prototype work.

It is a **non-winning** artifact. The final selected V8 candidate used the V3-derived control binary, global `numactl --interleave=0,1`, inherited explicit CPU-buffer policy and the winning runtime geometry. The patch is not credited with the 176.093 tok/s result and is not presented as a complete bit-identical reconstruction series.
