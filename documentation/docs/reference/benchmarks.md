# Benchmarks

Performance characteristics of FastWorker on common hardware.

## Test Setup

- **Hardware**: Apple M1, 16GB RAM
- **Python**: 3.12
- **OS**: macOS 14
- **Task**: `add(x, y)` returning `x + y` (CPU-trivial)
- **Concurrency**: 1 (single-threaded control plane)

## Throughput

| Workers | Tasks/min | Latency (p50) | Latency (p99) |
|---|---|---|---|
| 1 (control plane only) | ~2,500 | 18ms | 45ms |
| 2 (+1 subworker) | ~4,200 | 22ms | 58ms |
| 4 (+3 subworkers) | ~6,800 | 28ms | 72ms |

## Latency Breakdown

For a single task execution (local, no network):

| Phase | Time |
|---|---|
| Client serialize + send | ~0.5ms |
| Network (localhost TCP) | ~0.2ms |
| Control plane deserialize | ~0.3ms |
| Task execution (add, trivial) | ~0.01ms |
| Result serialize + send | ~0.4ms |
| Client deserialize | ~0.3ms |
| **Total round-trip** | **~2ms** |

With subworkers on the same machine, add ~1-2ms for the additional hop.

## Memory

| Component | Idle | Under load (100 concurrent) |
|---|---|---|
| Control plane | ~25MB | ~40MB |
| Subworker | ~20MB | ~30MB |
| Client | ~10MB | ~15MB |

## Scaling Notes

- Throughput scales linearly with subworkers up to ~8 workers on a single machine
- Beyond 10K tasks/min, socket contention on the control plane becomes the bottleneck
- Network latency dominates for distributed workers (>1ms per hop)
- Result cache memory grows linearly with `--result-cache-size`

For workloads above 10K tasks/min, consider Celery + Redis or a partitioned control plane topology.
