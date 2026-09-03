# Results

This directory contains aggregate machine-readable evidence and publication tables. Row-level prediction and decision files are excluded from the release package.

Key evidence:

- `phase5_walk_forward_results.json`: five-fold expanding-window forecasting;
- `phase6_statistical_comparison.json`: paired loss-difference analysis;
- `phase9_anomaly_methods.json`: supplied-label agreement only;
- `tinyml_cpp_parity.json`: Python/host-C++ agreement;
- `tinyml_device_benchmark_v2.json`: physical ESP8266 HIL evidence;
- `phase12_device_timing_distribution.json`: 30 timing batches;
- `phase13_resource_analysis.json`: RAM, flash, and IRAM accounting;
- `tables/`: publication-ready aggregate CSV/Markdown/LaTeX tables.

Legacy keys containing `_kwh` do not establish physical units. Use the corrected normalized-unit records and documentation.
