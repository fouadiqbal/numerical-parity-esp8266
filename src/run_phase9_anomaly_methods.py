"""Phase 9 comparison of prespecified anomaly-analysis methods."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


TARGET = "Electricity_Consumed"
FEATURES = [
    "lag_1",
    "lag_2",
    "lag_48",
    "lag_336",
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
]
METHOD_ORDER = [
    "static_residual_p99",
    "adaptive_ewma_residual_p99",
    "rolling_week_residual_p99",
    "split_conformal_95",
    "isolation_forest_5pct",
]
DISPLAY_NAMES = {
    "static_residual_p99": "Static residual p99",
    "adaptive_ewma_residual_p99": "Adaptive EWMA p99",
    "rolling_week_residual_p99": "Rolling-week p99",
    "split_conformal_95": "Split conformal 95%",
    "isolation_forest_5pct": "Isolation Forest 5%",
}
EWMA_ALPHA = 0.02
ROLLING_WINDOW = 336
ISOLATION_CONTAMINATION = 0.05
SEED = 42


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def classification(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | int]:
    actual = actual.astype(bool)
    predicted = predicted.astype(bool)
    tp = int(np.sum(actual & predicted))
    fp = int(np.sum(~actual & predicted))
    fn = int(np.sum(actual & ~predicted))
    tn = int(np.sum(~actual & ~predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "alerts": int(predicted.sum()),
        "alert_rate_percent": float(100.0 * predicted.mean()),
    }


def adaptive_ewma_decisions(
    calibration_residuals: np.ndarray, test_residuals: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float]:
    mean = float(calibration_residuals.mean())
    variance = float(calibration_residuals.var(ddof=1))
    initial_p99 = float(np.quantile(calibration_residuals, 0.99))
    multiplier = (initial_p99 - mean) / np.sqrt(variance)
    decisions = np.zeros(len(test_residuals), dtype=bool)
    thresholds = np.empty(len(test_residuals), dtype=np.float64)
    for index, residual in enumerate(test_residuals):
        threshold = max(0.0, mean + multiplier * np.sqrt(max(variance, 0.0)))
        thresholds[index] = threshold
        decisions[index] = residual > threshold
        delta = float(residual) - mean
        updated_mean = mean + EWMA_ALPHA * delta
        variance = (1.0 - EWMA_ALPHA) * (
            variance + EWMA_ALPHA * delta * delta
        )
        mean = updated_mean
    return decisions, thresholds, float(multiplier)


def rolling_decisions(
    calibration_residuals: np.ndarray, test_residuals: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    history = deque(calibration_residuals[-ROLLING_WINDOW:].tolist(), maxlen=ROLLING_WINDOW)
    decisions = np.zeros(len(test_residuals), dtype=bool)
    thresholds = np.empty(len(test_residuals), dtype=np.float64)
    for index, residual in enumerate(test_residuals):
        threshold = float(np.quantile(np.asarray(history), 0.99))
        thresholds[index] = threshold
        decisions[index] = residual > threshold
        history.append(float(residual))
    return decisions, thresholds


def conformal_threshold(calibration_residuals: np.ndarray, alpha: float) -> float:
    n = len(calibration_residuals)
    rank = min(n, math.ceil((n + 1) * (1.0 - alpha)))
    return float(np.sort(calibration_residuals)[rank - 1])


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=repository / "data/source/extracted/smart_meter_data.csv",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=repository / "results"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(csv_path)
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="raise")
    frame = frame.sort_values("Timestamp").reset_index(drop=True)
    frame["lag_1"] = frame[TARGET].shift(1)
    frame["lag_2"] = frame[TARGET].shift(2)
    frame["lag_48"] = frame[TARGET].shift(48)
    frame["lag_336"] = frame[TARGET].shift(336)
    frame["hour"] = frame["Timestamp"].dt.hour
    frame["day_of_week"] = frame["Timestamp"].dt.dayofweek
    frame["month"] = frame["Timestamp"].dt.month
    frame["is_weekend"] = (frame["day_of_week"] >= 5).astype(int)
    model_frame = frame.dropna(subset=FEATURES).reset_index(drop=True)

    train_end = int(len(model_frame) * 0.80)
    training = model_frame.iloc[:train_end]
    test = model_frame.iloc[train_end:]
    fit_end = int(len(training) * 0.80)
    fit = training.iloc[:fit_end]
    calibration = training.iloc[fit_end:]

    x_fit = fit[FEATURES].to_numpy(dtype=np.float64)
    y_fit = fit[TARGET].to_numpy(dtype=np.float64)
    mean = x_fit.mean(axis=0)
    scale = x_fit.std(axis=0)
    scale[scale == 0] = 1.0
    design = np.column_stack([np.ones(len(x_fit)), (x_fit - mean) / scale])
    parameters, *_ = np.linalg.lstsq(design, y_fit, rcond=None)

    def forecast(partition: pd.DataFrame) -> np.ndarray:
        values = partition[FEATURES].to_numpy(dtype=np.float64)
        return parameters[0] + ((values - mean) / scale) @ parameters[1:]

    calibration_residual = np.abs(
        calibration[TARGET].to_numpy(dtype=np.float64) - forecast(calibration)
    )
    test_residual = np.abs(
        test[TARGET].to_numpy(dtype=np.float64) - forecast(test)
    )
    supplied_label = (
        test["Anomaly_Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("abnormal")
        .to_numpy()
    )

    static_threshold = float(np.quantile(calibration_residual, 0.99))
    static_decision = test_residual > static_threshold
    adaptive_decision, adaptive_thresholds, adaptive_multiplier = adaptive_ewma_decisions(
        calibration_residual, test_residual
    )
    rolling_decision, rolling_thresholds = rolling_decisions(
        calibration_residual, test_residual
    )
    conformal_value = conformal_threshold(calibration_residual, alpha=0.05)
    conformal_decision = test_residual > conformal_value

    isolation_features = [TARGET] + FEATURES
    scaler = StandardScaler()
    isolation_fit = scaler.fit_transform(fit[isolation_features])
    isolation_test = scaler.transform(test[isolation_features])
    isolation = IsolationForest(
        n_estimators=200,
        contamination=ISOLATION_CONTAMINATION,
        random_state=SEED,
        n_jobs=-1,
    ).fit(isolation_fit)
    isolation_decision = isolation.predict(isolation_test) == -1

    decisions = {
        "static_residual_p99": static_decision,
        "adaptive_ewma_residual_p99": adaptive_decision,
        "rolling_week_residual_p99": rolling_decision,
        "split_conformal_95": conformal_decision,
        "isolation_forest_5pct": isolation_decision,
    }
    method_details = {
        "static_residual_p99": {
            "threshold": static_threshold,
            "calibration_percentile": 99.0,
        },
        "adaptive_ewma_residual_p99": {
            "alpha": EWMA_ALPHA,
            "initial_threshold": float(adaptive_thresholds[0]),
            "final_threshold": float(adaptive_thresholds[-1]),
            "initial_standard_deviation_multiplier": adaptive_multiplier,
            "update_order": "decide using past state, then update with current residual",
        },
        "rolling_week_residual_p99": {
            "window_rows": ROLLING_WINDOW,
            "window_interpretation": "seven days at half-hourly sampling",
            "percentile": 99.0,
            "initial_threshold": float(rolling_thresholds[0]),
            "final_threshold": float(rolling_thresholds[-1]),
            "update_order": "decide using past window, then append current residual",
        },
        "split_conformal_95": {
            "alpha": 0.05,
            "symmetric_absolute_residual_threshold": conformal_value,
            "finite_sample_rank": min(
                len(calibration_residual),
                math.ceil((len(calibration_residual) + 1) * 0.95),
            ),
            "coverage_warning": "standard exchangeability assumptions are questionable for time series",
        },
        "isolation_forest_5pct": {
            "features": isolation_features,
            "n_estimators": 200,
            "contamination": ISOLATION_CONTAMINATION,
            "random_state": SEED,
            "configuration_warning": "5% contamination mirrors the dataset-wide supplied-label rate and may favor agreement",
        },
    }

    results = []
    for method in METHOD_ORDER:
        results.append(
            {
                "method": method,
                **classification(supplied_label, decisions[method]),
                "details": method_details[method],
            }
        )
    results.sort(key=lambda row: row["f1"], reverse=True)

    report = {
        "phase": 9,
        "experiment": "prespecified_anomaly_method_comparison",
        "comparison_target": "agreement with supplied Isolation-Forest-generated labels",
        "not_established": "validated real-world electrical anomaly detection",
        "units": "normalized dataset target units; physical kWh not established",
        "dataset": {
            "csv_sha256": sha256(csv_path),
            "fit_rows": len(fit),
            "calibration_rows": len(calibration),
            "test_rows": len(test),
            "supplied_test_abnormal": int(supplied_label.sum()),
            "supplied_test_normal": int((~supplied_label).sum()),
        },
        "methods_sorted_by_f1": results,
        "limitations": [
            "Supplied labels are algorithm-generated rather than independent physical ground truth.",
            "Isolation Forest contamination uses the known 5% dataset label rate, creating circularity risk.",
            "EWMA alpha, rolling-window length, and p99 level were prespecified but not externally validated.",
            "Adaptive thresholds update using every residual, so sustained anomalies can raise the threshold.",
            "Split-conformal marginal coverage is not guaranteed under temporal dependence and distribution shift.",
            "Method rankings are descriptive on one future holdout and were not tested on an official anomaly dataset.",
        ],
    }
    (output_dir / "phase9_anomaly_methods.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    flat = []
    for row in results:
        flat.append({key: value for key, value in row.items() if key != "details"})
    pd.DataFrame(flat).to_csv(output_dir / "phase9_anomaly_methods.csv", index=False)
    pd.DataFrame(
        {
            "Timestamp": test["Timestamp"].to_numpy(),
            "absolute_residual_normalized": test_residual,
            "supplied_abnormal_label": supplied_label.astype(int),
            "adaptive_threshold": adaptive_thresholds,
            "rolling_threshold": rolling_thresholds,
            **{method: decision.astype(int) for method, decision in decisions.items()},
        }
    ).to_csv(output_dir / "phase9_anomaly_decisions.csv", index=False)

    fig, ax = plt.subplots(figsize=(8.2, 5.8))
    annotation_offsets = {
        "static_residual_p99": (6, 5),
        "adaptive_ewma_residual_p99": (-145, 12),
        "rolling_week_residual_p99": (6, 5),
        "split_conformal_95": (8, 12),
        "isolation_forest_5pct": (8, 5),
    }
    for row in results:
        ax.scatter(row["recall"], row["precision"], s=70)
        ax.annotate(
            DISPLAY_NAMES[row["method"]],
            (row["recall"], row["precision"]),
            xytext=annotation_offsets[row["method"]],
            textcoords="offset points",
        )
    ax.set_xlabel("Recall against supplied labels")
    ax.set_ylabel("Precision against supplied labels")
    ax.set_title("Phase 9: anomaly-method agreement trade-offs")
    ax.set_xlim(0, 0.65)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase9_anomaly_precision_recall.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9.2, 5.5))
    plot_rows = sorted(results, key=lambda row: row["f1"], reverse=True)
    positions = np.arange(len(plot_rows))
    ax.bar(positions, [row["f1"] for row in plot_rows], color="#6C5B7B")
    ax.set_xticks(
        positions,
        [DISPLAY_NAMES[row["method"]] for row in plot_rows],
        rotation=18,
        ha="right",
    )
    ax.set_ylabel("F1 against supplied labels")
    ax.set_title("Phase 9: descriptive method comparison")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase9_anomaly_f1_comparison.png", dpi=200)
    plt.close(fig)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
