"""Five-fold leakage-safe rolling-origin forecasting evaluation.

The experiment uses expanding training windows, a distinct 400-row calibration
window, and a later non-overlapping 400-row test window in each fold. Forecasts
are one-step-ahead evaluations using lag values available at prediction time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.stats import t as student_t
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression


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
TARGET = "Electricity_Consumed"
MODEL_ORDER = [
    "persistence_lag_1",
    "seasonal_naive_lag_48",
    "linear_regression",
    "random_forest",
    "hist_gradient_boosting",
    "compact_edge_linear_float32",
]
DISPLAY_NAMES = {
    "persistence_lag_1": "Persistence (1)",
    "seasonal_naive_lag_48": "Seasonal naive (48)",
    "linear_regression": "Linear regression",
    "random_forest": "Random forest",
    "hist_gradient_boosting": "Hist. gradient boost",
    "compact_edge_linear_float32": "Compact edge LR (FP32)",
}
SEED = 42
FOLDS = 5
CALIBRATION_ROWS = 400
TEST_ROWS = 400


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = actual - predicted
    denominator = np.abs(actual) + np.abs(predicted)
    smape = np.divide(
        2.0 * np.abs(error),
        denominator,
        out=np.zeros_like(error, dtype=np.float64),
        where=denominator > 0,
    )
    return {
        "mae_normalized": float(np.mean(np.abs(error))),
        "rmse_normalized": float(np.sqrt(np.mean(error**2))),
        "smape_percent": float(100.0 * np.mean(smape)),
    }


def confidence_interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    sample_std = float(array.std(ddof=1))
    critical = float(student_t.ppf(0.975, df=len(array) - 1))
    half_width = critical * sample_std / np.sqrt(len(array))
    return {
        "mean": mean,
        "sample_standard_deviation": sample_std,
        "ci95_lower": mean - half_width,
        "ci95_upper": mean + half_width,
        "ci_method": "two-sided Student-t interval over five fold metrics",
    }


def edge_float32_prediction(
    x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray
) -> np.ndarray:
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
    weighted32 = scaled32 * coefficients32
    return (
        intercept32 + np.sum(weighted32, axis=1, dtype=np.float32)
    ).astype(np.float64)


def fit_predict_models(
    train: pd.DataFrame, test: pd.DataFrame
) -> dict[str, np.ndarray]:
    x_train = train[FEATURES].to_numpy(dtype=np.float64)
    y_train = train[TARGET].to_numpy(dtype=np.float64)
    x_test = test[FEATURES].to_numpy(dtype=np.float64)

    predictions: dict[str, np.ndarray] = {
        "persistence_lag_1": test["lag_1"].to_numpy(dtype=np.float64),
        "seasonal_naive_lag_48": test["lag_48"].to_numpy(dtype=np.float64),
    }

    linear = LinearRegression().fit(x_train, y_train)
    predictions["linear_regression"] = linear.predict(x_test)

    forest = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=-1,
    ).fit(x_train, y_train)
    predictions["random_forest"] = forest.predict(x_test)

    boosting = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=0.1,
        random_state=SEED,
    ).fit(x_train, y_train)
    predictions["hist_gradient_boosting"] = boosting.predict(x_test)
    predictions["compact_edge_linear_float32"] = edge_float32_prediction(
        x_train, y_train, x_test
    )
    return predictions


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

    initial_train_rows = len(model_frame) - FOLDS * TEST_ROWS - CALIBRATION_ROWS
    if initial_train_rows <= 0:
        raise ValueError("Dataset is too short for the configured folds")

    fold_results: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    absolute_errors: dict[str, list[np.ndarray]] = {name: [] for name in MODEL_ORDER}

    for fold_index in range(FOLDS):
        train_end = initial_train_rows + fold_index * TEST_ROWS
        calibration_end = train_end + CALIBRATION_ROWS
        test_end = calibration_end + TEST_ROWS
        train = model_frame.iloc[:train_end]
        calibration = model_frame.iloc[train_end:calibration_end]
        test = model_frame.iloc[calibration_end:test_end]

        if not (
            train["Timestamp"].max()
            < calibration["Timestamp"].min()
            < calibration["Timestamp"].max()
            < test["Timestamp"].min()
        ):
            raise AssertionError(f"Temporal ordering failed in fold {fold_index + 1}")

        predictions = fit_predict_models(train, test)
        actual = test[TARGET].to_numpy(dtype=np.float64)
        model_metrics = {}
        fold_predictions = pd.DataFrame(
            {
                "fold": fold_index + 1,
                "Timestamp": test["Timestamp"].to_numpy(),
                "actual_normalized": actual,
            }
        )
        for model_name in MODEL_ORDER:
            predicted = predictions[model_name]
            model_metrics[model_name] = regression_metrics(actual, predicted)
            absolute_errors[model_name].append(np.abs(actual - predicted))
            fold_predictions[model_name] = predicted
        prediction_frames.append(fold_predictions)

        fold_results.append(
            {
                "fold": fold_index + 1,
                "train_rows": len(train),
                "calibration_rows": len(calibration),
                "test_rows": len(test),
                "train_start": train["Timestamp"].min().isoformat(),
                "train_end": train["Timestamp"].max().isoformat(),
                "calibration_start": calibration["Timestamp"].min().isoformat(),
                "calibration_end": calibration["Timestamp"].max().isoformat(),
                "test_start": test["Timestamp"].min().isoformat(),
                "test_end": test["Timestamp"].max().isoformat(),
                "model_metrics": model_metrics,
            }
        )

    all_predictions = pd.concat(prediction_frames, ignore_index=True)
    summaries = []
    for model_name in MODEL_ORDER:
        fold_mae = [
            float(fold["model_metrics"][model_name]["mae_normalized"])
            for fold in fold_results
        ]
        fold_rmse = [
            float(fold["model_metrics"][model_name]["rmse_normalized"])
            for fold in fold_results
        ]
        fold_smape = [
            float(fold["model_metrics"][model_name]["smape_percent"])
            for fold in fold_results
        ]
        summaries.append(
            {
                "model": model_name,
                "fold_mae": confidence_interval(fold_mae),
                "fold_rmse": confidence_interval(fold_rmse),
                "fold_smape": confidence_interval(fold_smape),
                "pooled_test_metrics": regression_metrics(
                    all_predictions["actual_normalized"].to_numpy(dtype=np.float64),
                    all_predictions[model_name].to_numpy(dtype=np.float64),
                ),
            }
        )
    summaries.sort(key=lambda row: row["fold_mae"]["mean"])

    edge_linear_difference = np.abs(
        all_predictions["compact_edge_linear_float32"].to_numpy(dtype=np.float64)
        - all_predictions["linear_regression"].to_numpy(dtype=np.float64)
    )

    report = {
        "phase": 5,
        "experiment": "five_fold_expanding_window_forecasting",
        "forecast_mode": (
            "rolling one-step-ahead; each lag uses an observation available before "
            "the prediction timestamp"
        ),
        "units": "normalized dataset target units; physical kWh not established",
        "dataset": {
            "source": "https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset",
            "csv_sha256": sha256(csv_path),
            "rows_after_lag_336": len(model_frame),
        },
        "fold_design": {
            "folds": FOLDS,
            "initial_training_rows": initial_train_rows,
            "calibration_rows_per_fold": CALIBRATION_ROWS,
            "test_rows_per_fold": TEST_ROWS,
            "non_overlapping_test_rows_total": FOLDS * TEST_ROWS,
            "training_window": "expanding",
            "calibration_window": "fixed length, immediately after training",
            "test_window": "fixed length, immediately after calibration",
        },
        "features": FEATURES,
        "seed": SEED,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "fold_results": fold_results,
        "summary_sorted_by_mean_fold_mae": summaries,
        "edge_float32_vs_linear_float64": {
            "tested_predictions": len(edge_linear_difference),
            "mean_absolute_prediction_difference": float(edge_linear_difference.mean()),
            "maximum_absolute_prediction_difference": float(edge_linear_difference.max()),
        },
        "limitations": [
            "Only five folds are available in this short 104-day normalized case study.",
            "Student-t intervals over five folds are imprecise and folds are temporally dependent.",
            "The evaluation is rolling one-step-ahead, not a 400-step recursive forecast.",
            "The calibration blocks are reserved for later anomaly-threshold analysis.",
            "Official-dataset external validation remains unrun.",
        ],
    }
    (output_dir / "phase5_walk_forward_results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    fold_rows = []
    for fold in fold_results:
        for model_name in MODEL_ORDER:
            fold_rows.append(
                {
                    "fold": fold["fold"],
                    "model": model_name,
                    "train_rows": fold["train_rows"],
                    "calibration_rows": fold["calibration_rows"],
                    "test_rows": fold["test_rows"],
                    "test_start": fold["test_start"],
                    "test_end": fold["test_end"],
                    **fold["model_metrics"][model_name],
                }
            )
    pd.DataFrame(fold_rows).to_csv(
        output_dir / "phase5_walk_forward_fold_metrics.csv", index=False
    )
    all_predictions.to_csv(
        output_dir / "phase5_walk_forward_predictions.csv", index=False
    )

    sorted_models = [row["model"] for row in summaries]
    means = [row["fold_mae"]["mean"] for row in summaries]
    lower = [
        row["fold_mae"]["mean"] - row["fold_mae"]["ci95_lower"]
        for row in summaries
    ]
    upper = [
        row["fold_mae"]["ci95_upper"] - row["fold_mae"]["mean"]
        for row in summaries
    ]
    positions = np.arange(len(sorted_models))
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.bar(positions, means, color="#2878B5")
    ax.errorbar(
        positions,
        means,
        yerr=np.vstack([lower, upper]),
        fmt="none",
        ecolor="black",
        capsize=5,
        linewidth=1.2,
    )
    ax.set_xticks(
        positions,
        [DISPLAY_NAMES[name] for name in sorted_models],
        rotation=18,
        ha="right",
    )
    ax.set_ylabel("Mean fold MAE (normalized target units)")
    ax.set_title("Phase 5: five-fold rolling-origin comparison (95% t intervals)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase5_walk_forward_model_comparison.png", dpi=200)
    plt.close(fig)

    box_data = [np.concatenate(absolute_errors[name]) for name in sorted_models]
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.boxplot(box_data, tick_labels=[DISPLAY_NAMES[name] for name in sorted_models], showfliers=False)
    ax.set_ylabel("Absolute error (normalized target units)")
    ax.set_title("Phase 5: absolute-error distributions across 2,000 test predictions")
    ax.tick_params(axis="x", rotation=18)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "phase5_walk_forward_error_distribution.png", dpi=200)
    plt.close(fig)

    print(json.dumps(report["summary_sorted_by_mean_fold_mae"], indent=2))


if __name__ == "__main__":
    main()
