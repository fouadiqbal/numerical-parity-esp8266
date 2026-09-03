# Phase 19 — Ranked Next Embedded-ML Research Projects

Date: 2026-09-03  
Status: complete (planning decision; no new project experiment has been run)

## Scoring method

Every criterion is scored from 1 to 10. For **hardware cost**, 10 means cheapest/easiest to obtain. For **difficulty**, 10 means hardest. The overall score emphasizes novelty and publication potential while applying a small penalty for difficulty:

`Overall = 0.20×Novelty + 0.15×DataQuality + 0.15×EmbeddedFeasibility + 0.10×HardwareCost + 0.15×ResearchDepth + 0.20×PublicationPotential + 0.05×(10−Difficulty)`

Scores are planning judgments, not experimental results. Hardware prices vary by country and date; the cost score therefore represents relative bill-of-materials burden rather than a quoted price.

## Ranking

| Rank | Project | Novelty | Data quality | Embedded feasibility | Hardware cost (10=cheap) | Research depth | Publication potential | Difficulty (10=hard) | Overall |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **1** | **Cross-condition motor/bearing fault detection with compressed TinyML** | 8 | 9 | 8 | 8 | 9 | 9 | 7 | **8.25** |
| **2** | Gas-sensor drift adaptation with a minimal sensor subset | 8 | 8 | 8 | 7 | 9 | 9 | 7 | **8.00** |
| **3** | Noise-robust keyword spotting with distillation on ESP32-S3 | 6 | 9 | 8 | 7 | 8 | 8 | 6 | **7.45** |
| **4** | Subject-independent HAR with adaptive personalization | 6 | 8 | 9 | 9 | 7 | 7 | 4 | **7.40** |
| **5** | Streaming IoT intrusion detection on a low-cost gateway | 7 | 8 | 6 | 8 | 8 | 8 | 7 | **7.25** |
| **6** | Air-quality forecasting/calibration under site and sensor drift | 7 | 8 | 7 | 6 | 8 | 8 | 7 | **7.20** |
| **7** | Physical-unit household load forecasting and edge drift detection | 6 | 8 | 7 | 5 | 9 | 7 | 8 | **6.80** |
| **8** | Sensor-subset-aware hydraulic condition monitoring | 7 | 9 | 5 | 2 | 9 | 8 | 9 | **6.70** |
| **9** | Compressed turbofan remaining-useful-life prediction | 5 | 8 | 5 | 3 | 9 | 7 | 8 | **6.10** |
| **10** | Explainable AI4I failure classifier on ESP8266 | 4 | 5 | 10 | 10 | 5 | 4 | 2 | **6.00** |

## What each project would actually contribute

### 1. Cross-condition motor/bearing fault detection

- **Dataset:** Paderborn Bearing DataCenter.
- **Research gap:** generalization from artificial to real damage and across operating conditions after feature/model compression.
- **Edge target:** existing ESP8266 for a compact feature model; ESP32-S3 if raw-window DSP is needed.
- **Later hardware:** low-voltage DC motor, digital accelerometer, mechanically safe normal/fault conditions.
- **Why first:** best combination of EEE relevance, signal-processing depth, achievable hardware and publishable experimental structure.

### 2. Gas-sensor drift adaptation

- **Dataset:** UCI Gas Sensor Array Drift at Different Concentrations.
- **Research gap:** temporal domain adaptation with minimal sensors and calibrated uncertainty.
- **Edge target:** ESP8266/ESP32.
- **Risk:** reproducing known gas concentrations safely and accurately is much harder than buying an inexpensive sensor module.

### 3. Noise-robust keyword spotting

- **Dataset:** Google Speech Commands plus a separately collected local-noise test set.
- **Research gap:** teacher–student distillation and real-device false-trigger robustness.
- **Edge target:** ESP32-S3 + I2S microphone; Espressif provides a relevant offline speech stack.
- **Risk:** the benchmark is crowded, so deployment alone is not novel.

### 4. Subject-independent HAR

- **Dataset:** UCI HAR.
- **Research gap:** unseen-subject performance, personalization with very little calibration data, and feature-cost ablation.
- **Edge target:** ESP8266/ESP32 + IMU.
- **Risk:** excellent learning project but a weaker EEE identity and a mature benchmark.

### 5. Streaming IoT intrusion detection

- **Dataset:** UCI N-BaIoT.
- **Research gap:** streaming feature extraction cost, cross-device transfer and false alarms rather than only offline classification.
- **Edge target:** Raspberry Pi/router gateway; reduced ESP32 prototype possible.
- **Risk:** packet capture and stateful feature generation dominate the engineering effort.

### 6. Air-quality forecasting and calibration

- **Dataset:** UCI Beijing Multi-Site Air Quality.
- **Research gap:** station-transfer and low-cost-sensor domain adaptation with uncertainty.
- **Edge target:** ESP8266/ESP32 environmental node.
- **Risk:** a credible calibration study needs access to reference-grade measurements.

### 7. Physical-unit smart-meter continuation

- **Dataset:** UCI Individual Household Electric Power Consumption, followed by a safe isolated sensing setup.
- **Research gap:** distribution shift, adaptive thresholds and full sensing-to-inference cost.
- **Edge target:** ESP8266/ESP32.
- **Risk:** mains safety, calibration and the fact that it is an extension rather than a visibly different second project.

### 8. Hydraulic condition monitoring

- **Dataset:** UCI Condition Monitoring of Hydraulic Systems.
- **Research gap:** how few sensors and how small a model can preserve multi-component condition estimates.
- **Edge target:** ESP32-S3/Raspberry Pi.
- **Risk:** the public data is strong but a faithful physical rig is not low cost.

### 9. Turbofan RUL

- **Dataset:** NASA C-MAPSS.
- **Research gap:** uncertainty-aware RUL under strict engine-level splits and edge budgets.
- **Edge target:** ESP32-S3/Raspberry Pi using replayed sensor-cycle vectors.
- **Risk:** no realistic low-cost physical validation, simulated benchmark, crowded literature, and license clarification required before redistribution.

### 10. AI4I failure classification

- **Dataset:** UCI AI4I 2020.
- **Research gap:** explainability and cost-sensitive decisions.
- **Edge target:** ESP8266.
- **Risk:** labels follow known synthetic rules, so high accuracy and successful deployment would add little research novelty.

## Final selection

Proceed with **Project 1: Cross-condition motor/bearing fault detection with compressed TinyML** after the current smart-meter manuscript reaches a submission-ready state.

Provisional project title:

> **Cross-Condition Bearing Fault Detection with Compressed TinyML: From Public High-Rate Signals to Low-Cost Embedded Validation**

The project should explicitly separate three evidence layers:

1. **Public benchmark evidence:** leakage-safe Paderborn experiments.
2. **Computational deployment evidence:** host/device parity, resources, latency and energy for the exported student.
3. **Low-cost physical evidence:** a newly collected sensor domain on a small motor, including calibration limits and domain-shift analysis.

## First milestone for the selected project

Do not buy hardware or train a GAN yet. The first milestone is a dataset ingestion and split audit:

1. create a new repository or top-level project directory;
2. add the exact CC BY-NC 4.0 notice and required Paderborn citation;
3. write a downloader that fetches selected archives without committing them;
4. generate SHA-256 hashes and an immutable manifest;
5. parse a small subset and verify channel names, shapes, sampling rate and bearing identities;
6. define bearing-identity and operating-condition splits before extracting windows.

## Immediate sequence

The master plan now returns to the current smart-meter paper:

- **Phase 20:** produce the detailed conference-paper structure.
- **Phase 21:** define and generate question-driven figures from verified evidence.
- **Phase 22:** build publication tables.
- **Phase 23:** complete a primary-source related-work gap matrix.

