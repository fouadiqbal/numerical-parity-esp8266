# Research Project State

Last updated: 2026-09-03  
Current milestone: **Phase 27 complete; GitHub publication is pending confirmation**

## Research boundary

This project evaluates a smart-meter dataset in Python, exports a compact standardized linear model, and verifies that the exported computation runs consistently on a physical ESP8266EX/NodeMCU. It does **not** yet include calibrated voltage/current sensing, mains-energy measurement, sensor calibration, a field trial, or measured energy per inference.

## Verified evidence

| Evidence | Verified value |
|---|---:|
| Dataset rows used | 5,000 half-hourly rows |
| Complete future held-out set | 933 rows |
| Python/device prediction agreement | 933/933 |
| Python/device threshold-decision agreement | 933/933 |
| Maximum absolute prediction difference | 0.000000089 normalized target units |
| Device-side edge-model MAE | 0.130783707 normalized target units |
| Device-side edge-model RMSE | 0.162389636 normalized target units |
| Supplied-label confusion matrix | TP 8, FP 0, FN 44, TN 881 |
| Precision / recall / F1 | 1.000000 / 0.153846 / 0.266667 |
| Physical timing batches | 30 batches × 2,000 predictions |
| Mean batch-average pure-inference time | 50.427 microseconds |
| Batch-average p5 / p95 | 50.365 / 50.539 microseconds |
| Full validation-loop elapsed time | 60,122 microseconds |
| Normal firmware resources | RAM 36%, flash 24%, IRAM 92% |
| Validation firmware resources | RAM 37%, flash 28%, IRAM 92% |
| Telemetry evidence | Five HTTP 200 records; ThingSpeak entries 386–390 during capture |

## Important files

- Notebook: `smart_meter_energy_load_forecasting.ipynb`
- Training/export: `tools/train_tinyml_edge_model.py`
- Build/upload workflow: `tools/esp8266_workflow.ps1`
- Firmware: `firmware/esp8266_smart_meter/esp8266_smart_meter.ino`
- Generated edge model: `firmware/esp8266_smart_meter/tinyml_model.h`
- Benchmark evidence: `outputs/tinyml_device_benchmark.json`
- Corrected physical benchmark: `outputs/tinyml_device_benchmark_v2.json`
- Raw physical capture: `data/esp8266/esp8266_serial_20260903_025705.jsonl` (local/ignored)
- Corrected edge metrics: `outputs/tinyml_edge_metrics_v2.json`
- Model manifest: `outputs/tinyml_model_manifest.json`
- Compiled-host parity evidence: `outputs/tinyml_cpp_parity.json`
- Firmware compile evidence: `outputs/phase10_firmware_builds.json`
- HIL report: `outputs/tinyml_hardware_in_loop_validation.md`
- Local prediction table: `outputs/tinyml_edge_test_predictions.csv`
- Current manuscript: `../outputs/smart_meter_energy_manuscript_esp8266_updated.docx`
- Phase 0 audit: `docs/PHASE_0_MANUSCRIPT_AUDIT.md`
- Phase 1 research questions: `docs/PHASE_1_RESEARCH_QUESTIONS.md`
- Phase 2 contributions: `docs/PHASE_2_DEFENSIBLE_CONTRIBUTIONS.md`
- Phase 3 dataset validation: `docs/PHASE_3_DATASET_VALIDATION.md`
- Dataset integrity evidence: `outputs/dataset_integrity.json`
- Phase 4 forecasting baselines: `docs/PHASE_4_FORECASTING_BASELINES.md`
- Phase 4 machine-readable results: `outputs/phase4_forecasting_results.json`
- Phase 5 walk-forward report: `docs/PHASE_5_WALK_FORWARD_VALIDATION.md`
- Phase 5 machine-readable results: `outputs/phase5_walk_forward_results.json`
- Phase 6 statistical report: `docs/PHASE_6_STATISTICAL_COMPARISON.md`
- Phase 6 machine-readable results: `outputs/phase6_statistical_comparison.json`
- Phase 7 ablation report: `docs/PHASE_7_FEATURE_ABLATION.md`
- Phase 7 machine-readable results: `outputs/phase7_feature_ablation.json`
- Phase 8 threshold report: `docs/PHASE_8_THRESHOLD_SENSITIVITY.md`
- Phase 8 machine-readable results: `outputs/phase8_threshold_sensitivity.json`
- Phase 9 anomaly-method report: `docs/PHASE_9_ANOMALY_METHODS.md`
- Phase 9 machine-readable results: `outputs/phase9_anomaly_methods.json`
- Phase 10 export report: `docs/PHASE_10_EDGE_MODEL_EXPORT.md`
- Phase 11 HIL evidence report: `docs/PHASE_11_HIL_VALIDATION.md`
- Phase 11 machine-readable audit: `outputs/phase11_hil_evidence_layers.json`
- Phase 12 timing report: `docs/PHASE_12_EMBEDDED_TIMING.md`
- Phase 12 timing analysis: `outputs/phase12_timing_analysis.json`
- Phase 12 physical distribution: `outputs/phase12_device_timing_distribution.json`
- Benchmark-ready build record: `outputs/phase12_benchmark_ready_builds.json`
- Phase 13 resource report: `docs/PHASE_13_RESOURCE_ANALYSIS.md`
- Phase 13 resource evidence: `outputs/phase13_resource_analysis.json`
- Phase 14 quantization report: `docs/PHASE_14_QUANTIZATION.md`
- Phase 14 offline comparison: `outputs/phase14_quantization_results.json`
- Phase 14 physical comparison: `outputs/phase14_device_quantization.json`
- Generated fused FP32 model: `firmware/esp8266_smart_meter/tinyml_fused_model.h`
- Generated Q15/Q30 model: `firmware/esp8266_smart_meter/tinyml_fixed_model.h`
- Phase 15 energy protocol: `docs/PHASE_15_ENERGY_MEASUREMENT_PROTOCOL.md`
- Phase 15 machine-readable protocol: `outputs/phase15_energy_measurement_protocol.json`
- Phase 16 sensing protocol: `docs/PHASE_16_PHYSICAL_SENSING_PROTOCOL.md`
- Phase 16 machine-readable protocol: `outputs/phase16_physical_sensing_protocol.json`
- Phase 17 dataset research: `docs/PHASE_17_DATASET_RESEARCH.md`
- Phase 17 machine-readable shortlist: `outputs/phase17_dataset_shortlist.json`
- Phase 18 edge-generative-AI assessment: `docs/PHASE_18_EDGE_GENERATIVE_AI.md`
- Phase 18 machine-readable assessment: `outputs/phase18_edge_ai_assessment.json`
- Phase 19 next-project ranking: `docs/PHASE_19_NEXT_PROJECT_RANKING.md`
- Phase 19 machine-readable ranking: `outputs/phase19_project_ranking.json`
- Phase 20 paper structure: `docs/PHASE_20_PAPER_STRUCTURE.md`
- Phase 20 machine-readable structure: `outputs/phase20_paper_structure.json`
- Phase 21 figure plan and captions: `docs/PHASE_21_FIGURES.md`
- Phase 21 reproducible figure generator: `tools/run_phase21_figures.py`
- Phase 21 figure manifest and hashes: `outputs/phase21_figure_manifest.json`
- Phase 21 generated publication figures: `figures/fig01_*.{png,pdf,svg}` through `figures/fig10_*.{png,pdf,svg}`
- Phase 22 table report: `docs/PHASE_22_TABLES.md`
- Phase 22 reproducible table generator: `tools/run_phase22_tables.py`
- Phase 22 table manifest and hashes: `outputs/phase22_table_manifest.json`
- Phase 22 publication tables: `tables/publication_tables.{md,tex}` and `tables/table01_*.csv` through `tables/table11_*.csv`
- Phase 23 gap-analysis report: `docs/PHASE_23_RELATED_WORK.md`
- Phase 23 reproducible literature-artifact generator: `tools/run_phase23_related_work.py`
- Phase 23 machine-readable evidence: `outputs/phase23_related_work.json`
- Phase 23 study matrix: `tables/phase23_related_work_matrix.csv`
- Phase 23 bibliography: `references/references.bib`
- Phase 24 copyright/licensing report: `docs/PHASE_24_COPYRIGHT_LICENSING.md`
- Phase 24 machine-readable audit: `outputs/phase24_licensing_audit.json`
- Phase 24 reproducible audit generator: `tools/run_phase24_copyright_audit.py`
- Third-party rights notice: `THIRD_PARTY_NOTICES.md`
- Phase 25 package report: `docs/PHASE_25_REPRODUCIBILITY_PACKAGE.md`
- Phase 25 package builder: `tools/build_phase25_reproducibility_package.py`
- Clean staged repository: `release/smart-meter-esp8266-reproducibility/`
- Reproducibility manifest: `release/smart-meter-esp8266-reproducibility/REPRODUCIBILITY_MANIFEST.json`
- Phase 25 package validation evidence: `outputs/phase25_package_validation.json`
- Phase 26 final claims audit: `docs/PHASE_26_FINAL_CLAIMS_AUDIT.md`
- Phase 26 machine-readable audit: `outputs/phase26_claims_audit.json`
- Phase 27 final-paper report: `docs/PHASE_27_FINAL_PAPER.md`
- Phase 27 LaTeX source: `manuscript/smart_meter_esp8266_edge_ml.tex`
- Phase 27 compiled paper: `manuscript/smart_meter_esp8266_edge_ml.pdf`
- Phase 27 validation record: `outputs/phase27_final_paper_validation.json`

## Files that must remain private or regenerated

- `firmware/esp8266_smart_meter/tinyml_validation_data.h` contains dataset-derived held-out rows. It is intentionally ignored by Git pending dataset-license confirmation.
- Wi-Fi SSIDs, passwords, ThingSpeak keys, personal access tokens, and other credentials must never be committed.
- Raw dataset files should not be redistributed until the license and provenance audit is complete.

## Reproduction commands

From the repository root:

```powershell
python tools/train_tinyml_edge_model.py
python tools/test_generated_cpp_model.py
python tools/run_phase11_hil_evidence_audit.py
python tools/run_phase12_timing_analysis.py
python tools/run_phase13_resource_analysis.py
python tools/run_phase22_tables.py
python tools/run_phase23_related_work.py
python tools/run_phase24_copyright_audit.py
python tools/build_phase25_reproducibility_package.py
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Build
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Build -FullValidation
```

The full-validation command requires the locally regenerated `tinyml_validation_data.h`. Hardware upload additionally requires the correct board connection and COM port.

## Pending external action

The public GitHub repository was cloned into `tmp/github-publish-esp8266`, but the new ESP8266 package has **not** been copied, committed, or pushed in this phase. Publication remains paused until the phase-by-phase work reaches an appropriate confirmed milestone.

## Selected research-question hierarchy

- **Primary:** numerical portability and measured embedded cost of transferring a leakage-aware compact forecasting model from Python to C++ on ESP8266.
- **Supporting:** forecasting accuracy versus deployability under stronger temporal evaluation.
- **Supporting:** threshold sensitivity and decision reproducibility against supplied, unverified anomaly labels.

## Selected contribution set

1. Leakage-aware temporal evaluation.
2. Transparent residual anomaly analysis against supplied labels.
3. Reproducible compact-model export from Python to C++.
4. Complete 933-row ESP8266 HIL verification with numerical, timing, and resource evidence.

## Phase 3 dataset decision

- The current Kaggle file is retained as a normalized development/HIL-parity case study.
- Its physical kWh and weather units cannot be verified because every numeric column is scaled approximately from 0 to 1 and inverse-scaling metadata is absent.
- It must not remain the paper's only primary scientific dataset.
- UCI Individual Household Electric Power Consumption is preferred for forecasting.
- REFIT and its annotated anomaly extension are preferred for measured multi-household and anomaly experiments.

## Next action

Publish the audited reproducibility package to GitHub after final action-time confirmation, then verify the public repository layout, links, rendered manuscript, and research-profile presentation. Hardware sensing and ESP32 field-validation results remain future experimental work.
