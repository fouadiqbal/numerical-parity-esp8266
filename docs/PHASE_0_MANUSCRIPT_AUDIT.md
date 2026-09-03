# Phase 0 — Current Manuscript Audit

Status: **complete as an audit; no new experimental result is claimed**  
Audited manuscript: `outputs/smart_meter_energy_manuscript_esp8266_updated.docx`  
Audit date: 2026-09-03

## Claim labels

- `[VERIFIED]`: directly supported by retained code, output files, serial evidence, or the current manuscript.
- `[SUPPORTED BUT LIMITED]`: supported only inside the stated dataset, split, device, or test conditions.
- `[NEEDS EXPERIMENT]`: plausible, but a new experiment is required.
- `[UNSUPPORTED]`: not demonstrated by the current evidence.
- `[SHOULD BE REMOVED]`: wording that would materially misrepresent the work.

## A. Current contributions

1. `[VERIFIED]` A leakage-aware, chronological workflow was used instead of a random train/test split. Lagged rows are formed before an 80/20 chronological division, and threshold calibration is confined to earlier training data.
2. `[SUPPORTED BUT LIMITED]` Persistence, linear regression, random forest, forecast-residual anomaly detection, and Isolation Forest were compared on one Kaggle dataset and one future holdout.
3. `[VERIFIED]` A separate compact deployment model—standardized linear regression—was exported as C++ constants for ESP8266 inference.
4. `[VERIFIED]` All 933 held-out feature vectors were replayed on a physical ESP8266EX/NodeMCU, providing complete held-out-set hardware-in-the-loop (HIL) coverage.
5. `[VERIFIED]` The device matched the stored Python reference for all 933 predictions and all 933 threshold decisions; maximum absolute prediction difference was 0.000000089 normalized target units. Phase 3 established that physical kWh cannot be verified from the scaled source file.
6. `[SUPPORTED BUT LIMITED]` Three complete benchmark passes produced pure-model mean inference times of 50.840, 50.730, and 50.683 microseconds (mean 50.751 microseconds). Three runs demonstrate repeatability only weakly; they are not a latency distribution.
7. `[VERIFIED]` The measured firmware builds reported 36% dynamic RAM, 24% flash, and 92% IRAM for the normal build, and 36% RAM, 28% flash, and 92% IRAM for the full-validation build.
8. `[SUPPORTED BUT LIMITED]` ThingSpeak HTTP 200 responses and entry numbers after validation show that the existing telemetry path remained functional. They do not establish secure, reliable, or long-term deployment.

## B. Claimed contributions versus defensible wording

| Topic | Defensible current claim | Classification |
|---|---|---|
| Forecasting | The notebook evaluates several forecasting baselines on one chronological holdout. | `[SUPPORTED BUT LIMITED]` |
| Anomaly analysis | Residual and Isolation Forest decisions are compared with supplied labels. | `[SUPPORTED BUT LIMITED]` |
| Edge deployment | A compact linear forecasting computation was exported to and executed on ESP8266. | `[VERIFIED]` |
| Numerical portability | ESP8266 reproduced the stored software reference across 933 held-out vectors within the stated tolerance. | `[VERIFIED]` |
| Embedded feasibility | The tested computation fits and runs in the measured firmware configuration. | `[SUPPORTED BUT LIMITED]` |
| Smart-meter prototype | A calibrated electrical smart meter was built and validated. | `[SHOULD BE REMOVED]` |
| Real-world anomaly detection | The system detects genuine electrical anomalies in the field. | `[UNSUPPORTED]` |

## C. Experimentally supported contributions

- `[VERIFIED]` Dataset size used by the notebook: 5,000 half-hourly rows.
- `[VERIFIED]` Complete future held-out HIL set: 933 rows.
- `[VERIFIED]` Python/device prediction agreement: 933/933.
- `[VERIFIED]` Python/device anomaly-decision agreement: 933/933.
- `[VERIFIED]` Maximum absolute numerical difference: 0.000000089 normalized target units.
- `[VERIFIED]` Device-side edge-model forecasting metrics: MAE 0.130783707 and RMSE 0.162389636 in normalized target units on the 933-row test set.
- `[VERIFIED]` Supplied-label confusion matrix for the deployed threshold: TP 8, FP 0, FN 44, TN 881; precision 1.000000, recall 0.153846, F1 0.266667.
- `[VERIFIED]` Three whole-test inference runs: 50.840, 50.730, and 50.683 microseconds per prediction; mean 50.751 microseconds.
- `[VERIFIED]` Full validation loop elapsed time: 60,141 microseconds, distinct from the pure per-inference benchmark.
- `[VERIFIED]` No multimeter, calibrated energy sensor, complete sensing circuit, or mains-energy measurement was used.

The anomaly metrics above measure agreement with dataset-provided labels. They do not validate the physical or semantic correctness of those labels.

## D. Unsupported or hazardous claims

| Claim | Classification | Required correction |
|---|---|---|
| “A validated ESP8266 smart meter” | `[SHOULD BE REMOVED]` | Use “ESP8266 hardware-in-the-loop inference validation.” |
| “Real-time smart-meter operation” | `[UNSUPPORTED]` | The measured inference kernel is fast, but sensing, preprocessing, networking, and scheduling were not benchmarked end to end. |
| “Accurate anomaly detection” | `[SHOULD BE REMOVED]` | Recall is 0.154 at the deployed threshold and label provenance is unverified. |
| “Field validated” or “utility ready” | `[SHOULD BE REMOVED]` | No field trial or utility deployment occurred. |
| “Energy efficient” or “low power” | `[NEEDS EXPERIMENT]` | Current and energy per inference were not measured. |
| “Secure IoT telemetry” | `[UNSUPPORTED]` | HTTP success was observed; security and TLS were not evaluated. |
| “Sensor accuracy” or “calibrated ADC” | `[SHOULD BE REMOVED]` | No calibrated electrical sensor or reference instrument was used. |
| “Generalizable forecasting performance” | `[UNSUPPORTED]` | One dataset and one holdout are insufficient. |
| “First” or “novel algorithm” | `[UNSUPPORTED]` | A structured peer-reviewed literature search has not yet established this. |

## E. Likely reviewer criticisms

1. **Dataset provenance is weak.** `[NEEDS EXPERIMENT]` The Kaggle page alone does not establish the primary data source, collection procedure, label-generation mechanism, or publication license.
2. **The temporal evaluation is too narrow.** `[SUPPORTED BUT LIMITED]` A single chronological holdout is better than random splitting, but does not establish performance across seasons or operating regimes.
3. **Statistical evidence is missing.** `[NEEDS EXPERIMENT]` There are no rolling-origin folds, confidence intervals, paired tests, or forecast-error uncertainty estimates.
4. **Baselines are incomplete.** `[NEEDS EXPERIMENT]` A seasonal-naive lag-48 baseline and a stronger boosting model are absent.
5. **Feature value is unknown.** `[NEEDS EXPERIMENT]` No ablation establishes whether weather, calendar, or lag groups add useful information.
6. **The anomaly threshold is conservative and under-justified.** `[VERIFIED]` It yields 8 true positives and 44 false negatives against the supplied labels; threshold sensitivity has not been studied.
7. **Labels may not represent genuine electrical anomalies.** `[SUPPORTED BUT LIMITED]` The current experiment tests agreement with supplied labels only.
8. **HIL replay is not online sensing.** `[VERIFIED]` Stored test vectors validate arithmetic portability and device execution, not sensor acquisition, calibration, or real-world timing.
9. **Latency evidence is too small.** `[NEEDS EXPERIMENT]` Three aggregate passes do not support median, standard deviation, tail latency, or component-level timing claims.
10. **IRAM headroom is tight.** `[SUPPORTED BUT LIMITED]` Reported 92% IRAM use may constrain TLS, drivers, buffering, and larger models.
11. **Telemetry is not a security study.** `[SUPPORTED BUT LIMITED]` Successful HTTP writes do not demonstrate confidentiality, authentication robustness, availability, or long-duration reliability.
12. **The related-work section is underdeveloped.** `[NEEDS EXPERIMENT]` The current reference set is not enough to substantiate a research gap.

## F. Novelty assessment

- `[UNSUPPORTED]` Linear regression, random forest, residual thresholding, Isolation Forest, and persistence forecasting are not new algorithms.
- `[SUPPORTED BUT LIMITED]` The strongest current contribution is the reproducible engineering chain from a chronological Python pipeline to generated C++ constants and complete 933-row physical-device replay with numerical and decision parity.
- `[NEEDS EXPERIMENT]` Whether that combination is sufficiently distinctive for a particular conference must be established by the Phase 23 literature-gap analysis.
- `[SUPPORTED BUT LIMITED]` The work can be positioned as a reproducibility and constrained-deployment study, not as a new smart-meter sensing platform or anomaly algorithm.

## G. Dataset weaknesses

- `[VERIFIED]` The working data came from the Kaggle dataset published by account `ziya07` and contains 5,000 half-hourly records.
- `[NEEDS EXPERIMENT]` The primary creator, original collection system, exact provenance, license, and anomaly-label construction must be confirmed from authoritative sources.
- `[SUPPORTED BUT LIMITED]` Roughly 104 days of half-hourly data cannot represent all annual seasons.
- `[NEEDS EXPERIMENT]` Data integrity checks should record timestamp coverage, duplicates, missing intervals, value ranges, and a cryptographic file hash.
- `[NEEDS EXPERIMENT]` Publication permission for redistributed rows, including the generated full-validation header, must be established. Until then, dataset-derived test vectors must remain uncommitted.
- `[UNSUPPORTED]` Supplied anomaly labels should not be treated as independently verified physical events.

## H. Statistical weaknesses

- `[SUPPORTED BUT LIMITED]` Results currently depend on one 80/20 chronological split.
- `[NEEDS EXPERIMENT]` Four or five rolling-origin folds are needed to estimate temporal variability.
- `[NEEDS EXPERIMENT]` Forecast metrics need fold means, standard deviations, and confidence intervals.
- `[NEEDS EXPERIMENT]` Paired error comparisons or a suitable time-series test are required before describing small model differences as meaningful.
- `[NEEDS EXPERIMENT]` Feature-group ablation is required.
- `[NEEDS EXPERIMENT]` Anomaly threshold sensitivity and alternative adaptive thresholds are required.
- `[SUPPORTED BUT LIMITED]` Only 52 supplied positives occur in the 933-row test set, so precision/recall estimates are sensitive to a small number of decisions.

## I. Hardware-validation strengths

- `[VERIFIED]` Validation ran on a physical ESP8266EX/NodeMCU rather than only in a simulator.
- `[VERIFIED]` Every held-out vector was evaluated, not a hand-selected subset.
- `[VERIFIED]` Both continuous predictions and binary threshold decisions were checked.
- `[VERIFIED]` Numerical error was bounded and reported rather than described qualitatively.
- `[VERIFIED]` Build-time RAM, flash, and IRAM values were recorded for normal and validation firmware.
- `[SUPPORTED BUT LIMITED]` ThingSpeak responses confirm post-validation communication in the observed runs.
- `[VERIFIED]` The manuscript separates HIL computation from calibrated electrical sensing.

## J. Copyright and licensing concerns

- `[NEEDS EXPERIMENT]` Confirm the Kaggle dataset license and trace the original creator before distributing the data or dataset-derived validation vectors.
- `[VERIFIED]` The repository code is intended to be distributed under its included MIT license; this does not relicense third-party data.
- `[SUPPORTED BUT LIMITED]` Original plots generated from the analysis can normally be used as author-created figures, but the underlying dataset still requires correct attribution and license compliance.
- `[SHOULD BE REMOVED]` Do not copy figures, diagrams, screenshots, or substantial text from other papers without permission or a license basis; redraw concepts and cite sources.
- `[NEEDS EXPERIMENT]` Complete a citation, license, and text-similarity audit before submission.

## K. Reproducibility weaknesses

- `[NEEDS EXPERIMENT]` Record the exact dataset URL, version/download date, license, and SHA-256 hash.
- `[NEEDS EXPERIMENT]` Pin exact Python package versions and provide an environment file.
- `[SUPPORTED BUT LIMITED]` The training/export script improves reproducibility, but the complete experiment is not yet automated from raw data to every paper table and figure.
- `[NEEDS EXPERIMENT]` Add an automated host-side Python-versus-generated-C++ test before flashing hardware.
- `[NEEDS EXPERIMENT]` Record split indices and threshold-calibration boundaries in machine-readable metadata.
- `[SUPPORTED BUT LIMITED]` The current firmware workflow is Windows/COM-port oriented; document Arduino CLI setup and add platform-neutral instructions where practical.
- `[VERIFIED]` Wi-Fi and ThingSpeak credentials must remain placeholders or local secrets and must never be committed.
- `[VERIFIED]` The dataset-derived `tinyml_validation_data.h` is ignored by Git and should be regenerated locally until redistribution rights are verified.
- `[NEEDS EXPERIMENT]` Preserve raw serial logs, firmware/toolchain versions, board definition, and commands for each reported hardware benchmark.

## L. Missing experiments, in priority order

1. `[NEEDS EXPERIMENT]` Dataset provenance, license, integrity, and label audit.
2. `[NEEDS EXPERIMENT]` Seasonal-naive lag-48 and gradient-boosting baselines.
3. `[NEEDS EXPERIMENT]` Four-to-five-fold rolling-origin validation.
4. `[NEEDS EXPERIMENT]` Confidence intervals and paired forecast-error comparison.
5. `[NEEDS EXPERIMENT]` Feature-group ablation.
6. `[NEEDS EXPERIMENT]` Residual-threshold sensitivity and alert-count analysis.
7. `[NEEDS EXPERIMENT]` Adaptive/rolling residual and prediction-interval comparisons.
8. `[NEEDS EXPERIMENT]` Automated Python-to-C++ software-reference test separated from HIL replay.
9. `[NEEDS EXPERIMENT]` Larger repeated timing study with mean, median, standard deviation, minimum, maximum, and percentiles.
10. `[NEEDS EXPERIMENT]` Timing decomposition for preprocessing, inference, acquisition, and communication.
11. `[NEEDS EXPERIMENT]` Parameter count, arithmetic-operation count, constant-storage size, and IRAM-headroom discussion.
12. `[NEEDS EXPERIMENT]` FP32 versus an appropriate fixed-point/reduced-precision engineering comparison.
13. `[NEEDS EXPERIMENT]` Real sensing and energy measurement remain future protocols until safe isolated hardware and reference instruments are available.

## Phase 0 decision

The project has a defensible conference-paper core: reproducible transfer and complete held-out-set HIL verification of a compact forecasting computation on ESP8266. It is **not yet conference-ready** because dataset provenance, multi-fold temporal evaluation, statistical analysis, anomaly-threshold analysis, literature-gap evidence, and a complete reproducibility package remain unfinished.

The next authorized milestone is **Phase 1 — redefine the research question**. No Phase 1 wording should be treated as final until the user confirms Phase 0.
