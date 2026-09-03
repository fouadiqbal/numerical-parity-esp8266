"""Create a deterministic integrity report for the working smart-meter CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


EXPECTED_COLUMNS = [
    "Timestamp",
    "Electricity_Consumed",
    "Temperature",
    "Humidity",
    "Wind_Speed",
    "Avg_Past_Consumption",
    "Anomaly_Label",
]

NUMERIC_COLUMNS = EXPECTED_COLUMNS[1:6]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def parse_args() -> argparse.Namespace:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=repository / "data/source/extracted/smart_meter_data.csv",
    )
    parser.add_argument(
        "--zip",
        type=Path,
        default=repository / "data/source/smart-meter-dataset.zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repository / "results/dataset_integrity.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()
    zip_path = args.zip.resolve()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if columns != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected columns: {columns}")
        rows = list(reader)

    blank_cells = sum(
        value is None or value.strip() == ""
        for row in rows
        for value in row.values()
    )
    timestamps = [datetime.fromisoformat(row["Timestamp"]) for row in rows]
    non_30_minute_intervals = sum(
        (current - previous).total_seconds() != 1800
        for previous, current in zip(timestamps, timestamps[1:])
    )

    numeric_summary = {}
    for column in NUMERIC_COLUMNS:
        values = [float(row[column]) for row in rows]
        numeric_summary[column] = {
            "minimum": min(values),
            "maximum": max(values),
            "mean": sum(values) / len(values),
        }

    report = {
        "source_listing": "https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset",
        "local_csv": "data/source/extracted/smart_meter_data.csv",
        "local_zip": "data/source/smart-meter-dataset.zip",
        "csv_bytes": csv_path.stat().st_size,
        "zip_bytes": zip_path.stat().st_size,
        "csv_sha256": sha256(csv_path),
        "zip_sha256": sha256(zip_path),
        "rows": len(rows),
        "columns": columns,
        "first_timestamp": timestamps[0].isoformat(sep=" "),
        "last_timestamp": timestamps[-1].isoformat(sep=" "),
        "unique_timestamps": len(set(timestamps)),
        "duplicate_timestamps": len(timestamps) - len(set(timestamps)),
        "non_30_minute_consecutive_intervals": non_30_minute_intervals,
        "blank_cells": blank_cells,
        "label_counts": dict(sorted(Counter(row["Anomaly_Label"] for row in rows).items())),
        "numeric_summary": numeric_summary,
        "unit_warning": (
            "Every numeric column has observed minimum 0 and maximum approximately 1. "
            "Physical units stated on the source page are not recoverable from this file "
            "without authoritative inverse-scaling metadata."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
