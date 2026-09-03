# Phase 5 — Five-Fold Walk-Forward Validation

Status: **complete for the normalized Kaggle-derived case study**  
Execution date: 2026-09-03  
Reproduction script: `tools/run_phase5_walk_forward.py`

## Objective

Determine whether the Phase 4 model ranking persists across multiple future intervals and whether the compact float32 edge representation remains competitive with ordinary float64 linear regression.

## Input and forecast mode

- Dataset SHA-256: `D48DF940FD29444FB9222FC0B59CFDE632E147CCD1D49DC7BED9D5F9DC88F588`
- Rows after lag construction: 4,664
- Features: lag 1, lag 2, lag 48, lag 336, hour, weekday, month, and weekend flag
- Forecast mode: rolling one-step-ahead; each lag value is observed before its prediction timestamp
- Units: normalized dataset target units

This is not a 400-step recursive forecast. Within each test block, newly observed past loads become available to subsequent one-step-ahead predictions.

## Fold design

Five non-overlapping 400-row test blocks were used. Training expanded by 400 rows each fold. A separate 400-row calibration block always occurred after training and before testing; it was preserved for later anomaly-threshold experiments and was not used to fit forecasting models in that fold.

| Fold | Training rows | Calibration rows | Test rows | Test period |
|---:|---:|---:|---:|---|
| 1 | 2,264 | 400 | 400 | 2024-03-03 to 2024-03-11 |
| 2 | 2,664 | 400 | 400 | 2024-03-11 to 2024-03-20 |
| 3 | 3,064 | 400 | 400 | 2024-03-20 to 2024-03-28 |
| 4 | 3,464 | 400 | 400 | 2024-03-28 to 2024-04-05 |
| 5 | 3,864 | 400 | 400 | 2024-04-05 to 2024-04-14 |

Every model used the same fold boundaries. Future test observations never entered that fold’s training or calibration interval.

## Fold-level MAE

| Model | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
|---|---:|---:|---:|---:|---:|
| Compact edge LR, FP32 | 0.141301 | 0.133270 | 0.130560 | 0.132190 | 0.131969 |
| Linear regression | 0.141301 | 0.133270 | 0.130560 | 0.132190 | 0.131969 |
| Random forest | 0.141747 | 0.133910 | 0.133170 | 0.134637 | 0.132715 |
| Histogram gradient boosting | 0.145919 | 0.141561 | 0.136532 | 0.141150 | 0.135417 |
| Seasonal naive, lag 48 | 0.200716 | 0.194415 | 0.185682 | 0.177882 | 0.185351 |
| Persistence, lag 1 | 0.202395 | 0.188871 | 0.189551 | 0.188545 | 0.188137 |

## Overall results

The confidence intervals below are two-sided Student-t intervals over five fold-level values.

| Rank | Model | Mean MAE ± SD | 95% CI for mean MAE | Mean RMSE ± SD | Pooled MAE |
|---:|---|---:|---:|---:|---:|
| 1 | Compact edge LR, FP32 | 0.133858 ± 0.004271 | [0.128555, 0.139161] | 0.165970 ± 0.004175 | 0.133858 |
| 2 | Linear regression | 0.133858 ± 0.004271 | [0.128555, 0.139161] | 0.165970 ± 0.004175 | 0.133858 |
| 3 | Random forest | 0.135236 ± 0.003713 | [0.130626, 0.139846] | 0.167993 ± 0.003135 | 0.135236 |
| 4 | Histogram gradient boosting | 0.140116 ± 0.004235 | [0.134857, 0.145375] | 0.174222 ± 0.003543 | 0.140116 |
| 5 | Seasonal naive, lag 48 | 0.188809 ± 0.008865 | [0.177802, 0.199816] | 0.235346 ± 0.008103 | 0.188809 |
| 6 | Persistence, lag 1 | 0.191500 ± 0.006112 | [0.183910, 0.199089] | 0.237066 ± 0.007700 | 0.191500 |

## Compact-model numerical comparison

The compact model was fitted in standardized form and its means, scales, intercept, coefficients, inputs, and accumulation were emulated with float32. Ordinary linear regression used scikit-learn’s float64 computation.

Across the 2,000 non-overlapping test predictions:

- mean absolute compact-versus-linear prediction difference: `8.6559674673802875e-09` normalized units;
- maximum absolute difference: `2.7524578227744456e-08` normalized units.

This establishes near-identical software accuracy for this simple model representation. It is separate from the earlier 933-row physical ESP8266 HIL comparison.

## Scientific interpretation

- The compact float32 model and ordinary float64 linear regression were practically indistinguishable in every fold.
- Both linear models had lower mean MAE than the tree ensembles and naive baselines in all five folds.
- Random forest remained close to the linear models; statistical significance is evaluated in Phase 6 rather than inferred from rank.
- Histogram gradient boosting did not improve forecasting with the selected fixed configuration.
- Seasonal naive generally improved on persistence, but not in Fold 2.
- Fold 1 was the most difficult interval for every model, demonstrating temporal performance variation that the single holdout concealed.

## Output artifacts

- `outputs/phase5_walk_forward_results.json`: complete fold design, metrics, uncertainty, environment, and limitations.
- `outputs/phase5_walk_forward_fold_metrics.csv`: 30 fold/model metric records.
- `outputs/phase5_walk_forward_predictions.csv`: 2,000 test timestamps with predictions from all six models.
- `outputs/phase5_walk_forward_model_comparison.png`: mean fold MAE with 95% t intervals.
- `outputs/phase5_walk_forward_error_distribution.png`: absolute-error distributions over all test predictions.

## Statistical limitations

- Five folds give imprecise uncertainty estimates.
- Training windows overlap and time-series errors are dependent, so the t intervals are descriptive rather than proof of independence.
- Overlapping confidence intervals do not by themselves establish equivalence or non-significance.
- Phase 6 must use paired forecast errors and dependence-aware interpretation.
- The short normalized case study does not provide annual seasonality or external validation.

## Publication value

The experiment replaces dependence on a single holdout with repeated future testing under a documented, leakage-safe protocol. It supports the claim that compact float32 linear inference preserves forecasting behavior across multiple time intervals, while showing why small model-ranking differences require paired statistical analysis.

## Phase 5 conclusion

The compact edge model remains competitive across all five folds and is numerically indistinguishable in forecasting accuracy from ordinary linear regression. This is a descriptive result for the current normalized dataset, not yet a statistical superiority or generalization claim.
