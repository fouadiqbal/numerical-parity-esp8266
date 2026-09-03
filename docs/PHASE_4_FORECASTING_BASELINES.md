# Phase 4 — Stronger Forecasting Baselines

Status: **complete for the normalized Kaggle-derived case study**  
Execution date: 2026-09-03  
Reproduction script: `tools/run_phase4_forecasting.py`

## Objective

Compare the required forecasting baselines on the same future chronological holdout while preserving the current ESP8266 deployment model as a distinct compact model.

## Input

- Source file: `data/source/extracted/smart_meter_data.csv`
- CSV SHA-256: `D48DF940FD29444FB9222FC0B59CFDE632E147CCD1D49DC7BED9D5F9DC88F588`
- Raw rows: 5,000
- Rows after causal lag-336 construction: 4,664
- Units: normalized dataset target units; physical kWh is not established

## Method

The data were sorted by timestamp. Causal lags 1, 2, 48, and 336 and calendar variables were generated. After removing the first 336 rows that lack a complete lag history, the earliest 80% formed the training interval and the latest 20% formed the future test interval.

| Partition | Rows | Time range |
|---|---:|---|
| Training | 3,731 | 2024-01-08 00:00 to 2024-03-25 17:00 |
| Future test | 933 | 2024-03-25 17:30 to 2024-04-14 03:30 |

No random train/test split was used. The learned models received the same eight lag/calendar predictors. The two naive baselines used only their specified historical target.

## Models

1. Persistence using lag 1.
2. Seasonal naive using lag 48, representing the same half-hour on the previous day.
3. Ordinary linear regression fit on all 3,731 training rows.
4. Random forest with 200 estimators, maximum depth 12, minimum leaf size 2, and seed 42.
5. Histogram gradient boosting with 200 iterations, learning rate 0.05, 31 maximum leaves, minimum leaf size 20, L2 regularization 0.1, and seed 42.
6. Compact standardized linear model matching the deployment protocol. It was fit on the earliest 2,984 training rows while the next 747 rows remained reserved for anomaly calibration.

## Results

| Rank by MAE | Model | MAE | RMSE | sMAPE (%) |
|---:|---|---:|---:|---:|
| 1 | Compact edge linear | 0.130784 | 0.162390 | 39.802 |
| 2 | Linear regression | 0.130960 | 0.162529 | 39.862 |
| 3 | Random forest | 0.132761 | 0.165213 | 40.179 |
| 4 | Histogram gradient boosting | 0.136093 | 0.170102 | 40.953 |
| 5 | Seasonal naive, lag 48 | 0.183463 | 0.230878 | 56.380 |
| 6 | Persistence, lag 1 | 0.188160 | 0.232248 | 57.969 |

All MAE and RMSE values are in normalized target units.

## Scientific interpretation

- The seasonal-naive lag-48 baseline improved on lag-1 persistence, confirming that daily periodicity is worth including as a baseline.
- On this one holdout, the compact edge model reduced MAE by 30.493% relative to persistence and 28.714% relative to seasonal naive.
- The compact edge model’s MAE was only 0.134% lower than full-training linear regression. This tiny difference may reflect temporal variation or sampling and must not be called statistically meaningful before Phase 5–6.
- Random forest and histogram gradient boosting did not improve on the two linear models under the selected configurations.
- This ranking applies only to this normalized, provenance-limited dataset and single future interval.
- The high sMAPE values are influenced by targets near zero; MAE and RMSE remain the primary metrics for this case study.

## Output artifacts

- `outputs/phase4_forecasting_results.json`: configuration, environment, split, metrics, and limitations.
- `outputs/phase4_forecasting_predictions.csv`: all 933 actual values and six model predictions.
- `outputs/phase4_forecasting_comparison.png`: publication-oriented MAE/RMSE comparison.
- `tools/run_phase4_forecasting.py`: deterministic reproduction code.

## Environment recorded by the run

- Python 3.13.2
- NumPy 2.5.2
- Pandas 3.0.5
- scikit-learn 1.9.0
- Random seed 42 for stochastic estimators

## Publication value

Phase 4 replaces a weak baseline set with daily seasonal naive and gradient boosting comparisons, and it treats the deployed edge model as a separate candidate. It provides a reproducible foundation for the accuracy-versus-deployability question.

## Limitations and claims boundary

- This is one chronological holdout, not evidence across temporal folds.
- Fit time is machine-dependent and is not used as a model-quality claim.
- Hyperparameters were not exhaustively optimized.
- The current values are normalized and cannot be presented as verified kWh.
- No result here establishes household, seasonal, or cross-dataset generalization.
- No small difference between learned models is claimed to be statistically meaningful.
- The recommended official UCI/REFIT dataset experiment remains separate and unrun.

## Phase 4 conclusion

All six required model categories were evaluated without temporal shuffling. The compact edge linear model is a credible deployment candidate on this holdout, but its apparent advantage over ordinary linear regression is too small to interpret without rolling-origin and paired statistical analysis. Phase 5 will therefore use identical fold boundaries for every model.
