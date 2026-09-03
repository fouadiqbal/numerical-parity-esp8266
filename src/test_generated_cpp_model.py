"""Compile and execute the generated C++ model against all Python test rows."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


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
PREDICTION_TOLERANCE = 1e-6


def locate_compiler(explicit: Path | None) -> Path:
    candidates = [
        explicit,
        Path(os.environ["CXX"]) if os.environ.get("CXX") else None,
        Path(shutil.which("g++")) if shutil.which("g++") else None,
        Path(r"C:\Program Files\CodeBlocks\MinGW\bin\g++.exe"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("No host g++ compiler found; pass --compiler")


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=repository / "data/source/extracted/smart_meter_data.csv",
    )
    parser.add_argument("--compiler", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=repository / "results/tinyml_cpp_parity.json",
    )
    return parser.parse_args()


def prepare_reference(csv_path: Path) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
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
    frame = frame.dropna(subset=FEATURES).reset_index(drop=True)

    train_end = int(len(frame) * 0.80)
    training = frame.iloc[:train_end]
    test = frame.iloc[train_end:].copy()
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

    def predict(partition: pd.DataFrame) -> np.ndarray:
        x = partition[FEATURES].to_numpy(dtype=np.float64)
        return parameters[0] + ((x - mean) / scale) @ parameters[1:]

    calibration_residual = np.abs(
        calibration[TARGET].to_numpy(dtype=np.float64) - predict(calibration)
    )
    threshold = float(np.quantile(calibration_residual, 0.99))
    reference_prediction = predict(test)
    reference_anomaly = (
        np.abs(test[TARGET].to_numpy(dtype=np.float64) - reference_prediction)
        > threshold
    )
    return test, reference_prediction, reference_anomaly


def main() -> None:
    args = parse_args()
    repository = Path(__file__).resolve().parents[1]
    compiler = locate_compiler(args.compiler)
    test, reference_prediction, reference_anomaly = prepare_reference(args.csv.resolve())
    compiler_environment = os.environ.copy()
    compiler_environment["PATH"] = (
        str(compiler.parent) + os.pathsep + compiler_environment.get("PATH", "")
    )

    compiler_version = subprocess.run(
        [str(compiler), "--version"],
        check=True,
        capture_output=True,
        text=True,
        env=compiler_environment,
    ).stdout.splitlines()[0]

    with tempfile.TemporaryDirectory(prefix="tinyml_cpp_parity_") as temp_name:
        executable = Path(temp_name) / "tinyml_model_runner.exe"
        compile_command = [
            str(compiler),
            "-std=c++17",
            "-O2",
            "-static",
            "-I",
            str(repository / "tests/cpp"),
            "-I",
            str(repository / "esp8266"),
            str(repository / "tests/cpp/tinyml_model_runner.cpp"),
            "-o",
            str(executable),
        ]
        compile_result = subprocess.run(
            compile_command,
            check=True,
            capture_output=True,
            text=True,
            env=compiler_environment,
        )
        input_rows = []
        for _, row in test.iterrows():
            values = [float(row[name]) for name in FEATURES] + [float(row[TARGET])]
            input_rows.append(" ".join(f"{value:.17g}" for value in values))
        execution = subprocess.run(
            [str(executable)],
            input="\n".join(input_rows) + "\n",
            check=True,
            capture_output=True,
            text=True,
        )

    output_rows = [line.split() for line in execution.stdout.splitlines() if line.strip()]
    if len(output_rows) != len(test):
        raise AssertionError(f"Expected {len(test)} C++ rows, received {len(output_rows)}")
    cpp_prediction = np.asarray([float(row[0]) for row in output_rows])
    cpp_anomaly = np.asarray([bool(int(row[1])) for row in output_rows])
    difference = np.abs(cpp_prediction - reference_prediction)
    prediction_pass = difference <= PREDICTION_TOLERANCE
    anomaly_pass = cpp_anomaly == reference_anomaly

    report = {
        "phase": 10,
        "test": "generated_cpp_model_vs_python_reference",
        "rows": len(test),
        "target_units": "normalized dataset units; physical kWh not established",
        "prediction_tolerance": PREDICTION_TOLERANCE,
        "prediction_matches": int(prediction_pass.sum()),
        "prediction_mismatches": int((~prediction_pass).sum()),
        "mean_absolute_numerical_difference": float(difference.mean()),
        "maximum_absolute_numerical_difference": float(difference.max()),
        "anomaly_decision_matches": int(anomaly_pass.sum()),
        "anomaly_decision_mismatches": int((~anomaly_pass).sum()),
        "compiler": {
            "path": str(compiler),
            "version": compiler_version,
            "standard": "C++17",
            "optimization": "-O2",
            "stderr": compile_result.stderr,
        },
        "passed": bool(prediction_pass.all() and anomaly_pass.all()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
