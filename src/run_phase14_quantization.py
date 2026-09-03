"""Compare FP32, fused FP32, INT8-style, and Q15/Q30 fixed-point inference."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/source/extracted/smart_meter_data.csv"
MANIFEST = ROOT / "results/tinyml_model_manifest.json"
OUTPUT_JSON = ROOT / "results/phase14_quantization_results.json"
OUTPUT_CSV = ROOT / "results/phase14_quantization_predictions.csv"
HEADER = ROOT / "esp8266/tinyml_fixed_model.h"
FUSED_HEADER = ROOT / "esp8266/tinyml_fused_model.h"
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
FEATURE_MAXIMUM = np.array([1, 1, 1, 1, 23, 6, 12, 1], dtype=np.float64)
Q_BITS = 30
Q_SCALE = 1 << Q_BITS


def prepare() -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(DATASET)
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
    train_end = int(len(frame) * 0.8)
    return frame.iloc[:train_end].copy(), frame.iloc[train_end:].copy()


def fp32_standardized(
    x: np.ndarray,
    intercept: float,
    means: np.ndarray,
    scales: np.ndarray,
    coefficients: np.ndarray,
) -> np.ndarray:
    means32 = means.astype(np.float32)
    scales32 = scales.astype(np.float32)
    coefficients32 = coefficients.astype(np.float32)
    predictions = []
    for row in x.astype(np.float32):
        value = np.float32(intercept)
        for index in range(row.size):
            standardized = np.float32(
                np.float32(row[index] - means32[index]) / scales32[index]
            )
            value = np.float32(
                value + np.float32(standardized * coefficients32[index])
            )
        predictions.append(float(value))
    return np.array(predictions)


def fp32_fused(
    x: np.ndarray, raw_bias: float, raw_weights: np.ndarray
) -> np.ndarray:
    weights32 = raw_weights.astype(np.float32)
    predictions = []
    for row in x.astype(np.float32):
        value = np.float32(raw_bias)
        for index in range(row.size):
            value = np.float32(
                value + np.float32(row[index] * weights32[index])
            )
        predictions.append(float(value))
    return np.array(predictions)


def fixed_point(
    x: np.ndarray,
    actual: np.ndarray,
    raw_bias: float,
    raw_weights: np.ndarray,
    threshold: float,
    input_bits: int,
) -> dict:
    integer_maximum = (1 << (input_bits - 1)) - 1
    quantized_x = np.rint(
        np.clip(x, 0.0, FEATURE_MAXIMUM)
        / FEATURE_MAXIMUM
        * integer_maximum
    ).astype(np.int64)
    multipliers = np.rint(
        raw_weights * FEATURE_MAXIMUM / integer_maximum * Q_SCALE
    ).astype(np.int64)
    bias = int(round(raw_bias * Q_SCALE))
    threshold_q = int(round(threshold * Q_SCALE))
    prediction_q = bias + quantized_x @ multipliers
    prediction = prediction_q.astype(np.float64) / Q_SCALE
    actual_q = np.rint(actual * Q_SCALE).astype(np.int64)
    anomaly = np.abs(actual_q - prediction_q) > threshold_q
    return {
        "input_bits": input_bits,
        "integer_maximum": integer_maximum,
        "quantized_x": quantized_x,
        "multipliers_q30": multipliers,
        "bias_q30": bias,
        "threshold_q30": threshold_q,
        "prediction_q30": prediction_q,
        "prediction": prediction,
        "anomaly": anomaly,
    }


def regression(actual: np.ndarray, prediction: np.ndarray) -> dict:
    error = actual - prediction
    return {
        "mae_normalized": float(np.mean(np.abs(error))),
        "rmse_normalized": float(np.sqrt(np.mean(error**2))),
    }


def classification(labels: np.ndarray, decisions: np.ndarray) -> dict:
    tp = int(np.sum(labels & decisions))
    fp = int(np.sum(~labels & decisions))
    fn = int(np.sum(labels & ~decisions))
    tn = int(np.sum(~labels & ~decisions))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def c_array(values: np.ndarray) -> str:
    return ", ".join(str(int(value)) for value in values)


def c_float_array(values: np.ndarray) -> str:
    formatted = []
    for value in values:
        text = f"{float(value):.9g}"
        if "." not in text and "e" not in text.lower():
            text += ".0"
        formatted.append(text + "f")
    return ", ".join(formatted)


def c_float(value: float) -> str:
    return c_float_array(np.array([value], dtype=np.float64))


def main() -> None:
    _, test = prepare()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    trained = manifest["training_float64"]
    intercept = float(trained["intercept"])
    means = np.array(trained["feature_mean"], dtype=np.float64)
    scales = np.array(trained["feature_scale"], dtype=np.float64)
    coefficients = np.array(trained["coefficients"], dtype=np.float64)
    threshold = float(trained["residual_threshold"])

    x = test[FEATURES].to_numpy(dtype=np.float64)
    actual = test["Electricity_Consumed"].to_numpy(dtype=np.float64)
    labels = (
        test["Anomaly_Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin({"abnormal", "anomaly", "1", "true", "yes"})
        .to_numpy()
    )
    reference = intercept + ((x - means) / scales) @ coefficients
    reference_anomaly = np.abs(actual - reference) > threshold
    raw_weights = coefficients / scales
    raw_bias = intercept - float(np.sum(means * raw_weights))

    current_fp32 = fp32_standardized(x, intercept, means, scales, coefficients)
    fused_fp32 = fp32_fused(x, raw_bias, raw_weights)
    q7 = fixed_point(x, actual, raw_bias, raw_weights, threshold, input_bits=8)
    q15 = fixed_point(x, actual, raw_bias, raw_weights, threshold, input_bits=16)

    methods: dict[str, tuple[np.ndarray, np.ndarray, dict]] = {
        "standardized_fp32": (
            current_fp32,
            np.abs(actual - current_fp32) > np.float32(threshold),
            {
                "core_numeric_state_bytes": 104,
                "source_level_kernel": "8 subtract + 8 divide + 8 multiply + 8 add",
            },
        ),
        "fused_affine_fp32": (
            fused_fp32,
            np.abs(actual - fused_fp32) > np.float32(threshold),
            {
                "core_numeric_state_bytes": 40,
                "source_level_kernel": "8 multiply + 8 add",
            },
        ),
        "fixed_q7_q30": (
            q7["prediction"],
            q7["anomaly"],
            {
                "core_numeric_state_bytes": 40,
                "generic_input_range_metadata_bytes": 32,
                "source_level_kernel": "8 integer multiply + 8 integer add with int64 accumulator",
            },
        ),
        "fixed_q15_q30": (
            q15["prediction"],
            q15["anomaly"],
            {
                "core_numeric_state_bytes": 40,
                "generic_input_range_metadata_bytes": 32,
                "source_level_kernel": "8 integer multiply + 8 integer add with int64 accumulator",
            },
        ),
    }

    method_results = {}
    for name, (prediction, decision, engineering) in methods.items():
        method_results[name] = {
            **regression(actual, prediction),
            "maximum_absolute_deviation_from_float64_reference": float(
                np.max(np.abs(prediction - reference))
            ),
            "mean_absolute_deviation_from_float64_reference": float(
                np.mean(np.abs(prediction - reference))
            ),
            "decision_agreement_with_float64_reference": int(
                np.sum(decision == reference_anomaly)
            ),
            "decision_disagreements_with_float64_reference": int(
                np.sum(decision != reference_anomaly)
            ),
            "classification_against_supplied_labels": classification(labels, decision),
            **engineering,
        }

    result = {
        "phase": 14,
        "target_units": "normalized dataset units; physical kWh not established",
        "test_rows": len(test),
        "reference": {
            **regression(actual, reference),
            "threshold_normalized": threshold,
            "classification_against_supplied_labels": classification(
                labels, reference_anomaly
            ),
        },
        "representations": method_results,
        "fixed_point_design": {
            "equation": "prediction_q30 = bias_q30 + sum(input_q * multiplier_q30)",
            "feature_maximum": FEATURE_MAXIMUM.tolist(),
            "q15_integer_maximum": q15["integer_maximum"],
            "bias_q30": q15["bias_q30"],
            "multipliers_q30": q15["multipliers_q30"].tolist(),
            "threshold_q30": q15["threshold_q30"],
            "accumulator": "signed int64",
            "input_clipping": "[0, per-feature maximum]",
        },
        "selection": {
            "offline_candidate": "fixed_q15_q30",
            "reason": (
                "It removes floating-point divisions and preserves every test decision; "
                "physical latency and firmware-size measurements are required before adoption."
            ),
            "tflite_micro": "not used; unnecessary for a single affine equation",
        },
    }
    OUTPUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    pd.DataFrame(
        {
            "timestamp": test["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S"),
            "actual_normalized": actual,
            "reference_float64": reference,
            "standardized_fp32": current_fp32,
            "fused_affine_fp32": fused_fp32,
            "fixed_q7_q30": q7["prediction"],
            "fixed_q15_q30": q15["prediction"],
            "reference_anomaly": reference_anomaly.astype(int),
            "fixed_q15_anomaly": q15["anomaly"].astype(int),
        }
    ).to_csv(OUTPUT_CSV, index=False)

    anomaly_indices = np.flatnonzero(reference_anomaly)[:4]
    normal_candidates = np.flatnonzero(~reference_anomaly)
    normal_positions = np.linspace(0, len(normal_candidates) - 1, 4, dtype=int)
    vector_indices = np.unique(
        np.concatenate([normal_candidates[normal_positions], anomaly_indices])
    )[:8]
    q_vectors = q15["quantized_x"][vector_indices]
    q_predictions = q15["prediction_q30"][vector_indices]
    q_decisions = q15["anomaly"][vector_indices].astype(np.uint8)

    lines = [
        "#pragma once",
        "",
        "#include <Arduino.h>",
        "",
        "namespace tinyml_fixed_q15 {",
        f"constexpr size_t FEATURE_COUNT = {len(FEATURES)};",
        f"constexpr size_t TEST_VECTOR_COUNT = {len(vector_indices)};",
        f"constexpr int Q_BITS = {Q_BITS};",
        f"constexpr int64_t Q_SCALE = {Q_SCALE}LL;",
        "constexpr int32_t INPUT_MAXIMUM = 32767;",
        f"constexpr int64_t BIAS_Q30 = {q15['bias_q30']}LL;",
        f"constexpr int64_t THRESHOLD_Q30 = {q15['threshold_q30']}LL;",
        "constexpr int32_t MULTIPLIER_Q30[FEATURE_COUNT] = {"
        + c_array(q15["multipliers_q30"])
        + "};",
        "constexpr float FEATURE_MAXIMUM[FEATURE_COUNT] = {"
        + c_float_array(FEATURE_MAXIMUM)
        + "};",
        "constexpr int16_t TEST_FEATURES_Q15[TEST_VECTOR_COUNT][FEATURE_COUNT] = {",
    ]
    for row in q_vectors:
        lines.append("    {" + c_array(row) + "},")
    lines.extend(
        [
            "};",
            "constexpr int64_t TEST_EXPECTED_PREDICTION_Q30[TEST_VECTOR_COUNT] = {"
            + c_array(q_predictions)
            + "};",
            "constexpr uint8_t TEST_EXPECTED_ANOMALY[TEST_VECTOR_COUNT] = {"
            + c_array(q_decisions)
            + "};",
            "",
            "inline int16_t quantizeFeature(float value, size_t index) {",
            "  const float clipped = constrain(value, 0.0f, FEATURE_MAXIMUM[index]);",
            "  return static_cast<int16_t>(lroundf(",
            "      clipped / FEATURE_MAXIMUM[index] * INPUT_MAXIMUM));",
            "}",
            "",
            "inline int64_t predictQ30(const int16_t featuresQ15[FEATURE_COUNT]) {",
            "  int64_t prediction = BIAS_Q30;",
            "  for (size_t index = 0; index < FEATURE_COUNT; ++index) {",
            "    prediction += static_cast<int64_t>(featuresQ15[index]) *",
            "                  MULTIPLIER_Q30[index];",
            "  }",
            "  return prediction;",
            "}",
            "",
            "inline float dequantizePrediction(int64_t predictionQ30) {",
            "  return static_cast<float>(predictionQ30) / static_cast<float>(Q_SCALE);",
            "}",
            "",
            "inline bool isAnomaly(float actualNormalized, int64_t predictionQ30) {",
            "  const int64_t actualQ30 = static_cast<int64_t>(",
            "      llroundf(actualNormalized * static_cast<float>(Q_SCALE)));",
            "  const int64_t difference = actualQ30 >= predictionQ30",
            "      ? actualQ30 - predictionQ30",
            "      : predictionQ30 - actualQ30;",
            "  return difference > THRESHOLD_Q30;",
            "}",
            "}  // namespace tinyml_fixed_q15",
            "",
        ]
    )
    HEADER.write_text("\n".join(lines), encoding="utf-8")

    fused_lines = [
        "#pragma once",
        "",
        "#include <Arduino.h>",
        "",
        "namespace tinyml_fused_fp32 {",
        f"constexpr size_t FEATURE_COUNT = {len(FEATURES)};",
        f"constexpr float BIAS = {c_float(raw_bias)};",
        f"constexpr float RESIDUAL_THRESHOLD_NORMALIZED = {c_float(threshold)};",
        "constexpr float WEIGHTS[FEATURE_COUNT] = {"
        + c_float_array(raw_weights)
        + "};",
        "",
        "inline float predictNormalized(const float features[FEATURE_COUNT]) {",
        "  float prediction = BIAS;",
        "  for (size_t index = 0; index < FEATURE_COUNT; ++index) {",
        "    prediction += features[index] * WEIGHTS[index];",
        "  }",
        "  return prediction;",
        "}",
        "",
        "inline bool isAnomaly(float actualNormalized, float predictedNormalized) {",
        "  return fabsf(actualNormalized - predictedNormalized) >",
        "      RESIDUAL_THRESHOLD_NORMALIZED;",
        "}",
        "}  // namespace tinyml_fused_fp32",
        "",
    ]
    FUSED_HEADER.write_text("\n".join(fused_lines), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
