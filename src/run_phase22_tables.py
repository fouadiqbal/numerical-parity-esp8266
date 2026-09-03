#!/usr/bin/env python3
"""Generate Phase 22 publication tables from verified local evidence artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
TABLE_DIR = ROOT / "tables"


@dataclass
class Table:
    number: int
    slug: str
    caption: str
    placement: str
    columns: list[str]
    rows: list[list[Any]]
    note: str
    sources: list[str]
    status: str = "complete"


def load_json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def f6(value: float) -> str:
    return f"{value:.6f}"


def f3(value: float) -> str:
    return f"{value:.3f}"


def pct(value: float) -> str:
    return f"{value:.2f}"


def dt(value: str) -> str:
    return value.replace("T", " ")[:16]


def display_name(value: str) -> str:
    names = {
        "compact_edge_linear": "Compact edge linear",
        "compact_edge_linear_float32": "Compact edge linear (FP32)",
        "linear_regression": "Linear regression",
        "random_forest": "Random forest",
        "hist_gradient_boosting": "Histogram gradient boosting",
        "seasonal_naive_lag_48": "Seasonal naive (lag 48)",
        "persistence_lag_1": "Persistence (lag 1)",
        "lag_plus_calendar_plus_weather": "Lag + calendar + weather",
        "weather_only": "Weather only",
        "calendar_only": "Calendar only",
        "lag_plus_calendar": "Lag + calendar",
        "lag_plus_weather": "Lag + weather",
        "lag_only": "Lag only",
        "split_conformal_95": "Split conformal (95%)",
        "adaptive_ewma_residual_p99": "Adaptive EWMA residual (p99)",
        "rolling_week_residual_p99": "Rolling-week residual (p99)",
        "static_residual_p99": "Static residual (p99)",
        "isolation_forest_5pct": "Isolation forest (5%)",
    }
    return names.get(value, value.replace("_", " ").title())


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def tex_escape(value: Any) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "±": r"$\pm$",
        "µ": r"$\mu$",
        "–": "--",
        "—": "---",
        "×": r"$\times$",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def config_text(model: dict[str, Any]) -> str:
    cfg = model["configuration"]
    name = model["model"]
    if name == "compact_edge_linear":
        return "Standardized least squares; 8 features; 2,984 fit + 747 calibration; FP32 deployment"
    if name == "linear_regression":
        return "OLS with intercept; 3,731 training rows"
    if name == "random_forest":
        return f"{cfg['n_estimators']} trees; depth {cfg['max_depth']}; min leaf {cfg['min_samples_leaf']}; seed {cfg['random_state']}"
    if name == "hist_gradient_boosting":
        return f"lr={cfg['learning_rate']}; iter={cfg['max_iter']}; leaves={cfg['max_leaf_nodes']}; min leaf={cfg['min_samples_leaf']}; L2={cfg['l2_regularization']}"
    if name == "seasonal_naive_lag_48":
        return "Previous-day value at 30-min sampling (lag 48)"
    return "Previous observation (lag 1)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def build_tables() -> list[Table]:
    ds = load_json("results/dataset_integrity.json")
    p4 = load_json("results/phase4_forecasting_results.json")
    p5 = load_json("results/phase5_walk_forward_results.json")
    p7 = load_json("results/phase7_feature_ablation.json")
    p8 = load_json("results/phase8_threshold_sensitivity.json")
    p9 = load_json("results/phase9_anomaly_methods.json")
    host = load_json("results/tinyml_cpp_parity.json")
    device = load_json("results/tinyml_device_benchmark_v2.json")
    timing = load_json("results/phase12_device_timing_distribution.json")
    p13 = load_json("results/phase13_resource_analysis.json")

    p4_by_name = {row["model"]: row for row in p4["results_sorted_by_mae"]}
    compact = p4_by_name["compact_edge_linear"]

    tables: list[Table] = []

    tables.append(Table(
        1,
        "dataset_characteristics",
        "Characteristics of the normalized smart-meter development dataset.",
        "main",
        ["Characteristic", "Value", "Interpretation"],
        [
            ["Source", ds["source_listing"], "Third-party Kaggle listing"],
            ["Local file fingerprint", ds["csv_sha256"], "SHA-256 identifies the exact analyzed CSV"],
            ["Rows / variables", f"{ds['rows']:,} / {len(ds['columns'])}", "Seven columns including timestamp and supplied label"],
            ["Time span", f"{dt(ds['first_timestamp'])} to {dt(ds['last_timestamp'])}", "Approximately 104 days"],
            ["Sampling interval", "30 min", f"{ds['non_30_minute_consecutive_intervals']} non-30-min gaps; {ds['duplicate_timestamps']} duplicate timestamps"],
            ["Missing cells", f"{ds['blank_cells']}", "No blank cells in the local CSV"],
            ["Supplied labels", f"Normal {ds['label_counts']['Normal']:,}; Abnormal {ds['label_counts']['Abnormal']:,}", "Abnormal prevalence 5.00%"],
            ["Rows after maximum lag", f"{p4['dataset']['rows_after_lag_336']:,}", "336 half-hour samples represent seven days"],
            ["Measurement units", "Not recoverable", "Numeric fields are normalized; physical kWh/weather units are not established"],
        ],
        "The CSV is suitable for a reproducible normalized case study and hardware-in-the-loop portability experiment. It is not sufficient by itself for claims stated in physical energy units. Supplied anomaly labels are publisher-described algorithmic labels rather than independently verified electrical events.",
        ["results/dataset_integrity.json", "results/phase4_forecasting_results.json"],
    ))

    table2_rows = []
    for result in p4["results_sorted_by_mae"]:
        model = result["model"]
        deploy = "Selected" if model == "compact_edge_linear" else ("Reference" if model == "linear_regression" else "Benchmark")
        table2_rows.append([display_name(model), config_text(result), deploy])
    tables.append(Table(
        2,
        "forecasting_models",
        "Forecasting models and prespecified configurations.",
        "supplementary",
        ["Model", "Configuration", "Role"],
        table2_rows,
        "All learned models use the same leakage-aware lag/calendar inputs in the main comparison. The compact model reserves part of the chronological training window for residual-threshold calibration and is exported as FP32 constants.",
        ["results/phase4_forecasting_results.json"],
    ))

    split_rows = [[
        "Single holdout",
        "—",
        f"{p4['split']['train_rows']:,}",
        "—",
        f"{p4['split']['test_rows']:,}",
        f"{dt(p4['split']['test_start'])} to {dt(p4['split']['test_end'])}",
    ]]
    split_rows.append([
        "Compact final fit/calibration",
        "—",
        f"{p8['split']['fit_rows']:,}",
        f"{p8['split']['calibration_rows']:,}",
        f"{p8['split']['test_rows']:,}",
        f"{dt(p8['split']['test_start'])} to {dt(p8['split']['test_end'])}",
    ])
    for fold in p5["fold_results"]:
        split_rows.append([
            "Expanding walk-forward",
            fold["fold"],
            f"{fold['train_rows']:,}",
            f"{fold['calibration_rows']:,}",
            f"{fold['test_rows']:,}",
            f"{dt(fold['test_start'])} to {dt(fold['test_end'])}",
        ])
    tables.append(Table(
        3,
        "chronological_split_configuration",
        "Chronological holdout and walk-forward split configurations.",
        "supplementary",
        ["Protocol", "Fold", "Train rows", "Calibration rows", "Test rows", "Test interval"],
        split_rows,
        "All splits preserve temporal order. Walk-forward test windows are non-overlapping and contain 400 rows each (2,000 total). Each lag uses only an observation available before its prediction timestamp.",
        ["results/phase4_forecasting_results.json", "results/phase5_walk_forward_results.json"],
    ))

    tables.append(Table(
        4,
        "forecasting_results",
        "Single chronological holdout forecasting results.",
        "supplementary",
        ["Model", "MAE", "RMSE", "sMAPE (%)", "Observed fit time (s)"],
        [[
            display_name(row["model"]),
            f6(row["mae_normalized"]),
            f6(row["rmse_normalized"]),
            f3(row["smape_percent"]),
            f"{row['fit_seconds_observed']:.4f}",
        ] for row in p4["results_sorted_by_mae"]],
        "MAE and RMSE are in normalized target units. Fit times are observed development-machine timings and are not embedded-device inference times. The compact model uses fewer fitting rows because 747 earlier rows are reserved for anomaly calibration.",
        ["results/phase4_forecasting_results.json"],
    ))

    tables.append(Table(
        5,
        "walk_forward_results",
        "Five-fold expanding-window forecasting performance.",
        "main",
        ["Model", "MAE mean ± SD", "MAE 95% CI", "RMSE mean ± SD", "Pooled sMAPE (%)"],
        [[
            display_name(row["model"]),
            f"{f6(row['fold_mae']['mean'])} ± {f6(row['fold_mae']['sample_standard_deviation'])}",
            f"[{f6(row['fold_mae']['ci95_lower'])}, {f6(row['fold_mae']['ci95_upper'])}]",
            f"{f6(row['fold_rmse']['mean'])} ± {f6(row['fold_rmse']['sample_standard_deviation'])}",
            f3(row["pooled_test_metrics"]["smape_percent"]),
        ] for row in p5["summary_sorted_by_mean_fold_mae"]],
        "Intervals are two-sided Student-t intervals over five fold-level metrics and should be interpreted descriptively. Metrics use normalized target units. Test windows are non-overlapping; training windows expand.",
        ["results/phase5_walk_forward_results.json"],
    ))

    tables.append(Table(
        6,
        "feature_ablation",
        "Compact FP32 model feature-group ablation across five temporal folds.",
        "supplementary",
        ["Feature group", "Features (n)", "MAE mean ± SD", "MAE 95% CI", "RMSE mean ± SD"],
        [[
            display_name(row["group"]),
            row["feature_count"],
            f"{f6(row['fold_mae']['mean'])} ± {f6(row['fold_mae']['sample_standard_deviation'])}",
            f"[{f6(row['fold_mae']['ci95_lower'])}, {f6(row['fold_mae']['ci95_upper'])}]",
            f"{f6(row['fold_rmse']['mean'])} ± {f6(row['fold_rmse']['sample_standard_deviation'])}",
        ] for row in p7["summary_sorted_by_mean_fold_mae"]],
        "All metrics are in normalized target units. Differences between feature groups are small; the opaque Avg_Past_Consumption field is excluded because its construction and leakage properties are undocumented.",
        ["results/phase7_feature_ablation.json"],
    ))

    tables.append(Table(
        7,
        "anomaly_detection_results",
        "Residual and isolation-forest anomaly-method agreement with supplied labels.",
        "main",
        ["Method", "TP", "FP", "FN", "TN", "Precision", "Recall", "F1", "Alerts (%)"],
        [[
            display_name(row["method"]), row["true_positive"], row["false_positive"],
            row["false_negative"], row["true_negative"], f3(row["precision"]),
            f3(row["recall"]), f3(row["f1"]), f"{row['alerts']} ({pct(row['alert_rate_percent'])})",
        ] for row in p9["methods_sorted_by_f1"]],
        "These values measure agreement with 52 abnormal and 881 normal publisher-supplied test labels. Those labels are described as Isolation-Forest-generated and are not validated physical anomaly ground truth; therefore the table does not establish real-world event-detection performance.",
        ["results/phase9_anomaly_methods.json"],
    ))

    tables.append(Table(
        8,
        "threshold_sensitivity",
        "Static residual-threshold sensitivity on the chronological test set.",
        "supplementary",
        ["Calibration percentile", "Threshold", "TP", "FP", "FN", "TN", "Precision", "Recall", "F1", "Alert rate (%)"],
        [[
            f"{row['calibration_percentile']:g}", f6(row["threshold_normalized"]),
            row["true_positive"], row["false_positive"], row["false_negative"], row["true_negative"],
            f3(row["precision"]), f3(row["recall"]), f3(row["f1"]), pct(row["alert_rate_percent"]),
        ] for row in p8["results"]],
        "Thresholds are percentiles of absolute residuals on the 747-row chronological calibration set and use normalized units. Classification metrics use the same unverified publisher-supplied labels described in Table 7.",
        ["results/phase8_threshold_sensitivity.json"],
    ))

    device_full = device["full_test_validation"]
    tables.append(Table(
        9,
        "esp8266_numerical_parity",
        "Numerical and anomaly-decision parity across Python, host C++, and physical ESP8266 execution.",
        "main",
        ["Layer", "Target", "Vectors", "Prediction matches", "Max. |difference|", "Decision matches", "Evidence"],
        [
            ["Reference", "Python float64", 933, "Reference", "Reference", "Reference", f"MAE={f6(compact['mae_normalized'])}; RMSE={f6(compact['rmse_normalized'])}"],
            ["Host export", "C++17 FP32, x86-64", host["rows"], f"{host['prediction_matches']}/{host['rows']}", f"{host['maximum_absolute_numerical_difference']:.3e}", f"{host['anomaly_decision_matches']}/{host['rows']}", "Generated header vs Python reference"],
            ["Physical HIL", device["device"], device_full["vectors"], f"{device_full['prediction_parity_passed']}/{device_full['vectors']}", f"{device_full['max_prediction_difference_normalized']:.3e}", f"{device_full['anomaly_parity_passed']}/{device_full['vectors']}", f"Replayed held-out vectors; mean kernel time {f3(timing['mean'])} µs"],
        ],
        "Differences are absolute differences in normalized prediction units. The physical test replays fixed held-out feature vectors stored in program flash; it validates numerical portability and decisions, not live sensor acquisition or field anomaly accuracy.",
        ["results/phase4_forecasting_results.json", "results/tinyml_cpp_parity.json", "results/tinyml_device_benchmark_v2.json", "results/phase12_device_timing_distribution.json"],
    ))

    normal = p13["whole_firmware"]["normal"]
    full = p13["whole_firmware"]["full_validation"]
    resource_rows = []
    for key, label in [("ram", "Data RAM"), ("iram", "Instruction RAM"), ("flash_code", "Flash code")]:
        n = normal[key]
        v = full[key]
        resource_rows.append([
            label,
            f"{n['used_bytes']:,} / {n['available_bytes']:,} ({n['used_percent_exact']:.2f}%)",
            f"{n['headroom_bytes']:,} ({n['headroom_percent_exact']:.2f}%)",
            f"{v['used_bytes']:,} / {v['available_bytes']:,} ({v['used_percent_exact']:.2f}%)",
            f"{v['headroom_bytes']:,} ({v['headroom_percent_exact']:.2f}%)",
        ])
    resource_rows.append([
        "Core numeric model state",
        f"{p13['parameter_accounting']['core_numeric_state_bytes_float32']} B",
        "Not a whole-firmware capacity measure",
        f"{p13['parameter_accounting']['core_numeric_state_bytes_float32']} B",
        "26 FP32 values; excludes code/metadata",
    ])
    tables.append(Table(
        10,
        "hardware_resource_utilization",
        "ESP8266 resource utilization for normal and full-validation firmware.",
        "main",
        ["Resource", "Normal used", "Normal headroom", "Validation used", "Validation headroom"],
        resource_rows,
        "Whole-firmware values include the ESP8266 core, Wi-Fi, HTTP, serial reporting, model, and application. Validation vectors are experimental payload rather than model parameters. IRAM is the principal integration constraint, with 5,193 B headroom.",
        ["results/phase13_resource_analysis.json"],
    ))

    current_work_row = ["This work", "Normalized 5,000-row case-study dataset", "Single holdout + 5-fold expanding window", "Agreement with supplied algorithmic labels", "Physical ESP8266EX", "933/933 predictions and decisions", "50.427 µs batch-mean kernel; RAM/IRAM/flash reported", "Physical units and real-event ground truth unavailable"]
    phase23_path = OUT / "phase23_related_work.json"
    if phase23_path.exists():
        phase23 = load_json("results/phase23_related_work.json")
        related_rows = [current_work_row]
        for study in phase23["studies"]:
            if study["table11"]:
                related_rows.append([
                    f"{study['authors_short']} ({study['year']}) [{study['key']}]",
                    study["dataset"],
                    study["temporal_evaluation"],
                    study["anomaly_evidence"],
                    study["hardware"],
                    study["full_vector_parity"],
                    study["measured_cost"],
                    study["limitation"],
                ])
        table11_status = "complete_verified_phase23"
        table11_note = "External rows come from the targeted Phase 23 peer-reviewed gap analysis. Citation keys map to references/references.bib. The search is not a systematic review and does not support a 'first' claim. Metrics are not compared numerically across incompatible datasets/tasks."
        table11_sources = ["results/phase23_related_work.json", "references/references.bib"]
    else:
        related_rows = [
            current_work_row,
            ["Phase 23 verified studies", "TO BE POPULATED", "TO BE POPULATED", "TO BE POPULATED", "TO BE POPULATED", "TO BE POPULATED", "TO BE POPULATED", "No rows will be added without source verification"],
        ]
        table11_status = "awaiting_phase23_related_work"
        table11_note = "The current-work row is complete. External comparison rows are intentionally deferred to Phase 23, which requires verified peer-reviewed sources and DOI/URL checks. This placeholder must not appear in a submitted manuscript."
        table11_sources = ["results/phase5_walk_forward_results.json", "results/phase9_anomaly_methods.json", "results/tinyml_device_benchmark_v2.json", "results/phase12_device_timing_distribution.json", "results/phase13_resource_analysis.json"]

    tables.append(Table(
        11,
        "comparison_with_related_studies",
        "Comparison with closely related forecasting, anomaly-detection, and edge-deployment studies.",
        "main",
        ["Study", "Dataset", "Temporal evaluation", "Anomaly evidence", "Hardware", "Full-vector parity", "Measured embedded cost", "Key limitation"],
        related_rows,
        table11_note,
        table11_sources,
        status=table11_status,
    ))
    return tables


def write_csv(table: Table) -> Path:
    path = TABLE_DIR / f"table{table.number:02d}_{table.slug}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(table.columns)
        writer.writerows(table.rows)
    return path


def markdown_table(table: Table) -> str:
    lines = [
        f"## Table {table.number}. {table.caption}",
        "",
        f"**Placement:** {table.placement.capitalize()}  ",
        f"**Status:** {table.status}",
        "",
        "| " + " | ".join(md_escape(x) for x in table.columns) + " |",
        "| " + " | ".join("---" for _ in table.columns) + " |",
    ]
    lines.extend("| " + " | ".join(md_escape(x) for x in row) + " |" for row in table.rows)
    lines.extend(["", f"*Note:* {table.note}", ""])
    return "\n".join(lines)


def latex_table(table: Table) -> str:
    colspec = "l" * len(table.columns)
    rows = [
        f"% Table {table.number}: {table.slug}",
        r"\begin{table*}[t]",
        r"\centering",
        f"\\caption{{{tex_escape(table.caption)}}}",
        f"\\label{{tab:{table.slug}}}",
        r"\scriptsize",
        r"\resizebox{\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{colspec}}}",
        r"\toprule",
        " & ".join(tex_escape(x) for x in table.columns) + r" \\",
        r"\midrule",
    ]
    rows.extend(" & ".join(tex_escape(x) for x in row) + r" \\" for row in table.rows)
    rows.extend([
        r"\bottomrule",
        r"\end{tabular}%",
        r"}",
        r"\vspace{2pt}",
        r"\begin{minipage}{0.98\textwidth}",
        f"\\footnotesize \\textit{{Note:}} {tex_escape(table.note)}",
        r"\end{minipage}",
        r"\end{table*}",
        "",
    ])
    return "\n".join(rows)


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    tables = build_tables()
    generated: list[Path] = []
    for table in tables:
        generated.append(write_csv(table))

    md_path = TABLE_DIR / "publication_tables.md"
    md_sections = [
        "# Publication Tables",
        "",
        "Generated from versioned local evidence by `python src/run_phase22_tables.py`.",
        "",
        "Main-paper set: Tables 1, 5, 7, 9, 10, and 11. Supplementary set: Tables 2, 3, 4, 6, and 8.",
        "",
        "Table 11 is populated from the verified Phase 23 literature artifact when `results/phase23_related_work.json` is present.",
        "",
    ]
    md_sections.extend(markdown_table(table) for table in tables)
    md_path.write_text("\n".join(md_sections).rstrip() + "\n", encoding="utf-8")
    generated.append(md_path)

    tex_path = TABLE_DIR / "publication_tables.tex"
    tex_header = (
        "% Generated by src/run_phase22_tables.py\n"
        "% Preamble requirements: \\usepackage{booktabs,graphicx}\n"
        "% Table 11 is populated only from the verified Phase 23 evidence artifact.\n\n"
    )
    tex_path.write_text(tex_header + "\n".join(latex_table(table) for table in tables), encoding="utf-8")
    generated.append(tex_path)

    standalone_path = TABLE_DIR / "publication_tables_standalone.tex"
    standalone_path.write_text(
        "\\documentclass[10pt]{article}\n"
        "\\usepackage[margin=12mm]{geometry}\n"
        "\\usepackage{booktabs,graphicx}\n"
        "\\begin{document}\n"
        "\\input{tables/publication_tables.tex}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    generated.append(standalone_path)

    manifest = {
        "phase": 22,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "src/run_phase22_tables.py",
        "table_count": len(tables),
        "main_paper_tables": [t.number for t in tables if t.placement == "main"],
        "supplementary_tables": [t.number for t in tables if t.placement == "supplementary"],
        "submission_blocker": None if next(t for t in tables if t.number == 11).status == "complete_verified_phase23" else "Table 11 external comparison rows require Phase 23 verified literature sources.",
        "tables": [
            {
                "number": t.number,
                "slug": t.slug,
                "caption": t.caption,
                "placement": t.placement,
                "status": t.status,
                "row_count": len(t.rows),
                "csv": str((TABLE_DIR / f"table{t.number:02d}_{t.slug}.csv").relative_to(ROOT)).replace("\\", "/"),
                "sources": t.sources,
            }
            for t in tables
        ],
        "generated_files": [],
    }
    for path in generated:
        manifest["generated_files"].append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest_path = OUT / "phase22_table_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(tables)} publication tables.")
    print(f"Markdown: {md_path.relative_to(ROOT)}")
    print(f"LaTeX: {tex_path.relative_to(ROOT)}")
    print(f"LaTeX compile check: {standalone_path.relative_to(ROOT)}")
    print(f"Manifest: {manifest_path.relative_to(ROOT)}")
    print(f"Table 11 status: {next(t for t in tables if t.number == 11).status}")


if __name__ == "__main__":
    main()
