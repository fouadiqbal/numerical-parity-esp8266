# Phase 27: Final LaTeX Paper

Status: **complete**  
Build date: 2026-09-03

## Deliverables

- Submitted conference paper: `manuscript/smart_meter_esp8266_edge_ml.pdf`
- Earlier repository implementation source: `manuscript/smart_meter_esp8266_edge_ml_repository_source.tex`
- BibTeX library: `references/references.bib`
- Build notes: `manuscript/README.md`
- Validation record: `outputs/phase27_final_paper_validation.json`

## Paper scope

The manuscript presents a bounded chronological case study of transferring a compact forecasting and residual-decision computation from Python to generated C++ and a physical ESP8266. It reports forecasting, threshold sensitivity, complete 933-row host/device parity, model-kernel timing, and whole-firmware resource evidence. It does not claim calibrated electrical sensing, verified kWh, real-event anomaly ground truth, energy efficiency, secure field operation, or algorithmic novelty.

The ESP32 field-validation section is intentionally reserved and contains no fabricated results. It specifies the measurements that must be added after a calibrated sensing experiment.

## Included publication material

- 6 conference-paper pages;
- 13 bibliography entries;
- 4 numbered tables;
- 5 numbered figure environments using 6 generated figure images;
- normalized-unit forecasting results and uncertainty;
- threshold/anomaly-method sensitivity;
- Python, host-C++, and physical ESP8266 parity;
- timing and whole-firmware RAM/IRAM/flash evidence;
- limitations, reproducibility, data availability, and future-work statements.

## Build and quality checks

The submitted PDF was rendered to six page images and visually inspected; no clipping, overlap, missing content, or unreadable tables/figures were found. Its 13 references and six embedded figures are retained for reviewer access.

The submitted PDF is the authoritative conference version. The earlier
repository implementation source is retained separately and is explicitly
labelled as a source snapshot in `manuscript/README.md`.
