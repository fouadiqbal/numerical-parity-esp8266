# Phase 8 — Residual-Threshold Sensitivity

Status: **complete for the normalized Kaggle-derived case study**  
Execution date: 2026-09-03  
Reproduction script: `tools/run_phase8_threshold_sensitivity.py`

## Objective

Measure how calibration-residual percentile changes affect precision, recall, F1, and alert volume for the compact edge model when compared with the dataset-supplied labels.

## Protocol

- Model-fit rows: 2,984
- Past calibration rows: 747
- Future test rows: 933
- Supplied test labels: 52 abnormal and 881 normal
- Thresholds: 90th, 92.5th, 95th, 97.5th, 99th, and 99.5th percentiles of **past calibration residuals**
- Test decision: absolute residual greater than the calibrated threshold
- Units: normalized target units

The chronological order is fit → calibration → future test. No future residual was used to calculate any threshold.

## Results

| Calibration percentile | Threshold | TP | FP | FN | TN | Precision | Recall | F1 | Alerts |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 90.0 | 0.284494 | 28 | 46 | 24 | 835 | 0.378 | 0.538 | 0.444 | 74 |
| 92.5 | 0.310073 | 27 | 31 | 25 | 850 | 0.466 | 0.519 | 0.491 | 58 |
| 95.0 | 0.343713 | 21 | 18 | 31 | 863 | 0.538 | 0.404 | 0.462 | 39 |
| 97.5 | 0.365361 | 17 | 6 | 35 | 875 | 0.739 | 0.327 | 0.453 | 23 |
| 99.0 | 0.383026 | 8 | 0 | 44 | 881 | 1.000 | 0.154 | 0.267 | 8 |
| 99.5 | 0.410987 | 4 | 0 | 48 | 881 | 1.000 | 0.077 | 0.143 | 4 |

## Scientific interpretation

- Raising the percentile trades recall and alert coverage for precision.
- The deployed 99th-percentile rule generated no false positives against supplied labels but missed 44 of 52 supplied positives.
- The 92.5th percentile had the highest observed test F1, 0.491, with 58 alerts, but also produced 31 false positives.
- The 97.5th percentile provides an intermediate descriptive trade-off: precision 0.739, recall 0.327, F1 0.453, and 23 alerts.
- The 99.5th percentile is even more conservative and detects only 4 supplied positives.

For the narrow objective of maximizing agreement F1 with these supplied labels, 99% appears unnecessarily conservative. For an application where false alarms are much more costly than missed events, the decision could differ. No application-specific error costs have been established.

## Selection warning

The 92.5th percentile is a **retrospective test-set observation**, not a newly approved deployment threshold. Choosing it because it performed best on the final test labels would contaminate future evaluation.

A valid next threshold-selection procedure should:

1. choose an operational cost function in advance;
2. select the percentile using training/calibration data or nested temporal folds;
3. lock the threshold;
4. evaluate it once on a separate future or official-dataset test set.

## Output artifacts

- `outputs/phase8_threshold_sensitivity.json`: split, thresholds, complete metrics, and selection warning.
- `outputs/phase8_threshold_sensitivity.csv`: six threshold records.
- `outputs/phase8_threshold_decisions.csv`: all 933 residuals, labels, and decisions.
- `outputs/phase8_precision_recall.png`.
- `outputs/phase8_f1_vs_threshold.png`.
- `outputs/phase8_alerts_vs_threshold.png`.

## Claims boundary

- The labels were described by the publisher as Isolation Forest outputs; they are not independently verified physical events.
- Precision and recall mean agreement with supplied labels only.
- The test contains only 52 supplied positives.
- No result validates detection of electrical faults, fraud, meter malfunction, or unsafe conditions.
- Threshold performance may change on another time interval or dataset.

## Publication value

The sensitivity analysis prevents a misleading presentation of precision 1.0 without its corresponding recall and alert-count cost. It turns the threshold into an explicit, inspectable operating trade-off.

## Phase 8 conclusion

The current 99th-percentile deployment rule prioritizes precision at the expense of recall. The paper should report the full sensitivity curve and retain the current threshold as the historical HIL configuration, not call it optimal.
