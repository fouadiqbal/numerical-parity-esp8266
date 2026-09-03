"""Convert a complete ESP8266 serial capture into a normalized HIL evidence record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--port", default="COM11")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "tinyml_device_benchmark_v2.json",
    )
    args = parser.parse_args()
    capture_path = args.capture.resolve()

    records = [
        json.loads(line)
        for line in capture_path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    spot_checks = [record for record in records if "tinyml_vector" in record]
    batches = [record for record in records if "tinyml_benchmark_batch" in record]
    summaries = [record for record in records if record.get("tinyml_summary") == 1]
    validations = [
        record for record in records if record.get("tinyml_full_validation") == 1
    ]
    telemetry = [record for record in records if "thingspeak_entry_id" in record]

    if len(spot_checks) != 8 or not all(item["parity_ok"] == 1 for item in spot_checks):
        raise ValueError("The eight-vector physical self-test is incomplete or failed.")
    if len(batches) != 30:
        raise ValueError(f"Expected 30 timing batches; found {len(batches)}.")
    if len(summaries) != 1 or len(validations) != 1:
        raise ValueError("Expected exactly one model summary and one full validation record.")

    summary = summaries[0]
    validation = validations[0]
    if validation["prediction_parity_passed"] != validation["vectors"]:
        raise ValueError("Full physical prediction parity failed.")
    if validation["anomaly_parity_passed"] != validation["vectors"]:
        raise ValueError("Full physical anomaly-decision parity failed.")

    manifest = json.loads(
        (ROOT / "results" / "tinyml_model_manifest.json").read_text(encoding="utf-8")
    )
    builds = json.loads(
        (ROOT / "results" / "phase12_benchmark_ready_builds.json").read_text(
            encoding="utf-8"
        )
    )

    output = {
        "schema_version": 2,
        "benchmark_date_local": "2026-09-03",
        "device": "ESP8266EX NodeMCU 1.0",
        "serial_port": args.port,
        "model": manifest["model_name"],
        "model_fingerprint_sha256": manifest["model_fingerprint_sha256"],
        "target_units": "normalized dataset units; physical kWh not established",
        "validation_mode": "replayed fixed held-out feature vectors from program flash",
        "source_capture": {
            "path": capture_path.relative_to(ROOT).as_posix()
            if capture_path.is_relative_to(ROOT)
            else str(capture_path),
            "sha256": sha256(capture_path),
            "first_capture_utc": records[0].get("captured_at_utc"),
            "last_capture_utc": records[-1].get("captured_at_utc"),
        },
        "spot_check": {
            "passed": sum(item["parity_ok"] for item in spot_checks),
            "total": len(spot_checks),
        },
        "timing": {
            "batches": len(batches),
            "inferences_per_batch": summary["inferences_per_batch"],
            "average_inference_us_across_batches": summary[
                "average_inference_us_across_batches"
            ],
            "minimum_batch_average_us": summary["minimum_batch_average_us"],
            "maximum_batch_average_us": summary["maximum_batch_average_us"],
            "batch_average_inference_us": [
                batch["average_inference_us"] for batch in batches
            ],
        },
        "full_test_validation": {
            "vectors": validation["vectors"],
            "prediction_parity_passed": validation["prediction_parity_passed"],
            "anomaly_parity_passed": validation["anomaly_parity_passed"],
            "max_prediction_difference_normalized": validation[
                "max_prediction_difference_normalized"
            ],
            "device_mae_normalized": validation["device_mae_normalized"],
            "device_rmse_normalized": validation["device_rmse_normalized"],
            "true_positive": validation["true_positive"],
            "false_positive": validation["false_positive"],
            "false_negative": validation["false_negative"],
            "true_negative": validation["true_negative"],
            "validation_elapsed_us": validation["validation_elapsed_us"],
            "validation_elapsed_us_per_vector": validation[
                "validation_elapsed_us"
            ]
            / validation["vectors"],
        },
        "whole_firmware_resources": builds["full_validation_build"],
        "telemetry_during_capture": {
            "records": len(telemetry),
            "all_http_200": bool(telemetry)
            and all(record["http_code"] == 200 for record in telemetry),
            "thing_speak_entry_ids": [
                record["thingspeak_entry_id"] for record in telemetry
            ],
            "raw_adc_range": [
                min(record["raw_adc"] for record in telemetry),
                max(record["raw_adc"] for record in telemetry),
            ],
            "warning": (
                "The unconnected/uncalibrated ADC telemetry is a connectivity check, "
                "not a physical energy measurement."
            ),
        },
        "limitations": [
            "Held-out vectors were replayed from program flash.",
            "No calibrated electrical sensing front end was used.",
            "No live lag-history buffer generated the model inputs.",
            "Timing covers model batches, not sensing-to-cloud latency.",
            "HTTP telemetry is not a secure-channel validation.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
