# Smart-Meter Forecasting and ESP8266 Edge-ML Reproducibility Package

This package reproduces the project's bounded claim: a compact nine-parameter forecasting computation and residual-threshold decision were transferred from Python to generated C++ and reproduced on a physical ESP8266 over a 933-row held-out partition. It does **not** claim calibrated smart-meter sensing, verified physical kWh, real-world anomaly detection, measured energy per inference, or a worldwide first.

## Package map

- `data/`: source acquisition, hashes, units warning, and deterministic split indices;
- `notebooks/`: output-cleared baseline notebook (51 code cells; 0 stored outputs removed);
- `src/`: preprocessing, forecasting, anomaly, export, parity, and figure/table scripts;
- `models/`: model manifest and parameter provenance;
- `esp8266/`: Arduino firmware, generated headers, credential template, capture tools, and build workflow;
- `results/`: aggregate JSON/CSV evidence and tables, without row-level predictions;
- `figures/`: 10 figures in PNG, PDF, and SVG;
- `tests/`: host-C++ and Arduino size-test sources;
- `references/`: verified Phase 23 BibTeX library;
- `manuscript/`: the authoritative six-page conference PDF, retained implementation source, and review notes;
- `docs/`: phase reports and evidence boundaries.

## Exact environment

Python evidence was generated with Python 3.13.2, NumPy 2.5.2, pandas 3.0.5, scikit-learn 1.9.0, SciPy 1.18.1, Matplotlib 3.11.1, and Seaborn 0.13.2. Randomized experiments use seed **42**. Create the environment with either:

```bash
conda env create -f environment.yml
conda activate smart-meter-esp8266-repro
```

or:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

## Reproduce the software experiments

Acquire and verify the dataset exactly as described in `data/README.md`, then run from the package root:

```bash
python src/audit_dataset.py
python src/run_phase4_forecasting.py
python src/run_phase5_walk_forward.py
python src/run_phase6_statistics.py
python src/run_phase7_ablation.py
python src/run_phase8_threshold_sensitivity.py
python src/run_phase9_anomaly_methods.py
python src/train_tinyml_edge_model.py
python src/test_generated_cpp_model.py
python src/run_phase14_quantization.py
python src/test_fixed_model_cpp.py
python src/run_phase21_figures.py
python src/run_phase23_related_work.py
python src/run_phase22_tables.py
```

Training regenerates two ignored local files: `results/tinyml_edge_test_predictions_v2.csv` and `esp8266/tinyml_validation_data.h`. They are required for local parity/full-device validation but must not be committed.

## Reproduce the ESP8266 experiment

1. Install Arduino IDE and the ESP8266 board core.
2. Copy `esp8266/secrets.example.h` to a private `esp8266/secrets.h`, or point the workflow to an existing private credential sketch.
3. Connect a NodeMCU 1.0/ESP8266EX with a data-capable USB cable and identify its COM port.
4. Build the public eight-vector self-test firmware:

   ```powershell
   powershell -ExecutionPolicy Bypass -File esp8266/esp8266_workflow.ps1 -Action Build -Port COM11
   ```

5. After acquiring the dataset and running `src/train_tinyml_edge_model.py`, upload the locally generated full-validation build:

   ```powershell
   powershell -ExecutionPolicy Bypass -File esp8266/esp8266_workflow.ps1 -Action Upload -Port COM11 -FullValidation
   ```

6. Close Arduino Serial Monitor and capture at least 90 seconds:

   ```powershell
   powershell -ExecutionPolicy Bypass -File esp8266/capture_esp8266_serial.ps1 -Port COM11 -DurationSeconds 90
   ```

7. Parse the private capture into aggregate evidence:

   ```bash
   python src/parse_phase11_device_capture.py data/esp8266/<capture>.jsonl --port COM11
   python src/parse_phase12_timing_capture.py data/esp8266/<capture>.jsonl
   ```

The device replay is HIL verification of numerical execution, not live calibrated sensing. Never connect mains voltage directly to an ESP8266.

## Verified evidence snapshot

- Python/ESP8266 prediction agreement: 933/933;
- threshold-decision agreement: 933/933;
- maximum absolute difference: 0.000000089 normalized target units;
- timing evidence: 30 batches × 2,000 predictions, mean 50.427 microseconds;
- full HIL validation firmware: RAM 37%, flash 28%, IRAM 92%;
- staged public eight-vector firmware: RAM 37%, flash 24%, IRAM 92%;
- anomaly result: agreement with supplied pseudo-labels, recall 0.154.

## Data, licensing, and citation

The source listing displays CC0, but its upstream measurement provenance is undocumented. Raw data and the complete validation vectors are not distributed. Original repository code/documentation are MIT licensed. See `THIRD_PARTY_NOTICES.md`, `docs/PHASE_24_COPYRIGHT_LICENSING.md`, and `CITATION.cff`.
