"""Phase 8 residual-threshold sensitivity for the deployed compact model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
PERCENTILES = [90.0, 92.5, 95.0, 97.5, 99.0, 99.5]


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
    if fit["Timestamp"].max() >= calibration["Timestamp"].min():
        raise AssertionError("Fit/calibration order failed")
    if calibration["Timestamp"].max() >= test["Timestamp"].min():
        raise AssertionError("Calibration/test order failed")

    x_fit = fit[FEATURES].to_numpy(dtype=np.float64)
    y_fit = fit[TARGET].to_numpy(dtype=np.float64)
    mean = x_fit.mean(axis=0)
    scale = x_fit.std(axis=0)
    scale[scale == 0] = 1.0
    design = np.column_stack([np.ones(len(x_fit)), (x_fit - mean) / scale])
    parameters, *_ = np.linalg.lstsq(design, y_fit, rcond=None)

    def predict(partition: pd.DataFrame) -> np.ndarray:
        values = partition[FEATURES].to_numpy(dtype=np.float64)
        return parameters[0] + ((values - mean) / scale) @ parameters[1:]

    calibration_residual = np.abs(
        calibration[TARGET].to_numpy(dtype=np.float64) - predict(calibration)
    )
    test_actual = test[TARGET].to_numpy(dtype=np.float64)
    test_residual = np.abs(test_actual - predict(test))
    supplied_label = (
        test["Anomaly_Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("abnormal")
        .to_numpy()
    )

    results = []
    decision_columns = {}
    for percentile in PERCENTILES:
        threshold = float(np.quantile(calibration_residual, percentile / 100.0))
        decision = test_residual > threshold
        result = {
            "calibration_percentile": percentile,
            "threshold_normalized": threshold,
            **classification(supplied_label, decision),
        }
        results.append(result)
        decision_columns[f"alert_p{str(percentile).replace('.', '_')}"] = decision.astype(int)

    highest_test_f1 = max(results, key=lambda row: row["f1"])
    report = {
        "phase": 8,
        "experiment": "compact_model_residual_threshold_sensitivity",
        "units": "normalized dataset target units; physical kWh not established",
        "dataset": {
            "csv_sha256": sha256(csv_path),
            "rows_after_lags": len(model_frame),
        },
        "split": {
            "fit_rows": len(fit),
            "calibration_rows": len(calibration),
            "test_rows": len(test),
            "fit_end": fit["Timestamp"].max().isoformat(),
            "calibration_start": calibration["Timestamp"].min().isoformat(),
            "calibration_end": calibration["Timestamp"].max().isoformat(),
            "test_start": test["Timestamp"].min().isoformat(),
            "test_end": test["Timestamp"].max().isoformat(),
        },
        "model": "standardized linear least squares software reference",
        "calibration_quantile_method": "numpy linear interpolation default",
        "supplied_test_labels": {
            "abnormal": int(supplied_label.sum()),
            "normal": int((~supplied_label).sum()),
            "ground_truth_warning": "labels are publisher-described Isolation Forest outputs, not independently validated physical events",
        },
        "results": results,
        "retrospective_highest_test_f1": {
            **highest_test_f1,
            "selection_warning": "descriptive only; selecting this threshold from test labels would bias a final evaluation",
        },
        "limitations": [
            "Thresholds use past calibration residuals, but threshold ranking is inspected against future supplied labels.",
            "Supplied labels are algorithm-generated and have unverified physical meaning.",
            "The test contains only 52 supplied positives.",
            "A deployable threshold must be selected without optimizing on the final test labels.",
        ],
    }
    (output_dir / "phase8_threshold_sensitivity.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(results).to_csv(
        output_dir / "phase8_threshold_sensitivity.csv", index=False
    )
    pd.DataFrame(
        {
            "Timestamp": test["Timestamp"].to_numpy(),
            "actual_normalized": test_actual,
            "absolute_residual_normalized": test_residual,
            "supplied_abnormal_label": supplied_label.astype(int),
            **decision_columns,
        }
    ).to_csv(output_dir / "phase8_threshold_decisions.csv", index=False)

    percentiles = [row["calibration_percentile"] for row in results]
    precision = [row["precision"] for row in results]
    recall = [row["recall"] for row in results]
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    ax.plot(recall, precision, marker="o", color="#2878B5")
    for row in results:
        ax.annotate(
            f"p{row['calibration_percentile']:g}",
            (row["recall"], row["precision"]),
            xytext=(5, 5),
            textcoords="offset points",
        )
    ax.set_xlabel("Recall against supplied labels")
    ax.set_ylabel("Precision against supplied labels")
    ax.set_title("Phase 8: residual-threshold precision–recall trade-off")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase8_precision_recall.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    ax.plot(percentiles, [row["f1"] for row in results], marker="o", color="#4C956C")
    ax.set_xlabel("Calibration residual percentile")
    ax.set_ylabel("F1 against supplied labels")
    ax.set_title("Phase 8: F1 decreases at conservative thresholds")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase8_f1_vs_threshold.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    ax.plot(percentiles, [row["alerts"] for row in results], marker="o", color="#C17C27")
    ax.axhline(int(supplied_label.sum()), color="#C44E52", linestyle="--", label="Supplied positives")
    ax.set_xlabel("Calibration residual percentile")
    ax.set_ylabel("Number of test alerts")
    ax.set_title("Phase 8: alert volume versus threshold")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "phase8_alerts_vs_threshold.png", dpi=200)
    plt.close(fig)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
