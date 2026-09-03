# Phase 10 — Reproducible ESP8266 Model Export

## Outcome

Phase 10 is complete. The compact forecasting model now has a reproducible Python-to-C++ export path, a machine-readable manifest, an independent compiled-host parity test, and successful ESP8266 firmware builds in both normal and 933-vector validation modes.

This phase validates numerical model transfer. It does not claim calibrated power sensing, live forecasting, or physical anomaly detection.

## Frozen model specification

- Model: standardized linear regression
- Target: `Electricity_Consumed`
- Target units: normalized dataset units; physical kWh is not established
- Training precision: Python `float64`
- Deployment precision: C++ `float32`
- Fit/calibration/test rows: 2,984 / 747 / 933
- Residual detector: absolute residual greater than the calibration-set 99th percentile
- Residual threshold: 0.3830260556 normalized target units in Python; 0.3830260634 after `float32` serialization
- Model fingerprint: `7E7F91C2B5597F57F7801830D9719B2FDB9A5987283FB0EFCFE2481F4B323003`

The inference equation is:

```text
prediction = intercept + Σ [((feature[i] - mean[i]) / scale[i]) × coefficient[i]]
```

## Feature contract

Feature order is part of the deployment interface and must not be changed without retraining and regenerating the header.

| Index | Feature | Meaning at 30-minute sampling |
|---:|---|---|
| 0 | `lag_1` | Previous sample |
| 1 | `lag_2` | Two samples earlier |
| 2 | `lag_48` | Same half-hour on the previous day |
| 3 | `lag_336` | Same half-hour on the previous week |
| 4 | `hour` | Local clock hour, 0–23 |
| 5 | `day_of_week` | Monday 0 through Sunday 6 |
| 6 | `month` | Calendar month, 1–12 |
| 7 | `is_weekend` | 1 for Saturday/Sunday, otherwise 0 |

| Feature | Mean | Scale | Coefficient |
|---|---:|---:|---:|
| `lag_1` | 0.3799574564 | 0.1638514661 | -0.0020018301 |
| `lag_2` | 0.3799492606 | 0.1638429727 | -0.0012800773 |
| `lag_48` | 0.3802920868 | 0.1631049524 | -0.0022238148 |
| `lag_336` | 0.3810412592 | 0.1627085272 | -0.0022778088 |
| `hour` | 11.4731903485 | 6.9324550281 | 0.0003858329 |
| `day_of_week` | 2.9597855228 | 1.9827654090 | 0.0006399844 |
| `month` | 1.7613941019 | 0.6903472240 | -0.0041192007 |
| `is_weekend` | 0.2761394102 | 0.4470866094 | 0.0021499011 |

Intercept: 0.3800952523.

## Generated artifacts

Running `python tools/train_tinyml_edge_model.py` produces:

- `firmware/esp8266_smart_meter/tinyml_model.h`: deployable constants, inference function, and eight public spot-check vectors
- `firmware/esp8266_smart_meter/tinyml_validation_data.h`: local 933-row validation header, intentionally ignored because it contains dataset-derived rows
- `outputs/tinyml_model_manifest.json`: parameters, feature contract, data split, hashes, precision, and environment
- `outputs/tinyml_edge_metrics_v2.json`: Python reference metrics with corrected units
- `outputs/tinyml_edge_test_predictions_v2.csv`: row-level Python reference predictions

The source CSV is bound to SHA-256 `D48DF940FD29444FB9222FC0B59CFDE632E147CCD1D49DC7BED9D5F9DC88F588`.

## Independent compiled-C++ parity test

`python tools/test_generated_cpp_model.py` compiles a small C++17 runner against the generated Arduino header, executes all 933 test rows outside Python, and compares its output with the Python reference file.

| Check | Result |
|---|---:|
| Predictions within `1e-6` tolerance | 933 / 933 |
| Prediction mismatches | 0 |
| Mean absolute numerical difference | 0.000000017288 normalized units |
| Maximum absolute numerical difference | 0.000000075572 normalized units |
| Anomaly-decision agreement | 933 / 933 |
| Anomaly-decision mismatches | 0 |

Compiler: MinGW-w64 g++ 8.1.0, C++17, `-O2`. The machine-readable record is `outputs/tinyml_cpp_parity.json`.

This host test is independent of the Python inference implementation but is not a device benchmark. It specifically catches generated-header, feature-order, arithmetic, precision, and threshold-transfer errors before flashing hardware.

## ESP8266 compile verification

Both firmware modes compile for `esp8266:esp8266:nodemcuv2` after the normalized-unit migration.

| Build | RAM | IRAM | Flash code | Status |
|---|---:|---:|---:|---|
| Normal firmware | 29,340 / 80,192 B (36%) | 60,343 / 65,536 B (92%) | 257,508 / 1,048,576 B (24%) | Pass |
| 933-vector validation firmware | 29,676 / 80,192 B (37%) | 60,343 / 65,536 B (92%) | 297,844 / 1,048,576 B (28%) | Pass |

The firmware resource record is `outputs/phase10_firmware_builds.json`. IRAM use is high at 92%, so future networking, cryptography, or signal-processing additions need a fresh resource check.

## Reference test-set result

The frozen Python model obtained MAE 0.1307837086 and RMSE 0.1623896726 in normalized target units. With the historical 99th-percentile residual threshold, it produced TP=8, FP=0, FN=44, TN=881 against the supplied publisher-derived labels (precision 1.0, recall 0.1538, F1 0.2667).

These classification values are benchmark results against labels described by the dataset publisher as Isolation Forest outputs. They are not evidence of detection accuracy for physically confirmed electrical faults.

## Reproduction commands

```powershell
python tools/train_tinyml_edge_model.py
python tools/test_generated_cpp_model.py
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Build
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Build -FullValidation
```

## Phase decision

The exported linear model is the deployment candidate because it is transparent, compact, deterministic, and statistically indistinguishable from the unconstrained linear baseline in Phase 6. Phase 7 also showed no meaningful benefit from adding weather inputs, so the edge contract remains limited to lag and calendar features.

The next phase separates and audits three evidence layers: offline Python evaluation, compiled-host numerical parity, and physical ESP8266 hardware-in-the-loop execution.
