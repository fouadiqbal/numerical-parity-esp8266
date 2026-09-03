# Phase 13 — ESP8266 Resource and Operation Analysis

## Outcome

Phase 13 is complete. The deployable model has 9 trainable parameters, 26 total stored `float32` values when preprocessing and the anomaly threshold are included, and 104 bytes of core numeric state. Its source-level prediction equation performs 32 scalar arithmetic operations. Whole-firmware memory remains acceptable, but instruction RAM—not flash—is the main engineering constraint.

## Model-state accounting

| State | Count | `float32` bytes |
|---|---:|---:|
| Linear coefficients | 8 | 32 |
| Intercept | 1 | 4 |
| Feature means | 8 | 32 |
| Feature scales | 8 | 32 |
| Residual threshold | 1 | 4 |
| **Total deployed numeric state** | **26** | **104** |

The conventional trainable-parameter count is 9: eight coefficients plus one intercept. The means, scales, and threshold are fitted deployment state but are not trainable linear-model parameters.

Feature-name strings, C++ function instructions, array metadata, compiler alignment, the Arduino runtime, and application code are not included in the 104-byte numeric-state figure.

## Operation accounting

For each of eight features, the current source performs one subtraction, one division, one multiplication, and one accumulation addition:

| Operation | Count per prediction |
|---|---:|
| Subtractions | 8 |
| Divisions | 8 |
| Multiplications | 8 |
| Accumulation additions | 8 |
| **Core scalar arithmetic operations** | **32** |

The residual decision adds one subtraction, one absolute-value operation, and one comparison when the actual observation is available.

This is source-level operation counting, not a cycle count or instruction count. Compiler optimization, software floating-point implementation, and possible instruction expansion mean that “32 operations” must not be converted directly into CPU cycles.

## Validation payload is not model size

The public header includes eight spot-check vectors. Their raw numeric payload is approximately 328 bytes. The local full-validation header contains approximately 39,186 bytes of numeric test payload. The observed flash-code difference between normal and full-validation builds is 40,336 bytes, which is consistent with payload plus compilation overhead.

These held-out features, targets, expected predictions, and labels are experimental test data. They must not be counted as model parameters or included in a production firmware image.

## Whole-firmware resources

The current benchmark-ready firmware compiled as follows:

| Resource | Normal used | Normal headroom | Full-validation used | Full-validation headroom |
|---|---:|---:|---:|---:|
| RAM | 29,516 / 80,192 B (36.81%) | 50,676 B (63.19%) | 29,852 / 80,192 B (37.23%) | 50,340 B (62.77%) |
| Instruction RAM | 60,343 / 65,536 B (92.08%) | 5,193 B (7.92%) | 60,343 / 65,536 B (92.08%) | 5,193 B (7.92%) |
| Flash code | 257,796 / 1,048,576 B (24.59%) | 790,780 B (75.41%) | 298,132 / 1,048,576 B (28.43%) | 750,444 B (71.57%) |

These figures describe the whole firmware: ESP8266 core support, Wi‑Fi, HTTP, serial formatting, telemetry, self-test code, model code, and application state. They are not an isolated model footprint.

## Engineering interpretation

The compact model state is tiny relative to available RAM and flash. The important constraint is IRAM: only 5,193 bytes remain in both builds. Adding TLS, signal-processing libraries, or more interrupt-resident code may fail even when ordinary flash and data RAM appear plentiful.

Before any production claim:

1. Remove full-validation payloads and verbose self-test reporting.
2. Recompile after each networking, cryptography, DSP, or library change.
3. Generate and retain a linker map if an isolated code-size contribution is claimed.
4. Report both ordinary RAM and IRAM; neither can substitute for the other.
5. Keep a production configuration separate from the reproducibility/validation configuration.

## Paper-ready wording

> The linear forecaster contains nine trainable parameters. Including eight feature means, eight scales, and one residual threshold, deployment requires 26 32-bit numeric values (104 bytes), excluding code and metadata. The source-level prediction equation uses eight subtractions, eight divisions, eight multiplications, and eight accumulation additions. The complete benchmark-ready firmware occupied 29,516 of 80,192 data-RAM bytes and 257,796 of 1,048,576 flash-code bytes. Instruction RAM usage was 60,343 of 65,536 bytes, leaving 5,193 bytes and representing the principal integration constraint.

## Claims not supported

- “The complete model occupies exactly 104 bytes in the binary.”
- “The model requires exactly 32 CPU instructions or 32 cycles.”
- “All 29,516 RAM bytes are caused by machine learning.”
- “The 933-vector validation image represents production memory use.”
- “Large flash headroom guarantees that additional libraries will fit in IRAM.”

## Reproduction command

```powershell
python tools/run_phase13_resource_analysis.py
```

The machine-readable record is `outputs/phase13_resource_analysis.json`.

## Phase decision

The FP32 linear model is resource-feasible on the ESP8266. Phase 14 will test reduced precision against FP32 and will retain it only if it provides a measured advantage without unacceptable prediction or decision changes.
