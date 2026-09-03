"""Compile the generated Q15/Q30 model and compare all 933 rows with Python."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
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


def main() -> None:
    compiler = Path(r"C:\Program Files\CodeBlocks\MinGW\bin\g++.exe")
    if not compiler.is_file():
        found = shutil.which("g++")
        if not found:
            raise FileNotFoundError("No host g++ compiler found.")
        compiler = Path(found)
    environment = os.environ.copy()
    environment["PATH"] = str(compiler.parent) + os.pathsep + environment.get("PATH", "")

    predictions = pd.read_csv(ROOT / "results/phase14_quantization_predictions.csv")
    frame = pd.read_csv(ROOT / "data/source/extracted/smart_meter_data.csv")
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="raise")
    frame = frame.sort_values("Timestamp").reset_index(drop=True)
    target = "Electricity_Consumed"
    frame["lag_1"] = frame[target].shift(1)
    frame["lag_2"] = frame[target].shift(2)
    frame["lag_48"] = frame[target].shift(48)
    frame["lag_336"] = frame[target].shift(336)
    frame["hour"] = frame["Timestamp"].dt.hour
    frame["day_of_week"] = frame["Timestamp"].dt.dayofweek
    frame["month"] = frame["Timestamp"].dt.month
    frame["is_weekend"] = (frame["day_of_week"] >= 5).astype(int)
    frame = frame.dropna(subset=FEATURES).reset_index(drop=True)
    test = frame.iloc[int(len(frame) * 0.8) :].copy()

    with tempfile.TemporaryDirectory(prefix="fixed_model_cpp_") as temporary:
        executable = Path(temporary) / "fixed_model_runner.exe"
        compile_result = subprocess.run(
            [
                str(compiler),
                "-std=c++17",
                "-O2",
                "-static",
                "-I",
                str(ROOT / "tests/cpp"),
                "-I",
                str(ROOT / "esp8266"),
                str(ROOT / "tests/cpp/tinyml_fixed_model_runner.cpp"),
                "-o",
                str(executable),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        rows = []
        for _, row in test.iterrows():
            values = [float(row[name]) for name in FEATURES] + [float(row[target])]
            rows.append(" ".join(f"{value:.17g}" for value in values))
        execution = subprocess.run(
            [str(executable)],
            input="\n".join(rows) + "\n",
            check=True,
            capture_output=True,
            text=True,
        )

    output = [line.split() for line in execution.stdout.splitlines() if line.strip()]
    if len(output) != len(test):
        raise AssertionError(f"Expected {len(test)} output rows; received {len(output)}")
    cpp_prediction = np.array([float(row[0]) for row in output])
    cpp_decision = np.array([bool(int(row[1])) for row in output])
    python_prediction = predictions["fixed_q15_q30"].to_numpy()
    python_decision = predictions["fixed_q15_anomaly"].astype(bool).to_numpy()
    difference = np.abs(cpp_prediction - python_prediction)

    result = {
        "phase": 14,
        "test": "generated_q15_q30_cpp_vs_python",
        "rows": len(test),
        "prediction_tolerance_normalized": 1e-6,
        "prediction_matches": int(np.sum(difference <= 1e-6)),
        "maximum_absolute_difference_normalized": float(difference.max()),
        "decision_matches": int(np.sum(cpp_decision == python_decision)),
        "compiler": str(compiler),
        "compile_stderr": compile_result.stderr,
        "passed": bool(
            np.all(difference <= 1e-6) and np.all(cpp_decision == python_decision)
        ),
    }
    path = ROOT / "results/phase14_fixed_cpp_parity.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
