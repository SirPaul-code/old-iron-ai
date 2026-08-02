# Evidence audit and discrepancy resolution

This release uses the final V8 machine-readable summary as the highest-priority source for V8, followed by paired V6 data and validated V7 summaries for the earlier causal chain. Historical narrative is used only where it is not superseded by later evidence.

## Eight-minute `OK` versus controlled timings

The approximately eight-minute `OK` was an uncontrolled end-to-end smoke test. It combined process startup, model loading, prompt handling, agent-harness overhead and generation. It is retained only as project history and is not compared numerically with 38.721 or 176.093 tok/s.

## Why several no-mmap values appear

- **101.044 tok/s**: two-sample V5 discovery screen.
- **94.201 tok/s**: separate three-sample V5 validation.
- **93.134 tok/s**: combined median from paired V6 A/B cold loads, used for the causal mmap/no-mmap comparison.
- **104.415 tok/s**: V7 final baseline after policy screening and independent-load validation.

These belong to different stages and validation boundaries.

## Why V3 selected node 0 but V7 selected interleave

V3 evaluated explicit placement under the eager-lock/mmap-oriented path. Interleave was unstable there. V7 evaluated process policies after no-mmap allocation, automatic-balancing control and additional characterization. Under the corrected path, interleave allowed both memory controllers to contribute. A NUMA policy is not independent of the allocator and buffers it governs.

## 224 to 49 seconds versus 87.949 to 52.938 seconds

The 224 and 49 second values are derived from isolated fixed-prompt prefill medians. The 87.949 and 52.938 second values are measured wall times from a separate V7/V8 agentic fixture using a faster V7 baseline, request overhead and 32 generated tokens. They are not the same experiment.

## V8 source work versus selected winner

V8 screened explicit NUMA CPU buffer types, AVX1 Q8 prefetch variants and layer-wise MoE placement. None displaced its control. The selected result retained the V3-derived binary and global interleave; the large V8 gain came from runtime geometry, especially micro-batch 1024. The experimental patch is preserved for audit but is not presented as the cause of the headline number.

## Source identity

The validated binary recorded local research identity `39b0456b4addaa2058566ed6c993dcd71ed024f1`. The public base recorded by the handoff is `fb92d8f1873c96ec63f9c59721d58a55bf46d441`, and the expected reconstructed tree is `69250916f0566620e4034fff3c9b5b89fd35bfc8`. Because the complete ordered reconstruction series is absent, bit-identical public source reconstruction is not claimed.
