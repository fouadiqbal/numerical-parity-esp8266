# Phase 20 — Detailed Conference-Paper Structure

Date: 2026-09-03  
Status: complete (structure only; manuscript prose is reserved for Phase 27)

## Working title

> **Reproducible Python-to-ESP8266 Transfer of a Compact Load-Forecasting Pipeline with Full-Holdout Hardware-in-the-Loop Verification**

The title deliberately emphasizes numerical transfer and HIL verification. It does not describe the ESP8266 as a validated smart meter, claim calibrated energy sensing, or make anomaly detection the main novelty.

## Central research question

> To what extent can a compact, leakage-aware load-forecasting and residual-alert pipeline be transferred from Python to C++ on a resource-constrained ESP8266 while preserving numerical predictions and threshold decisions, and what measured latency and memory costs result?

## Front matter

### Abstract

Use a five-part structure in approximately 180–230 words:

1. **Context:** local load forecasting can support edge-side monitoring, but software-only accuracy does not establish reliable microcontroller transfer.
2. **Gap:** many prototype descriptions do not separate forecasting evaluation, numerical portability, device execution and real sensing evidence.
3. **Method:** chronological holdout plus five rolling-origin folds; six forecasting models; residual-threshold and comparator analysis; automated Python-to-C++ export; compiled-host and physical ESP8266 verification.
4. **Verified results:** compact/ordinary linear equivalence in the case study; complete 933-row prediction and decision agreement; maximum Python/device difference of `8.9e-8` normalized units; measured inference and resource results. Use the corrected Phase 11–14 numbers, not historical values superseded by later measurements.
5. **Boundary:** normalized, provenance-limited data and publisher-derived anomaly labels; no calibrated voltage/current sensing, energy-per-inference measurement, field deployment or validated electrical-fault detection.

Do not use “real-time,” “energy efficient,” “smart-meter hardware,” “field validated,” “first,” or “novel” in the abstract unless later evidence supports the exact phrase.

### Keywords

Suggested: `edge machine learning`, `ESP8266`, `load forecasting`, `hardware-in-the-loop`, `numerical portability`, `TinyML`, `time-series validation`.

Do not include `energy metering` as a keyword because energy was not physically measured.

## 1. Introduction

### 1.1 Motivation

- Explain why local forecasting can reduce dependence on continuous cloud inference and support timely residual monitoring.
- Distinguish electrical metering from computation performed after measurements already exist.
- Avoid generic sustainability claims unless directly cited in Phase 23.

### 1.2 Engineering problem

- A Python model can change numerically when preprocessing, constants, precision and accumulation are transferred to C++.
- Small prediction changes may cross an anomaly threshold even when aggregate MAE changes little.
- Embedded feasibility also depends on timing and separate data-RAM, flash and instruction-RAM constraints.

### 1.3 Research question and hypotheses

- State the central research question verbatim.
- H1: the compact float32 representation will remain practically equivalent to ordinary linear regression under chronological evaluation.
- H2: generated C++ and physical ESP8266 execution will reproduce the frozen software reference within a prespecified tolerance.
- H3: simpler algebraic representations can reduce kernel latency without changing held-out residual decisions.
- Treat H1–H3 as evaluated hypotheses for this case study, not universal claims.

### 1.4 Scope and evidence boundary

- Data: 5,000 half-hourly rows from a Kaggle-hosted, normalized, provenance-limited dataset.
- Device evidence: replay of already prepared held-out feature vectors on a physical ESP8266EX/NodeMCU.
- Explicitly exclude calibrated sensing, mains metering, field operation, energy-per-inference measurement and independent anomaly ground truth.

### 1.5 Paper organization

One short paragraph mapping Sections 2–15. Avoid repeating the contribution list here because Section 3 owns it.

## 2. Related Work

Phase 23 will supply the primary-source citations and gap matrix. This section must be drafted only after that search.

### 2.1 Smart-meter and household-load forecasting

- Chronological evaluation, persistence/seasonal-naive baselines and common regression/sequence models.
- Identify which studies use measured physical-unit datasets and which use normalized or synthetic data.

### 2.2 Residual-based time-series anomaly analysis

- Forecast-residual thresholds, adaptive thresholds, rolling thresholds, prediction intervals and Isolation Forest.
- Separate independently labelled faults from algorithm-generated anomaly labels.

### 2.3 TinyML and constrained edge inference

- Model compression, fixed-point/int8 representations, feature-processing cost and microcontroller resource reporting.

### 2.4 Python-to-device reproducibility and HIL validation

- Find studies reporting full-test-set host/device parity rather than a few demonstrations.
- Record whether they report prediction tolerance, decision mismatch, timing distribution and memory categories.

### 2.5 Literature synthesis

- End with a comparison matrix, not a “no one has done this” assertion.
- The proposed gap is the **joint, auditable evaluation** of chronological forecasting, generated model transfer, complete held-out-vector HIL parity and embedded cost on a highly constrained ESP8266.
- Do not use “first” unless Phase 23 provides unusually strong evidence.

## 3. Research Gap and Contributions

### 3.1 Research gap

Frame the gap as an integration and evidence-quality problem:

- forecasting accuracy is often reported without leakage-aware temporal evaluation;
- deployment is often claimed without numerical parity over the complete held-out set;
- anomaly precision may be reported without recall, threshold sensitivity or label provenance;
- whole-firmware memory and inference timing may be reported without distinguishing measurement boundaries.

### 3.2 Contribution 1 — Leakage-aware temporal evaluation

Six forecasting candidates evaluated with a future holdout and five expanding-window folds using past-only fitting/calibration.

**Does not prove:** cross-household or cross-dataset generalization.

### 3.3 Contribution 2 — Transparent residual-alert analysis

Past-calibrated residual thresholds, threshold sensitivity and comparison with adaptive, rolling, conformal and Isolation Forest methods.

**Does not prove:** real-world electrical anomaly detection because supplied labels are algorithm-derived.

### 3.4 Contribution 3 — Reproducible compact-model export

Fixed feature contract, generated C++ constants, compiled-host verification and explicit float/fixed-point alternatives.

**Does not prove:** that linear regression is a new model.

### 3.5 Contribution 4 — Complete held-out ESP8266 HIL verification

All 933 future held-out vectors tested on the physical device with prediction/decision parity, repeated kernel timing and firmware-resource accounting.

**Does not prove:** sensing accuracy, complete smart-meter latency, low energy, or utility deployment.

## 4. Dataset and Experimental Protocol

### 4.1 Dataset provenance and licensing status

- Report the Kaggle URL, uploader information, local source filename and SHA-256 hash.
- State that the upstream physical source, inverse scaling and redistribution license were not verified.
- Raw data must not be embedded in public artifacts pending license confirmation.

### 4.2 Dataset characteristics

- 5,000 half-hourly rows.
- Timestamp, normalized target, supplied weather/calendar/context columns and supplied anomaly label.
- All forecast errors use **normalized target units**, not verified kWh.

### 4.3 Integrity and preprocessing

- Sort by timestamp and verify monotonicity/duplicates/missingness.
- Construct causal lags 1, 2, 48 and 336.
- Explain why the first 336 rows are lost, leaving 4,664 model-ready rows.
- Exclude `Avg_Past_Consumption` because its construction is undocumented.

### 4.4 Single future holdout

- Training interval: 3,731 rows.
- Future test: 933 rows.
- For the deployed anomaly model, split the 3,731 past rows into 2,984 model-fit and 747 threshold-calibration rows.
- Include exact timestamps from Phase 4 in the split table.

### 4.5 Five-fold rolling-origin protocol

- Five non-overlapping 400-row future test blocks.
- Expanding training sizes of 2,264, 2,664, 3,064, 3,464 and 3,864 rows.
- A 400-row calibration block lies strictly between training and test in every fold.
- Forecast mode is rolling one-step-ahead with lags observed before each timestamp, not a 400-step recursive forecast.

### 4.6 Reproducibility controls

- Stochastic estimator seed 42.
- Record Python, NumPy, pandas and scikit-learn versions.
- Name scripts and immutable result artifacts.
- Preserve split definitions and dataset hash.

## 5. Forecasting Methodology

### 5.1 Forecasting task

Define one-step-ahead prediction of the normalized load target at half-hour resolution.

### 5.2 Naive baselines

- Persistence using lag 1.
- Seasonal naive using lag 48, the same half-hour on the preceding day.

### 5.3 Learned comparison models

- Ordinary linear regression.
- Random forest with the frozen Phase 4/5 hyperparameters.
- Histogram gradient boosting with the frozen Phase 4/5 hyperparameters.
- State that hyperparameters were fixed rather than exhaustively optimized.

### 5.4 Compact edge forecaster

- Eight inputs: lags 1, 2, 48, 336; hour; weekday; month; weekend flag.
- Training-derived mean and scale followed by a linear weighted sum.
- FP32 emulation during walk-forward evaluation.

### 5.5 Forecast metrics

- Primary: MAE and RMSE in normalized units.
- Secondary: sMAPE with a warning that near-zero targets inflate percentage errors.
- Do not report MAPE where zero or near-zero targets make it misleading.

## 6. Anomaly Detection Methodology

### 6.1 Residual definition

Define absolute one-step forecast residual and make clear that the detector operates after the actual target for that timestamp becomes available.

### 6.2 Chronological threshold calibration

- Fit forecaster on 2,984 past rows.
- Derive thresholds from the next 747 past residuals.
- Apply frozen thresholds to 933 later observations.

### 6.3 Threshold sensitivity

Evaluate calibration percentiles 90, 92.5, 95, 97.5, 99 and 99.5. Report precision, recall, F1, confusion counts and alert volume.

### 6.4 Comparator methods

- Static residual p99.
- Adaptive EWMA residual p99.
- Rolling-week residual p99 over 336 preceding residuals.
- Split-conformal 95% interval.
- Isolation Forest with 200 trees, seed 42 and 5% contamination.

### 6.5 Label semantics and selection rule

- Call every metric **agreement with supplied labels**.
- The publisher describes the labels as Isolation Forest outputs, not observed faults.
- Do not select 92.5% using final-test F1; retain p99 as the historical HIL configuration.

## 7. Edge Model Design

### 7.1 Frozen input contract

List feature names, ordering, types and normalization policy. Refer to the generated model manifest rather than manually copying constants into prose.

### 7.2 Standardized FP32 equation

Present:

`y_hat = intercept + Σ[((x_i − mean_i) / scale_i) × coefficient_i]`

### 7.3 Automated export pipeline

- Python training/export script generates the C++ model header.
- The header includes feature metadata, means, scales, coefficients, intercept and residual threshold.
- Validation vectors are generated locally but excluded from public redistribution pending dataset-license confirmation.

### 7.4 Compiled-host verification

Compile an independent C++ executable and compare every prediction/decision with Python before flashing.

### 7.5 Alternative numeric representations

- Standardized FP32.
- Algebraically fused FP32.
- Q15 input/Q30 accumulator fixed point.
- Explain why per-call float-to-fixed conversion can erase the fixed-point kernel advantage.

### 7.6 Model complexity

- Nine trainable parameters.
- Twenty-six stored float32 values including preprocessing state and threshold; 104 bytes.
- Source-level predictor: 8 subtractions, 8 divisions, 8 multiplications and 8 accumulation additions.
- Do not equate source operations with processor cycles.

## 8. ESP8266 Hardware-in-the-Loop Validation

### 8.1 Three-layer evidence architecture

1. Python offline reference.
2. Independently compiled host C++.
3. Physical ESP8266EX/NodeMCU replay.

### 8.2 Hardware and toolchain

- Identify board/chip, Arduino core/toolchain version and build configuration from stored compile evidence.
- Identify COM port only as experimental metadata if useful; do not publish Wi-Fi credentials or API keys.

### 8.3 Full-holdout replay protocol

- Load all 933 prepared feature vectors and reference values into the validation firmware.
- Compare numeric prediction with tolerance `1e-6` normalized units.
- Compare residual-threshold decisions exactly.

### 8.4 Timing protocol

- Thirty physical batches of 2,000 predictions.
- Report distributions of **batch-average model-kernel time**.
- Exclude sensing, feature preparation, networking and end-to-end alert delivery.

### 8.5 Telemetry check

- Report HTTP 200/ThingSpeak records only as communication evidence.
- Do not use telemetry success as proof of forecasting or sensing validity.

### 8.6 Evidence preservation

- Reference raw serial-capture filename and SHA-256 hash.
- Tie compiled firmware resource record to the exact validation build.

## 9. Experimental Results

### 9.1 Single-holdout forecasting results

- Present six-model MAE/RMSE/sMAPE table.
- Compact edge linear MAE `0.130784`; persistence MAE `0.188160`; seasonal-naive MAE `0.183463` normalized units.
- Describe the compact-versus-ordinary-linear difference as tiny, not superior.

### 9.2 Walk-forward forecasting results

- Present fold-level and aggregate results.
- Compact model mean MAE `0.133858 ± 0.004271`; mean RMSE `0.165970 ± 0.004175` across five folds.
- Explain that five folds yield descriptive, imprecise confidence intervals.

### 9.3 Residual-alert results

- Present the complete threshold trade-off.
- At p99: TP 8, FP 0, FN 44, TN 881; precision 1.0, recall 0.153846 and F1 0.266667 against supplied labels.
- At p92.5: observed F1 0.491, but identify this as retrospective and not a valid newly selected deployment threshold.
- Present the five-method comparison without declaring validated real-world detection.

### 9.4 Software and device parity

- Host C++: 933/933 predictions and 933/933 decisions within the specified tolerance.
- Physical ESP8266: 933/933 prediction and decision agreement.
- Maximum Python/device prediction difference: `8.9e-8` normalized units.
- Device MAE `0.130783707`; RMSE `0.162389636` normalized units.

### 9.5 Embedded timing results

- Standardized FP32 physical mean batch-average kernel time: use the exact selected experiment context.
- Main HIL benchmark: mean `50.4271 µs`, median `50.4028 µs`, p5–p95 `50.3646–50.5394 µs` across 30 batch averages.
- Representation comparison: standardized FP32 `50.6268 µs`, fused FP32 `16.3320 µs`, pre-quantized Q15 `8.8462 µs`, and Q15 including input conversion `54.3470 µs`.
- Do not merge the main HIL and representation-comparison captures as if they were one experiment.

## 10. Ablation and Statistical Analysis

### 10.1 Feature-group ablation

- Six prescribed groups: calendar, lag, weather, lag+calendar, lag+weather and all features.
- All mean MAEs lie within `0.00006756` normalized units.
- Weather reduced lag+calendar mean MAE by only 0.0264% and slightly increased RMSE.
- Engineering decision: keep the already verified eight-feature device contract and do not add weather inputs.

### 10.2 Paired forecast comparison

- Moving-block bootstrap with 10,000 replicates and 48-observation blocks.
- DM-style absolute-loss test with Bartlett Newey–West lag 48 and Holm adjustment.
- Compact versus ordinary linear: paired MAE difference approximately `−6.8e-11`, adjusted p `0.745049`; not distinguishable.
- Compact versus random forest: 1.019% lower MAE, adjusted p `0.034530`; statistically distinguishable under the specified assumptions but small.
- Compact versus naive baselines: larger differences under the prespecified procedure.

### 10.3 Statistical limitations

- Temporal dependence remains.
- Training histories overlap.
- Daily block/HAC length is a design choice.
- Asymptotic p-values may be optimistic for the short series.
- Statistical significance in one normalized dataset is not external validity.

## 11. Embedded Resource Analysis

### 11.1 Whole-firmware resource use

- Benchmark-ready normal firmware: data RAM `29,516/80,192 B` (36.81%), IRAM `60,343/65,536 B` (92.08%), flash code `257,796/1,048,576 B` (24.59%).
- Full-validation firmware: data RAM `29,852/80,192 B` (37.23%), IRAM `60,343/65,536 B` (92.08%), flash code `298,132/1,048,576 B` (28.43%).
- State exactly which build accompanies each HIL result.

### 11.2 Model state versus firmware footprint

Separate 104 bytes of core numeric model state from linked firmware, networking code, buffers and validation payload.

### 11.3 IRAM as the integration constraint

- Only 5,193 instruction-RAM bytes remain.
- Discuss likely competition from TLS, sensor drivers, DSP and interrupt-resident routines without predicting unmeasured memory use.

### 11.4 Representation trade-off

- Fused FP32 is the current deployment recommendation because it gives a measured speedup without requiring a fixed-point acquisition/history pipeline.
- Q15 is conditional on inputs already being maintained in fixed point.

## 12. Discussion

### 12.1 Answer to the research question

The compact computation was transferred reproducibly for the complete held-out-vector replay, with negligible numerical deviation and no threshold-decision mismatch. This answers numerical portability and model-kernel feasibility for the tested firmware, not complete smart-meter feasibility.

### 12.2 Accuracy–deployability trade-off

- The compact linear model matched ordinary linear behavior while using transparent, small state.
- More complex tree models did not improve the tested case sufficiently to justify their added deployment complexity.

### 12.3 Threshold behavior

- High precision at p99 hides poor recall.
- Operating-point selection requires independent ground truth and application-specific error costs.

### 12.4 What HIL parity means

- Strong evidence: faithful execution of frozen preprocessing/model/threshold logic.
- Missing evidence: sensor acquisition, calibration, feature-buffer maintenance under live sampling, end-to-end timing and field robustness.

### 12.5 Practical integration implication

The simple predictor is not the main memory problem; IRAM headroom and future sensing/networking software are the key integration risks.

## 13. Limitations

### 13.1 Dataset provenance, units and representativeness

- Upstream creator and physical collection procedure are not verified.
- Numeric values are normalized without inverse-scaling metadata.
- The 104-day span and one dataset do not support annual or cross-household conclusions.

### 13.2 Anomaly ground truth

Supplied labels are publisher-described Isolation Forest outputs and cannot establish electrical faults, fraud, unsafe behavior or meter malfunction.

### 13.3 HIL replay versus live sensing

Held-out vectors were embedded/replayed. The ESP8266 did not acquire calibrated voltage or current and was not validated as a smart meter.

### 13.4 Timing boundary

The reported microseconds measure batch-average model-kernel time, not sensing-to-alert latency.

### 13.5 Energy boundary

No measured energy per inference or average system power is available. Datasheet arithmetic, if mentioned, remains a non-result sensitivity estimate.

### 13.6 Statistical and external-validity limits

Five overlapping expanding folds and one dataset limit uncertainty interpretation; no official-dataset replication is complete.

## 14. Future Work

### 14.1 Official measured-data replication

Repeat the complete pipeline on UCI Individual Household Electric Power Consumption and/or REFIT, using confirmed licenses, physical units and immutable dataset versions. Mark all related values `[RESULT TO BE COMPUTED]` until run.

### 14.2 Physical sensing system

Follow the Phase 16 protocol: isolated voltage/current sensing, reviewed conditioning/protection, simultaneous ADC, calibrated reference instrument, known-load experiments and uncertainty analysis. Do not imply that buying one resistor completes this requirement.

### 14.3 Energy measurement

Use a suitable power profiler with GPIO timing markers and repeated long inference batches. Report the complete measurement boundary and uncertainty budget.

### 14.4 Independent anomaly validation

Evaluate locked thresholds on independently annotated anomalies such as the DOI-backed REFIT anomaly resource, with application costs specified before test evaluation.

### 14.5 Full sensing-to-decision integration

Measure acquisition, DSP/feature preparation, inference, communication and idle/duty-cycle components separately before making real-time or low-power claims.

## 15. Conclusion

Use one compact paragraph:

1. Restate the narrow problem: reproducible transfer of a compact forecasting/residual computation.
2. Report complete 933-row prediction and decision agreement, maximum numerical difference, selected latency result and principal resource constraint.
3. State that fused FP32 was the practical representation selected from the measured comparison.
4. Close with the exact boundary: computational HIL feasibility was demonstrated; calibrated smart-meter sensing and real-world anomaly validity remain future work.

Do not introduce new citations, methods, numbers or claims in the conclusion.

## Evidence-to-section map

| Paper section | Primary local evidence | Status |
|---|---|---|
| 1, 3 | `docs/PHASE_1_RESEARCH_QUESTIONS.md`, `docs/PHASE_2_DEFENSIBLE_CONTRIBUTIONS.md` | Verified framing |
| 2 | Phase 23 literature search | Not yet complete |
| 4 | `docs/PHASE_3_DATASET_VALIDATION.md`, `outputs/dataset_integrity.json` | Verified with provenance limitations |
| 5, 9.1 | `docs/PHASE_4_FORECASTING_BASELINES.md` | Complete for normalized case study |
| 4.5, 9.2 | `docs/PHASE_5_WALK_FORWARD_VALIDATION.md` | Complete for normalized case study |
| 10.2 | `docs/PHASE_6_STATISTICAL_COMPARISON.md` | Complete under stated assumptions |
| 10.1 | `docs/PHASE_7_FEATURE_ABLATION.md` | Complete for linear model |
| 6.3, 9.3 | `docs/PHASE_8_THRESHOLD_SENSITIVITY.md` | Complete; supplied-label agreement only |
| 6.4, 9.3 | `docs/PHASE_9_ANOMALY_METHODS.md` | Complete; supplied-label agreement only |
| 7 | `docs/PHASE_10_EDGE_MODEL_EXPORT.md`, `docs/PHASE_14_QUANTIZATION.md` | Complete |
| 8, 9.4 | `docs/PHASE_11_HIL_VALIDATION.md` | Complete physical held-out replay |
| 8.4, 9.5 | `docs/PHASE_12_EMBEDDED_TIMING.md` | Complete for model-kernel timing |
| 11 | `docs/PHASE_13_RESOURCE_ANALYSIS.md`, `docs/PHASE_14_QUANTIZATION.md` | Complete |
| 13.5, 14.3 | `docs/PHASE_15_ENERGY_MEASUREMENT_PROTOCOL.md` | Future protocol; no measured result |
| 13.3, 14.2 | `docs/PHASE_16_PHYSICAL_SENSING_PROTOCOL.md` | Future protocol; no sensing result |

## Recommended writing order

Write Sections 4–11 first because their evidence is already fixed. Then write Sections 12–15. Write Sections 1 and 3 after the results are stable. Write Section 2 after Phase 23, and write the abstract last. This order reduces the chance that the introduction or abstract promises more than the evidence supports.

## Phase decision

The manuscript now has a complete 15-section conference-paper topology with explicit evidence ownership and claim boundaries. Phase 21 should design the required figures, determine which belong in the main paper versus supplementary material, and regenerate any figure whose current labeling could imply physical kWh or real anomaly ground truth.

