# Phase 17 — Dataset Research for the Next Embedded-ML Project

Date: 2026-09-03  
Status: complete (desk research; no dataset downloaded or redistributed)

## Decision

The recommended second project is **low-cost motor/bearing condition monitoring with compressed edge inference**. Start with the Paderborn University Bearing DataCenter for reproducible algorithm development, then collect a clearly separate low-cost vibration dataset from a small DC motor. The public benchmark and the later physical experiment must not be presented as the same sensing domain.

This choice fits an EEE research profile better than another generic tabular classification exercise. It supports signal processing, motor behavior, domain shift, model compression, microcontroller deployment, and a defensible hardware-validation story.

## Selection criteria

Candidates were checked against official dataset pages where possible. “TinyML suitability” means a credible compact **inference** path; it does not mean the full raw dataset or the training process belongs on a microcontroller.

| Candidate | Official source and license | Size and modality | Labels / sample rate | Candidate model and target | TinyML suitability | Research opportunity | Difficulty / publication potential |
|---|---|---|---|---|---|---|---|
| **Paderborn Bearing DataCenter** | [Paderborn University](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter), **CC BY-NC 4.0**; attribution required, noncommercial academic use | About **5.1 GB compressed** across 32 archives; synchronous vibration, two motor currents, speed, torque, load and temperature; 2,560 four-second records (32 bearing states × 4 conditions × 20) | 26 damaged and 6 healthy bearing states; current and vibration at **64 kHz** | FFT/band-energy features + logistic regression, small MLP, RF student or 1-D CNN; ESP8266 for feature-level model, ESP32-S3 for richer raw-window inference | High for compact engineered features; medium for raw 64-kHz windows | Cross-condition and real-vs-artificial-damage generalization; feature/model co-design; public-to-low-cost-sensor domain shift | Intermediate/advanced; **high** if physical validation is rigorous |
| **UCI Condition Monitoring of Hydraulic Systems** | [UCI](https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems), **CC BY 4.0** | 2,205 60-second cycles; 73.1 MB archive; 17 sensor streams | Cooler 3 states, valve 4, pump leakage 3, accumulator 4, plus stability; pressure/power 100 Hz, flow 10 Hz, temperature/vibration/derived 1 Hz | Feature selection + compact multi-output classifier; ESP32-S3 or Raspberry Pi gateway | High for a selected sensor subset | Sensor-subset selection under memory/energy constraints; uncertainty across simultaneous faults | Advanced; high data quality, but physical rig is expensive |
| **NASA C-MAPSS** | [NASA/Data.gov](https://catalog.data.gov/dataset/cmapss-jet-engine-simulated-data), public access; **no explicit license is stated on the catalog record**, so verify reuse terms before redistribution | Compressed text archive; four multivariate run-to-failure subsets; 26 columns per cycle | FD001–FD004: 100–260 training and 100–259 test engine trajectories; 1 or 6 operating conditions; 1 or 2 fault modes; sampled by operating cycle, not wall-clock Hz | Tiny temporal regressor or selected-feature MLP for RUL; ESP32-S3/Raspberry Pi using replayed sensor-cycle vectors | Medium | Accuracy–memory trade-off and calibrated uncertainty for RUL | Advanced; deep research value, but simulated and difficult to validate physically |
| **UCI Human Activity Recognition Using Smartphones** | [UCI](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones), **CC BY 4.0** | 10,299 windows; 58.2 MB; 3-axis accelerometer + 3-axis gyroscope from 30 people | 6 activities; **50 Hz**, 2.56-second/128-sample windows with 50% overlap; 561 derived features | Feature subset + linear/SVM/tree student or small 1-D CNN; ESP8266/ESP32 + MPU6050-class IMU | Very high | Subject-independent validation, adaptive personalization and feature-cost ablation | Beginner/intermediate; moderate novelty unless validation is unusually strong |
| **Google Speech Commands v2** | [TensorFlow Datasets](https://www.tensorflow.org/datasets/catalog/speech_commands); Google’s [tutorial states CC BY](https://www.tensorflow.org/tutorials/audio/simple_audio) | TFDS download 2.37 GiB, prepared size 8.17 GiB; one-second mono WAV clips | 35 recorded words in the original release; the common TFDS task has 12 classes; **16 kHz** | MFCC/log-mel + depthwise CNN; ESP32-S3 with I2S microphone | High on ESP32-S3; low on ESP8266 for a beginner end-to-end audio pipeline | Noise/domain adaptation, distillation and real-device false-trigger analysis | Intermediate; strong benchmark, crowded research area |
| **UCI Gas Sensor Array Drift at Different Concentrations** | [UCI](https://archive.ics.uci.edu/dataset/270/gas+sensor+array+drift+dataset+at+different+concentrations), **CC BY 4.0**; page also says research-only and requires two citations, so follow the stricter stated conditions | 13,910 measurements; 9.6 MB; 16 chemical sensors represented by 128 transient-response features over 36 months | 6 gases plus concentration; processed feature vectors, no raw uniform sample rate supplied | Feature selection + compact classifier/regressor; ESP8266/ESP32 with low-cost gas sensors for a separate domain study | High for feature vectors | Temporal drift adaptation, minimal-sensor selection and uncertainty under calibration shift | Intermediate/advanced; high publication potential, but safe calibrated gas collection is difficult |
| **UCI Beijing Multi-Site Air Quality** | [UCI](https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data), **CC BY 4.0** | 420,768 rows; 7.8 MB; 6 pollutants + 6 meteorological variables at 12 sites | Hourly records, March 2013–February 2017; regression/forecasting; missing values present | Compact boosted/tree student or linear temporal model; ESP8266/ESP32 sensor node | High | Station-transfer, missing-data robustness and low-cost sensor calibration/domain adaptation | Intermediate; good societal value, but ground-truth calibration is costly |
| **UCI Individual Household Electric Power Consumption** | [UCI](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption), **CC BY 4.0** | 2,075,259 rows; 19.7 MB download/126.8 MB text; one household over 47 months | One-minute electrical measurements and three submeters; about 1.25% missing | Linear/compact MLP/boosted student; ESP8266/ESP32 | Very high for compact forecasting | Stronger physical-unit replication of the current project; drift and uncertainty | Intermediate; useful extension, but not sufficiently distinct as a second project |
| **UCI N-BaIoT** | [UCI](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot), **CC BY 4.0** | 7,062,606 instances; 1.7 GB; packet-stream statistics from 9 commercial IoT devices | Benign vs malicious or 10 attacks + benign; event/packet sequential data, not a fixed sensor sample rate | Feature-selected classifier/autoencoder student; Raspberry Pi/router gateway, possibly ESP32 for precomputed statistics | Medium | Device-transfer, streaming-feature cost and false-alarm calibration | Advanced; good publication value, but packet feature extraction is the real embedded bottleneck |
| **UCI AI4I 2020 Predictive Maintenance** | [UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), **CC BY 4.0** | 10,000 rows; 509.8 KB; six principal process features plus IDs/targets | Machine failure and five generated failure modes; no physical sample rate | Logistic regression/tree/small MLP; ESP8266 | Very high computationally | Explainability and cost-sensitive learning demonstrations | Beginner; **low-to-moderate publication potential** because the data and rules are synthetic |

## Why Paderborn is the preferred dataset

The official data page provides both realistic lifetime damage and artificially introduced damage, four controlled operating conditions, motor-current and vibration channels, and explicit licensing. Its companion paper reports 64-kHz synchronous acquisition and explains why current-based diagnosis could reduce sensor cost. Those properties create research questions beyond chasing classification accuracy:

1. How much accuracy is lost when a 64-kHz laboratory signal is reduced to a small set of edge-computable spectral features?
2. Do models trained on artificial damage generalize to real lifetime damage?
3. Does a model remain reliable when speed, torque or radial load changes?
4. What is the Pareto frontier among accuracy, feature-extraction cost, model size, latency and energy?
5. How badly does a public-dataset model transfer to a low-cost accelerometer and small motor, and can limited calibration data reduce the gap?

## Recommended end-to-end protocol

1. **Dataset:** download only from Paderborn; store locally; record archive names and SHA-256 hashes; do not commit the data because CC BY-NC and repository size make redistribution inappropriate.
2. **Split:** split by bearing identity, not random windows. Keep at least one operating condition or damage group for out-of-domain testing.
3. **Baselines:** majority class, logistic regression on RMS/kurtosis/crest factor/band energies, random forest or gradient boosting, and one small 1-D CNN.
4. **Compression:** feature selection, tree/linear distillation, pruning where supported, int8 or fixed-point export, and a transparent C/C++ reference implementation.
5. **Embedded target:** begin with the existing ESP8266 for compact feature-level inference; use ESP32-S3 if raw-window DSP or a neural model exceeds the ESP8266 memory/timing budget.
6. **Physical validation:** later use a low-voltage DC motor, a safe mechanical imbalance or replaceable worn bearing, and a digital accelerometer. Call this a separate low-cost validation domain; do not claim it reproduces Paderborn’s industrial test rig.
7. **Measurements:** prediction parity, macro-F1/balanced accuracy, per-condition confusion matrices, model/feature memory, latency distribution, and measured energy using the Phase 15 protocol.

## Dataset-use cautions

- Paderborn data is **noncommercial** and attribution is required. Commit download instructions and hashes, not archives.
- NASA C-MAPSS is public-access data, but the catalog page does not provide a named reuse license. Treat “public” as access status, not automatic permission to republish files.
- The UCI gas-drift page combines a CC BY 4.0 badge with stricter narrative language (“research purposes” and required citations). Follow the stricter terms and document both citations.
- For human/audio datasets, preserve official subject/speaker splits to avoid identity leakage.
- A result from replayed benchmark vectors on an MCU proves computational deployment, not real sensor acquisition.

## Sources checked

- [Paderborn Bearing DataCenter overview and license](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter)
- [Paderborn dataset contents and downloads](https://mb.uni-paderborn.de/kat/forschung/bearing-datacenter/data-sets-and-download)
- [Paderborn companion paper](https://mb.uni-paderborn.de/fileadmin-mb/kat/PDF/Veroeffentlichungen/20160703_PHME16_CM_bearing.pdf)
- [NASA C-MAPSS catalog record](https://catalog.data.gov/dataset/cmapss-jet-engine-simulated-data)
- [TensorFlow Speech Commands catalog](https://www.tensorflow.org/datasets/catalog/speech_commands)
- All UCI records linked in the comparison table.

