# Giving Old Iron a Second Life: Topology-Aware LLM Inference on a Dual-Socket Sandy Bridge Server

## Abstract

This report describes the characterization and optimization of an approximately 85 GiB Qwen3-Coder-Next Q8_0 GGUF model on a 2012 HP ProLiant DL380p Gen8 equipped with two Intel Xeon E5-2660 processors, 173 GiB of DDR3 memory and one NVIDIA RTX 3080 with 10 GiB VRAM. Because the model was much larger than GPU memory, ordinary host RAM and the two-socket NUMA topology were directly involved in inference.

The study separated model loading, cold prompt-prefill, cached turns and generated-token throughput. A controlled mmap-oriented baseline processed the fixed prompt workload at 38.721 tokens per second. The final V8 candidate reached a median of 176.093 tokens per second over six samples and two independent cold process loads, a 4.55x increase in cold prompt-prefill throughput. In the recorded agentic fixture, generated-token throughput remained approximately 15–16 tokens per second and short cached follow-up turns remained around 2.7 seconds.

The largest validated steps were changing the model-loading path from mmap to no-mmap, using both NUMA memory controllers with a stable process policy, avoiding an unfavorable CPU-worker geometry and increasing the physical micro-batch from 512 to 1024 after the host path had been corrected. Experimental in-engine NUMA allocation, AVX1 prefetch and alternative MoE placement branches did not beat their controls.

V8 should therefore be understood as a practical system-optimization result rather than a prefill-only product. Cold prefill provides the cleanest repeated headline measurement, but the optimized host was already useful for unattended coding, research and authorized security work. Later, longer OpenCode sessions exposed a new class of bottlenecks involving context growth, KV-cache behaviour and agent orchestration. Those questions form the V9 research direction and are not published here as code or validated results.

## 1. Motivation

The practical objective was to run coding, technical research and authorized security tasks locally for hours without depending on cloud session limits or variable usage cost. A memory-rich server already existed, but it was old, loud and built around a dual-socket Sandy Bridge topology that modern inference defaults were not designed around.

The first crude end-to-end smoke test took roughly eight minutes to return a one-line `OK`. It proved only that the model server and agent harness could communicate. It did not separate model startup, prompt ingestion, runtime overhead and output generation, so it is not used as a benchmark baseline.

A repeatable benchmark programme was built around `llama.cpp` to determine whether the old host could become practically useful and which parts of the system were responsible for the delay. The objective was broader than maximizing one number: model loading, fresh-context processing, cached interaction and generation all needed to be measured separately so that an improvement in one phase would not be misrepresented as an improvement in every phase.

## 2. Reference system

The server contained two Xeon E5-2660 v1 processors. Each socket provided eight physical cores and its own local DDR3 channels. Linux exposed two NUMA nodes with a local distance of 10 and a remote distance of 20. Approximately 96.6 GiB was attached to node 0 and 80.6 GiB to node 1.

The RTX 3080 provided only 10 GiB VRAM, so the majority of the 85 GiB quantized model remained in system memory. The GPU was attached through a riser and powered by a separate PSU because it did not fit conventionally in the chassis.

This arrangement made the host data path part of inference in practice. The GPU could only execute work as quickly as model data and intermediate tensors could be supplied by the CPUs and memory subsystem.

## 3. Measurement boundaries

The final public handoff preserved three prompt SHA-256 fingerprints and the reported 8,663-token input, but not the original prompt text. The repository therefore publishes a fingerprints-only provenance manifest instead of reconstructing or fabricating replacement prompts.

Most characterization requests generated one token, making request time predominantly prompt-prefill time. Prefix-cache reuse was disabled for cold-prefill measurements.

The following quantities were kept distinct:

- **Cold process load:** a newly started `llama.cpp` server process.
- **Cold prompt-prefill:** processing the complete input without prefix-cache reuse.
- **Cached turn:** a follow-up request that can reuse a previously processed prefix.
- **Decode:** generation of output tokens after prefill.
- **Agentic fixture:** a narrow three-turn request shape that includes request overhead, prefill, cache reuse and 32 generated tokens.

Discovery screens could use one or two samples. A final claim required independent cold process loads, deterministic correctness evidence and repeated measurements.

NUMA policy was verified with `/proc/<pid>/numa_maps`, `numastat -p`, `/proc/<pid>/status` and the effective process command line. A wrapper such as `numactl` was treated as an intended policy rather than proof of physical page placement.

## 4. Experimental progression

### 4.1 Deferred locking was a negative result

An early `MLOCK_ONFAULT` approach produced approximately 6.19 and 28.19 prompt tokens per second. Deferring faults moved expensive page population into the measured request path and created highly unstable behaviour. The branch was rejected.

### 4.2 NUMA placement mattered

V3 used eager allocation and explicit placement to compare the two memory nodes. Preferred node 0 produced 48.495 and 48.986 tok/s. Preferred node 1 produced 31.213 and 31.391 tok/s. The median difference was approximately 55.7%.

This was an important causal result: physical placement alone could change prompt throughput materially. It also contradicted the simple assumption that the socket physically closer to the GPU must be the best location. CPU-side MoE work and aggregate host-memory behaviour mattered more than PCIe proximity alone.

Interleaving was unstable at this stage, ranging from 32.042 to 48.246 tok/s. That did not invalidate interleaving as a later strategy; it showed that memory policy could not be evaluated independently of the model-loading path.

### 4.3 Automatic balancing was primarily a determinism control

V4 compared automatic NUMA balancing and several CPU-affinity arrangements. Disabling balancing reduced pathological placement changes but did not create the final speedup by itself. It was retained during controlled experiments so the kernel would not migrate pages while a placement hypothesis was being measured, and the original value was restored after each arm.

CPU affinity also failed to explain the primary ceiling. Some node-pinned arrangements were slower than allowing the process to use the complete host.

### 4.4 More workers could be slower

The V5 thread matrix showed that worker geometry needed to be treated separately for prompt processing and decode. Under the same mmap stage, `threads=8, threads-batch=32` reached 38.770 tok/s, while `threads=16, threads-batch=32` fell to 24.865 tok/s.

On this host, adding workers could increase synchronization, cache pressure and traffic over the inter-socket QPI link. Logical CPU count was therefore not a suitable default for every worker pool.

### 4.5 The loading path was the first major breakthrough

A V5 no-mmap screen reached 101.044 tok/s and was followed by a paired V6 programme. Six samples over two cold loads were collected for each mode.

The mmap median was 38.721 tok/s. The no-mmap median was 93.134 tok/s, approximately 2.405x faster. Cold model load time also fell from roughly 1,386 seconds to roughly 475 seconds.

The page-placement evidence was important: mmap could show nearly ideal node-0 placement and still remain slow. Therefore the result could not be attributed merely to one mode putting pages on the correct socket. The loading and allocation path affected how useful work overlapped across CPU, memory and GPU.

A loader-policy mmap arm fell to roughly 25.16 tok/s. A no-repack no-mmap arm remained near 92.92 tok/s. These controls strengthened the conclusion that the no-mmap path, rather than a superficial command-line difference, was responsible for the first large improvement.

### 4.6 Both memory controllers became useful

V7 combined the no-mmap path with process-level interleaving over both NUMA nodes, automatic balancing disabled and the stable 8/32 worker policy. The validated median was 104.415 tok/s over six samples and two independent cold loads.

Supporting hardware measurements showed:

- GPU utilization: 38.49% on the mmap baseline and 97.45% on the V7 profile.
- CPU IPC: 0.446 and 1.852 respectively.
- Local memory triad: 19.515 GiB/s on node 0 and 19.685 GiB/s on node 1.
- Concurrent aggregate triad: 39.185 GiB/s.

The near-additive concurrent bandwidth demonstrated that the two old memory controllers still provided useful aggregate capacity. The corrected pipeline was able to keep the GPU occupied instead of leaving it waiting for the host.

### 4.7 V8 exposed micro-batch geometry as another major control

V8 screened explicit allocator, AVX1 prefetch, MoE placement and runtime configurations. The custom allocator, AVX and MoE variants did not beat their controls and are preserved as negative research results.

The runtime screen produced the decisive result:

- V7-shaped runtime: 102.286 tok/s.
- Batch 4096 / micro-batch 512: 102.466 tok/s.
- CPU MoE 46: 100.803 tok/s.
- Micro-batch 256: 60.432 tok/s.
- Micro-batch 1024: 174.483 tok/s.

The final selected candidate retained batch 2048 and used micro-batch 1024, threads 8, batch threads 32, CPU MoE 45, automatic GPU-layer selection, no-mmap loading and global interleave.

Final validation produced six samples across two independent cold process loads:

- Minimum: 173.411 tok/s.
- Median: 176.093 tok/s.
- Maximum: 176.922 tok/s.
- Coefficient of variation: 0.69%.

The gain over the V7 median was 1.686x. Relative to the paired controlled mmap baseline, the final cold-prefill result was approximately 4.55x higher.

## 5. Practical interpretation

For the fixed input of approximately 8.7k tokens, the isolated cold-prefill stage corresponds to roughly 224.3 seconds at 38.721 tok/s and 49.3 seconds at 176.093 tok/s.

The separate agentic fixture provides a more complete view of the resulting runtime behaviour. The first turn fell from 87.949 seconds on the V7 baseline to 52.938 seconds on V8. Short cached follow-up turns remained around 2.7 seconds, and recorded generation was approximately 15–16 tok/s.

The practical outcome was therefore not limited to a faster synthetic prefill chart. The optimized V8 profile made the server useful for unattended local coding, research and authorized security tasks. Fresh sessions became substantially less expensive, cached interaction remained responsive enough for the intended workflow, and generation speed was already usable for overnight work.

## 6. Why the result is plausible

The headline result shows how poorly the initial software path used the available machine and how much performance could be recovered without replacing the model, GPU or server.

The causal chain supported by the experiments is:

1. The oversized model made host DDR3 part of the hot path.
2. The two-socket machine had non-uniform memory access, and V3 proved that page location changed performance.
3. The mmap path remained slow even with favourable placement, while paired no-mmap was approximately 2.4x faster.
4. The V7 policy made both memory controllers productive and raised GPU utilization substantially.
5. Once that path was corrected, V8 showed that a larger micro-batch could expose much more prompt-processing throughput.
6. The resulting profile retained usable generated-token speed and cached-turn behaviour for the intended local-agent workload.

No single vague “optimization” produced the result. It was the combination of controlled measurement, corrected loading, topology-aware placement, appropriate workers and runtime geometry.

## 7. Negative findings and scientific value

The project preserves failed experiments because they narrow the explanation:

- Deferred fault locking was unstable and slow.
- Socket affinity did not reliably improve the workload.
- More worker threads could regress performance.
- A promising one-load `THP=never` observation did not become the final causal explanation.
- Explicit in-engine NUMA buffer types did not beat global process interleave.
- AVX1 Q8 prefetch variants did not beat the control.
- Alternative MoE placement did not beat the control.

A credible performance report must make it possible to distinguish the winning configuration from abandoned hypotheses.

## 8. Applying the methodology on another host

The exact V8 values should not be copied blindly. A different DIMM population, CPU generation, model quantization, GPU, `llama.cpp` build or context target can change the winner.

The transferable result is the method:

1. Capture the hardware topology and current production state read-only.
2. Record the exact `llama.cpp` binary identity and supported flags.
3. Select the workload objective.
4. Measure loading, cold prompt-prefill, cached turns and generation separately.
5. Generate a staged matrix from safe hypotheses.
6. Run candidates on an isolated loopback port.
7. Record effective arguments, physical page placement, raw timing fields and correctness hashes.
8. Repeat the winner across independent cold loads.
9. Present evidence and rollback instructions before deployment.

The runner treats OOM, unsupported flags and startup failures as candidate-local results and restores saved kernel settings after each arm.

The broader proof of concept is that a machine does not need to match this HP server for the investigation to be useful. A single-socket workstation, old EPYC server, mixed-GPU host or memory-constrained desktop may expose different bottlenecks, but each can benefit from measuring its actual topology and workload instead of assuming that defaults are optimal.

## 9. V9 research direction

V8 completed the first phase: it produced a stable, practical local inference profile and an evidence-backed explanation of the largest gains.

The next phase began when longer OpenCode sessions and more complex agentic workflows accumulated much larger active contexts. At that point the optimization target expanded beyond initial model loading and fresh-context ingestion. Context growth, KV-cache placement and compression, CPU/GPU MoE division, long-context generation and agent-runtime orchestration became first-class variables.

That work is referred to as V9. It is intentionally represented here only as a research direction. No V9 implementation, benchmark code or unvalidated result is included in the V8 publication.

## 10. Limitations

This is a single-host study. It is not a model-quality evaluation, a concurrent serving benchmark, a power/TCO comparison or a claim against modern AI hardware. The deterministic output fixture is deliberately narrow. The final runtime screens used one sample per candidate before repeated validation of the selected winner.

The 176.093 tok/s headline is a cold prompt-prefill result. It is the strongest repeated and controlled measurement, not a replacement for the separately reported generation and agentic-fixture numbers.

The original prompt text and complete ordered source-patch series were not present in the public handoff. The repository therefore publishes prompt fingerprints, normalized evidence and source provenance without claiming a bit-identical public reconstruction.

No complete V9 long-context study is included in this release.

## 11. Conclusion

Old hardware can lose commercial value before it loses practical value. The DL380p Gen8 remained limited by power use, noise, CPU generation and GPU memory, but it also retained 173 GiB of RAM, two memory controllers and enough aggregate capacity to run a model that could not fit on the GPU.

By measuring the real topology instead of treating the host as a flat pool of RAM and threads, cold prompt-prefill increased from 38.721 to 176.093 tok/s. More importantly, the resulting V8 profile was usable as a complete local inference system for the intended workload: generated-token speed remained around 15–16 tok/s, cached follow-up turns remained short, and unattended coding and research tasks became practical.

The broader lesson is not tied to this exact server or these exact flags. Old or unconventional hardware may still have substantial useful capacity hidden behind unsuitable defaults. The correct response is to measure the machine that actually exists, identify the current bottleneck and adapt the inference path to it.

V8 records that completed result. V9 continues the same process at the next layer, where long context and agent orchestration become the bottleneck rather than basic host-side throughput.
