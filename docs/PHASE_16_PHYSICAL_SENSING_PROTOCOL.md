# Phase 16 — Future Physical Smart-Meter Validation Protocol

## Outcome

Phase 16 is complete as a future hardware-validation design. The current project has **not** performed calibrated voltage sensing, current sensing, real-power measurement, or energy metering. The unconnected ESP8266 `A0` values and placeholder `load_kw` conversion remain connectivity demonstrations only.

The recommended research architecture uses galvanically isolated voltage and current sensing, a simultaneous-sampling external ADC, a calibrated reference power analyzer, and staged validation beginning at safe isolated low voltage. Any mains-connected construction or installation must be performed and reviewed by a qualified person in a suitable enclosure.

## Why the current A0 prototype is not a smart meter

The ESP8266EX contains one 10-bit SAR ADC. Espressif documents a 0–1.0 V external input range for the bare-chip TOUT input, while NodeMCU development boards may add clone-specific dividers. Espressif also notes that Wi‑Fi and internal current-state changes can affect ADC behavior.

For real power, voltage and current waveforms must be sampled with known timing and phase. A single on-chip channel cannot sample both simultaneously. Therefore the current expression:

```text
prototype_load = raw_adc / 1023 × 2.0
```

has no calibrated electrical meaning and must be removed from the scientific measurement path.

## Recommended architecture

```text
Isolated voltage transducer ─┐
                             ├─ signal conditioning ─ simultaneous ADC ─ SPI ─ ESP8266
Split-core current transformer┘                                      │
                                                                    ├─ power/energy calculation
                                                                    ├─ 30-minute aggregation
                                                                    ├─ lag-history buffer
                                                                    └─ fused-FP32 forecast/anomaly logic
```

### Voltage channel

Use an approved isolated low-voltage AC-AC adapter or certified isolated voltage transducer. An AC-AC adapter provides galvanic isolation from mains and produces a low-voltage waveform that can be conditioned for the ADC. Do not implement a direct mains resistor divider on a breadboard.

The conditioning circuit requires reviewed scaling, bias/common-mode design, anti-alias filtering, input protection, and component voltage/power ratings. Exact resistor values must be calculated for the selected adapter and ADC after their datasheets and tolerances are fixed; the missing 22 kΩ resistor is therefore not the current blocker.

### Current channel

Use a split-core current transformer so the conductor does not need to be cut. Select either a voltage-output CT with an internal burden or a current-output CT with a correctly rated external burden and protection network.

Never leave a current-output CT secondary open-circuit while it surrounds an energized conductor. The burden, clamp/protection elements, anti-alias filter, and ADC full-scale range must be designed together.

### ADC

A two-channel simultaneous-sampling converter is preferred. Texas Instruments specifies the ADS131M02 as a two-channel, 24-bit, simultaneous-sampling delta-sigma ADC with rates up to 64 kSPS, SPI, programmable gain, phase calibration, and energy-metering applications.

This recommendation does not mean a bare ADS131M02 should be wired casually on a breadboard. Use a reviewed PCB or evaluation platform with correct supplies, reference, grounding, protection, sensor conditioning, creepage, and enclosure design.

### Reference instrument

Use a calibrated power/energy analyzer with documented voltage, current, real-power, power-factor, and accumulated-energy accuracy. A basic multimeter alone cannot provide a complete phase-aware real-power reference. Record instrument model, serial number, calibration status, range, accuracy specification, and measurement boundary.

## Safer staged implementation

### Stage A — Firmware and low-voltage simulation

- Continue using fixed vectors and synthetic sensor streams.
- Implement timestamp synchronization, missing-sample handling, 30-minute aggregation, and the 336-sample circular history buffer.
- Verify fused-FP32 and optional Q15 results against Python.
- No mains connection.

### Stage B — Isolated low-voltage AC bench

- Use an isolated low-voltage AC supply.
- Test resistive loads at several known levels.
- Compare ADC-derived voltage/current/power with a suitable low-voltage reference setup.
- Characterize offset, gain, noise, linearity, clipping, and temperature drift.
- Validate firmware calculations before any mains-connected trial.

### Stage C — Enclosed mains validation

- Qualified person performs installation and review.
- Use certified isolation components, fuse/protection, strain relief, flame-rated enclosure, and compliant PCB spacing.
- Keep the user and computer isolated from hazardous conductors.
- Begin with known commercial loads and a calibrated reference analyzer.
- Stop if reference disagreement, heating, instability, or clipping is observed.

### Stage D — Field dataset

- Collect synchronized 30-minute energy intervals for long enough to populate a 336-sample one-week lag and multiple evaluation weeks.
- Preserve raw waveform summaries and reference readings.
- Annotate switching events and faults only when their physical cause is known.
- Split calibration, development, and final evaluation chronologically.

## Signal-processing and metering equations

At an initial simultaneous sampling target such as 4 kSPS per channel for 50 Hz evaluation, calculate over exact timestamped windows:

```text
Vrms = sqrt(mean(v[n]^2))
Irms = sqrt(mean(i[n]^2))
real power = mean(v[n] × i[n])
apparent power = Vrms × Irms
power factor = real power / apparent power
energy = Σ (real power over window × window duration)
```

Before these equations, remove calibrated channel offsets and apply voltage/current gain and phase corrections. For non-sinusoidal loads, retain sufficient sample rate and bandwidth to capture relevant harmonics.

Aggregate calibrated energy into 30-minute intervals to match the current forecasting contract. The live device must then maintain lag 1, lag 2, lag 48, and lag 336 values plus calendar features. Weather inputs remain excluded because Phase 7 found no meaningful benefit and their original provenance was uncertain.

## Calibration procedure

1. **Zero test:** record both channels with no applied signal to estimate offset, noise, and drift.
2. **Voltage gain:** compare several isolated voltage levels with the reference instrument.
3. **Current gain:** use multiple known current levels spanning the intended range.
4. **Phase correction:** use a resistive load first, then loads with different power factors.
5. **Linearity:** fit calibration coefficients on designated calibration points only.
6. **Held-out validation:** reserve independent load levels and time periods for final accuracy evaluation.
7. **Energy integration:** compare accumulated Wh over sufficiently long intervals, not only instantaneous watts.
8. **Repeatability:** repeat after warm-up and at different board temperatures.
9. **Clipping and overload:** verify that rated maximum inputs do not saturate the ADC or exceed component ratings.

Do not tune coefficients on the same readings later reported as final accuracy.

## Known-load experiment matrix

| Load category | Purpose | Examples only |
|---|---|---|
| Zero/no load | Offset and false-energy drift | Sensor installed, load disconnected |
| Low resistive | Low-end sensitivity | Approved lamp or resistor fixture |
| Medium/high resistive | Gain and linearity | Approved heater/kettle under supervision |
| Inductive | Phase and power factor | Fan or small motor |
| Electronic/nonlinear | Harmonics and crest factor | LED driver or laptop supply |
| Step changes | Transient response | Controlled load switching |

Actual equipment must be selected within sensor, supply, enclosure, and reference-instrument ratings.

## Accuracy and uncertainty reporting

For voltage, current, real power, and energy, report:

- signed error and absolute error;
- MAE and RMSE;
- percentage error, excluding or separately treating near-zero denominators;
- maximum absolute error;
- bias and 95% agreement limits or an equivalent difference analysis;
- calibration versus held-out results;
- repeatability across runs;
- missing data and packet loss;
- uncertainty contributions from reference instrument, sensors, burden/divider tolerances, ADC gain/reference, phase correction, sampling clock, temperature, and numerical integration.

Define acceptance criteria before viewing final-test results. Example targets must come from the intended application or publication venue rather than being retrofitted to observed performance.

## Required evidence before stronger claims

The project may be described as a calibrated smart-meter/edge-ML prototype only after it has:

1. reference-traceable voltage, current, real-power, and energy results;
2. a documented uncertainty budget;
3. held-out calibration validation;
4. synchronized timestamps and packet-loss reporting;
5. live operation of the 336-sample history buffer;
6. edge/cloud prediction agreement on newly collected physical data;
7. anomaly labels tied to independently verified physical events;
8. a reviewed safety boundary and enclosed installation.

## Primary sources

- Espressif, ESP8266EX ADC and electrical documentation: https://documentation.espressif.com/0a-esp8266ex_datasheet_en.html
- Espressif, ESP8266 ADC FAQ/resources: https://www.espressif.com/en/products/socs/esp8266ex/resources
- Texas Instruments, ADS131M02 product page and datasheet: https://www.ti.com/product/ADS131M02
- OpenEnergyMonitor, isolated AC-AC adapter voltage sensing: https://docs.openenergymonitor.org/electricity-monitoring/voltage-sensing/measuring-voltage-with-an-acac-power-adapter.html

## Phase decision

Physical energy sensing remains future work and is separated from the current paper’s verified HIL contribution. The immediate software milestone is a live timestamped aggregation and lag-buffer implementation tested with synthetic or safely replayed data. Phase 17 will identify stronger official datasets suitable for the next embedded-ML research project.
