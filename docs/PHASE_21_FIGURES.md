# Phase 21 — Publication Figure Set

Date: 2026-09-03  
Status: complete with one explicitly interim figure

## Outcome

Ten consistently styled scientific figures were generated from the verified Phase 4–14 artifacts. Each is available as 300-dpi PNG plus vector PDF and SVG in `figures/`. No external images, screenshots, logos or third-party artwork were used.

Figure 8 is intentionally **not** called a prediction-error distribution. The physical ESP8266 capture retained complete match counts and the maximum absolute difference, but not all 933 per-vector device differences. The generated Figure 8 shows only the evidence actually stored. A true distribution requires a new instrumented physical capture.

## Figure plan

### Figure 1 — Complete cloud-to-edge architecture

**Scientific question:** Which parts of the proposed system were actually implemented, and which sensing components remain future work?

**Answer shown:** The solid path covers normalized dataset processing, chronological modelling, generated C++, ESP8266 held-out-vector replay and a telemetry connectivity check. Isolated calibrated voltage/current sensing appears as a dashed future path.

**Suggested caption:**

> Implemented computation and future sensing architecture. Solid boxes indicate evidence produced in the reported experiments. The physical ESP8266 replayed prepared held-out feature vectors and completed a separate HTTP telemetry check. The dashed red sensing path was not implemented; therefore the experiment does not constitute calibrated smart-meter measurement.

**Placement:** Main paper, near the end of the Introduction or start of Methodology.

**Files:** `fig01_cloud_to_edge_architecture.{png,pdf,svg}`

### Figure 2 — Chronological walk-forward protocol

**Scientific question:** Does the evaluation preserve training → calibration → future-test order across every fold?

**Answer shown:** Five expanding training histories are followed by a distinct 400-row calibration interval and a non-overlapping 400-row future test interval.

**Suggested caption:**

> Five-fold expanding-window protocol. In each fold, model fitting uses only the blue past interval, threshold calibration uses the subsequent orange interval, and evaluation uses the later green interval. The 2,000 test predictions are non-overlapping across folds.

**Placement:** Main paper, Dataset and Experimental Protocol.

**Files:** `fig02_walk_forward_protocol.{png,pdf,svg}`

### Figure 3 — Forecasting model comparison

**Scientific question:** Does the compact float32 model retain the forecasting behavior of ordinary linear regression, and how does it compare with the prespecified baselines?

**Answer shown:** The two linear models have nearly identical five-fold mean MAE and lower mean MAE than the tested tree and naive models.

**Suggested caption:**

> Mean MAE across five expanding-window folds for six forecasting candidates. Error bars are descriptive 95% Student-t intervals over five fold-level MAEs. Values are normalized target units; physical kWh was not recoverable. Overlapping intervals are not used as a significance test.

**Placement:** Main paper, Experimental Results.

**Files:** `fig03_forecasting_model_comparison.{png,pdf,svg}`

### Figure 4 — Feature ablation

**Scientific question:** Do lag, calendar or supplied weather variables produce a consistent practical forecasting gain?

**Answer shown:** Paired fold differences are small and change direction. The mean differences are tiny relative to fold-to-fold variation.

**Suggested caption:**

> Paired fold-level MAE difference between each feature group and the complete lag+calendar+weather group. Grey points/lines show individual folds and blue diamonds show mean paired differences. The narrow magnitude and inconsistent direction do not justify adding weather-input complexity to the deployed model.

**Placement:** Supplementary material, or combine with the statistical comparison if space permits.

**Files:** `fig04_feature_ablation.{png,pdf,svg}`

### Figure 5 — Anomaly precision–recall operating points

**Scientific question:** How does a past-calibrated residual percentile trade supplied-label precision against recall?

**Answer shown:** Increasing the percentile raises precision while sharply reducing recall.

**Suggested caption:**

> Precision–recall operating points for thresholds obtained from the past calibration residuals. Metrics indicate agreement with publisher-supplied, algorithm-derived labels, not validated physical electrical anomalies.

**Placement:** Supplementary material; combine with Figure 6 for a full-page anomaly-analysis panel if needed.

**Files:** `fig05_anomaly_precision_recall.{png,pdf,svg}`

### Figure 6 — F1 and alert volume versus threshold

**Scientific question:** Is the historical p99 operating point conservative, and what alert-volume cost accompanies lower thresholds?

**Answer shown:** The retrospective highest test F1 occurs at p92.5, whereas p99 produces only eight alerts and much lower recall. The p92.5 marker is descriptive and must not be selected from the final test labels.

**Suggested caption:**

> Supplied-label F1 and alert volume across six calibration-residual percentiles. The dashed line marks the historical p99 HIL configuration. The p92.5 maximum is retrospective test-set information and is not treated as a newly selected deployment threshold.

**Placement:** Supplementary material or Anomaly Results.

**Files:** `fig06_f1_and_alerts_vs_threshold.{png,pdf,svg}`

### Figure 7 — Python → C++ → ESP8266 validation pipeline

**Scientific question:** How was numerical portability established before and after flashing the device?

**Answer shown:** Python reference predictions were checked against independently compiled C++ and then against physical ESP8266 replay over all 933 vectors and decisions.

**Suggested caption:**

> Three-layer numerical-validation pipeline. Generated C++ reproduced 933/933 Python predictions and threshold decisions within the declared tolerance before flashing; physical ESP8266 replay subsequently reproduced all 933 predictions and decisions. This validates the frozen computation, not live sensing.

**Placement:** Main paper, HIL Validation.

**Files:** `fig07_python_cpp_esp8266_validation.{png,pdf,svg}`

### Figure 8 — Interim HIL parity and aggregate error bound

**Scientific question:** What physical Python/device error evidence is currently available?

**Answer shown:** All 933 predictions and decisions matched; the maximum observed prediction difference was `8.9e-8`, below the `1e-6` tolerance. The distribution shape is unknown.

**Suggested interim caption:**

> Aggregate physical-device parity evidence. All 933 held-out predictions and residual decisions matched the software reference within the declared tolerance, with a maximum observed prediction difference of `8.9e-8` normalized units. The serial capture did not retain each per-vector difference, so this figure is not a prediction-error distribution.

**Placement:** Interim main-paper figure. In the final layout, combine with Figure 7 or replace it with the true distribution described below.

**Files:** `fig08_hil_parity_error_bounds_INTERIM.{png,pdf,svg}`

**Required replacement experiment:**

1. Add a validation-only JSONL record for each vector containing vector index, software-reference prediction, device prediction, absolute difference, reference decision and device decision.
2. Rebuild and upload the same model/feature contract on the physical ESP8266.
3. Capture all 933 records, the aggregate summary and firmware-build metadata.
4. Hash the raw capture and verify that all vector indices occur exactly once.
5. Plot a histogram plus empirical cumulative distribution of the **measured device differences** and annotate mean, median, p95, p99 and maximum.
6. Keep this verbose logging disabled in the latency benchmark because serial output would contaminate timing.

Until that run exists, do not reconstruct or simulate a device-error distribution from the aggregate maximum.

### Figure 9 — ESP8266 latency distribution

**Scientific question:** How stable is physical model-kernel timing across repeated batches?

**Answer shown:** Thirty 2,000-inference batch averages cluster near 50.4 µs, with a small number of higher batch averages.

**Suggested caption:**

> Distribution of 30 physical ESP8266 batch-average model-kernel times, with 2,000 predictions per batch. The mean was 50.4271 µs and the median 50.4028 µs; p5–p95 was 50.3646–50.5394 µs. These are batch averages and exclude sensing, feature preparation and communication.

**Placement:** Main paper, Embedded Results.

**Files:** `fig09_esp8266_latency_distribution.{png,pdf,svg}`

### Figure 10 — RAM, flash and IRAM utilization

**Scientific question:** Which memory category creates the main integration constraint?

**Answer shown:** Instruction RAM is approximately 92.1% used in both builds, whereas data RAM and flash code have substantially more headroom.

**Suggested caption:**

> Whole-firmware resource utilization for normal and full-validation builds. Instruction RAM used 60,343/65,536 bytes in both builds, leaving 5,193 bytes and representing the principal integration constraint. Values include firmware, networking, logging and application state; they are not model-only footprints.

**Placement:** Main paper, Embedded Resource Analysis.

**Files:** `fig10_memory_flash_iram_utilization.{png,pdf,svg}`

## Main-paper layout recommendation

Ten separate figures are too many for a typical short IEEE conference paper. Retain the full set in the reproducibility package, but use this compact main-paper arrangement:

1. Figure 1: architecture.
2. Figure 2: chronological protocol.
3. Figure 3: forecasting comparison.
4. Combined Figure 7+8: validation pipeline plus measured parity/error evidence.
5. Figure 9: latency distribution.
6. Figure 10: resource utilization.

Place Figures 4–6 in supplementary material unless the venue allows more pages. If anomaly analysis is central to the target venue, replace one main result figure with a combined Figure 5+6 panel.

## Visual and scientific quality controls

- 300-dpi PNG and vector PDF/SVG outputs.
- DejaVu Sans embedded as TrueType-compatible PDF text.
- Color-vision-deficiency-conscious palette plus differing marks/lines.
- Normalized-unit labels wherever physical units are unverified.
- “Against supplied labels” written on anomaly axes.
- No screenshots or copyrighted third-party figures.
- Timing explicitly says batch average and 2,000 predictions per batch.
- Resource plot explicitly says whole firmware.
- Figure 8 limitation is visible in the figure, caption and manifest.

## Reproduction

From the repository root with the project’s Python 3.13 environment:

```powershell
& 'C:\Users\fouad\AppData\Local\Programs\Python\Python313\python.exe' tools\run_phase21_figures.py
```

The script reads only stored Phase 5, 7, 8, 11–13 result files. It writes all figure variants and `outputs/phase21_figure_manifest.json`, including SHA-256 hashes.

## Phase decision

The publication figure design is complete and nine requested questions have final evidence-backed visualizations. The requested Python/device **distribution** remains a documented measurement gap; an aggregate parity/error-bound figure is supplied without pretending it is a distribution. Phase 22 should now convert verified results into compact publication tables and identify which tables belong in the main paper versus supplementary material.

