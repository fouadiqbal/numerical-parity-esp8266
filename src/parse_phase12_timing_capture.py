"""Parse ESP8266 JSONL benchmark batches into publication-ready summaries."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path, help="JSONL serial capture")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/phase12_device_timing_distribution.json"),
    )
    args = parser.parse_args()
    capture_path = args.capture.resolve()

    batches: list[dict] = []
    for line_number, line in enumerate(
        capture_path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on line {line_number}: {error}") from error
        if "tinyml_benchmark_batch" in record:
            batches.append(record)

    if len(batches) < 30:
        raise ValueError(
            f"Expected at least 30 timing batches; found {len(batches)}. "
            "Capture a complete post-boot benchmark sequence."
        )

    values = [float(batch["average_inference_us"]) for batch in batches]
    inferences = {int(batch["inferences"]) for batch in batches}
    if len(inferences) != 1:
        raise ValueError("Timing batches do not use a consistent inference count.")

    result = {
        "phase": 12,
        "source_capture": capture_path.relative_to(Path.cwd()).as_posix()
        if capture_path.is_relative_to(Path.cwd())
        else str(capture_path),
        "batch_count": len(values),
        "inferences_per_batch": next(iter(inferences)),
        "timing_unit": "microseconds per prediction",
        "mean": statistics.fmean(values),
        "sample_standard_deviation": statistics.stdev(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "p05": percentile(values, 0.05),
        "q1": percentile(values, 0.25),
        "q3": percentile(values, 0.75),
        "p95": percentile(values, 0.95),
        "maximum": max(values),
        "interquartile_range": percentile(values, 0.75)
        - percentile(values, 0.25),
        "batch_averages": values,
        "limitations": [
            "Batch averages are not individual-cycle measurements.",
            "Results apply to the recorded board, firmware, compiler, and clock setup.",
            "This is model-kernel timing, not sensing-to-alert or network latency.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
