# Phase 2 — Defensible Research Contributions

Status: **complete; awaiting the next phase**  
Date: 2026-09-03

## Contribution policy

The paper will use exactly four contributions. They describe the paper’s technical value without claiming a new forecasting algorithm, a new anomaly-detection algorithm, calibrated electrical sensing, or field deployment. Later experiments may strengthen these contributions, but uncomputed findings must remain `[RESULT TO BE COMPUTED]`.

## Contribution 1 — Leakage-aware temporal evaluation

### Proposed contribution

> A leakage-aware temporal evaluation framework for half-hourly load forecasting that preserves chronological order and separates model fitting, anomaly-threshold calibration, and future held-out testing.

### What is new

The individual forecasting models are standard. The contribution is the paper’s explicit, reproducible temporal protocol and its consistent use across forecasting, residual calibration, anomaly comparison, and deployment-model selection. It prevents the misleading performance estimates that can result from random train/test splitting of lagged time-series observations.

This should be described as a **methodological and reproducibility contribution**, not as the first chronological forecasting framework.

### Current supporting evidence

- `[VERIFIED]` Rows are ordered by timestamp and divided chronologically rather than randomly.
- `[VERIFIED]` Lagged model rows use an 80/20 past-to-future division.
- `[VERIFIED]` Residual-threshold calibration is performed inside the earlier training interval before evaluation on the future test interval.
- `[VERIFIED]` The final held-out interval contains 933 observations.
- `[SUPPORTED BUT LIMITED]` The current evidence comes from one dataset and one chronological holdout.

### Evidence still required

- `[RESULT TO BE COMPUTED]` Four or five rolling-origin train/calibration/test folds.
- `[RESULT TO BE COMPUTED]` Fold-level means, variability, and confidence intervals.
- `[RESULT TO BE COMPUTED]` Seasonal-naive and boosting-model results under exactly the same protocol.

### What it does not prove

- It does not prove generalization across seasons, households, countries, or utilities.
- It does not make the underlying models algorithmically novel.
- It does not prove that every feature improves forecasting.

## Contribution 2 — Transparent residual anomaly analysis

### Proposed contribution

> A transparent forecast-residual anomaly-analysis procedure that calibrates decisions using past residuals, reports threshold trade-offs against dataset-supplied labels, and distinguishes label agreement from validated physical anomaly detection.

### What is new

The residual rule and Isolation Forest are established methods. The paper’s contribution is a transparent evaluation layer that connects forecasting residuals, calibration data, alert thresholds, supplied-label agreement, and embedded decision reproduction while explicitly preserving label uncertainty.

The final contribution will be credible only if the planned threshold-sensitivity analysis is completed. Until then, it is a **partially supported contribution**, not a completed finding.

### Current supporting evidence

- `[VERIFIED]` Threshold calibration uses earlier residuals rather than future test residuals.
- `[VERIFIED]` The deployed threshold yields TP 8, FP 0, FN 44, and TN 881 against the supplied labels.
- `[VERIFIED]` The corresponding precision, recall, and F1 are 1.000000, 0.153846, and 0.266667.
- `[VERIFIED]` The ESP8266 reproduced all 933 stored software threshold decisions.
- `[SUPPORTED BUT LIMITED]` These metrics establish agreement only with supplied labels whose physical provenance is not yet verified.

### Evidence still required

- `[RESULT TO BE COMPUTED]` Metrics and alert counts at the prescribed percentile thresholds.
- `[RESULT TO BE COMPUTED]` Precision–recall, F1-versus-threshold, and alert-count plots.
- `[RESULT TO BE COMPUTED]` Comparisons with adaptive residual, rolling residual, prediction-interval, and Isolation Forest decisions under a consistent protocol.
- `[RESULT TO BE VERIFIED]` Authoritative anomaly-label provenance.

### What it does not prove

- It does not prove accurate detection of real electrical faults.
- It does not establish that the supplied anomaly labels are physically correct.
- It does not establish that the current threshold is optimal or transferable.
- It is not a novel anomaly-detection algorithm.

## Contribution 3 — Reproducible compact-model export

### Proposed contribution

> A reproducible deployment path that trains a compact standardized linear forecasting model, exports ordered preprocessing and model constants to C++, and prepares the same held-out feature representation for constrained ESP8266 execution.

### What is new

The linear model itself is not new. The contribution is the explicit and auditable conversion pathway: fixed feature ordering, training-derived means and scales, coefficients, intercept, threshold, generated C++ constants, and device-compatible validation inputs. This supports inspection and numerical traceability better than manually transcribing parameters.

### Current supporting evidence

- `[VERIFIED]` `tools/train_tinyml_edge_model.py` calculates training-set feature means and standard deviations, fits the compact model, and writes `tinyml_model.h`.
- `[VERIFIED]` The generated header preserves the feature count, feature ordering, intercept, feature means, scales, coefficients, residual threshold, and reference vectors.
- `[VERIFIED]` The firmware invokes the generated constants for device inference.
- `[SUPPORTED BUT LIMITED]` Dataset-derived full-validation rows are generated locally and withheld from Git pending license confirmation.

### Evidence still required

- `[RESULT TO BE COMPUTED]` An automated host-side compilation test that compares Python predictions with generated C++ predictions before flashing.
- `[RESULT TO BE COMPUTED]` A machine-readable model manifest containing feature order, parameter values, split identifiers, numerical representation, and source-data hash.
- `[RESULT TO BE VERIFIED]` Exact package and toolchain versions in a reproducible environment.

### What it does not prove

- It does not prove that linear regression is the best forecasting model.
- It does not prove portability to every microcontroller or compiler.
- It does not prove quantized or fixed-point equivalence.
- It does not include sensor calibration or data acquisition.

## Contribution 4 — Complete held-out-set ESP8266 HIL verification

### Proposed contribution

> Complete hardware-in-the-loop verification of the exported forecasting computation over all 933 future held-out observations on a physical ESP8266, reporting numerical prediction parity, threshold-decision parity, measured inference time, and compiled RAM, flash, and IRAM utilization.

### What is new

The paper does not merely demonstrate that one example runs. It evaluates the complete held-out feature set on the physical target and reports both numerical and binary-decision mismatches together with implementation costs. The literature review must still determine how uncommon this level of full-set device verification is; the paper must not use “first” without that evidence.

### Current supporting evidence

- `[VERIFIED]` All 933 held-out feature vectors were evaluated on a physical ESP8266EX/NodeMCU.
- `[VERIFIED]` Prediction agreement was 933/933.
- `[VERIFIED]` Threshold-decision agreement was 933/933.
- `[VERIFIED]` Maximum absolute Python/device prediction difference was 0.000000089 normalized target units; physical kWh is not established by the scaled file.
- `[VERIFIED]` Three pure-inference passes measured 50.840, 50.730, and 50.683 microseconds per prediction, with a mean of 50.751 microseconds.
- `[VERIFIED]` The full validation loop took 60,141 microseconds; it is reported separately from pure inference.
- `[VERIFIED]` Normal firmware used 36% RAM, 24% flash, and 92% IRAM; full-validation firmware used 36% RAM, 28% flash, and 92% IRAM.
- `[SUPPORTED BUT LIMITED]` Successful ThingSpeak writes after validation demonstrate observed telemetry continuity only.

### Evidence still required

- `[RESULT TO BE COMPUTED]` Mean absolute numerical difference, in addition to the retained maximum.
- `[RESULT TO BE COMPUTED]` A sufficiently large latency sample for median, standard deviation, minimum, maximum, and percentiles.
- `[RESULT TO BE COMPUTED]` Separate preprocessing, inference, communication, and any future acquisition timing.
- `[RESULT TO BE COMPUTED]` Model parameter count, arithmetic-operation count, constant-storage size, and resource-headroom analysis.
- `[RESULT TO BE VERIFIED]` Board core, compiler, Arduino CLI, and firmware dependency versions.

### What it does not prove

- It does not prove calibrated voltage, current, power, or energy measurement.
- It does not prove real-time end-to-end smart-meter operation.
- It does not prove field reliability, sensor accuracy, security, or utility readiness.
- It does not prove low-power or energy-efficient operation.

## Evidence maturity summary

| Contribution | Present maturity | Main dependency before final paper |
|---|---|---|
| 1. Temporal evaluation | Supported but limited | Walk-forward folds and statistical analysis |
| 2. Residual anomaly analysis | Partially supported | Threshold sensitivity and label provenance |
| 3. Compact-model export | Strongly supported | Automated pre-flash Python/C++ test and manifest |
| 4. Complete ESP8266 HIL verification | Strongly supported within replay scope | Expanded timing/resource analysis and toolchain metadata |

## Manuscript-ready contribution paragraph

The final introduction may use the following structure after the pending experiments are completed:

> This study makes four contributions. First, it establishes a leakage-aware temporal protocol that separates forecasting-model fitting, residual-threshold calibration, and future evaluation. Second, it provides a transparent residual anomaly-analysis framework that reports threshold trade-offs against supplied labels while distinguishing label agreement from physical fault validation. Third, it implements a reproducible Python-to-C++ export path for a compact standardized linear forecasting model with explicit feature ordering and preprocessing constants. Fourth, it verifies the exported computation on a physical ESP8266 over the complete 933-observation held-out set and reports numerical agreement, decision agreement, inference latency, and compiled memory utilization.

This paragraph describes the intended final contribution set. Any component depending on later phases must be revised or removed if its required experiment is not completed.

## Phase 2 decision

Retain exactly these four contribution categories. Do not elevate the anomaly detector, ESP8266 sensing, telemetry, or any “first” claim into the main novelty. Phase 3 must now determine whether the dataset and its supplied labels can legally and scientifically support publication.
