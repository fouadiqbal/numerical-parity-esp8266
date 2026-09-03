# ESP8266 Smart-Meter Prototype

This firmware reads the ESP8266 `A0` input, calculates a placeholder load value,
flags readings above a demonstration threshold, drives the onboard LED, and sends
three fields to ThingSpeak every 20 seconds.

It also embeds a standardized linear forecasting model trained from the same Kaggle
dataset and eight lag/calendar features used by the notebook. Thirty seconds after
boot, the board runs held-out parity vectors and benchmarks the learned model's
inference time once, allowing a serial monitor time to attach.

## Current status

- Board upload tested on `COM11`
- 2.4 GHz Wi-Fi connection verified
- ThingSpeak HTTP response `200` verified
- ThingSpeak entry IDs verified
- Forced anomaly test verified with ADC `1000`, load `1.955 kW`, and anomaly `YES`
- Trained edge-model inference verified on the physical ESP8266
- Python/ESP8266 prediction and anomaly parity passed for all 933 held-out vectors
- Device inference time measured over 30 batches: mean `50.427 us` per prediction

The load conversion is not calibrated and must not be presented as a real power
measurement.

## Prepare credentials

1. Copy `secrets.example.h` to `secrets.h`.
2. Enter the Wi-Fi SSID, Wi-Fi password, and ThingSpeak Write API Key.
3. Keep `secrets.h` private. It is excluded by the repository `.gitignore`.

## Open in Arduino IDE

Open `esp8266_smart_meter.ino`, select the matching ESP8266 board, select `COM11`,
and upload. Use Serial Monitor at 115200 baud.

## Continue in VS Code

Open the repository folder in VS Code and edit the firmware files here. A
`platformio.ini` configuration is included for a NodeMCU 1.0 board on `COM11`.
If PlatformIO is installed, open this firmware directory as the project and use
its Build, Upload, and Monitor actions. Otherwise, continue uploading the `.ino`
file through Arduino IDE.

This local workspace also includes VS Code tasks that use Arduino IDE's bundled
CLI and obtain credentials from the existing private Arduino sketch without
copying them into the repository:

- `ESP8266: Build`
- `ESP8266: Upload COM11`
- `ESP8266: Monitor COM11`

Run them from **Terminal → Run Task** in VS Code. The workflow creates a temporary
private build directory and removes it after building or uploading.

For a controlled diagnostic without connecting anything to `A0`, run the workflow
with `-TestMode`. It transmits ADC values `100`, `500`, `900`, and `1000` in order.
The repository source remains in normal A0 mode because the change exists only in
the temporary build copy.

Expected serial records use JSON Lines format:

```json
{"uptime_ms":20000,"raw_adc":10,"load_kw":0.020,"anomaly":0,"wifi_rssi_dbm":-55,"http_code":200,"thingspeak_entry_id":20}
```

From a PowerShell terminal at the repository root, capture these records with:

```powershell
powershell -ExecutionPolicy Bypass -File src/capture_esp8266_serial.ps1
```

Close Arduino Serial Monitor before running the capture tool because only one
program can own `COM11` at a time. Captures are written under `data/esp8266/` and
are excluded from version control.

Convert the latest JSONL capture to a Colab-ready CSV with:

```powershell
powershell -ExecutionPolicy Bypass -File src/convert_esp8266_jsonl_to_csv.ps1
```

## Verified hardware run — 2026-09-02

- Device detected as ESP8266EX with 4 MB flash
- Improved firmware compiled with 35% RAM and 24% flash usage
- Flash upload completed and its hash was verified
- Live ThingSpeak entry IDs `149`, `150`, and `151` returned HTTP `200`
- Local JSONL capture recorded entry IDs `153`, `154`, and `155`
- Observed raw ADC values were `15`–`18` with the analog input unconnected
- Observed Wi-Fi RSSI was approximately `-71` to `-77 dBm`

### Controlled diagnostic sequence

Because no resistor divider or multimeter was available, the complete pipeline was
tested with a temporary firmware-only ADC sequence. The source firmware remained in
normal A0 mode.

| ADC | Prototype load | Anomaly | ThingSpeak entry |
|---:|---:|---:|---:|
| 100 | 0.196 kW | 0 | 212 |
| 500 | 0.978 kW | 0 | 213 |
| 900 | 1.760 kW | 0 | 214 |
| 1000 | 1.955 kW | 1 | 215 |

The next value, ADC 100, returned the system to anomaly 0 at entry 216. Normal A0
firmware was then restored and verified with entries 219 and 220.

### TinyML edge-inference validation

The compact edge model was trained with `src/train_tinyml_edge_model.py` using
the same public dataset and feature schema as the notebook. The generated constants
and inference function are in `tinyml_model.h`. The public firmware runs eight
embedded held-out spot checks by default. On the ESP8266, these reproduced the
Python predictions and anomaly decisions.

| Measurement | Verified result |
|---|---:|
| Full prediction parity | 933/933 passed |
| Full anomaly-decision parity | 933/933 passed |
| Maximum Python/device difference | 0.000000089 normalized target units |
| Residual threshold | 0.383026 normalized target units |
| Timed predictions | 30 batches x 2,000 |
| Batch-average inference time | 50.361-50.700 us (mean 50.427 us) |
| Whole-firmware RAM use | 29,852 / 80,192 bytes (37%) |
| Whole-firmware flash-code use | 298,132 / 1,048,576 bytes (28%) |

The device test replays fixed held-out feature vectors. It proves that the trained
model executes correctly on the ESP8266, but it is not yet a live energy forecast:
real forecasting requires calibrated energy measurements and a timestamped history
buffer for the 1, 2, 48, and 336-sample lags. The corrected detailed benchmark
record is in `results/tinyml_device_benchmark_v2.json`; the earlier record is
retained for traceability.

The complete 933-row validation dataset is intentionally not committed because it
contains dataset-derived records. Download the source dataset, run
`src/train_tinyml_edge_model.py`, and use the workflow's `-FullValidation` switch
to generate and compile the local flash-resident validation header:

```powershell
powershell -ExecutionPolicy Bypass -File src/esp8266_workflow.ps1 -Action Upload -Port COM11 -FullValidation
```

The values in this validation are normalized dataset values. The source dataset
does not provide the inverse transformation needed to recover physical kWh, so the
validation must not be described as a calibrated energy measurement.

## ThingSpeak field map

| ThingSpeak field | Firmware value |
|---|---|
| Field 1 | `raw_adc` |
| Field 2 | `load_kw` |
| Field 3 | `anomaly` (`0` or `1`) |

## Safety

- Never connect mains voltage directly to the ESP8266.
- Confirm the permitted `A0` voltage range for the exact board before wiring a sensor.
- The bare ESP8266 ADC accepts 0–1.0 V; some NodeMCU boards include an input divider.
- Use an isolated and correctly conditioned sensor interface for field measurements.
- Keep the sensor stage disconnected until its schematic and component ratings have
  been reviewed.

## Next engineering milestones

1. Verify the exact board model and `A0` input range.
2. Select an isolated current-sensing circuit and document its ratings.
3. Collect calibration pairs from a trusted reference meter.
4. Replace the placeholder load conversion with a fitted calibration equation.
5. Export ThingSpeak data and compare edge anomaly flags with the Python model.
6. Measure packet loss, latency, memory use, and edge/cloud detection agreement.

## Security limitation

The current request uses HTTP to remain compatible with the already verified
prototype. The Write API Key is therefore not protected in transit. Before field
deployment, migrate to HTTPS with certificate validation or to a secured MQTT
workflow.
