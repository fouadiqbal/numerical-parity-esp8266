# Phase 22 — Publication Tables

## Outcome

Phase 22 is complete. Eleven required tables were generated from the repository's versioned evidence artifacts. Each table has a CSV source, and the complete set is available in both Markdown and LaTeX form.

Table 11 was subsequently populated from the verified Phase 23 peer-reviewed gap-analysis artifact. Its citation keys map to `references/references.bib`. Because Phase 23 is a targeted rather than systematic review, Table 11 does not support a worldwide “first” claim.

## Main-paper tables

| No. | Table | Purpose |
|---:|---|---|
| 1 | Dataset characteristics | Defines the analyzed normalized case-study data and its provenance limitations. |
| 5 | Walk-forward results | Reports the stronger five-fold expanding-window forecasting evaluation. |
| 7 | Anomaly detection results | Compares residual and Isolation Forest methods against supplied labels. |
| 9 | ESP8266 numerical parity | Connects Python, host C++, and physical-device evidence. |
| 10 | Hardware resource utilization | Reports RAM, IRAM, flash, and core numeric state without conflating them. |
| 11 | Comparison with related studies | Compares the work with ten source-verified studies selected in Phase 23. |

## Supplementary tables

| No. | Table | Purpose |
|---:|---|---|
| 2 | Forecasting models | Preserves model configurations and experimental roles. |
| 3 | Chronological splits | Makes holdout, compact calibration, and walk-forward windows auditable. |
| 4 | Single-holdout results | Retains the preliminary forecasting comparison. |
| 6 | Feature ablation | Reports six feature-group variants over identical temporal folds. |
| 8 | Threshold sensitivity | Shows the precision/recall/alert-rate trade-off across residual percentiles. |

This division gives the short paper six primary tables while retaining all requested evidence in the supplement. Depending on the venue's page limit, Tables 1 and 10 may be shortened in the manuscript while the full CSV versions remain supplementary.

## Generated artifacts

- `tables/publication_tables.md`: readable master table set with captions and notes.
- `tables/publication_tables.tex`: LaTeX table blocks for an IEEE-style manuscript; requires `booktabs` and `graphicx`.
- `tables/publication_tables_standalone.tex`: minimal wrapper used to compile-check all LaTeX tables.
- `tables/table01_*.csv` through `tables/table11_*.csv`: one machine-readable file per table.
- `outputs/phase22_table_manifest.json`: placement, status, source paths, row counts, sizes, and SHA-256 hashes.
- `tools/run_phase22_tables.py`: deterministic table generator.

## Evidence and wording safeguards

1. Forecasting MAE and RMSE are labeled as normalized target units because physical kWh cannot be recovered from the source file.
2. Anomaly classification is described as agreement with publisher-supplied algorithmic labels, not detection of validated electrical events.
3. The physical ESP8266 experiment is described as replayed held-out-vector hardware-in-the-loop validation, not live sensor validation.
4. Device timing is identified as model-kernel timing based on 30 batch averages, not sensing-to-cloud latency or individual-cycle timing.
5. Whole-firmware RAM, IRAM, and flash are separated from the 104-byte core numeric model state.
6. Table 11 contains only Phase 23 records checked against publisher/proceedings/DOI sources.

## Reproduction and audit

Run from the repository root:

```powershell
python tools/run_phase22_tables.py
```

The generator reads existing JSON evidence directly, rewrites all table artifacts, and produces a manifest with hashes. It does not download data, retrain a model, contact external services, or expose ignored credentials and validation payloads.

## Phase decision

The evidence is now organized into a paper-sized main set and a complete supplementary set. Phase 23 has replaced the Table 11 placeholder with source-verified comparisons. Cross-study accuracy values are deliberately not ranked because the datasets, tasks, units, and evaluation protocols are incompatible.
