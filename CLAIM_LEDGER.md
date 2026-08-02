# Public claim ledger

| Claim | Evidence in this repository | Qualification |
|---|---|---|
| Final median 176.092507 tok/s, range 173.411–176.922, CV 0.69%, six samples / two loads | `evidence/v8/RESULTS_SUMMARY.json`, `evidence/v8/FINAL_ENGINE_CANDIDATE.json` | Cold prompt-prefill only. |
| V8 was 1.686x faster than V7 | `evidence/v8/RESULTS_SUMMARY.json` | Same final V8 programme and fixed corpus. |
| Approx. 4.55x over paired mmap baseline | `data/v6-load-path.csv`, `data/study-summary.json`, `data/v8-summary.json` | Derived from 38.721 vs 176.093. |
| Node0 placement beat node1 by 55.7% | `data/v3-numa-placement.csv` | V3 eager-lock/mmap path; not universal. |
| Paired no-mmap beat mmap by about 2.405x | `data/v6-load-path.csv` | Six samples and two process loads per mode. |
| GPU utilization 38.49% to 97.45% | `data/v7-summary.json` | V7 profile comparison, not final V8 telemetry. |
| Concurrent memory bandwidth 39.185 GiB/s | `data/v7-summary.json` | STREAM-like triad aggregate. |
| V8 gain came mainly from ubatch 1024 | `evidence/v8/RESULTS_SUMMARY.json` runtime screen | Strong controlled screen; exact microarchitectural mechanism remains an interpretation. |
| Custom allocator/AVX/MoE variants did not win | `evidence/v8/RESULTS_SUMMARY.json`, `evidence/v8/FINAL_REPORT.md` content mirrored in `docs/negative-results.md` | Do not credit custom kernels with the headline result. |
| Agentic first turn 87.949 s to 52.938 s | `evidence/v8/AGENTIC_REPORT.json` | Narrow 3-turn fixture with 32 generated tokens. |
| Decode remained around 15–16 tok/s | `evidence/v8/AGENTIC_REPORT.json` | Recorded fixture only. |
| Exact public source rebuild is not claimed | `docs/source-provenance.md`, `experiments/README.md` | Result evidence is preserved; complete ordered patch reconstruction is absent. |
