# Phase 12 — Embedded Timing Analysis

## Outcome

Phase 12 is complete. After the benchmark upgrade, the corrected full-validation firmware was flashed to COM11 and produced 30 timing batches of 2,000 predictions each. Mean batch-average model-kernel time was 50.4271 µs, and all 933 prediction and decision parity checks passed. Both the raw JSONL capture and its derived timing summary are retained.

This remains kernel timing rather than sensing-to-cloud latency or energy per inference.

## Historical timing design

- Device: ESP8266EX NodeMCU 1.0
- Recorded runs: 3
- Predictions per run: 16,000
- Total timed predictions: 48,000
- Retained level: one average per run, not individual inference timings
- Timed section: model arithmetic kernel
- Not included: sensing, feature acquisition, lag-buffer updates, serial formatting, HTTP transmission, or end-to-end alert delivery

## Descriptive result

| Statistic | Time per prediction |
|---|---:|
| Run 1 mean | 50.840 µs |
| Run 2 mean | 50.730 µs |
| Run 3 mean | 50.683 µs |
| Mean of run means | 50.751 µs |
| Sample standard deviation of run means | 0.0806 µs |
| Minimum–maximum | 50.683–50.840 µs |
| Coefficient of variation | 0.159% |
| Implied arithmetic throughput | 19,704 predictions/s |

A two-sided Student-t interval computed from the three run means is 50.551–50.951 µs. This is included only as a descriptive calculation: `n=3` is too small to establish a reliable latency distribution, and independence and stationarity are unverified.

## Rerun with 30 physical batches

The 2026-09-03 rerun retained all 30 batch averages rather than one aggregate per boot.

| Statistic | Batch-average time per prediction |
|---|---:|
| Batches | 30 |
| Predictions per batch | 2,000 |
| Total timed predictions | 60,000 |
| Mean | 50.4271 µs |
| Sample standard deviation | 0.0724 µs |
| Median | 50.4028 µs |
| Minimum / maximum | 50.3615 / 50.7000 µs |
| p5 / p95 | 50.3646 / 50.5394 µs |
| Q1 / Q3 | 50.3900 / 50.4380 µs |
| Interquartile range | 0.0480 µs |

These percentiles describe batch averages, not the latency of individual predictions. The raw capture SHA-256 is `E13D469866C635EC58C1BFD515DC4595EF8D4559AFB900D040449F133D4A80A8`.

## Timing-component separation

| Component | Current evidence |
|---|---:|
| Pure model inference | 50.4271 µs/prediction (mean batch average) |
| Full validation loop | 60,122 µs for 933 vectors |
| Full validation loop per vector | 64.4394 µs/vector |
| Estimated loop overhead beyond model call | 14.0123 µs/vector |
| Estimated overhead share of validation loop | 21.74% |
| Feature acquisition and lag-history update | Not measured |
| Sensor conversion | Not implemented |
| Residual-decision-only timing | Not separately measured |
| HTTP request latency | Not measured |
| End-to-end sensing-to-alert latency | Not measured |

The 13.709 µs value is a subtraction of two aggregates. It includes flash-resident vector loading, error accumulation, threshold comparison, and branching; it is not a direct timing measurement of any one step.

## Benchmark upgrade implemented

The firmware self-test now performs 30 timing batches with 2,000 predictions per batch. Each batch emits one JSON record containing:

```json
{"tinyml_benchmark_batch":0,"inferences":2000,"elapsed_us":101004,"average_inference_us":50.501999}
```

The record above is the first observed batch from the retained physical capture.

`tools/capture_esp8266_serial.ps1` now supports a finite capture duration, defaulting to 90 seconds. `tools/parse_phase12_timing_capture.py` requires at least 30 batches and calculates mean, sample standard deviation, median, interquartile range, p5, p95, minimum, and maximum.

The benchmark-ready code compiles with these resources:

| Build | RAM | IRAM | Flash code |
|---|---:|---:|---:|
| Normal | 29,516 / 80,192 B (36%) | 60,343 / 65,536 B (92%) | 257,796 / 1,048,576 B (24%) |
| Full validation | 29,852 / 80,192 B (37%) | 60,343 / 65,536 B (92%) | 298,132 / 1,048,576 B (28%) |

## Completed capture procedure

1. The CH340 device was confirmed on COM11.
2. The benchmark-ready full-validation firmware compiled and uploaded successfully; flash verification passed.
3. A 90-second serial capture retained all 30 batches, the 933-vector validation summary, and telemetry.
4. The capture was parsed into normalized HIL and timing-distribution JSON records.
5. A Wi‑Fi-disabled matched-condition comparison remains optional future work and is not part of the current result.

```powershell
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Upload -Port COM11
powershell -ExecutionPolicy Bypass -File tools/capture_esp8266_serial.ps1 -Port COM11 -DurationSeconds 90
python tools/parse_phase12_timing_capture.py data/esp8266/esp8266_serial_<timestamp>.jsonl
```

Only one process can own COM11. Arduino Serial Monitor must be closed before upload or capture.

## Paper-ready wording now supported

> On a physical ESP8266EX, 30 batches of 2,000 predictions produced a mean batch-average model-kernel time of 50.4271 µs (median 50.4028 µs; p5–p95 50.3646–50.5394 µs). These are distributions of batch averages, not individual-inference latencies. The measurement excludes sensing, feature preparation, communications, and end-to-end alert delivery.

## Claims not supported

- A universal ESP8266 inference latency.
- A p95 or worst-case individual-inference latency; the reported p95 is for batch averages.
- End-to-end real-time system response.
- Network latency based only on HTTP status 200.
- Energy consumption inferred from execution time.
- Statistical confidence based on 48,000 predictions treated as independent observations.

## Reproduction commands

```powershell
python tools/run_phase12_timing_analysis.py
python -m py_compile tools/parse_phase12_timing_capture.py
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Build
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Build -FullValidation
```

## Phase decision

The three-run historical timing is retained for traceability, while the 30-batch physical rerun is the canonical timing result. Phase 13 quantifies model parameters, arithmetic operations, static storage, whole-firmware memory, and resource headroom.
