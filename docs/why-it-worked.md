# Why the optimization worked

The final result is best explained as a sequence of bottlenecks rather than one magic flag.

## 1. Host memory was part of inference

The model was approximately 85 GiB while the RTX 3080 had 10 GiB VRAM. Most weights remained in DDR3. Host allocation, bandwidth and placement therefore affected every cold prompt.

## 2. The host was not one uniform pool

Each Xeon had its own local memory. V3 placed the model predominantly on each node in turn and measured 48.74 versus 31.30 tok/s. That 55.7% difference established that physical location was causal.

## 3. Placement was not the whole story

The paired V6 mmap mode remained near 38.721 tok/s even when page distribution looked favourable. No-mmap reached 93.134 tok/s and loaded the model in roughly one third of the time. Therefore the important difference was the loading/allocation path and how work overlapped, not merely which node contained more pages.

## 4. Both memory controllers could contribute

V7 used no-mmap with process-level interleave. Local memory triads measured 19.515 and 19.685 GiB/s; concurrent execution reached 39.185 GiB/s. Recorded GPU utilization increased from 38.49% to 97.45%. The GPU had not become faster; the corrected host path stopped starving it as often.

## 5. Worker count had to match the topology

Using more logical CPUs was not automatically beneficial. The 16/32 worker shape fell to 24.865 tok/s while 8/32 reached 38.770 in the same V5 stage. The extra workers introduced synchronization, cache pressure and cross-socket communication.

## 6. Micro-batch size became important after the host path was fixed

With the corrected V7-like pipeline, micro-batch 512 remained near 102 tok/s. Micro-batch 256 fell to 60.432, while 1024 reached 174.483. The final repeated validation reached 176.093 tok/s.

The large V8 step should therefore be credited to runtime geometry on top of the corrected loading and NUMA pipeline. The explicit allocator, custom AVX1 prefetch and alternative MoE placement prototypes did not win their screens.

## Supported conclusion

The old hardware retained useful aggregate memory capacity, but modern defaults did not automatically exploit its topology for this oversized hybrid CPU/GPU workload. Adapting the software path to the actual machine transformed an impractical cold-prefill path into a useful one without changing the model or GPU.
