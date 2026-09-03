"""Train and export a compact forecasting/anomaly model for ESP8266.

The model is a standardized linear regressor using the same eight lag/calendar
features as the research notebook. Anomalies are forecast residuals above the
99th percentile of a chronological calibration segment.
"""

from __future__ import annotations

import json
import hashlib
import platform
from pathlib import Path

import numpy as np
import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPOSITORY_ROOT / "data/source/extracted/smart_meter_data.csv"
MODEL_HEADER_PATH = (
    REPOSITORY_ROOT
    / "esp8266/tinyml_model.h"
)
VALIDATION_HEADER_PATH = (
    REPOSITORY_ROOT
    / "esp8266/tinyml_validation_data.h"
)
METRICS_PATH = REPOSITORY_ROOT / "results/tinyml_edge_metrics_v2.json"
MODEL_MANIFEST_PATH = REPOSITORY_ROOT / "results/tinyml_model_manifest.json"
TEST_PREDICTIONS_PATH = (
    REPOSITORY_ROOT / "results/tinyml_edge_test_predictions_v2.csv"
)

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


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = actual - predicted
    return {
        "mae_normalized": float(np.mean(np.abs(error))),
        "rmse_normalized": float(np.sqrt(np.mean(error**2))),
    }


def classification_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | int]:
    actual = actual.astype(bool)
    predicted = predicted.astype(bool)
    tp = int(np.sum(actual & predicted))
    fp = int(np.sum(~actual & predicted))
    fn = int(np.sum(actual & ~predicted))
    tn = int(np.sum(~actual & ~predicted))
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


def c_float(value: float) -> str:
    text = f"{value:.9g}"
    if "." not in text and "e" not in text.lower():
        text += ".0"
    return text + "f"


def c_array(values: np.ndarray) -> str:
    return ", ".join(c_float(float(value)) for value in values)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    frame = pd.read_csv(DATASET_PATH)
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="raise")
    frame = frame.sort_values("Timestamp").reset_index(drop=True)

    energy = "Electricity_Consumed"
    frame["lag_1"] = frame[energy].shift(1)
    frame["lag_2"] = frame[energy].shift(2)
    frame["lag_48"] = frame[energy].shift(48)
    frame["lag_336"] = frame[energy].shift(336)
    frame["hour"] = frame["Timestamp"].dt.hour
    frame["day_of_week"] = frame["Timestamp"].dt.dayofweek
    frame["month"] = frame["Timestamp"].dt.month
    frame["is_weekend"] = (frame["day_of_week"] >= 5).astype(int)
    frame = frame.dropna(subset=FEATURES).reset_index(drop=True)

    train_end = int(len(frame) * 0.8)
    train = frame.iloc[:train_end].copy()
    test = frame.iloc[train_end:].copy()
    fit_end = int(len(train) * 0.8)
    fit = train.iloc[:fit_end].copy()
    calibration = train.iloc[fit_end:].copy()

    x_fit = fit[FEATURES].to_numpy(dtype=np.float64)
    y_fit = fit[energy].to_numpy(dtype=np.float64)
    feature_mean = x_fit.mean(axis=0)
    feature_scale = x_fit.std(axis=0)
    feature_scale[feature_scale == 0] = 1.0
    x_fit_scaled = (x_fit - feature_mean) / feature_scale
    design = np.column_stack([np.ones(len(x_fit_scaled)), x_fit_scaled])
    parameters, *_ = np.linalg.lstsq(design, y_fit, rcond=None)
    intercept = float(parameters[0])
    coefficients = parameters[1:]

    def predict(partition: pd.DataFrame) -> np.ndarray:
        values = partition[FEATURES].to_numpy(dtype=np.float64)
        return intercept + ((values - feature_mean) / feature_scale) @ coefficients

    calibration_prediction = predict(calibration)
    calibration_error = np.abs(
        calibration[energy].to_numpy(dtype=np.float64) - calibration_prediction
    )
    anomaly_threshold = float(np.quantile(calibration_error, 0.99))

    test_prediction = predict(test)
    test_actual = test[energy].to_numpy(dtype=np.float64)
    test_residual = np.abs(test_actual - test_prediction)
    predicted_anomaly = test_residual > anomaly_threshold
    true_anomaly = (
        test["Anomaly_Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin({"abnormal", "anomaly", "1", "true", "yes"})
        .to_numpy()
    )

    metrics = {
        "schema_version": 2,
        "model": "standardized_linear_regression_residual_detector",
        "target_units": "normalized dataset units; physical kWh not established",
        "feature_names": FEATURES,
        "dataset_rows_raw": 5000,
        "dataset_rows_after_lags": int(len(frame)),
        "fit_rows": int(len(fit)),
        "calibration_rows": int(len(calibration)),
        "test_rows": int(len(test)),
        "residual_threshold_normalized": anomaly_threshold,
        **regression_metrics(test_actual, test_prediction),
        "classification": classification_metrics(true_anomaly, predicted_anomaly),
    }

    # Prefer a mix of normal and detected-anomaly vectors for firmware validation.
    anomaly_indices = np.flatnonzero(predicted_anomaly)[:4]
    normal_candidates = np.flatnonzero(~predicted_anomaly)
    normal_positions = np.linspace(0, len(normal_candidates) - 1, 4, dtype=int)
    normal_indices = normal_candidates[normal_positions]
    vector_indices = np.unique(np.concatenate([normal_indices, anomaly_indices]))[:8]
    vector_features = test.iloc[vector_indices][FEATURES].to_numpy(dtype=np.float64)
    vector_actual = test_actual[vector_indices]
    vector_prediction = test_prediction[vector_indices]
    vector_anomaly = predicted_anomaly[vector_indices].astype(int)

    header_lines = [
        "#pragma once",
        "",
        "#include <Arduino.h>",
        "",
        "namespace tinyml_model {",
        f"constexpr size_t FEATURE_COUNT = {len(FEATURES)};",
        f"constexpr size_t TEST_VECTOR_COUNT = {len(vector_indices)};",
        'constexpr const char* TARGET_UNITS = "normalized_dataset_units";',
        f"constexpr float INTERCEPT = {c_float(intercept)};",
        f"constexpr float RESIDUAL_THRESHOLD_NORMALIZED = {c_float(anomaly_threshold)};",
        f"constexpr float FEATURE_MEAN[FEATURE_COUNT] = {{{c_array(feature_mean)}}};",
        f"constexpr float FEATURE_SCALE[FEATURE_COUNT] = {{{c_array(feature_scale)}}};",
        f"constexpr float COEFFICIENTS[FEATURE_COUNT] = {{{c_array(coefficients)}}};",
        "constexpr const char* FEATURE_NAMES[FEATURE_COUNT] = {",
        "    " + ", ".join(f'\"{name}\"' for name in FEATURES),
        "};",
        "constexpr float TEST_FEATURES[TEST_VECTOR_COUNT][FEATURE_COUNT] = {",
    ]
    for row in vector_features:
        header_lines.append(f"    {{{c_array(row)}}},")
    header_lines.extend(
        [
            "};",
            f"constexpr float TEST_ACTUAL_NORMALIZED[TEST_VECTOR_COUNT] = {{{c_array(vector_actual)}}};",
            f"constexpr float TEST_EXPECTED_PREDICTION_NORMALIZED[TEST_VECTOR_COUNT] = {{{c_array(vector_prediction)}}};",
            "constexpr uint8_t TEST_EXPECTED_ANOMALY[TEST_VECTOR_COUNT] = {"
            + ", ".join(str(int(value)) for value in vector_anomaly)
            + "};",
            "",
            "inline float predictNormalized(const float features[FEATURE_COUNT]) {",
            "  float prediction = INTERCEPT;",
            "  for (size_t index = 0; index < FEATURE_COUNT; ++index) {",
            "    const float standardized =",
            "        (features[index] - FEATURE_MEAN[index]) / FEATURE_SCALE[index];",
            "    prediction += standardized * COEFFICIENTS[index];",
            "  }",
            "  return prediction;",
            "}",
            "",
            "inline bool isAnomaly(float actualNormalized, float predictedNormalized) {",
            "  return fabsf(actualNormalized - predictedNormalized) > RESIDUAL_THRESHOLD_NORMALIZED;",
            "}",
            "}  // namespace tinyml_model",
            "",
        ]
    )

    MODEL_HEADER_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_HEADER_PATH.write_text("\n".join(header_lines), encoding="utf-8")

    full_test_features = test[FEATURES].to_numpy(dtype=np.float64)
    validation_lines = [
        "#pragma once",
        "",
        "#include <Arduino.h>",
        "#include <pgmspace.h>",
        "",
        '#include "tinyml_model.h"',
        "",
        "namespace tinyml_validation {",
        f"constexpr size_t VECTOR_COUNT = {len(test)};",
        "const float FEATURES[VECTOR_COUNT][tinyml_model::FEATURE_COUNT] PROGMEM = {",
    ]
    for row in full_test_features:
        validation_lines.append(f"    {{{c_array(row)}}},")
    validation_lines.extend(
        [
            "};",
            "const float ACTUAL_NORMALIZED[VECTOR_COUNT] PROGMEM = {",
            "    " + c_array(test_actual),
            "};",
            "const float EXPECTED_PREDICTION_NORMALIZED[VECTOR_COUNT] PROGMEM = {",
            "    " + c_array(test_prediction),
            "};",
            "const uint8_t EXPECTED_ANOMALY[VECTOR_COUNT] PROGMEM = {",
            "    " + ", ".join(str(int(value)) for value in predicted_anomaly),
            "};",
            "const uint8_t TRUE_ANOMALY[VECTOR_COUNT] PROGMEM = {",
            "    " + ", ".join(str(int(value)) for value in true_anomaly),
            "};",
            "",
            "inline void loadFeatures(size_t vectorIndex, float destination[tinyml_model::FEATURE_COUNT]) {",
            "  for (size_t featureIndex = 0;",
            "       featureIndex < tinyml_model::FEATURE_COUNT;",
            "       ++featureIndex) {",
            "    destination[featureIndex] =",
            "        pgm_read_float(&FEATURES[vectorIndex][featureIndex]);",
            "  }",
            "}",
            "",
            "inline float actualNormalized(size_t vectorIndex) {",
            "  return pgm_read_float(&ACTUAL_NORMALIZED[vectorIndex]);",
            "}",
            "",
            "inline float expectedPredictionNormalized(size_t vectorIndex) {",
            "  return pgm_read_float(&EXPECTED_PREDICTION_NORMALIZED[vectorIndex]);",
            "}",
            "",
            "inline bool expectedAnomaly(size_t vectorIndex) {",
            "  return pgm_read_byte(&EXPECTED_ANOMALY[vectorIndex]) != 0;",
            "}",
            "",
            "inline bool trueAnomaly(size_t vectorIndex) {",
            "  return pgm_read_byte(&TRUE_ANOMALY[vectorIndex]) != 0;",
            "}",
            "}  // namespace tinyml_validation",
            "",
        ]
    )
    VALIDATION_HEADER_PATH.write_text(
        "\n".join(validation_lines), encoding="utf-8"
    )
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    serialized = {
        "intercept": float(np.float32(intercept)),
        "feature_mean": feature_mean.astype(np.float32).astype(float).tolist(),
        "feature_scale": feature_scale.astype(np.float32).astype(float).tolist(),
        "coefficients": coefficients.astype(np.float32).astype(float).tolist(),
        "residual_threshold": float(np.float32(anomaly_threshold)),
    }
    fingerprint_payload = json.dumps(
        {
            "features": FEATURES,
            "target_units": "normalized_dataset_units",
            "serialized_float32": serialized,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    manifest = {
        "schema_version": 1,
        "model_name": "compact_standardized_linear_forecaster",
        "model_fingerprint_sha256": hashlib.sha256(fingerprint_payload).hexdigest().upper(),
        "dataset": {
            "source": "https://www.kaggle.com/datasets/ziya07/smart-meter-electricity-consumption-dataset",
            "csv_sha256": sha256(DATASET_PATH),
            "raw_rows": 5000,
            "rows_after_lags": int(len(frame)),
        },
        "target": energy,
        "target_units": "normalized dataset units; physical kWh not established",
        "features_in_order": FEATURES,
        "split": {
            "fit_rows": int(len(fit)),
            "calibration_rows": int(len(calibration)),
            "test_rows": int(len(test)),
            "fit_start": fit["Timestamp"].min().isoformat(),
            "fit_end": fit["Timestamp"].max().isoformat(),
            "calibration_start": calibration["Timestamp"].min().isoformat(),
            "calibration_end": calibration["Timestamp"].max().isoformat(),
            "test_start": test["Timestamp"].min().isoformat(),
            "test_end": test["Timestamp"].max().isoformat(),
        },
        "training_float64": {
            "intercept": intercept,
            "feature_mean": feature_mean.tolist(),
            "feature_scale": feature_scale.tolist(),
            "coefficients": coefficients.tolist(),
            "residual_threshold": anomaly_threshold,
        },
        "serialized_cpp_float32": serialized,
        "inference_formula": "intercept + sum(((x[i] - mean[i]) / scale[i]) * coefficient[i])",
        "threshold_formula": "abs(actual_normalized - predicted_normalized) > residual_threshold_normalized",
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    MODEL_MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    prediction_frame = pd.DataFrame(
        {
            "timestamp": test["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S"),
            "actual_normalized": test_actual,
            "predicted_normalized": test_prediction,
            "absolute_residual_normalized": test_residual,
            "predicted_anomaly": predicted_anomaly.astype(int),
            "true_anomaly": true_anomaly.astype(int),
        }
    )
    prediction_frame.to_csv(TEST_PREDICTIONS_PATH, index=False)
    print(json.dumps(metrics, indent=2))
    print(f"Model header: {MODEL_HEADER_PATH}")
    print(f"Validation header: {VALIDATION_HEADER_PATH}")
    print(f"Metrics: {METRICS_PATH}")
    print(f"Model manifest: {MODEL_MANIFEST_PATH}")
    print(f"Test predictions: {TEST_PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
