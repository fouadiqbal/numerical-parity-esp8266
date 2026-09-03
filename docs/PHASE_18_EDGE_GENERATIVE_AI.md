# Phase 18 — Realistic Generative AI for Low-Resource Edge Research

Date: 2026-09-03  
Status: complete (feasibility assessment; no generative model has been trained)

## Decision

A language model or general-purpose text generator is **not an appropriate ESP8266 objective** for this research. The defensible generative-AI direction is:

> Train a conditional time-series generator on a PC/Colab to augment rare motor/bearing conditions, distil the resulting knowledge into a compact discriminative student, and deploy only that student on the microcontroller.

This is genuinely related to generative modelling, but the paper must state clearly that the generator runs off-device. A second, optional embedded experiment may use a very small autoencoder whose decoder reconstructs a sensor window for anomaly scoring. That is a narrow generative model, not an LLM.

## Why an ESP8266 LLM is the wrong target

- The existing project’s normal ESP8266 build already reports **92% IRAM use**, even though its deployed predictor is only a compact linear calculation.
- Espressif’s current [ESP-DL documentation](https://docs.espressif.com/projects/esp-dl/en/release-v1.1/esp32s3/introduction.html) targets ESP32-family chips such as ESP32, ESP32-S2, ESP32-S3 and ESP32-C3; it does not present ESP8266 as a supported neural-inference target.
- [TensorFlow Lite for Microcontrollers](https://github.com/tensorflow/tflite-micro) is intended for constrained microcontrollers, but feasibility remains model-, operator-, memory- and board-specific. Framework availability is not evidence that an LLM is useful or deployable.
- Generating prose is not part of the physical condition-monitoring problem. It would add memory and evaluation complexity without improving the core scientific question.

“Not appropriate” does not mean mathematically impossible to produce a toy character sequence. It means the task would not be useful, reproducible, or scientifically proportionate on this hardware.

## Opportunity assessment

| Direction | Where training runs | What runs at the edge | Suitable hardware | Scientific value | Decision |
|---|---|---|---|---|---|
| **Conditional synthetic sensor augmentation** | PC/Colab: conditional VAE, TimeGAN or related generator | Compressed classifier only | ESP8266 for feature model; ESP32-S3 for small raw-window model | Tests whether synthetic rare-fault data improves real held-out performance after compression | **Primary recommendation** |
| **Generative anomaly detection with a tiny autoencoder** | PC/Colab | Encoder + decoder; reconstruction error becomes anomaly score | ESP32-S3 preferred; a linear/tiny dense autoencoder may fit ESP8266 | Edge-resident reconstruction, threshold calibration and drift analysis | **Secondary experiment** |
| **Teacher–student distillation** | Large teacher on PC/Colab | Small student | ESP8266/ESP32-S3 | Strong bridge between sophisticated training and tiny inference; not itself generative AI | **Use as enabling method** |
| **Keyword-conditioned device control** | PC/Colab | Keyword classifier, not a generator | ESP32-S3 + I2S microphone | Useful embedded AI; Espressif provides offline speech-command tooling | Good future project, but separate from motor monitoring |
| **Sensor-to-text status reports** | PC/gateway for language generation | Device transmits structured state; optional fixed templates locally | Raspberry Pi for small local language model; cloud otherwise | Human-readable maintenance reporting | Later gateway study; do not call fixed templates generative AI |
| **Tiny text generation** | PC | Token generator | ESP8266 | Little task relevance and severe memory/latency constraints | Reject |
| **Edge vision-language model** | Workstation | VLM inference | Raspberry Pi/Jetson-class target, not ESP8266 | Potential multimodal inspection study | Separate advanced project |
| **On-device time-series GAN/diffusion training** | Microcontroller | Generator training and sampling | None of the current target boards | Excessive computation and weak justification | Reject |

## Recommended research question

**Can training-only conditional synthetic augmentation improve balanced fault detection on real, unseen bearing identities and operating conditions while the final compressed student retains microcontroller-level memory, latency, and numerical-parity guarantees?**

This question is stronger than “use a GAN and report accuracy” because it requires evidence that the synthetic data adds utility under a strict real-data test protocol.

## Experimental design

### 1. Split before generation

Partition the public dataset by bearing identity and operating condition. The generator, feature scaler, feature selector, teacher and student must see only the training partition. Never generate first and randomly split afterward; that would allow information from test bearings to influence training.

### 2. Compare fair augmentation baselines

Keep the final student architecture and training budget fixed. Compare:

1. real training data only;
2. class weighting;
3. random oversampling;
4. conventional signal augmentation such as amplitude scaling, jitter and time shifting;
5. conditional VAE augmentation;
6. one adversarial time-series method such as TimeGAN, only if the simpler VAE is insufficient.

TimeGAN is a relevant reference because it explicitly combines adversarial and supervised objectives to preserve temporal dynamics, but it is not automatically the best choice for a small dataset. A VAE is simpler to reproduce and ablate.

### 3. Evaluate the synthetic data, not only the classifier

- **Downstream utility:** macro-F1, balanced accuracy, per-class recall and PR-AUC on real held-out data.
- **Calibration:** Brier score or expected calibration error on real held-out data.
- **Signal fidelity:** power-spectral-density distance, band-energy distribution, autocorrelation error and relevant bearing-frequency content.
- **Diversity:** within-class coverage and duplicate/near-duplicate rate.
- **Memorization check:** nearest-neighbour distance from each synthetic sequence to the real training sequences.
- **Sensitivity:** synthetic-to-real ratios such as 0.25×, 0.5×, 1× and 2×.

No claim of benefit is allowed unless improvement occurs on real, identity-separated test data and survives uncertainty analysis across folds/seeds.

### 4. Compress and deploy only the selected student

Compare FP32, fused/feature-normalized FP32, and integer or int8 inference where appropriate. Record:

- model parameters and storage;
- feature-buffer and inference-arena memory;
- per-window DSP cost separately from model-only latency;
- repeated physical-device latency;
- host C/C++ and device prediction/decision parity;
- energy per complete sensing-to-decision cycle when the Phase 15 equipment is available.

### 5. Keep deployment claims precise

Allowed claim if verified: “A student trained with synthetic augmentation was deployed and benchmarked on ESP8266/ESP32-S3.”

Disallowed claim unless separately implemented and measured: “The generative model ran on the ESP8266.”

## Optional edge-resident autoencoder experiment

A small dense autoencoder can reconstruct a short engineered-feature vector. Train only on healthy training data, export the encoder and decoder, and use reconstruction error as the anomaly score. Compare it with Mahalanobis distance, one-class linear baselines and a compact discriminative classifier. Select the threshold using a validation set, not the test set.

This route is feasible only after memory and operator support are measured. On ESP8266, start with a linear or very small dense autoencoder written as generated C/C++; on ESP32-S3, an int8 neural implementation is more realistic.

## Hardware boundary

- **ESP8266:** compact handcrafted-feature models, linear/dense students, telemetry, and parity testing.
- **ESP32-S3:** preferred upgrade for raw signal windows, audio, int8 neural models and Espressif’s inference libraries. Espressif documents [offline speech command recognition](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/speech_command_recognition/README.html) at 16 kHz on ESP32-S3, illustrating the class of workload this board is designed to support.
- **Raspberry Pi/Jetson:** small language/vision-language models or a local generative gateway. These are edge computers, not equivalent to an ESP8266-class MCU.

## Primary references for later related-work writing

- J. Yoon, D. Jarrett and M. van der Schaar, [“Time-series Generative Adversarial Networks,” NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/hash/c9efe5f26cd17ba6216bbe2a7d26d490-Abstract.html).
- D. P. Kingma and M. Welling, [“Auto-Encoding Variational Bayes”](https://arxiv.org/abs/1312.6114).
- G. Hinton, O. Vinyals and J. Dean, [“Distilling the Knowledge in a Neural Network”](https://arxiv.org/abs/1503.02531).
- [TensorFlow Lite Micro repository](https://github.com/tensorflow/tflite-micro).
- [Espressif ESP-DL documentation](https://docs.espressif.com/projects/esp-dl/en/release-v1.1/esp32s3/introduction.html).

These references establish method families and platform capabilities. They do not establish that the proposed experiment will work; that requires the measurements above.

