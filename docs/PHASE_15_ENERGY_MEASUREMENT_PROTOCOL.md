# Phase 15 — Future Energy-per-Inference Measurement Protocol

## Outcome

Phase 15 is complete as a future experimental protocol. **No energy-per-inference measurement has been performed.** The current timing results cannot be converted into measured energy because supply voltage and time-varying current were not recorded.

The recommended practical instrument is a Nordic Power Profiler Kit II (PPK2) used with long inference batches and a GPIO timing marker. A Joulescope JS220 is the higher-performance alternative for finer transient measurements. An ordinary multimeter is not fast enough to resolve 9–51 µs inference events, although it remains useful for general electrical checks.

## Why time alone is insufficient

Electrical energy is:

```text
E = integral(V(t) × I(t) dt)
```

For sampled measurements:

```text
E_batch = Σ [V[k] × I[k] × Δt]
```

Knowing only inference time does not reveal the current waveform. ESP8266 current changes with CPU, radio, sleep state, board regulator, LEDs, USB-UART circuitry, and firmware activity. Therefore `voltage × datasheet current × measured time` is not an experimental result.

## Required hardware

### Recommended lower-cost research setup

1. Nordic Power Profiler Kit II.
2. Two data-capable USB cables if the source configuration needs its full current capability.
3. Short power leads/jumpers suitable for the selected board rail.
4. One jumper from an ESP8266 GPIO timing marker to a PPK2 digital input.
5. The NodeMCU/ESP8266 board and a computer running nRF Connect for Desktop with the Power Profiler application.
6. Optional USB isolator or isolated serial adapter if simultaneous debugging is required and the power topology has been reviewed.

Nordic specifies a 200 nA–1 A measurement range, 100 ksps sampling, source and ammeter modes, and digital inputs for code-synchronized capture. The high-current range has materially lower accuracy than a precision laboratory power analyzer, so instrument uncertainty must be included.

### Higher-performance setup

1. Joulescope JS220.
2. Stable external supply appropriate for the selected measurement boundary.
3. Rated leads and a GPIO trigger connection.
4. Joulescope software for simultaneous voltage/current capture and energy integration.

The JS220 specification lists 300 kHz bandwidth and 2 MS/s simultaneous current and voltage ADC sampling. This is better suited to examining short transients, although batched inference remains preferable for repeatability.

### INA219 position

An INA219 module is useful for slower board-level current and power monitoring, and Texas Instruments documents it as an I²C current/power monitor. It is not selected for resolving a single 8.8–50.6 µs inference. It may be used only for long-batch average-power screening, not as the primary publication instrument for microsecond event energy.

## Define the measurement boundary first

Two valid but different experiments are possible.

| Boundary | Supply point | Includes | Excludes |
|---|---|---|---|
| ESP8266-side board rail | Confirmed 3.3 V rail | Module and downstream 3.3 V loads | Bypassed USB input/regulator losses |
| Complete development board | Confirmed 5 V/VIN or approved board input | Regulator and other powered board components | Host PC and network infrastructure |

The exact NodeMCU clone power circuit must be inspected before connecting an external source. Do not power the board simultaneously from USB and an external 3.3 V source unless the board schematic and isolation arrangement explicitly make it safe. The paper must state which boundary was measured.

## Firmware instrumentation

Use a dedicated benchmark build with one otherwise unused GPIO:

```cpp
digitalWrite(MEASURE_PIN, HIGH);
for (uint32_t i = 0; i < N; ++i) {
  benchmarkSink += inference(...);
}
digitalWrite(MEASURE_PIN, LOW);
```

The volatile sink prevents the compiler from deleting the inference loop. The GPIO rising and falling edges define the integration window in the power-profiler trace.

At 100 ksps, one sample occurs every 10 µs. The fastest pre-quantized Q15 kernel is shorter than one sample, so single-call PPK2 waveforms are inadequate. Use approximately one million predictions per marked batch, producing multi-second windows that can be integrated reliably.

## Experimental design

Test these representations:

- standardized FP32;
- fused-affine FP32;
- Q15/Q30 with inputs already stored in Q15 form.

Use two separately reported conditions:

1. Wi‑Fi disabled to isolate model computation.
2. Wi‑Fi connected but with transmissions prohibited during the marked batch, representing system context without packet spikes inside the integration window.

For each representation and condition:

1. Use one board, supply voltage, CPU frequency, compiler version, and optimization level.
2. Execute five unrecorded warm-up batches.
3. Record at least 30 batches of one million predictions.
4. Interleave or randomize representation order to reduce temperature and time drift.
5. Record matched idle/no-op windows under the same condition.
6. Retain raw profiler files, firmware hash, model fingerprint, and ambient notes.
7. Repeat on another board if device-to-device generalization is claimed.

## Calculation

For each marked batch:

```text
gross energy per inference = E_batch / N
incremental energy per inference = (E_batch − P_idle × T_batch) / N
average batch power = E_batch / T_batch
```

Report gross and baseline-subtracted incremental energy separately. Gross energy describes the powered device during computation; incremental energy attempts to isolate added computational cost and is sensitive to how the baseline is defined.

Summarize the 30 batches using median, interquartile range, p5–p95, mean, standard deviation, and confidence intervals over batch-level observations. Do not treat individual profiler samples as independent experiments.

## Uncertainty budget

At minimum, account for:

- profiler current and voltage accuracy in the active range;
- range switching, burden voltage, and supply droop;
- sample timing and GPIO edge alignment;
- between-batch repeatability;
- board temperature and radio-state variability;
- baseline subtraction;
- voltage measurement location;
- board-to-board variation if relevant.

Propagate voltage, current, and time uncertainties or use batch resampling when the waveform integration software supplies energy directly. State instrument model, firmware/software version, range behavior, sampling configuration, and calibration status.

## Datasheet-only sensitivity calculation

Espressif gives a 15 mA modem-sleep example in which the CPU remains operational and the Wi‑Fi modem is disabled. If—purely illustratively—3.3 V and 15 mA are multiplied by the measured kernel times, the products are:

| Path | Illustrative product |
|---|---:|
| Standardized FP32 | 2.506 µJ/inference |
| Fused-affine FP32 | 0.808 µJ/inference |
| Pre-quantized Q15 | 0.438 µJ/inference |
| Q15 including float conversion | 2.690 µJ/inference |

These are **not measured values**, are not estimates of the Wi‑Fi-enabled NodeMCU experiment, omit development-board losses and dynamic current, and must not appear in the manuscript’s experimental results. Their only purpose is to show how a future calculation would combine voltage, current, and time.

## Safety and practical limits

- This experiment measures the low-voltage ESP8266 supply only; it does not require or authorize any mains connection.
- Confirm polarity and the selected board rail before powering the board.
- Respect the profiler’s voltage/current limits and transient-current requirements.
- Prevent USB and external supplies from back-powering each other.
- Start with current limiting enabled where supported.
- Stop if the board, cable, or instrument becomes warm or unstable.

## Primary sources

- Nordic Semiconductor, Power Profiler Kit II product page: https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2
- Nordic Semiconductor, PPK2 measurement resolution: https://docs.nordicsemi.com/r/bundle/ug_ppk2/page/ug/ppk/ppk_measure_resolution.html
- Nordic Semiconductor, PPK2 measurement accuracy: https://docs.nordicsemi.com/r/bundle/ug_ppk2/page/ug/ppk/ppk_measure_accuracy.html
- Joulescope JS220 description and specifications: https://download.joulescope.com/products/JS220/JS220-K000/description.html
- Espressif, ESP8266EX datasheet: https://documentation.espressif.com/0a-esp8266ex_datasheet_en.html
- Texas Instruments, INA219 product and datasheet: https://www.ti.com/product/INA219

## Phase decision

Energy per inference remains explicitly future work. Timing reductions may motivate the experiment, but they are not energy measurements. Phase 16 will specify the separate isolated and calibrated electrical-sensing validation required for a genuine smart-meter prototype.
