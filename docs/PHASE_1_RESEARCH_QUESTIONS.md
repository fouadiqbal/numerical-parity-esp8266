# Phase 1 — Revised Research Questions

Status: **complete; awaiting confirmation before Phase 2**  
Date: 2026-09-03

## Research framing

The paper should be framed as a constrained and reproducible model-transfer study. The physical ESP8266 is used to verify that a compact forecasting computation can be transferred from Python to embedded C++ while retaining numerical behavior. The paper is not framed as a new anomaly-detection algorithm, a calibrated electrical meter, or a field deployment.

## Candidate research questions

### RQ1 — Numerical portability and embedded cost (preferred)

> **To what extent can a lightweight load-forecasting model, developed with leakage-aware chronological evaluation, be transferred from Python to C++ on an ESP8266 while preserving its numerical outputs across a complete future holdout, and what measured latency and memory costs accompany that transfer?**

Why it is defensible:

- It matches the strongest existing evidence: all 933 held-out rows were replayed on a physical ESP8266.
- It makes numerical portability measurable through prediction mismatches, maximum and mean numerical differences, and decision mismatches.
- It makes the embedded cost measurable through inference latency, RAM, flash, and IRAM.
- It does not imply calibrated electrical sensing or field validation.
- It leaves room for stronger chronological validation and statistical experiments without making their uncomputed results part of the current claim.

Evidence already available:

- 933/933 prediction agreement.
- 933/933 anomaly-threshold decision agreement.
- Maximum absolute Python/device difference of 0.000000089 normalized target units; Phase 3 found that physical kWh cannot be recovered from the scaled file.
- Three pure-inference passes with a mean of 50.751 microseconds.
- Recorded RAM, flash, and IRAM utilization for normal and validation firmware.

Evidence still required to answer it rigorously:

- An automated Python-versus-generated-C++ software-reference test before flashing.
- A larger timing sample supporting median, standard deviation, minimum, maximum, and percentile latency.
- Explicit model parameter, operation, and storage counts.
- Stronger chronological forecasting experiments establishing whether the compact deployment model is competitive.

What RQ1 does **not** ask or prove:

- Whether the ESP8266 accurately measures electrical voltage, current, power, or energy.
- Whether the overall sensing-to-cloud system operates in real time.
- Whether the design is energy efficient or low power.
- Whether the supplied anomaly labels represent real physical faults.
- Whether the system is ready for field or utility deployment.

### RQ2 — Forecasting accuracy versus deployability

> **What forecasting-accuracy trade-off results from replacing larger software baselines with a compact standardized linear model suitable for ESP8266 execution under leakage-free temporal evaluation?**

Why it is useful:

- It connects forecasting quality to the engineering reason for using a compact model.
- It permits a fair comparison among persistence, seasonal naive, linear regression, random forest, gradient boosting, and the compact edge model.
- It can show whether complexity is justified rather than assuming that the largest model is best.

Current status:

- The notebook contains one chronological holdout and several baseline results.
- A complete answer requires the seasonal-naive lag-48 baseline, a boosting model, rolling-origin folds, confidence intervals, and paired error analysis.
- Until those experiments are complete, claims about the compact model being “competitive” remain `[RESULT TO BE COMPUTED]`.

What RQ2 does **not** prove:

- Generalization to other households, climates, countries, or seasons.
- Superiority on datasets that were not evaluated.
- Embedded energy efficiency, because device energy was not measured.

### RQ3 — Threshold behavior under uncertain anomaly labels

> **How does residual-threshold selection affect precision, recall, F1 score, and alert frequency against the dataset-supplied anomaly labels, and can the selected decision rule be reproduced consistently on the ESP8266?**

Why it is useful:

- It addresses the deployed detector’s high precision but low recall rather than describing it as strong.
- It separates threshold sensitivity from numerical implementation parity.
- It treats alert count as an operational trade-off.

Current status:

- At the deployed threshold, the held-out confusion matrix is TP 8, FP 0, FN 44, TN 881, with precision 1.000000, recall 0.153846, and F1 0.266667.
- The ESP8266 reproduced all 933 stored software threshold decisions.
- Percentile sensitivity and adaptive/rolling threshold experiments remain `[RESULT TO BE COMPUTED]`.

What RQ3 does **not** prove:

- That the supplied labels are independently verified electrical anomalies.
- That the detector identifies real faults in an operating electrical system.
- That the current threshold is optimal outside this dataset and evaluation interval.

## Selected primary question

**RQ1 is the primary research question.**

RQ2 should become a supporting model-selection question. RQ3 should become a supporting anomaly-analysis question rather than the paper’s central novelty claim.

This hierarchy keeps the research story coherent:

1. Select and evaluate a compact model using leakage-aware temporal methods.
2. Export the model reproducibly from Python to C++.
3. verify software-reference behavior before hardware execution.
4. Replay the complete future holdout on the physical ESP8266.
5. quantify numerical agreement, latency, and resource use.
6. Analyze anomaly-threshold behavior cautiously against supplied labels.

## Why this framing is stronger than the original framing

The broader “smart-meter forecasting and anomaly detection” framing invites claims the current experiments cannot support. It suggests calibrated sensing, a validated anomaly detector, or an operational smart-meter system even though the ESP8266 consumed stored feature vectors and no electrical reference instrument was used.

The preferred question is stronger because:

- **The unit of evidence is explicit.** It concerns an exported computation evaluated over 933 held-out vectors.
- **The comparison is reproducible.** Python, generated C++, and physical-device outputs can be checked directly.
- **The constraints are measurable.** Latency and compiled memory use are reported independently of sensing and communication.
- **The evaluation boundary is honest.** HIL replay is not presented as electrical measurement or field validation.
- **The research gap can be tested.** Phase 23 can investigate whether complete held-out-set parity reporting on this resource-constrained platform is underrepresented in prior work.
- **Future experiments strengthen the same story.** Walk-forward validation, ablation, statistical testing, timing distributions, and reduced-precision comparison all answer parts of the selected question.

## Working objective for the manuscript

> Develop and evaluate a reproducible, leakage-aware pipeline for selecting a compact load-forecasting model, generating its embedded C++ representation, and verifying numerical equivalence and implementation cost on a physical ESP8266 across the complete future held-out set.

This is a research objective, not a result. Its successful components must be supported separately by retained experiments.

## Phase 1 decision

Use **RQ1 as the primary research question**, **RQ2 as the forecasting/model-selection supporting question**, and **RQ3 as a cautious threshold-analysis supporting question**. The next phase may translate this hierarchy into exactly three or four contributions, with each contribution stating its evidence and limits.
