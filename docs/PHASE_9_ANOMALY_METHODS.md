# Phase 9 — Anomaly-Method Comparison

Status: **complete for the normalized Kaggle-derived case study**  
Execution date: 2026-09-03  
Reproduction script: `tools/run_phase9_anomaly_methods.py`

## Objective

Compare the deployed static residual rule with sequential adaptive and rolling thresholds, a split-conformal prediction interval, and Isolation Forest without tuning any method on the future test labels.

## Evidence boundary

The outcome is **agreement with dataset-supplied, publisher-described Isolation-Forest-generated labels**. It is not validated real-world electrical anomaly detection.

## Common protocol

- Model-fit rows: 2,984
- Past calibration rows: 747
- Future test rows: 933
- Supplied test positives: 52
- Supplied test negatives: 881
- All residual thresholds were initialized from past data.
- Adaptive and rolling methods made each decision before incorporating the current residual.

## Prespecified methods

1. **Static residual p99:** fixed 99th percentile of calibration residuals; this is the HIL deployment rule.
2. **Adaptive EWMA residual p99:** initialized to the static p99 operating point, with EWMA alpha 0.02; the state updates after each decision.
3. **Rolling-week residual p99:** 99th percentile of the previous 336 residuals, representing seven days at half-hourly sampling.
4. **Split conformal 95%:** symmetric absolute-residual interval using the finite-sample calibration rank 711 of 747.
5. **Isolation Forest 5%:** 200 trees, seed 42, trained on past standardized target/lag/calendar features with contamination 0.05.

## Results

| Rank by F1 | Method | TP | FP | FN | TN | Precision | Recall | F1 | Alerts |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Split conformal 95% | 21 | 18 | 31 | 863 | 0.538 | 0.404 | 0.462 | 39 |
| 2 | Adaptive EWMA p99 | 16 | 14 | 36 | 867 | 0.533 | 0.308 | 0.390 | 30 |
| 3 | Rolling-week p99 | 10 | 1 | 42 | 880 | 0.909 | 0.192 | 0.317 | 11 |
| 4 | Static residual p99 | 8 | 0 | 44 | 881 | 1.000 | 0.154 | 0.267 | 8 |
| 5 | Isolation Forest 5% | 19 | 114 | 33 | 767 | 0.143 | 0.365 | 0.205 | 133 |

## Sequential-threshold behavior

- Adaptive EWMA threshold increased from 0.383026 to 0.424410 normalized units.
- Rolling-week p99 threshold increased from 0.372474 to 0.420065 normalized units.
- The increasing thresholds show that the future residual distribution differed from the earlier calibration state.
- Because adaptive methods update from all residuals, sustained unusual behavior can raise the threshold and reduce later sensitivity.

## Scientific interpretation

- The 95% split-conformal interval had the highest descriptive F1, but it does not establish valid time-series coverage because exchangeability is doubtful.
- Adaptive EWMA increased recall relative to static p99, but generated 14 supplied-label false positives and its operating point drifted upward.
- Rolling-week p99 preserved high precision and slightly improved recall over the static detector.
- Static p99 remained the most conservative method and retained perfect supplied-label precision at very low recall.
- Isolation Forest generated 133 alerts despite a 5% training contamination setting, indicating a distribution shift or mismatch between our past-trained feature configuration and the publisher’s undisclosed labeling configuration.
- The poor Isolation Forest agreement cannot be interpreted as evidence that Isolation Forest is generally inferior.

## Method recommendation

- Preserve static p99 as the exact historical ESP8266 HIL configuration.
- Use split conformal and rolling residual thresholds as transparent research comparators.
- Do not change the deployed threshold from this test-set comparison.
- Do not make a final anomaly-method recommendation until the experiment is repeated on the DOI-backed annotated REFIT anomaly dataset.
- Treat the Isolation Forest comparison as a demonstration of label-method circularity and configuration sensitivity, not an algorithm contest.

## Output artifacts

- `outputs/phase9_anomaly_methods.json`: complete configurations, metrics, and limitations.
- `outputs/phase9_anomaly_methods.csv`: flat five-method results.
- `outputs/phase9_anomaly_decisions.csv`: sequential thresholds and 933 method decisions.
- `outputs/phase9_anomaly_precision_recall.png`.
- `outputs/phase9_anomaly_f1_comparison.png`.

## Limitations

- The label column is not independent physical ground truth.
- Isolation Forest contamination uses the known 5% dataset label fraction, which creates circularity risk even though future labels were not used in fitting.
- EWMA alpha, rolling window, and p99 setting were engineering choices, not externally validated optima.
- Split-conformal marginal coverage is not guaranteed under temporal dependence or distribution shift.
- Rankings are descriptive for one future holdout.
- No anomaly method was tested against a confirmed electrical fault event.

## Publication value

The comparison replaces a single fixed threshold with several transparent, reproducible operating mechanisms and exposes the consequences of adaptation, alert volume, label circularity, and uncertain ground truth.

## Phase 9 conclusion

No method can be called a validated real-world anomaly detector from this dataset. Split conformal produced the best supplied-label F1, while rolling p99 offered the strongest high-precision alternative. The static p99 rule remains important only because it is the configuration already reproduced by the physical ESP8266.
