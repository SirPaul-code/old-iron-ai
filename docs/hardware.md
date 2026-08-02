# Reference hardware and topology

| Component | Reference system |
|---|---|
| Server | HP ProLiant DL380p Gen8 |
| CPUs | 2x Intel Xeon E5-2660 v1, 8 cores / 16 threads each |
| Logical CPUs | 32 |
| NUMA nodes | 2 |
| Node 0 memory | 96,619 MiB reported |
| Node 1 memory | 80,633 MiB reported |
| Usable memory | approximately 173 GiB |
| NUMA distance | local 10, remote 20 |
| GPU | NVIDIA GeForce RTX 3080, 10,240 MiB |
| GPU link class | PCIe 3.0 x16 |
| OS | Ubuntu 24.04 LTS, Linux 6.8 family |

The RTX 3080 was installed externally through a riser and powered by a separate PSU because it did not fit normally in the chassis. This physical arrangement motivated GPU and kernel-error gates after an early loose power-connector incident produced an Xid 79 / fallen-off-bus state.

No complete wall-power measurement was collected. GPU power observed during one profile is not sufficient for a system-level energy or ecological comparison because the server also includes two CPUs, many DIMMs, disks, fans and a separate GPU PSU.
