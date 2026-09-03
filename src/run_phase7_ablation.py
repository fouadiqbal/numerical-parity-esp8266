"""Phase 7 feature-group ablation for compact float32 linear forecasting."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import t as student_t


TARGET = "Electricity_Consumed"
CALENDAR = ["hour", "day_of_week", "month", "is_weekend"]
LAG = ["lag_1", "lag_2", "lag_48", "lag_336"]
WEATHER = ["Temperature", "Humidity", "Wind_Speed"]
FEATURE_GROUPS = {
    "calendar_only": CALENDAR,
    "lag_only": LAG,
    "weather_only": WEATHER,
    "lag_plus_calendar": LAG + CALENDAR,
    "lag_plus_weather": LAG + WEATHER,
    "lag_plus_calendar_plus_weather": LAG + CALENDAR + WEATHER,
}
DISPLAY_NAMES = {
    "calendar_only": "Calendar only",
    "lag_only": "Lag only",
    "weather_only": "Weather only",
    "lag_plus_calendar": "Lag + calendar",
    "lag_plus_weather": "Lag + weather",
    "lag_plus_calendar_plus_weather": "Lag + calendar + weather",
}
FOLDS = 5
CALIBRATION_ROWS = 400
TEST_ROWS = 400


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = actual - predicted
    return {
        "mae_normalized": float(np.mean(np.abs(error))),
        "rmse_normalized": float(np.sqrt(np.mean(error**2))),
    }


def interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    sample_std = float(array.std(ddof=1))
    half_width = float(
        student_t.ppf(0.975, len(array) - 1)
        * sample_std
        / np.sqrt(len(array))
    )
    return {
        "mean": mean,
        "sample_standard_deviation": sample_std,
        "ci95_lower": mean - half_width,
        "ci95_upper": mean + half_width,
    }


def compact_float32_predict(
    train: pd.DataFrame, test: pd.DataFrame, features: list[str]
) -> np.ndarray:
    x_train = train[features].to_numpy(dtype=np.float64)
    y_train = train[TARGET].to_numpy(dtype=np.float64)
    x_test = test[features].to_numpy(dtype=np.float64)
    mean64 = x_train.mean(axis=0)
    scale64 = x_train.std(axis=0)
    scale64[scale64 == 0] = 1.0
    design = np.column_stack(
        [np.ones(len(x_train)), (x_train - mean64) / scale64]
    )
    parameters, *_ = np.linalg.lstsq(design, y_train, rcond=None)
    mean32 = mean64.astype(np.float32)
    scale32 = scale64.astype(np.float32)
    intercept32 = np.float32(parameters[0])
    coefficients32 = parameters[1:].astype(np.float32)
    scaled32 = (x_test.astype(np.float32) - mean32) / scale32
    return (
        intercept32
        + np.sum(scaled32 * coefficients32, axis=1, dtype=np.float32)
    ).astype(np.float64)


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
    model_frame = frame.dropna(subset=LAG).reset_index(drop=True)

    initial_train_rows = len(model_frame) - FOLDS * TEST_ROWS - CALIBRATION_ROWS
    fold_results = []
    prediction_frames = []
    for fold_index in range(FOLDS):
        train_end = initial_train_rows + fold_index * TEST_ROWS
        calibration_end = train_end + CALIBRATION_ROWS
        test_end = calibration_end + TEST_ROWS
        train = model_frame.iloc[:train_end]
        calibration = model_frame.iloc[train_end:calibration_end]
        test = model_frame.iloc[calibration_end:test_end]
        if train["Timestamp"].max() >= calibration["Timestamp"].min():
            raise AssertionError("Training/calibration order failed")
        if calibration["Timestamp"].max() >= test["Timestamp"].min():
            raise AssertionError("Calibration/test order failed")

        actual = test[TARGET].to_numpy(dtype=np.float64)
        group_metrics = {}
        predictions = pd.DataFrame(
            {
                "fold": fold_index + 1,
                "Timestamp": test["Timestamp"].to_numpy(),
                "actual_normalized": actual,
            }
        )
        for group_name, features in FEATURE_GROUPS.items():
            predicted = compact_float32_predict(train, test, features)
            group_metrics[group_name] = metrics(actual, predicted)
            predictions[group_name] = predicted
        prediction_frames.append(predictions)
        fold_results.append(
            {
                "fold": fold_index + 1,
                "train_rows": len(train),
                "calibration_rows": len(calibration),
                "test_rows": len(test),
                "test_start": test["Timestamp"].min().isoformat(),
                "test_end": test["Timestamp"].max().isoformat(),
                "group_metrics": group_metrics,
            }
        )

    summaries = []
    for group_name, features in FEATURE_GROUPS.items():
        mae = [
            float(fold["group_metrics"][group_name]["mae_normalized"])
            for fold in fold_results
        ]
        rmse = [
            float(fold["group_metrics"][group_name]["rmse_normalized"])
            for fold in fold_results
        ]
        summaries.append(
            {
                "group": group_name,
                "feature_count": len(features),
                "features": features,
                "fold_mae": interval(mae),
                "fold_rmse": interval(rmse),
            }
        )
    summaries.sort(key=lambda row: row["fold_mae"]["mean"])

    lookup = {row["group"]: row for row in summaries}
    full_mae = lookup["lag_plus_calendar_plus_weather"]["fold_mae"]["mean"]
    marginal = {
        "weather_added_to_lag_plus_calendar_mae_change": float(
            full_mae - lookup["lag_plus_calendar"]["fold_mae"]["mean"]
        ),
        "calendar_added_to_lag_plus_weather_mae_change": float(
            full_mae - lookup["lag_plus_weather"]["fold_mae"]["mean"]
        ),
    }

    report = {
        "phase": 7,
        "experiment": "compact_float32_feature_group_ablation",
        "units": "normalized dataset target units; physical units not established",
        "dataset": {
            "csv_sha256": sha256(csv_path),
            "rows_after_lag_336": len(model_frame),
        },
        "fold_design": {
            "folds": FOLDS,
            "initial_training_rows": initial_train_rows,
            "calibration_rows_per_fold": CALIBRATION_ROWS,
            "test_rows_per_fold": TEST_ROWS,
            "forecast_mode": "rolling one-step-ahead",
        },
        "model": "standardized linear least squares with float32 inference emulation",
        "feature_groups": FEATURE_GROUPS,
        "excluded_opaque_feature": {
            "name": "Avg_Past_Consumption",
            "reason": "source page does not define its rolling window or prove it is causal",
        },
        "fold_results": fold_results,
        "summary_sorted_by_mean_fold_mae": summaries,
        "marginal_mean_mae_changes_negative_is_improvement": marginal,
        "limitations": [
            "Weather fields are normalized and lack measurement provenance.",
            "Contemporaneous weather is treated as available at prediction time; weather-forecast uncertainty is not modeled.",
            "Linear-model ablation does not establish feature utility for nonlinear models.",
            "Only five folds from the short case study are available.",
            "Feature groups are correlated, so marginal differences are descriptive rather than causal effects.",
        ],
    }
    (output_dir / "phase7_feature_ablation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    rows = []
    for fold in fold_results:
        for group_name in FEATURE_GROUPS:
            rows.append(
                {
                    "fold": fold["fold"],
                    "group": group_name,
                    "feature_count": len(FEATURE_GROUPS[group_name]),
                    **fold["group_metrics"][group_name],
                }
            )
    pd.DataFrame(rows).to_csv(output_dir / "phase7_feature_ablation.csv", index=False)
    pd.concat(prediction_frames, ignore_index=True).to_csv(
        output_dir / "phase7_feature_ablation_predictions.csv", index=False
    )

    groups = [row["group"] for row in summaries]
    deltas_scaled = [
        100_000.0 * (row["fold_mae"]["mean"] - full_mae) for row in summaries
    ]
    positions = np.arange(len(groups))
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.barh(positions, deltas_scaled, color="#4C956C")
    ax.set_yticks(positions, [DISPLAY_NAMES[group] for group in groups])
    ax.invert_yaxis()
    ax.set_xlabel("Mean MAE increase relative to full group (×10⁻⁵ normalized units)")
    ax.set_title("Phase 7: removing feature groups produced only small MAE changes")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase7_feature_ablation.png", dpi=200)
    plt.close(fig)

    print(json.dumps(report["summary_sorted_by_mean_fold_mae"], indent=2))
    print(json.dumps(marginal, indent=2))


if __name__ == "__main__":
    main()
