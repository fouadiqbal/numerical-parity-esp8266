# Phase 25 — Reproducibility Package

Status: **complete; clean package generated and locally validated**  
Date: 2026-09-03  
Package: `release/smart-meter-esp8266-reproducibility/`

## Outcome

The release package is built from an explicit allowlist rather than by copying the local workspace. It contains the requested research-repository structure and excludes raw data, credentials, raw serial captures, row-level prediction/decision files, and the complete 933-vector validation header.

The package supports three distinct reproducibility layers:

1. **Software reproduction:** acquire the exact source CSV, verify its hash, rerun preprocessing, forecasting, anomaly analyses, model export, host-C++ parity, figures, and tables.
2. **Public firmware self-test:** compile the released ESP8266 sketch with eight compact regression vectors embedded in `tinyml_model.h`.
3. **Full physical reproduction:** locally regenerate `tinyml_validation_data.h`, upload the full-validation firmware, capture COM-port JSONL privately, and parse it into aggregate evidence.

## Required repository structure

| Requested item | Package implementation |
|---|---|
| `data/README.md` | Dataset URL/API command, Version 1, CC0 listing, exact hashes, schema warning, and no-redistribution rule |
| `notebooks/` | Baseline notebook with outputs and execution counts removed |
| `src/` | Preprocessing, experiments, model export, parity, physical-capture parsing, and figure/table generators |
| `models/` | Model manifest and model-artifact explanation |
| `esp8266/` | Firmware, three generated model headers, credential template, Arduino workflow, and serial capture utilities |
| `results/` | Aggregate JSON/CSV evidence and publication tables; no per-row predictions |
| `figures/` | Ten figures in PNG, PDF, and SVG |
| `requirements.txt` | Six direct Python dependencies pinned to evidence-generating versions |
| `environment.yml` | Named Python 3.13.2 environment with exact dependency versions |
| `README.md` | End-to-end software and physical-device reproduction instructions |
| `LICENSE` | MIT License for author-owned repository material |
| `CITATION.cff` | Software citation metadata without inventing a DOI or publication |

Additional folders provide `tests/`, `references/`, and `docs/`.

## Deterministic research metadata

- Global randomized-experiment seed: **42**.
- Dataset: Kaggle `ziya07/smart-meter-electricity-consumption-dataset`, Version 1.
- Extracted CSV SHA-256: `D48DF940FD29444FB9222FC0B59CFDE632E147CCD1D49DC7BED9D5F9DC88F588`.
- Exact split ranges: `data/split_indices.json`, using zero-based half-open ranges after chronological sorting and 336-row lag removal.
- Exact parameters: `models/model_manifest.json` and generated C++ headers.
- Exact environment: `requirements.txt` and `environment.yml`.
- Every packaged file: size and SHA-256 in `REPRODUCIBILITY_MANIFEST.json`.

## Deliberate exclusions

The package generator fails if it finds:

- `smart_meter_data.csv` or the source ZIP;
- `secrets.h`;
- `tinyml_validation_data.h`;
- known token/API-key patterns;
- stored notebook outputs.

Raw COM-port captures and row-level prediction/decision CSVs are also omitted. The `.gitignore` preserves these controls after users regenerate private artifacts locally.

The public `tinyml_model.h` retains eight small regression vectors required by the firmware self-test. The complete 933-row header remains excluded.

## Validation performed

The package builder checks denied filenames, likely secret patterns, and notebook output counts. Phase 25 validation additionally checks:

- requested top-level paths exist;
- the manifest hash for every packaged file is current;
- all source paths were adapted from `outputs/` to `results/` and from the original firmware layout to `esp8266/`;
- JSON and notebook artifacts parse;
- Python source compiles;
- no absolute local workspace path appears in the release;
- no disallowed row-level prediction/decision CSV is present.

Functional validation also passed:

- staged host-C++ model: 933/933 predictions and 933/933 threshold decisions matched, with maximum absolute difference `7.557157177817686e-08` normalized target units;
- staged public ESP8266 firmware build: 30,124/80,192 RAM bytes (37%), 60,463/65,536 IRAM bytes (92%), and 260,308/1,048,576 flash-code bytes (24%).

The exact validation record is `outputs/phase25_package_validation.json` in the development repository and `results/phase25_package_validation.json` in the staged package.

## Regeneration

From the development repository root:

```powershell
python tools/build_phase25_reproducibility_package.py
```

The builder only replaces the exact generated target after verifying its sentinel file. It will not delete an unrelated directory.

## Publication status

The package is ready for final claims auditing, but it has not been pushed to GitHub. Phase 26 must scan the final paper and public-facing README sentence by sentence for unsupported wording before a remote release or manuscript submission.
