"""Run Phase 4 chronological forecasting baselines on the normalized case study.

This experiment intentionally reports normalized target units. It does not treat
the source file's scaled values as verified physical kWh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
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
SEED = 42


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = actual - predicted
    denominator = np.abs(actual) + np.abs(predicted)
    smape_terms = np.divide(
        2.0 * np.abs(error),
        denominator,
        out=np.zeros_like(error, dtype=np.float64),
        where=denominator > 0,
    )
    return {
        "mae_normalized": float(np.mean(np.abs(error))),
        "rmse_normalized": float(np.sqrt(np.mean(error**2))),
        "smape_percent": float(100.0 * np.mean(smape_terms)),
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
    if frame["Timestamp"].duplicated().any():
        raise ValueError("Duplicate timestamps are not allowed")

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
    train = model_frame.iloc[:train_end].copy()
    test = model_frame.iloc[train_end:].copy()
    if train["Timestamp"].max() >= test["Timestamp"].min():
        raise AssertionError("Chronological split failed")

    x_train = train[FEATURES].to_numpy(dtype=np.float64)
    y_train = train[TARGET].to_numpy(dtype=np.float64)
    x_test = test[FEATURES].to_numpy(dtype=np.float64)
    y_test = test[TARGET].to_numpy(dtype=np.float64)

    predictions: dict[str, np.ndarray] = {
        "persistence_lag_1": test["lag_1"].to_numpy(dtype=np.float64),
        "seasonal_naive_lag_48": test["lag_48"].to_numpy(dtype=np.float64),
    }
    configurations: dict[str, dict[str, object]] = {
        "persistence_lag_1": {"kind": "naive", "lag": 1},
        "seasonal_naive_lag_48": {"kind": "seasonal_naive", "lag": 48},
    }
    fit_seconds: dict[str, float] = {
        "persistence_lag_1": 0.0,
        "seasonal_naive_lag_48": 0.0,
    }

    linear = LinearRegression()
    started = time.perf_counter()
    linear.fit(x_train, y_train)
    fit_seconds["linear_regression"] = time.perf_counter() - started
    predictions["linear_regression"] = linear.predict(x_test)
    configurations["linear_regression"] = {
        "kind": "LinearRegression",
        "fit_intercept": True,
        "training_rows": len(train),
    }

    forest = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=-1,
    )
    started = time.perf_counter()
    forest.fit(x_train, y_train)
    fit_seconds["random_forest"] = time.perf_counter() - started
    predictions["random_forest"] = forest.predict(x_test)
    configurations["random_forest"] = {
        "kind": "RandomForestRegressor",
        "n_estimators": 200,
        "max_depth": 12,
        "min_samples_leaf": 2,
        "random_state": SEED,
        "training_rows": len(train),
    }

    boosting = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=0.1,
        random_state=SEED,
    )
    started = time.perf_counter()
    boosting.fit(x_train, y_train)
    fit_seconds["hist_gradient_boosting"] = time.perf_counter() - started
    predictions["hist_gradient_boosting"] = boosting.predict(x_test)
    configurations["hist_gradient_boosting"] = {
        "kind": "HistGradientBoostingRegressor",
        "learning_rate": 0.05,
        "max_iter": 200,
        "max_leaf_nodes": 31,
        "min_samples_leaf": 20,
        "l2_regularization": 0.1,
        "random_state": SEED,
        "training_rows": len(train),
    }

    # Match the deployed edge protocol: the earliest 80% of the training block
    # fits the model while the latest 20% remains available for calibration.
    edge_fit_end = int(len(train) * 0.80)
    edge_fit = train.iloc[:edge_fit_end]
    x_edge_fit = edge_fit[FEATURES].to_numpy(dtype=np.float64)
    y_edge_fit = edge_fit[TARGET].to_numpy(dtype=np.float64)
    feature_mean = x_edge_fit.mean(axis=0)
    feature_scale = x_edge_fit.std(axis=0)
    feature_scale[feature_scale == 0] = 1.0
    edge_design = np.column_stack(
        [np.ones(len(x_edge_fit)), (x_edge_fit - feature_mean) / feature_scale]
    )
    started = time.perf_counter()
    edge_parameters, *_ = np.linalg.lstsq(edge_design, y_edge_fit, rcond=None)
    fit_seconds["compact_edge_linear"] = time.perf_counter() - started
    predictions["compact_edge_linear"] = edge_parameters[0] + (
        (x_test - feature_mean) / feature_scale
    ) @ edge_parameters[1:]
    configurations["compact_edge_linear"] = {
        "kind": "standardized_linear_least_squares",
        "training_rows": len(edge_fit),
        "reserved_calibration_rows": len(train) - len(edge_fit),
        "feature_count": len(FEATURES),
        "numerical_representation_in_python": "float64",
        "deployment_representation": "float32 C++ constants",
    }

    results = []
    for model_name, prediction in predictions.items():
        results.append(
            {
                "model": model_name,
                **metrics(y_test, prediction),
                "fit_seconds_observed": fit_seconds[model_name],
                "configuration": configurations[model_name],
            }
        )
    results.sort(key=lambda item: item["mae_normalized"])

    report = {
        "phase": 4,
        "experiment": "chronological_forecasting_baselines_normalized_case_study",
        "units": "normalized dataset target units; physical kWh not established",
        "dataset": {
            "source": "https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset",
            "csv_sha256": sha256(csv_path),
            "raw_rows": len(frame),
            "rows_after_lag_336": len(model_frame),
        },
        "split": {
            "method": "single chronological 80/20 holdout",
            "train_rows": len(train),
            "test_rows": len(test),
            "train_start": train["Timestamp"].min().isoformat(),
            "train_end": train["Timestamp"].max().isoformat(),
            "test_start": test["Timestamp"].min().isoformat(),
            "test_end": test["Timestamp"].max().isoformat(),
        },
        "features": FEATURES,
        "seed": SEED,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "results_sorted_by_mae": results,
        "limitations": [
            "Single chronological holdout; rolling-origin validation is Phase 5.",
            "All target values are normalized; physical kWh cannot be inferred.",
            "This case study has undocumented measurement provenance.",
            "Observed fit time is machine-dependent and is not a model-quality metric.",
        ],
    }

    json_path = output_dir / "phase4_forecasting_results.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    prediction_frame = pd.DataFrame(
        {
            "Timestamp": test["Timestamp"].to_numpy(),
            "actual_normalized": y_test,
            **{name: values for name, values in predictions.items()},
        }
    )
    prediction_frame.to_csv(
        output_dir / "phase4_forecasting_predictions.csv", index=False
    )

    names = [item["model"] for item in results]
    display_names = {
        "compact_edge_linear": "Compact edge LR",
        "linear_regression": "Linear regression",
        "random_forest": "Random forest",
        "hist_gradient_boosting": "Hist. gradient boost",
        "seasonal_naive_lag_48": "Seasonal naive (48)",
        "persistence_lag_1": "Persistence (1)",
    }
    mae_values = [item["mae_normalized"] for item in results]
    rmse_values = [item["rmse_normalized"] for item in results]
    positions = np.arange(len(names))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.bar(positions - width / 2, mae_values, width, label="MAE")
    ax.bar(positions + width / 2, rmse_values, width, label="RMSE")
    ax.set_xticks(positions, [display_names[name] for name in names], rotation=18, ha="right")
    ax.set_ylabel("Error (normalized target units)")
    ax.set_title("Phase 4: chronological holdout forecasting comparison")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "phase4_forecasting_comparison.png", dpi=200)
    plt.close(fig)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
