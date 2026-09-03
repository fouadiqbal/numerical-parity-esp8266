"""Quantify compact-model state, operations, firmware resources, and headroom."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "results" / "tinyml_model_manifest.json"
BUILDS_PATH = ROOT / "results" / "phase12_benchmark_ready_builds.json"
OUTPUT_PATH = ROOT / "results" / "phase13_resource_analysis.json"


def resource_summary(build: dict) -> dict:
    fields = {
        "ram": (build["ram_bytes"], build["ram_available_bytes"]),
        "iram": (build["iram_bytes"], build["iram_available_bytes"]),
        "flash_code": (
            build["flash_code_bytes"],
            build["flash_code_available_bytes"],
        ),
    }
    return {
        name: {
            "used_bytes": used,
            "available_bytes": available,
            "headroom_bytes": available - used,
            "used_percent_exact": used / available * 100,
            "headroom_percent_exact": (available - used) / available * 100,
        }
        for name, (used, available) in fields.items()
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    builds = json.loads(BUILDS_PATH.read_text(encoding="utf-8"))
    feature_count = len(manifest["features_in_order"])

    trainable_parameters = feature_count + 1  # coefficients and intercept
    preprocessing_values = feature_count * 2  # means and scales
    decision_values = 1  # threshold
    deployed_float_values = (
        trainable_parameters + preprocessing_values + decision_values
    )
    deployed_numeric_bytes = deployed_float_values * 4

    spot_check_numeric_bytes = (
        8 * feature_count * 4  # features
        + 8 * 4  # actuals
        + 8 * 4  # expected predictions
        + 8  # expected decisions as uint8
    )
    full_validation_payload_bytes = 933 * (
        feature_count * 4 + 4 + 4 + 1 + 1
    )

    result = {
        "phase": 13,
        "model": manifest["model_name"],
        "feature_count": feature_count,
        "parameter_accounting": {
            "trainable_parameters": trainable_parameters,
            "preprocessing_float_values": preprocessing_values,
            "decision_threshold_float_values": decision_values,
            "total_deployed_float_values": deployed_float_values,
            "core_numeric_state_bytes_float32": deployed_numeric_bytes,
            "definition": (
                "Core numeric state includes 8 coefficients, one intercept, "
                "8 means, 8 scales, and one residual threshold."
            ),
        },
        "operation_accounting_per_prediction": {
            "subtractions": feature_count,
            "divisions": feature_count,
            "multiplications": feature_count,
            "accumulation_additions": feature_count,
            "core_scalar_arithmetic_operations": feature_count * 4,
            "residual_decision_additional_operations": {
                "subtraction": 1,
                "absolute_value": 1,
                "comparison": 1,
            },
            "convention": (
                "Counts source-level scalar operations. It does not claim CPU cycles, "
                "instructions, or fused-operation behavior."
            ),
        },
        "validation_payload_estimates": {
            "public_eight_vector_spot_check_numeric_bytes": spot_check_numeric_bytes,
            "private_933_vector_payload_numeric_bytes": full_validation_payload_bytes,
            "full_build_flash_code_increase_bytes": (
                builds["full_validation_build"]["flash_code_bytes"]
                - builds["normal_build"]["flash_code_bytes"]
            ),
            "warning": (
                "Validation vectors are experimental test payload, not model parameters."
            ),
        },
        "whole_firmware": {
            "normal": resource_summary(builds["normal_build"]),
            "full_validation": resource_summary(builds["full_validation_build"]),
            "warning": (
                "Whole-firmware values include ESP8266 core, Wi-Fi, HTTP, serial logging, "
                "self-test code, and application state; they are not the model footprint."
            ),
        },
        "engineering_risk": {
            "primary_constraint": "instruction RAM",
            "reason": (
                "Both builds use 60,343 of 65,536 IRAM bytes, leaving only 5,193 bytes."
            ),
            "recommended_actions": [
                "recompile after every networking, TLS, DSP, or library addition",
                "remove validation vectors and self-test reporting from production builds",
                "generate a linker map before claiming isolated code-size cost",
                "avoid equating available flash with available IRAM",
            ],
        },
    }

    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
