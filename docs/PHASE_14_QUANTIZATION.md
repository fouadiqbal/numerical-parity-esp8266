# Phase 14 — FP32, Fused FP32, and Fixed-Point Comparison

## Outcome

Phase 14 is complete. A paired physical ESP8266 experiment compared four execution paths across 30 batches of 2,000 predictions each. All tested representations preserved every one of the 933 residual-threshold decisions.

The selected current deployment default is **fused-affine FP32**, not fixed point. It is 3.10× faster than the original standardized FP32 implementation, slightly smaller in the minimal firmware build, numerically equivalent for this task, and does not require redesigning feature acquisition and history storage.

Pre-quantized Q15/Q30 remains a conditional optimization. Its arithmetic kernel is 5.72× faster than standardized FP32, but converting eight floating-point inputs inside each prediction makes the complete path 7.35% slower than standardized FP32. Q15 should be adopted only when measurements are quantized once at acquisition and the lag buffer stores quantized values.

TensorFlow Lite Micro was not used because a runtime and interpreter are unnecessary for a single affine equation.

## Representations

### Standardized FP32

```text
prediction = intercept + Σ (((x[i] − mean[i]) / scale[i]) × coefficient[i])
```

This is the original exported implementation. It executes eight floating-point divisions per prediction.

### Fused-affine FP32

The preprocessing constants were algebraically folded into raw-space weights:

```text
raw_weight[i] = coefficient[i] / scale[i]
raw_bias = intercept − Σ (mean[i] × raw_weight[i])
prediction = raw_bias + Σ (x[i] × raw_weight[i])
```

The transformation does not retrain the model. It reduces the source-level kernel from 32 scalar arithmetic operations to eight multiplications and eight additions.

### Q7/Q30 and Q15/Q30 fixed point

Each input is mapped to a signed integer using a declared per-feature maximum. Raw-space weights and the bias are stored in Q30 form, and an `int64_t` accumulator evaluates:

```text
prediction_q30 = bias_q30 + Σ (input_q × multiplier_q30)
```

Q7 uses a maximum input code of 127. Q15 uses 32,767. The physical implementation used Q15 inputs, Q30 multipliers and output, and a signed 64-bit accumulator.

## Offline 933-row comparison

| Representation | MAE | RMSE | Maximum deviation from float64 | Decision agreement |
|---|---:|---:|---:|---:|
| Float64 reference | 0.1307837086 | 0.1623896726 | — | 933/933 reference |
| Standardized FP32 | 0.1307837089 | 0.1623896729 | 0.0000000756 | 933/933 |
| Fused-affine FP32 | 0.1307837073 | 0.1623896718 | 0.0000000807 | 933/933 |
| Q7/Q30 fixed | 0.1307726610 | 0.1623809782 | 0.0003536466 | 933/933 |
| Q15/Q30 fixed | 0.1307838374 | 0.1623898123 | 0.0000121095 | 933/933 |

The small apparent MAE improvement for Q7 is an incidental rounding effect on this test set, not evidence that quantization improves the underlying model. Q15 was preferred over Q7 for the engineering comparison because it reduces maximum numerical deviation by approximately 29× while retaining all decisions.

An independently compiled host-C++ test of the generated Q15 header passed all 933 predictions within `1e-6` of the Python fixed-point reference and matched all 933 decisions. Its maximum Python/C++ difference was `4.37e-7` normalized units.

## Paired physical ESP8266 timing

All four timing distributions were recorded during the same physical boot with Wi‑Fi enabled. Every row below contains 30 batch averages, with 2,000 predictions per batch.

| Execution path | Mean | Median | p5–p95 | Speed relative to standardized FP32 |
|---|---:|---:|---:|---:|
| Standardized FP32 | 50.6268 µs | 50.6088 µs | 50.5727–50.6739 µs | 1.00× |
| Fused-affine FP32 | 16.3320 µs | 16.2743 µs | 16.2264–16.4943 µs | **3.10× faster** |
| Q15 kernel, inputs already quantized | 8.8462 µs | 8.8085 µs | 8.7880–9.0301 µs | **5.72× faster** |
| Q15 plus float-to-Q15 conversion | 54.3470 µs | 54.3743 µs | 54.1441–54.4023 µs | **7.35% slower** |

The Q15 kernel result excludes feature quantization. This is valid only for an architecture that stores lagged measurements in Q15 form and generates calendar codes directly in the required integer representation. It must not be presented as the latency of accepting eight floating-point inputs.

## Physical full-validation result

| Check | Fused FP32 | Q15/Q30 |
|---|---:|---:|
| Decision agreement with reference | 933/933 | 933/933 |
| Maximum prediction difference | 0.000000089 | 0.000012100 |
| Device MAE | 0.130783722 | 0.130783767 |
| Device RMSE | 0.162389636 | 0.162389815 |

The supplied-label confusion matrix remains TP=8, FP=0, FN=44, TN=881 for both paths because no residual decisions changed. This is agreement with publisher-derived pseudo-labels, not accuracy on physically verified faults.

## Model and firmware memory

Analytical numeric state:

| Representation | Core numeric state | Additional generic input-range metadata |
|---|---:|---:|
| Standardized FP32 | 104 B | 0 B |
| Fused-affine FP32 | 40 B | 0 B |
| Q15/Q30 fixed | 40 B | 32 B |

Minimal otherwise comparable Arduino sketches compiled as follows:

| Sketch | RAM | IRAM | Flash code |
|---|---:|---:|---:|
| Standardized FP32 | 28,136 B | 59,143 B | 231,748 B |
| Fused-affine FP32 | 28,072 B | 59,143 B | 231,700 B |
| Q15 with pre-quantized input | 28,064 B | 59,143 B | 231,780 B |
| Q15 with float input conversion | 28,128 B | 59,143 B | 231,988 B |

Against standardized FP32, the fused sketch used 64 fewer RAM bytes and 48 fewer flash-code bytes. The pre-quantized Q15 sketch used 72 fewer RAM bytes but 32 more flash-code bytes. These small differences include linked code, input arrays, and sink types; they are not a byte-exact decomposition of model-only binary size.

The full comparison firmware, which intentionally embeds all three models, four benchmark reporters, and 933-row validation logic, used 30,716/80,192 RAM bytes (38%), 60,591/65,536 IRAM bytes (92%), and 301,348/1,048,576 flash-code bytes (28%). It is a research image, not the proposed production image.

## Implementation complexity

| Representation | Complexity | Main risk |
|---|---|---|
| Standardized FP32 | Low | Eight slow software floating-point divisions |
| Fused-affine FP32 | Low | Must regenerate fused weights whenever preprocessing/model changes |
| Q15 pre-quantized | Medium–high | Requires fixed-point feature acquisition, clipping policy, lag-buffer contract, and overflow analysis |
| Q15 with per-call conversion | Medium | Conversion overhead removes the latency advantage |

## Selection decision

**Use fused-affine FP32 for the current paper and prototype.** It provides the clearest deployability improvement with the smallest change in system assumptions.

Retain Q15/Q30 as a demonstrated optional path for the future live device. It becomes attractive only if:

1. sensor values are normalized and quantized once when acquired;
2. the 336-sample lag buffer stores Q15 values;
3. calendar features are generated directly as integer codes;
4. clipping bounds are validated on the new physical dataset;
5. overflow tests and cross-platform parity remain in continuous testing.

## Paper-ready wording

> Algebraically folding feature standardization into the FP32 coefficients reduced mean ESP8266 kernel time from 50.6268 to 16.3320 µs, a 3.10× speedup, while preserving all 933 held-out residual decisions. A Q15/Q30 kernel with pre-quantized inputs further reduced mean kernel time to 8.8462 µs and also preserved all decisions. However, quantizing eight floating-point inputs within each prediction increased mean time to 54.3470 µs. We therefore selected fused FP32 as the current deployment representation and treat fixed point as conditional on maintaining an integer-valued acquisition and lag-buffer pipeline.

## Reproduction commands

```powershell
& '<project-python>' tools/run_phase14_quantization.py
& '<project-python>' tools/test_fixed_model_cpp.py
powershell -ExecutionPolicy Bypass -File tools/esp8266_workflow.ps1 -Action Upload -Port COM11 -FullValidation
powershell -ExecutionPolicy Bypass -File tools/capture_esp8266_serial.ps1 -Port COM11 -DurationSeconds 90
& '<project-python>' tools/parse_phase14_device_capture.py data/esp8266/esp8266_serial_20260903_032018.jsonl
```

Key artifacts:

- `outputs/phase14_quantization_results.json`
- `outputs/phase14_fixed_cpp_parity.json`
- `outputs/phase14_device_quantization.json`
- `outputs/phase14_firmware_builds.json`
- `firmware/esp8266_smart_meter/tinyml_fused_model.h`
- `firmware/esp8266_smart_meter/tinyml_fixed_model.h`

The raw physical capture is locally retained with SHA-256 `5C981B1B789514BF30B714C781912620450C794279741465E11CAAC7FF519864`.

## Phase decision

Fused-affine FP32 is accepted as the current deployment recommendation. Q15/Q30 is a verified conditional optimization, not the default. Phase 15 will define an energy-per-inference measurement protocol and required hardware without fabricating measurements from timing data.
