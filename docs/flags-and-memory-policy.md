# Flags and deterministic memory policy

## Final V8 benchmark shape

```bash
numactl --interleave=0,1 /path/to/llama-server \
  --model /path/to/model.gguf \
  --alias local-model \
  --ctx-size 32768 \
  --n-predict 1 \
  --batch-size 2048 \
  --ubatch-size 1024 \
  --threads 8 \
  --threads-batch 32 \
  --threads-http 4 \
  --parallel 1 \
  --numa distribute \
  --jinja --perf --metrics \
  --n-cpu-moe 45 \
  --gpu-layers auto \
  --flash-attn auto \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --load-mode none \
  --host 127.0.0.1 \
  --port 18080
```

The benchmark request disabled prompt-cache reuse and normally generated one token. Paths, alias and port are illustrative; the performance-relevant values match the selected profile.

## Meaning of the controls

### `--load-mode none`

This selected the no-mmap loading/allocation path in the research build. The paired V6 median rose from 38.721 to 93.134 tok/s and cold process load time fell from roughly 1,386 to 475 seconds.

### `numactl --interleave=0,1`

This applied process-level interleaving across both NUMA nodes. It was selected only after no-mmap. The unstable V3 interleave result used a different loading path and should not be generalized to V7/V8.

### `--numa distribute`

This enabled llama.cpp's internal NUMA-aware distribution mode. It does not replace verification of physical pages and does not guarantee every allocation lands as intended.

### `kernel.numa_balancing=0`

Automatic balancing was disabled during controlled arms so the kernel would not migrate pages while a placement hypothesis was measured. V4 showed that this primarily improved determinism. The original setting was restored after every arm.

### `--threads 8` and `--threads-batch 32`

The decode/general worker pool and batch/prefill pool were tuned separately. `16/32` regressed to 24.865 tok/s while `8/32` reached 38.770 under the same mmap stage.

### `--batch-size 2048` and `--ubatch-size 1024`

The logical batch remained 2048 while the physical micro-batch rose to 1024. This was the decisive V8 control: 1024 reached 174.483 tok/s, compared with 60.432 for 256 and roughly 102.466 for batch 4096 / micro-batch 512.

### `--n-cpu-moe 45` and `--gpu-layers auto`

These settings matched the sparse model to the 10 GiB VRAM constraint. A V8 screen with 46 CPU-resident MoE layers reached 100.803 tok/s and was rejected.

### Q8 KV cache

`--cache-type-k q8_0` and `--cache-type-v q8_0` controlled KV precision in the recorded profile. They matter more as context grows; the cold-prefill benchmark prevented prefix-cache reuse from becoming the measured speedup.

### `--parallel 1`

The reference result used one slot. It is not aggregate multi-user throughput.

## Deterministic placement procedure

```bash
before="$(cat /proc/sys/kernel/numa_balancing)"
sudo sysctl -w kernel.numa_balancing=0

numactl --interleave=0,1 /path/to/llama-server ... &
pid=$!

numastat -p "$pid"
python3 scripts/summarize_numa_maps.py --pid "$pid"

# Run the byte-identical fixture and capture placement again.

sudo sysctl -w kernel.numa_balancing="$before"
```

V3 additionally used explicit preferred-node policies during eager allocation. The final V8 winner did not depend on the later in-engine `CPU_NUMA0`/`CPU_NUMA1` prototype; global process interleave remained selected.

## Required evidence

- Page counts before and after the request.
- RSS and locked-memory state.
- Effective command line and binary identity.
- NUMA-balancing and THP state.
- GPU availability and kernel Xid errors.
- Prompt SHA-256, cache state, raw llama.cpp timings and output hash.

The wrapper states the intended policy. The page counts show what actually happened.
