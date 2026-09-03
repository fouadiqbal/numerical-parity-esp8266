# Phase 6 — Paired Statistical Forecast Comparison

Status: **complete for the normalized Kaggle-derived case study**  
Execution date: 2026-09-03  
Reproduction script: `tools/run_phase6_statistics.py`

## Objective

Test whether the compact float32 edge model’s absolute forecast errors differ meaningfully from the other Phase 5 models on the same 2,000 timestamps.

## Input

- `outputs/phase5_walk_forward_predictions.csv`
- 2,000 unique, non-overlapping walk-forward test timestamps
- Reference model: compact standardized linear model with float32 inference emulation
- Loss: absolute error in normalized target units

For each timestamp, the paired difference is:

`absolute error of compact model − absolute error of comparator`

Negative values favor the compact model.

## Methods

### Moving-block bootstrap

- 10,000 bootstrap replicates.
- Contiguous block length 48, representing one day of half-hourly observations.
- Percentile 95% confidence interval for the mean paired MAE difference.
- Fixed seed beginning at 42, with a separate deterministic stream per comparison.

### Dependence-adjusted loss-differential test

A Diebold–Mariano-style test was applied to the absolute-loss differential. The standard error used a Bartlett Newey–West heteroskedasticity-and-autocorrelation-consistent variance with lag 48. Two-sided asymptotic normal p-values were adjusted across the five comparisons using Holm’s method.

This is described as **DM-style**, because expanding model fits, a short sample, and fixed daily HAC settings may not satisfy every classical Diebold–Mariano assumption.

## Results

| Comparator | Compact − comparator MAE | Relative change | Block-bootstrap 95% CI | Holm-adjusted p | Interpretation under specified test |
|---|---:|---:|---:|---:|---|
| Linear regression | −0.000000000068 | −0.000000051% | [−0.000000000444, 0.000000000378] | 0.745049 | Not distinguishable |
| Random forest | −0.001378 | −1.019% | [−0.002490, −0.000180] | 0.034530 | Distinguishable; small compact-model advantage |
| Histogram gradient boosting | −0.006258 | −4.466% | [−0.008475, −0.003911] | 0.000000192 | Distinguishable; compact model lower |
| Seasonal naive, lag 48 | −0.054951 | −29.104% | [−0.059999, −0.050036] | 2.27 × 10⁻⁹⁷ | Distinguishable; compact model lower |
| Persistence, lag 1 | −0.057642 | −30.100% | [−0.062364, −0.052358] | 1.77 × 10⁻¹¹⁴ | Distinguishable; compact model lower |

## Paired outcome counts

| Comparator | Compact lower error | Equal | Compact higher error |
|---|---:|---:|---:|
| Linear regression | 1,009 | 0 | 991 |
| Random forest | 1,035 | 0 | 965 |
| Histogram gradient boosting | 1,121 | 0 | 879 |
| Seasonal naive, lag 48 | 1,304 | 0 | 696 |
| Persistence, lag 1 | 1,320 | 0 | 680 |

The apparent absence of exact ties against ordinary linear regression is caused by very small float32-versus-float64 numerical differences. Its paired mean and interval demonstrate practical equivalence within this experiment; this is not a formal equivalence test.

## Scientific interpretation

1. **Compact versus ordinary linear regression:** no statistically distinguishable error difference was found. Their predictions differ only at numerical-precision scale.
2. **Compact versus random forest:** the selected procedure found a 1.019% relative MAE reduction with a Holm-adjusted p-value of 0.0345. The effect is statistically distinguishable under the specified assumptions but small in practical magnitude.
3. **Compact versus gradient boosting:** the compact model had a 4.466% lower paired MAE under the chosen fixed configurations.
4. **Compact versus naive baselines:** differences were both large and statistically distinguishable, supporting the value of learned lag/calendar relationships over direct lag copying in this dataset.
5. Statistical significance does not establish cross-dataset generalization, physical-unit accuracy, or superiority under other hyperparameters.

## Output artifacts

- `outputs/phase6_statistical_comparison.json`: complete methods, paired results, unadjusted and adjusted tests, and limitations.
- `outputs/phase6_statistical_comparison.csv`: flat comparison table.
- `outputs/phase6_paired_mae_differences.png`: paired MAE effects with daily-block bootstrap intervals.
- `tools/run_phase6_statistics.py`: deterministic implementation.

## Assumptions and limitations

- Forecast losses are temporally dependent; daily blocks and a daily HAC lag mitigate but do not eliminate model-risk in dependence estimation.
- The five expanding training histories overlap.
- The fixed 48-observation block/HAC length was chosen from the half-hourly daily cycle, not by an independently optimized selection rule.
- The asymptotic p-values may be optimistic in a short 104-day series.
- Holm adjustment covers only the five prespecified compact-model comparisons.
- The results apply to one normalized, provenance-limited dataset.
- A future official-dataset replication is required before making broad performance claims.

## Publication value

The experiment replaces rank-only statements with paired effect estimates, dependence-aware confidence intervals, multiplicity-adjusted inference, and practical-effect interpretation. It supports saying that the compact model matched ordinary linear regression and outperformed the tested naive baselines on this case study. It does not support saying that it is universally superior.

## Phase 6 conclusion

The compact float32 model is statistically indistinguishable from ordinary linear regression and retains a clear advantage over naive baselines under the stated procedure. Its small advantage over random forest should be reported with effect size and assumptions rather than as an unconditional superiority claim.
