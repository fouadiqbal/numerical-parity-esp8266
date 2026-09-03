# Phase 23 — Related-Work Gap Analysis

## Outcome

Phase 23 is complete as a targeted, source-verified gap analysis. The literature does **not** support claiming that load forecasting, prediction-residual anomaly detection, edge smart-meter analytics, TinyML benchmarking, or MCU-based load forecasting is new by itself.

The paper's defensible research position is narrower:

> A reproducible transfer-and-verification case study showing that a nine-parameter forecasting model and its residual-threshold decision rule can be exported from Python to generated C++ and reproduced across all 933 held-out vectors on a physical ESP8266, while separately reporting numerical error, decision agreement, kernel timing, data RAM, instruction RAM, and flash.

This combination was not found as the central protocol in the reviewed sample. That makes it a plausible differentiator, not proof of a worldwide first.

## Search protocol

- Search date: 3 September 2026.
- Review type: targeted gap analysis, not a systematic review or meta-analysis.
- Themes: household/smart-meter forecasting, prediction-based anomaly detection, edge energy analytics, TinyML benchmarking and compression, and physical embedded smart-meter/NILM validation.
- Primary sources: IEEE Xplore and IEEE-linked institutional records, ScienceDirect, Springer Nature, MDPI/Sensors, NeurIPS proceedings, OpenReview, MLCommons, and Crossref DOI metadata.
- Inclusion: peer-reviewed work relevant to at least one theme whose bibliographic record and technical claims could be checked on a publisher, proceedings, DOI, or accepted-manuscript page.
- Exclusion: unverified web summaries, student reports, unconfirmed preprints, and papers whose technical relevance could not be established from an authoritative record.

The search cannot establish an exhaustive negative claim. Phrases such as “the first,” “the only,” and “unprecedented” remain prohibited.

## What already exists

### Smart-meter forecasting

Shi et al. developed a pooling deep RNN using 920 Irish smart-meter customers and compared RMSE against ARIMA, SVR, and a classical deep RNN [shi2018pooling]. Kong et al. presented LSTM-based short-term individual-residential forecasting against multiple benchmarks [kong2019lstm]. Aurangzeb et al. later compared several recurrent/convolutional models and feature sets on Australian Smart Grid Smart City data [aurangzeb2024bilstm].

Therefore, neither smart-meter forecasting nor the use of lag/calendar features and neural baselines is a novelty claim for this project. The present compact linear model should be justified by deployability, auditability, and data limitations—not presented as a new forecasting algorithm.

### Prediction-based anomaly detection

Liu and Nielsen implemented scalable prediction-based online anomaly detection using a lambda architecture, real and synthetic data, and three baselines [liu2018scalable]. Utomo and Hsiung compared DNN, SVR, and KNN approaches in a multitier smart-meter edge architecture and reported Raspberry Pi latency and model size [utomo2020multitiered]. Hernández et al. combined next-hour energy prediction with activity alarms using seven months of measurements from a commercial meter in one household [hernandez2024daily].

Therefore, forecast-residual or prediction-based anomaly detection is established prior art. The current project's anomaly contribution is limited to transparent threshold sensitivity, method comparison, and deterministic device-side reproduction against supplied algorithmic labels. It does not introduce a novel detector and does not validate real electrical anomalies.

### Edge intelligence and constrained smart meters

Hu and Tang proposed edge-intelligence-enabled smart-meter architecture and cloud-edge DNN collaboration [hu2020edge]. More importantly, Li et al. demonstrated on-device load forecasting and distributed training on thirty Cortex-M4 microcontrollers with 192 KB SRAM, using two real datasets, chronological first-year/subsequent-half-year splits, five experiments with confidence intervals, and measurements of memory, training time, and communication [li2024federated].

Gajendran et al. provide especially close ESP8266 prior art: PZEM-004T modules and ESP8266 controllers acquire and transmit real residential measurements, while forecasting models are trained and evaluated in MATLAB on i7/RTX 3060 computer hardware [gajendran2026ihems]. Thus, “ESP8266 smart-meter forecasting system” is also too broad as a novelty claim. The distinction in this project is that the forecast equation and residual decision actually execute on the ESP8266 and are checked row by row; conversely, the AIP study has real sensing evidence that this project lacks.

This is direct, strong prior art. The present manuscript must not claim the first constrained-device load forecaster or the first intelligent smart meter. Its device is less capable and its experiment is simpler; its distinct evidence is the explicit Python-to-generated-C++-to-ESP8266 parity audit for every held-out vector and threshold decision.

### TinyML benchmarking and compression

MLPerf Tiny defines reproducible accuracy, latency, and energy benchmarks for ultra-low-power systems [banbury2021mlperf]. MCUNet jointly optimizes neural architectures and inference software for microcontrollers, reporting accuracy, SRAM, flash, and speed [lin2020mcunet].

These studies set a higher benchmarking standard than one average latency number. The project improved its timing evidence to 30 batch averages and reports RAM/IRAM/flash separately, but it still lacks measured energy per inference and individual-cycle latency samples. Its fused-FP32/fixed-point comparison is an engineering ablation, not a new quantization method.

### Physical embedded smart meters

Kolosov et al. implemented a 15-kHz custom meter with a signal-conditioning front end and embedded NILM, then evaluated measurement fidelity, latency, throughput, power, and efficiency across six hardware platforms [kolosov2025instrumental]. This is substantially stronger physical-sensing evidence than the present ESP8266 HIL replay.

The current work must continue to state that it has no calibrated voltage/current sensing, reference-meter comparison, or measured energy consumption. A physical ESP8266 executing replayed features is not equivalent to a validated smart meter.

## Gap matrix

The complete 12-study matrix is stored in `tables/phase23_related_work_matrix.csv`. Ten studies are also included in publication Table 11; MCUNet and the 2024 T2V-BiLSTM study remain supporting references to avoid making an already-wide table larger.

| Evidence dimension | Established in prior work | What remains defensible here |
|---|---|---|
| Household load forecasting | Deep RNN/LSTM and modern feature/model comparisons on real datasets | A deliberately tiny, transparent model evaluated under leakage-aware holdout and walk-forward protocols |
| Prediction-based anomalies | Online residual/prediction methods and field-context activity alarms | Threshold sensitivity and exact decision transfer, explicitly limited to supplied algorithmic labels |
| On-device load forecasting | Cortex-M4 hardware platform with distributed/split learning | ESP8266-specific generated C++ export and complete row-wise inference parity |
| TinyML performance | Standard latency/energy benchmarks and neural system–algorithm co-design | Application-specific timing plus data RAM, IRAM, flash, parameter, and operation accounting |
| Physical smart-meter validation | Calibrated/high-frequency sensing and multi-platform NILM benchmarking | No current claim; retained only as a future sensing protocol |
| Reproducibility | Benchmark suites and source-data releases exist | Traceable dataset hash, generated model constants, host parity test, raw serial provenance, and complete HIL test count |

## Recommended paper positioning

Use language like:

> Prior work has separately established accurate household load forecasting, prediction-based anomaly detection, edge smart-meter architectures, and MCU-based load forecasting. In contrast, this study focuses on the traceability of a deliberately compact pipeline across the software–hardware boundary. We evaluate whether generated C++ inference on a low-cost ESP8266 reproduces the Python reference predictions and residual-threshold decisions over the complete held-out feature set, and report the associated numerical deviation, latency distribution, and whole-firmware resource constraints.

Do not write:

- “We propose the first TinyML smart meter.”
- “No previous study has deployed load forecasting on a microcontroller.”
- “Our anomaly detector is novel.”
- “Our ESP8266 is a validated smart meter.”
- “Our approach is more accurate than prior work” when datasets, units, horizons, and protocols differ.
- “Energy efficient” until energy per inference is physically measured.

## Reviewer-facing strengths

1. Every one of 933 held-out predictions and decisions is checked on the physical device.
2. The model export is generated, not manually copied.
3. Python, host C++, and ESP8266 evidence layers are explicitly separated.
4. The resource report distinguishes 104-byte numeric state from whole-firmware data RAM, IRAM, and flash.
5. The anomaly limitations and missing physical units are reported instead of hidden.

## Reviewer-facing weaknesses that remain

1. The current dataset has unresolved provenance/licensing details and no recoverable physical units.
2. Supplied anomaly labels are algorithm-generated rather than verified events.
3. Only one physical ESP8266 configuration has been tested.
4. HIL features are replayed from flash; no live electrical sensing is present.
5. Energy per inference and end-to-end sensing-to-alert latency are not measured.
6. Generalization beyond one normalized 5,000-row dataset is not established.
7. The selected linear model is technically simple; the contribution depends on rigorous transfer validation and transparent reporting.

These limitations prevent a strong algorithmic-novelty paper today. They still permit a modest, honest embedded reproducibility/HIL case study, subject to Phase 24 licensing clearance and a suitable workshop, student conference, or applied embedded-systems venue.

## Verified bibliography

- [shi2018pooling] H. Shi, M. Xu, and R. Li, “Deep Learning for Household Load Forecasting—A Novel Pooling Deep RNN,” *IEEE Transactions on Smart Grid*, 2018. https://doi.org/10.1109/TSG.2017.2686012
- [kong2019lstm] W. Kong et al., “Short-Term Residential Load Forecasting Based on LSTM Recurrent Neural Network,” *IEEE Transactions on Smart Grid*, 2019. https://doi.org/10.1109/TSG.2017.2753802
- [liu2018scalable] X. Liu and P. S. Nielsen, “Scalable Prediction-Based Online Anomaly Detection for Smart Meter Data,” *Information Systems*, 2018. https://doi.org/10.1016/j.is.2018.05.007
- [utomo2020multitiered] D. Utomo and P.-A. Hsiung, “A Multitiered Solution for Anomaly Detection in Edge Computing for Smart Meters,” *Sensors*, 2020. https://doi.org/10.3390/s20185159
- [hu2020edge] H. Hu and L. Tang, “Edge Intelligence for Real-Time Data Analytics in an IoT-Based Smart Metering System,” *IEEE Network*, 2020. https://doi.org/10.1109/MNET.011.2000039
- [gajendran2026ihems] Gajendran P, Ranganayaki V, and Deepa S. N., “IoT-Based Home Energy Management Using Machine Learning and BiLSTM–GRU Forecasting,” *AIP Advances*, 2026. https://doi.org/10.1063/5.0339511
- [banbury2021mlperf] C. Banbury et al., “MLPerf Tiny Benchmark,” *NeurIPS Datasets and Benchmarks Track*, 2021. https://openreview.net/forum?id=8RxxwAut1BI
- [lin2020mcunet] J. Lin et al., “MCUNet: Tiny Deep Learning on IoT Devices,” *NeurIPS*, 2020. https://papers.nips.cc/paper/2020/hash/86c51678350f656dcc7f490a43946ee5-Abstract.html
- [hernandez2024daily] Á. Hernández et al., “Detection of Anomalies in Daily Activities Using Data from Smart Meters,” *Sensors*, 2024. https://doi.org/10.3390/s24020515
- [aurangzeb2024bilstm] K. Aurangzeb, S. I. Haider, and M. Alhussein, “Individual Household Load Forecasting Using Bi-Directional LSTM Network with Time-Based Embedding,” *Energy Reports*, 2024. https://doi.org/10.1016/j.egyr.2024.03.028
- [li2024federated] Y. Li, D. Qin, H. V. Poor, and Y. Wang, “Introducing Edge Intelligence to Smart Meters via Federated Split Learning,” *Nature Communications*, 2024. https://doi.org/10.1038/s41467-024-53352-9
- [kolosov2025instrumental] D. Kolosov, M. Robinson, P. A. Schirmer, and I. Mporas, “An Instrumental High-Frequency Smart Meter with Embedded Energy Disaggregation,” *Sensors*, 2025. https://doi.org/10.3390/s25175280

The machine-readable BibTeX file is `references/references.bib`.

## Reproduction

```powershell
python tools/run_phase23_related_work.py
python tools/run_phase22_tables.py
```

The first command regenerates the literature record, comparison matrix, and BibTeX file. The second uses the verified Phase 23 artifact to populate Table 11 and refresh the Phase 22 hashes.

## Phase decision

The paper will not be positioned as a novel forecasting/anomaly algorithm or the first edge smart meter. It will be positioned as a compact ESP8266 software-to-hardware reproducibility and HIL parity study. Phase 24 must now determine whether the dataset, code, figures, and planned public package can legally be redistributed and whether any manuscript text or graphics create copyright/similarity risks.
