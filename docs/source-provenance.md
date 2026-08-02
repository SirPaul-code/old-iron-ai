# Source provenance

The validated V8 binary recorded local research identity:

```text
39b0456b4addaa2058566ed6c993dcd71ed024f1
```

The research handoff also recorded public upstream base:

```text
fb92d8f1873c96ec63f9c59721d58a55bf46d441
```

and expected reconstructed tree:

```text
69250916f0566620e4034fff3c9b5b89fd35bfc8
```

The complete ordered patch sequence needed to prove a bit-identical rebuild was not present in the final public handoff. Therefore this repository preserves the combined experimental patch and result evidence but does **not** claim that applying that single patch to the public base reproduces the exact validated binary.

This boundary does not change the reported runtime measurements. It limits the source-reconstruction claim. The selected V8 result also did not depend on the experimental allocator, AVX1 or MoE branches beating their controls.
