# Phase 7 — Feature-Group Ablation

Status: **complete for the normalized Kaggle-derived case study**  
Execution date: 2026-09-03  
Reproduction script: `tools/run_phase7_ablation.py`

## Objective

Determine whether lag, calendar, or supplied weather variables materially improve the compact float32 linear forecaster, and whether unnecessary device inputs can be removed.

## Method

The same five expanding-window folds from Phase 5 were used. Each fold contained a past training interval, a later 400-row calibration interval, and a later 400-row one-step-ahead test interval. Every feature group used the same 2,000 test timestamps.

The model was standardized linear least squares with float32 inference emulation. Six prescribed feature groups were evaluated:

| Group | Features | Count |
|---|---|---:|
| Calendar only | hour, weekday, month, weekend | 4 |
| Lag only | lag 1, lag 2, lag 48, lag 336 | 4 |
| Weather only | temperature, humidity, wind speed | 3 |
| Lag + calendar | all four lags and four calendar variables | 8 |
| Lag + weather | four lags and three weather variables | 7 |
| Lag + calendar + weather | all eleven variables | 11 |

`Avg_Past_Consumption` was deliberately excluded. Its rolling window and causal construction are undocumented, so using it could introduce opaque preprocessing or leakage.

## Results

| Rank by MAE | Feature group | Mean MAE ± SD | 95% t interval | Mean RMSE ± SD |
|---:|---|---:|---:|---:|
| 1 | Lag + calendar + weather | 0.133823 ± 0.004198 | [0.128610, 0.139035] | 0.166092 ± 0.004093 |
| 2 | Weather only | 0.133848 ± 0.004323 | [0.128479, 0.139216] | 0.166287 ± 0.004152 |
| 3 | Calendar only | 0.133852 ± 0.004395 | [0.128395, 0.139309] | 0.165936 ± 0.004290 |
| 4 | Lag + calendar | 0.133858 ± 0.004271 | [0.128555, 0.139161] | 0.165970 ± 0.004175 |
| 5 | Lag + weather | 0.133865 ± 0.004203 | [0.128646, 0.139084] | 0.166327 ± 0.004034 |
| 6 | Lag only | 0.133890 ± 0.004279 | [0.128577, 0.139203] | 0.166218 ± 0.004127 |

All errors are in normalized target units.

## Marginal changes

- Adding weather to lag + calendar reduced mean MAE by only `0.00003528`, or 0.0264%.
- Adding calendar to lag + weather reduced mean MAE by only `0.00004261`, or 0.0318%.
- Lag-only MAE was only 0.0505% above the full eleven-feature group.
- Calendar only achieved a slightly lower RMSE than the full group even though its MAE was slightly higher.

## Scientific interpretation

No feature group produced a practically clear advantage. The full group ranked first by mean MAE, but all mean MAEs fell within a range of only `0.00006756`, and their fold-level confidence intervals overlap extensively.

The prescribed questions are answered as follows:

- **Which standalone group contributes most?** Weather only had the lowest standalone mean MAE, while calendar only had the lowest standalone RMSE. The difference is too small to call either dominant.
- **Do weather variables help?** They reduced mean MAE by 0.0264% when added to lag + calendar, but slightly increased RMSE. This is not convincing evidence of practical benefit.
- **Can the compact model eliminate features?** The experiment suggests that reducing the input set may cost very little on this dataset, but it does not identify one statistically established optimal subset.

The near-equality of calendar-only, weather-only, lag-only, and combined models is itself a warning about dataset quality: the target may contain little exploitable temporal structure beyond its central tendency, or the normalized features may not preserve meaningful physical relationships. This is an interpretation, not proof that the data are synthetic.

## Embedded-system decision

- Do not redesign the already validated eight-feature ESP8266 firmware solely from these tiny differences; preserving the verified HIL artifact is more valuable.
- Do not add the three weather inputs to the current ESP8266 model. Their marginal benefit is negligible, their physical provenance is unknown, and acquiring them would require additional sensors or a weather-forecast service.
- Revisit feature reduction only after repeating the ablation on the official UCI/REFIT pipeline.

## Output artifacts

- `outputs/phase7_feature_ablation.json`: feature definitions, folds, metrics, intervals, and limitations.
- `outputs/phase7_feature_ablation.csv`: 30 fold/group metric rows.
- `outputs/phase7_feature_ablation_predictions.csv`: all group predictions on 2,000 timestamps.
- `outputs/phase7_feature_ablation.png`: mean-MAE increase relative to the full group.
- `tools/run_phase7_ablation.py`: deterministic experiment.

## Assumptions and limitations

- The contemporaneous weather fields are treated as available at prediction time; weather-forecast uncertainty is not modeled.
- Weather values are normalized and lack collection provenance or inverse scaling.
- Results from a linear model do not establish feature importance for nonlinear estimators.
- Feature groups are correlated; marginal changes are descriptive, not causal effects.
- Five temporal folds are insufficient for a broad generalization claim.
- No paired feature-subset significance test was prespecified for this phase.

## Publication value

The ablation prevents an unsupported claim that weather or extensive lag engineering drives performance. It supports a more important engineering conclusion: the current dataset does not justify adding weather-input complexity to a constrained ESP8266 deployment.

## Phase 7 conclusion

The complete eleven-feature group had the lowest mean MAE, but the differences among all six groups were negligible. Weather inputs should not be added to the deployed model on the basis of this evidence. Stronger measured datasets are necessary to determine a meaningful feature set.
