"""Generate the Phase 21 publication-figure set from verified local artifacts.

The script deliberately does not synthesize a Python/device error distribution.
The physical capture contains aggregate match counts and a maximum difference,
not all 933 device-side differences. Figure 8 therefore visualizes the verified
aggregate parity and error bound and is marked as an interim replacement.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "results"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
RED = "#D55E00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
GREY = "#7A7A7A"
LIGHT_GREY = "#E6E6E6"
BLACK = "#1A1A1A"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.labelsize": 8.5,
        "axes.titlesize": 9.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#D9D9D9",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.7,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def read_json(name: str) -> dict:
    return json.loads((OUTPUTS / name).read_text(encoding="utf-8"))


def save_figure(fig: plt.Figure, stem: str) -> dict:
    files: dict[str, dict[str, object]] = {}
    for extension, kwargs in (
        ("png", {"dpi": 300}),
        ("pdf", {}),
        ("svg", {}),
    ):
        path = FIGURES / f"{stem}.{extension}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.04, **kwargs)
        files[extension] = {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        }
    plt.close(fig)
    return files


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    color: str,
    linestyle: str = "-",
    fontsize: float = 8.5,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.015",
        linewidth=1.25,
        edgecolor=color,
        facecolor="white",
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", color=BLACK, fontsize=fontsize)


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str = GREY,
    linestyle: str = "-",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.1,
            color=color,
            linestyle=linestyle,
        )
    )


def fig01_architecture() -> dict:
    fig, ax = plt.subplots(figsize=(7.16, 3.25))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    positions = [0.02, 0.22, 0.42, 0.62, 0.82]
    labels = [
        "Normalized data\n+ chronological\nsplits",
        "Python models\n+ threshold\ncalibration",
        "Generated C++\n+ compiled-host\nparity",
        "ESP8266 HIL\nvector replay\n+ timing",
        "HTTP/ThingSpeak\nconnectivity\ncheck",
    ]
    colors = [GREY, BLUE, GREEN, ORANGE, SKY]
    for index, (x, label, color) in enumerate(zip(positions, labels, colors)):
        add_box(ax, x, 0.53, 0.16, 0.22, label, color, fontsize=7.2)
        if index < len(positions) - 1:
            add_arrow(ax, (x + 0.16, 0.64), (positions[index + 1] - 0.008, 0.64))
    add_box(ax, 0.39, 0.10, 0.24, 0.20, "Future isolated and\ncalibrated V/I sensing", RED, "--", fontsize=7.6)
    add_arrow(ax, (0.63, 0.20), (0.70, 0.52), RED, "--")
    ax.text(0.51, 0.05, "Not implemented in the reported experiment", ha="center", color=RED, fontsize=7.5)
    ax.text(0.50, 0.91, "Verified computation path and excluded sensing path", ha="center", weight="bold")
    ax.text(0.50, 0.82, "Solid: implemented evidence   |   Dashed red: future work", ha="center", color=GREY)
    return save_figure(fig, "fig01_cloud_to_edge_architecture")


def fig02_walk_forward() -> dict:
    phase5 = read_json("phase5_walk_forward_results.json")
    folds = phase5["fold_results"]
    fig, ax = plt.subplots(figsize=(7.16, 3.2))
    for row, fold in enumerate(folds, start=1):
        y = len(folds) - row
        train = fold["train_rows"]
        calibration = fold["calibration_rows"]
        test = fold["test_rows"]
        ax.barh(y, train, left=0, height=0.56, color="#A9CCE3", edgecolor="white", label="Training" if row == 1 else None)
        ax.barh(y, calibration, left=train, height=0.56, color=ORANGE, edgecolor="white", label="Calibration" if row == 1 else None)
        ax.barh(y, test, left=train + calibration, height=0.56, color=GREEN, edgecolor="white", label="Future test" if row == 1 else None)
        ax.text(train + calibration + test + 35, y, f"{test} test", va="center", fontsize=7.2)
    ax.set_yticks(range(5), ["Fold 5", "Fold 4", "Fold 3", "Fold 2", "Fold 1"])
    ax.set_xlabel("Model-ready chronological row index")
    ax.set_xlim(0, 4800)
    ax.set_title("Five expanding-window folds preserve train → calibration → future-test order")
    ax.legend(ncol=3, loc="lower right", frameon=False)
    return save_figure(fig, "fig02_walk_forward_protocol")


def fig03_model_comparison() -> dict:
    data = pd.read_csv(OUTPUTS / "phase5_walk_forward_fold_metrics.csv")
    order = [
        "compact_edge_linear_float32",
        "linear_regression",
        "random_forest",
        "hist_gradient_boosting",
        "seasonal_naive_lag_48",
        "persistence_lag_1",
    ]
    labels = ["Compact LR\nFP32", "Linear\nregression", "Random\nforest", "Histogram\nboosting", "Seasonal naive\nlag 48", "Persistence\nlag 1"]
    grouped = data.groupby("model")["mae_normalized"]
    means = np.array([grouped.get_group(model).mean() for model in order])
    standard_deviations = np.array([grouped.get_group(model).std(ddof=1) for model in order])
    ci_half = 2.7764451051977987 * standard_deviations / np.sqrt(5)
    colors = [GREEN, BLUE, SKY, PURPLE, ORANGE, GREY]
    fig, ax = plt.subplots(figsize=(7.16, 3.55))
    x = np.arange(len(order))
    bars = ax.bar(x, means, yerr=ci_half, capsize=3, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Mean fold MAE (normalized target units)")
    ax.set_ylim(0, max(means + ci_half) * 1.13)
    ax.set_title("Compact and ordinary linear models have the lowest five-fold mean MAE")
    for bar, value in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.0055, f"{value:.4f}", ha="center", va="bottom", fontsize=7)
    ax.text(0.01, 0.97, "Error bars: descriptive 95% t intervals over five folds", transform=ax.transAxes, va="top", color=GREY, fontsize=7.2)
    return save_figure(fig, "fig03_forecasting_model_comparison")


def fig04_ablation() -> dict:
    data = pd.read_csv(OUTPUTS / "phase7_feature_ablation.csv")
    reference = data[data["group"] == "lag_plus_calendar_plus_weather"].set_index("fold")["mae_normalized"]
    order = ["calendar_only", "lag_only", "weather_only", "lag_plus_calendar", "lag_plus_weather", "lag_plus_calendar_plus_weather"]
    labels = ["Calendar", "Lag", "Weather", "Lag +\ncalendar", "Lag +\nweather", "All"]
    fig, ax = plt.subplots(figsize=(7.16, 3.55))
    x = np.arange(len(order))
    for fold in sorted(data["fold"].unique()):
        subset = data[data["fold"] == fold].set_index("group")
        delta = np.array([(subset.loc[group, "mae_normalized"] - reference.loc[fold]) * 1e4 for group in order])
        ax.plot(x, delta, color="#BDBDBD", linewidth=0.8, alpha=0.8)
        ax.scatter(x, delta, color="#8C8C8C", s=12, alpha=0.8)
    means = []
    for group in order:
        group_values = data[data["group"] == group].set_index("fold")["mae_normalized"]
        means.append(float(((group_values - reference) * 1e4).mean()))
    ax.scatter(x, means, marker="D", s=42, color=BLUE, edgecolor="white", linewidth=0.6, label="Mean paired difference", zorder=5)
    ax.axhline(0, color=BLACK, linewidth=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("MAE difference from all features (×10⁻⁴)")
    ax.set_title("Feature-group differences are small and inconsistent across folds")
    ax.legend(frameon=False, loc="upper right")
    return save_figure(fig, "fig04_feature_ablation")


def fig05_precision_recall() -> dict:
    data = pd.read_csv(OUTPUTS / "phase8_threshold_sensitivity.csv")
    fig, ax = plt.subplots(figsize=(3.5, 3.35))
    ax.plot(data["recall"], data["precision"], color=BLUE, marker="o", linewidth=1.5)
    for _, row in data.iterrows():
        ax.annotate(f"p{row['calibration_percentile']:g}", (row["recall"], row["precision"]), xytext=(4, 4), textcoords="offset points", fontsize=6.8)
    ax.set_xlabel("Recall against supplied labels")
    ax.set_ylabel("Precision against supplied labels")
    ax.set_xlim(0, 0.62)
    ax.set_ylim(0.30, 1.05)
    ax.set_title("Past-calibrated thresholds trade recall for precision")
    return save_figure(fig, "fig05_anomaly_precision_recall")


def fig06_f1_threshold() -> dict:
    data = pd.read_csv(OUTPUTS / "phase8_threshold_sensitivity.csv")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5.2, 4.6), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    ax1.plot(data["calibration_percentile"], data["f1"], color=BLUE, marker="o", linewidth=1.5)
    ax1.axvline(99, color=RED, linestyle="--", linewidth=1, label="Historical HIL p99")
    best = data.loc[data["f1"].idxmax()]
    ax1.scatter([best["calibration_percentile"]], [best["f1"]], marker="D", color=ORANGE, zorder=5, label="Retrospective highest F1")
    ax1.set_ylabel("F1 against\nsupplied labels")
    ax1.set_ylim(0, 0.58)
    ax1.legend(frameon=False, loc="lower left")
    ax2.bar(data["calibration_percentile"], data["alerts"], width=1.15, color=GREEN, alpha=0.85)
    ax2.axvline(99, color=RED, linestyle="--", linewidth=1)
    ax2.set_xlabel("Calibration-residual percentile")
    ax2.set_ylabel("Alerts on\n933 test rows")
    ax2.set_title("The p99 rule reduces alert volume at the cost of supplied-label recall", pad=8)
    fig.tight_layout(h_pad=0.8)
    return save_figure(fig, "fig06_f1_and_alerts_vs_threshold")


def fig07_validation_pipeline() -> dict:
    fig, ax = plt.subplots(figsize=(7.16, 3.05))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        (0.03, "Python\nreference", BLUE),
        (0.28, "Generated header\n+ C++17 host", GREEN),
        (0.55, "ESP8266EX\nphysical replay", ORANGE),
        (0.81, "Evidence\nrecord", PURPLE),
    ]
    for x, label, color in boxes:
        add_box(ax, x, 0.50, 0.16, 0.23, label, color)
    for left, right in ((0.19, 0.28), (0.44, 0.55), (0.71, 0.81)):
        add_arrow(ax, (left, 0.615), (right - 0.008, 0.615))
    ax.text(0.235, 0.76, "933/933 predictions\n933/933 decisions", ha="center", fontsize=7.2, color=GREEN)
    ax.text(0.495, 0.76, "933/933 predictions\n933/933 decisions", ha="center", fontsize=7.2, color=ORANGE)
    ax.text(0.50, 0.28, "Pre-flash compiled-host parity → complete physical held-out-vector parity", ha="center", weight="bold")
    ax.text(0.50, 0.13, "This validates numerical portability of frozen vectors; it does not validate live sensing.", ha="center", color=RED)
    ax.set_title("Python → generated C++ → ESP8266 validation pipeline")
    return save_figure(fig, "fig07_python_cpp_esp8266_validation")


def fig08_error_bounds() -> dict:
    device = read_json("tinyml_device_benchmark_v2.json")
    result = device["full_test_validation"]
    matches = [result["prediction_parity_passed"], result["anomaly_parity_passed"]]
    mismatches = [result["vectors"] - matches[0], result["vectors"] - matches[1]]
    maximum = result["max_prediction_difference_normalized"]
    tolerance = 1e-6
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.16, 3.35), gridspec_kw={"width_ratios": [1.15, 1]})
    x = np.arange(2)
    ax1.bar(x, matches, color=[BLUE, GREEN], label="Matches")
    ax1.bar(x, mismatches, bottom=matches, color=RED, label="Mismatches")
    ax1.set_xticks(x, ["Predictions", "Threshold\ndecisions"])
    ax1.set_ylabel("Held-out vectors")
    ax1.set_ylim(0, 1010)
    for index, value in enumerate(matches):
        ax1.text(index, value + 18, f"{value}/933", ha="center", fontsize=8)
    ax1.legend(frameon=False, loc="lower right")
    ax1.set_title("Complete-set agreement")
    ax2.set_yscale("log")
    ax2.scatter([0], [maximum], s=60, color=ORANGE, zorder=4, label="Observed maximum")
    ax2.axhline(tolerance, color=RED, linestyle="--", linewidth=1.2, label="Parity tolerance")
    ax2.set_xlim(-0.65, 0.65)
    ax2.set_xticks([0], ["Python–device\nabsolute difference"])
    ax2.set_ylabel("Normalized target units (log scale)")
    ax2.set_ylim(1e-9, 3e-6)
    ax2.annotate(f"max = {maximum:.1e}", (0, maximum), xytext=(12, -10), textcoords="offset points", fontsize=7.2)
    ax2.legend(frameon=False, loc="upper left")
    ax2.set_title("Verified aggregate error bound")
    fig.suptitle("HIL parity is verified; a per-vector device-error distribution was not captured", y=1.01, fontsize=9.5, weight="bold")
    return save_figure(fig, "fig08_hil_parity_error_bounds_INTERIM")


def fig09_latency() -> dict:
    timing = read_json("phase12_device_timing_distribution.json")
    values = np.asarray(timing["batch_averages"], dtype=float)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5.2, 4.4), gridspec_kw={"height_ratios": [2.2, 0.75]}, sharex=True)
    ax1.hist(values, bins=9, color=BLUE, edgecolor="white", linewidth=0.8)
    ax1.axvline(timing["mean"], color=RED, linewidth=1.2, label=f"Mean {timing['mean']:.4f} µs")
    ax1.axvline(timing["median"], color=ORANGE, linewidth=1.2, linestyle="--", label=f"Median {timing['median']:.4f} µs")
    ax1.set_ylabel("Batch count")
    ax1.set_title("ESP8266 model-kernel timing across 30 batch averages")
    ax1.legend(frameon=False)
    ax2.boxplot(values, orientation="horizontal", widths=0.55, patch_artist=True, boxprops={"facecolor": SKY, "edgecolor": BLUE}, medianprops={"color": ORANGE}, whiskerprops={"color": BLUE}, capprops={"color": BLUE}, flierprops={"markerfacecolor": RED, "markeredgecolor": RED, "markersize": 4})
    ax2.scatter(values, np.ones_like(values), s=9, color=BLACK, alpha=0.45, zorder=3)
    ax2.set_yticks([])
    ax2.set_xlabel("Batch-average time per prediction (µs); 2,000 predictions per batch")
    return save_figure(fig, "fig09_esp8266_latency_distribution")


def fig10_memory() -> dict:
    resources = read_json("phase13_resource_analysis.json")["whole_firmware"]
    categories = ["Data RAM", "Instruction RAM", "Flash code"]
    keys = ["ram", "iram", "flash_code"]
    normal = [resources["normal"][key]["used_percent_exact"] for key in keys]
    validation = [resources["full_validation"][key]["used_percent_exact"] for key in keys]
    x = np.arange(len(categories))
    width = 0.35
    fig, ax = plt.subplots(figsize=(5.6, 3.65))
    bars1 = ax.bar(x - width / 2, normal, width, color=BLUE, label="Normal firmware")
    bars2 = ax.bar(x + width / 2, validation, width, color=ORANGE, label="Full-validation firmware")
    ax.axhline(100, color=BLACK, linewidth=0.8)
    ax.set_xticks(x, categories)
    ax.set_ylabel("Used capacity (%)")
    ax.set_ylim(0, 108)
    ax.set_title("Instruction RAM, not data RAM or flash, limits integration headroom")
    ax.legend(frameon=False, loc="upper left")
    for bars in (bars1, bars2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5, f"{bar.get_height():.1f}%", ha="center", fontsize=7)
    ax.annotate("Only 5,193 B IRAM headroom", xy=(1, normal[1]), xytext=(1.52, 80), arrowprops={"arrowstyle": "->", "color": RED}, color=RED, fontsize=7.2)
    return save_figure(fig, "fig10_memory_flash_iram_utilization")


def main() -> None:
    figures = [
        (1, "Complete cloud-to-edge architecture", "main", "verified plus explicitly dashed future path", fig01_architecture),
        (2, "Chronological/walk-forward validation protocol", "main", "verified", fig02_walk_forward),
        (3, "Forecasting model comparison", "main", "verified", fig03_model_comparison),
        (4, "Feature ablation", "supplementary", "verified", fig04_ablation),
        (5, "Anomaly precision-recall curve", "supplementary", "agreement with supplied labels only", fig05_precision_recall),
        (6, "F1 and alerts versus threshold", "supplementary", "agreement with supplied labels only", fig06_f1_threshold),
        (7, "Python to C++ to ESP8266 validation pipeline", "main", "verified", fig07_validation_pipeline),
        (8, "Python/device parity and error bound", "interim main", "aggregate evidence only; true distribution pending per-vector device capture", fig08_error_bounds),
        (9, "ESP8266 latency distribution", "main", "distribution of 30 batch averages", fig09_latency),
        (10, "Memory, flash and IRAM utilization", "main", "verified whole-firmware builds", fig10_memory),
    ]
    manifest_entries = []
    for number, title, placement, evidence_status, function in figures:
        files = function()
        manifest_entries.append(
            {
                "figure": number,
                "title": title,
                "placement": placement,
                "evidence_status": evidence_status,
                "files": files,
            }
        )
    manifest = {
        "phase": 21,
        "date": "2026-09-03",
        "status": "generated_with_interim_figure_8",
        "environment": {
            "python": sys.version.split()[0],
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "style": {
            "png_dpi": 300,
            "vector_formats": ["PDF", "SVG"],
            "palette": "color-vision-deficiency-conscious Okabe-Ito-derived palette",
            "units_policy": "normalized target units where applicable; no physical kWh claim",
        },
        "figures": manifest_entries,
        "figure_8_limitation": "The physical capture retained 933/933 match counts and maximum absolute difference but not all per-vector device differences. The interim aggregate figure must be replaced after a newly instrumented physical run before calling it an error distribution.",
    }
    path = OUTPUTS / "phase21_figure_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(manifest_entries)} figures in PNG, PDF, and SVG.")
    print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
