"""Parse the paired FP32/fused/fixed ESP8266 quantization capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def describe(records: list[dict]) -> dict:
    if len(records) != 30:
        raise ValueError(f"Expected 30 batches; found {len(records)}.")
    values = [float(record["average_inference_us"]) for record in records]
    return {
        "batches": len(values),
        "inferences_per_batch": int(records[0]["inferences"]),
        "mean_us": statistics.fmean(values),
        "sample_standard_deviation_us": statistics.stdev(values),
        "median_us": statistics.median(values),
        "p05_us": percentile(values, 0.05),
        "p95_us": percentile(values, 0.95),
        "minimum_us": min(values),
        "maximum_us": max(values),
        "batch_average_us": values,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results/phase14_device_quantization.json",
    )
    args = parser.parse_args()
    capture = args.capture.resolve()
    records = [
        json.loads(line)
        for line in capture.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]

    fp32 = describe([r for r in records if "tinyml_benchmark_batch" in r])
    fused = describe([r for r in records if "fused_fp32_benchmark_batch" in r])
    fixed = describe([r for r in records if "fixed_q15_benchmark_batch" in r])
    fixed_with_conversion = describe(
        [r for r in records if "fixed_q15_with_quantization_batch" in r]
    )
    validation_records = [
        r for r in records if r.get("tinyml_full_validation") == 1
    ]
    if len(validation_records) != 1:
        raise ValueError("Expected one complete full-validation record.")
    validation = validation_records[0]
    fixed_summaries = [r for r in records if r.get("fixed_q15_summary") == 1]
    fused_summaries = [r for r in records if r.get("fused_fp32_summary") == 1]
    if len(fixed_summaries) != 1 or len(fused_summaries) != 1:
        raise ValueError("Representation self-test summaries are missing.")

    result = {
        "phase": 14,
        "date_local": "2026-09-03",
        "device": "ESP8266EX NodeMCU 1.0",
        "target_units": "normalized dataset units; physical kWh not established",
        "source_capture": {
            "path": capture.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(capture.read_bytes()).hexdigest().upper(),
        },
        "timing_distributions": {
            "standardized_fp32": fp32,
            "fused_affine_fp32": fused,
            "fixed_q15_prequantized_input": fixed,
            "fixed_q15_including_float_input_conversion": fixed_with_conversion,
        },
        "latency_comparisons": {
            "fused_fp32_speedup_vs_standardized": fp32["mean_us"]
            / fused["mean_us"],
            "prequantized_q15_speedup_vs_standardized": fp32["mean_us"]
            / fixed["mean_us"],
            "prequantized_q15_speedup_vs_fused": fused["mean_us"]
            / fixed["mean_us"],
            "q15_with_conversion_change_vs_standardized_percent": (
                fixed_with_conversion["mean_us"] / fp32["mean_us"] - 1.0
            )
            * 100,
        },
        "physical_full_validation": {
            "vectors": validation["vectors"],
            "standardized_fp32_prediction_parity": validation[
                "prediction_parity_passed"
            ],
            "standardized_fp32_decision_parity": validation[
                "anomaly_parity_passed"
            ],
            "fused_fp32_decision_agreement": validation[
                "fused_fp32_decision_agreement"
            ],
            "fused_fp32_max_difference_normalized": validation[
                "fused_fp32_max_difference_normalized"
            ],
            "fused_fp32_device_mae_normalized": validation[
                "fused_fp32_device_mae_normalized"
            ],
            "fused_fp32_device_rmse_normalized": validation[
                "fused_fp32_device_rmse_normalized"
            ],
            "fixed_q15_decision_agreement": validation[
                "fixed_q15_decision_agreement"
            ],
            "fixed_q15_max_difference_normalized": validation[
                "fixed_q15_max_difference_normalized"
            ],
            "fixed_q15_device_mae_normalized": validation[
                "fixed_q15_device_mae_normalized"
            ],
            "fixed_q15_device_rmse_normalized": validation[
                "fixed_q15_device_rmse_normalized"
            ],
        },
        "spot_checks": {
            "fused_fp32": fused_summaries[0],
            "fixed_q15": fixed_summaries[0],
        },
        "interpretation": {
            "selected_current_default": "fused_affine_fp32",
            "reason": (
                "It removes standardization divisions, preserves all decisions, and "
                "is 3x faster without requiring a fixed-point feature lifecycle."
            ),
            "conditional_option": "fixed_q15_q30",
            "condition": (
                "Use Q15 only when sensor/calendar features are quantized once at "
                "acquisition and the lag buffer stores Q15 values."
            ),
            "critical_fairness_result": (
                "Converting all float features to Q15 inside each prediction made the "
                "path slower than standardized FP32 in this implementation."
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
