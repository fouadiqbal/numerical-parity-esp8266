# Phase 26: Final Claims Audit

Status: **complete - passed**  
Audit date: 2026-09-03

## Scope

The public README, baseline notebook source, ESP8266 firmware README, and final LaTeX manuscript were checked for unsupported or stale claims. The reproducible audit is `tools/run_phase26_claims_audit.py`; its machine-readable result is `outputs/phase26_claims_audit.json`.

## Corrections completed

- Replaced physical-energy labels with **normalized target units** wherever inverse scaling is unavailable.
- Replaced the obsolete timing summary with the physical 30-batch result: 2,000 predictions per batch, mean 50.427 microseconds.
- Reworded "5,000 smart-meter readings" as "5,000 half-hourly dataset rows" and disclosed the undocumented primary provenance.
- Removed or bounded claims of deployment readiness, real-world anomaly performance, physical kWh accuracy, energy efficiency, security, novelty, and generalization.
- Added a prominent notebook scope note and confirmed that no traceback appears in any code cell.

## Audited disposition

| Claim family | Final disposition |
|---|---|
| Smart-meter terminology | Allowed only as a dataset/project descriptor or inside an explicit limitation |
| Real-time or field validation | Not asserted for the present system |
| Anomaly detection | Reported only as agreement with publisher-supplied algorithmic labels |
| Deployable, secure, low-power, or energy-efficient | Not asserted; required measurements are listed as future work |
| Generalizable | Not asserted beyond the evaluated dataset and splits |
| First or novel | Explicitly disclaimed as a broad contribution |

## Approved claim

> The project demonstrates reproducible numerical and threshold-decision portability for a compact model under complete 933-vector replay on one physical ESP8266, with measured model-kernel timing and whole-firmware resource accounting.

## Unsupported claims that remain prohibited

- calibrated smart-meter sensing or verified physical kWh;
- independently validated real-event anomaly detection;
- live on-device forecasting from a maintained lag buffer;
- end-to-end or network latency inferred from the kernel benchmark;
- measured power or energy per inference;
- secure field deployment;
- cross-dataset or seasonal generalization;
- algorithmic novelty or a worldwide first.

## Validation result

The audit found 35 candidate occurrences. Every occurrence was either an explicit boundary, a contextual descriptor, or ordinary non-priority language. Unsupported claims remaining: **0**. Stale result patterns: **0**. Traceback code cells: **0**.
