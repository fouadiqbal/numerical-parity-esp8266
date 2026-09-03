"""Audit and separate offline, compiled-host, and physical ESP8266 evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "results"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest().upper()


def main() -> None:
    metrics_path = OUTPUTS / "tinyml_edge_metrics_v2.json"
    host_path = OUTPUTS / "tinyml_cpp_parity.json"
    device_path = OUTPUTS / "tinyml_device_benchmark_v2.json"
    builds_path = OUTPUTS / "phase12_benchmark_ready_builds.json"

    metrics = read_json(metrics_path)
    host = read_json(host_path)
    device = read_json(device_path)
    builds = read_json(builds_path)
    device_full = device["full_test_validation"]

    if metrics["test_rows"] != 933:
        raise ValueError("Expected the frozen 933-row test partition.")
    if not host["passed"] or host["prediction_matches"] != metrics["test_rows"]:
        raise ValueError("Compiled-host parity evidence is incomplete.")
    if device_full["prediction_parity_passed"] != metrics["test_rows"]:
        raise ValueError("Physical-device prediction parity evidence is incomplete.")
    if device_full["anomaly_parity_passed"] != metrics["test_rows"]:
        raise ValueError("Physical-device anomaly parity evidence is incomplete.")

    device_confusion = {
        "true_positive": device_full["true_positive"],
        "false_positive": device_full["false_positive"],
        "false_negative": device_full["false_negative"],
        "true_negative": device_full["true_negative"],
    }
    python_confusion = {
        key: metrics["classification"][key]
        for key in device_confusion
    }
    if device_confusion != python_confusion:
        raise ValueError("Device and Python confusion matrices differ.")

    result = {
        "phase": 11,
        "title": "HIL evidence separation audit",
        "target_units": "normalized dataset units; physical kWh not established",
        "evidence_layers": [
            {
                "layer": 1,
                "name": "offline_python_evaluation",
                "execution_target": "desktop Python",
                "vectors": metrics["test_rows"],
                "source": metrics_path.relative_to(ROOT).as_posix(),
                "proves": [
                    "chronological reference predictions and residual decisions",
                    "reference forecasting and supplied-label classification metrics",
                ],
                "does_not_prove": [
                    "C++ numerical portability",
                    "physical ESP8266 execution",
                    "calibrated energy sensing",
                ],
            },
            {
                "layer": 2,
                "name": "compiled_host_cpp_parity",
                "execution_target": "independently compiled C++17 executable",
                "vectors": host["rows"],
                "prediction_matches": host["prediction_matches"],
                "anomaly_decision_matches": host["anomaly_decision_matches"],
                "maximum_absolute_difference_normalized": host[
                    "maximum_absolute_numerical_difference"
                ],
                "source": host_path.relative_to(ROOT).as_posix(),
                "proves": [
                    "generated-header arithmetic and feature-order parity",
                    "float64-to-float32 transfer within the declared tolerance",
                ],
                "does_not_prove": [
                    "ESP8266 timing or resource behavior",
                    "live sensor or network operation",
                ],
            },
            {
                "layer": 3,
                "name": "physical_esp8266_hil_replay",
                "execution_target": device["device"],
                "benchmark_date": device["benchmark_date_local"],
                "vectors": device_full["vectors"],
                "prediction_matches": device_full["prediction_parity_passed"],
                "anomaly_decision_matches": device_full["anomaly_parity_passed"],
                "maximum_absolute_difference_normalized": device_full[
                    "max_prediction_difference_normalized"
                ],
                "mean_pure_inference_us": device["timing"][
                    "average_inference_us_across_batches"
                ],
                "full_validation_elapsed_us": device_full["validation_elapsed_us"],
                "source": device_path.relative_to(ROOT).as_posix(),
                "proves": [
                    "fixed held-out vectors execute on a physical ESP8266EX",
                    "device decisions reproduce the exported Python decisions",
                    "pure-inference timing for this firmware/compiler/board setup",
                ],
                "does_not_prove": [
                    "live forecasting from an on-device lag buffer",
                    "calibrated voltage, current, power, or energy measurement",
                    "fault-detection performance on physically verified events",
                    "energy per inference",
                ],
            },
        ],
        "cross_layer_checks": {
            "python_vs_device_mae_absolute_difference": abs(
                metrics["mae_normalized"] - device_full["device_mae_normalized"]
            ),
            "python_vs_device_rmse_absolute_difference": abs(
                metrics["rmse_normalized"] - device_full["device_rmse_normalized"]
            ),
            "python_vs_device_confusion_matrix_equal": device_confusion
            == python_confusion,
            "normal_firmware_compiles": builds["normal_build"]["passed"],
            "full_validation_firmware_compiles": builds[
                "full_validation_build"
            ]["passed"],
        },
        "device_record": {
            "sha256": sha256(device_path),
            "schema_version": device["schema_version"],
            "unit_keys_corrected": True,
            "raw_capture_sha256": device["source_capture"]["sha256"],
        },
        "resource_interpretation": {
            "physical_device_validation_build_ram_bytes": device[
                "whole_firmware_resources"
            ]["ram_bytes"],
            "current_recompiled_validation_build_ram_bytes": builds[
                "full_validation_build"
            ]["ram_bytes"],
            "difference_bytes": builds["full_validation_build"]["ram_bytes"]
            - device["whole_firmware_resources"]["ram_bytes"],
            "explanation": (
                "The physical v2 record and the current compile record use the same "
                "benchmark-ready full-validation build."
            ),
        },
        "claim_boundary": (
            "The verified result is numerical portability of a compact model under "
            "held-out-vector replay on ESP8266, not a deployed smart meter."
        ),
    }

    output_path = OUTPUTS / "phase11_hil_evidence_layers.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
