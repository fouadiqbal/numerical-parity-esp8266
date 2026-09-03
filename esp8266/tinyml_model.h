#pragma once

#include <Arduino.h>

namespace tinyml_model {
constexpr size_t FEATURE_COUNT = 8;
constexpr size_t TEST_VECTOR_COUNT = 8;
constexpr const char* TARGET_UNITS = "normalized_dataset_units";
constexpr float INTERCEPT = 0.380095252f;
constexpr float RESIDUAL_THRESHOLD_NORMALIZED = 0.383026056f;
constexpr float FEATURE_MEAN[FEATURE_COUNT] = {0.379957456f, 0.379949261f, 0.380292087f, 0.381041259f, 11.4731903f, 2.95978552f, 1.7613941f, 0.27613941f};
constexpr float FEATURE_SCALE[FEATURE_COUNT] = {0.163851466f, 0.163842973f, 0.163104952f, 0.162708527f, 6.93245503f, 1.98276541f, 0.690347224f, 0.447086609f};
constexpr float COEFFICIENTS[FEATURE_COUNT] = {-0.00200183014f, -0.00128007726f, -0.00222381477f, -0.00227780882f, 0.000385832892f, 0.00063998438f, -0.00411920071f, 0.00214990113f};
constexpr const char* FEATURE_NAMES[FEATURE_COUNT] = {
    "lag_1", "lag_2", "lag_48", "lag_336", "hour", "day_of_week", "month", "is_weekend"
};
constexpr float TEST_FEATURES[TEST_VECTOR_COUNT][FEATURE_COUNT] = {
    {0.406554718f, 0.269519954f, 0.360318126f, 0.236967288f, 17.0f, 0.0f, 3.0f, 0.0f},
    {0.434912633f, 0.295206905f, 0.523550614f, 0.287556265f, 5.0f, 3.0f, 3.0f, 0.0f},
    {0.482667698f, 0.540741229f, 0.658239331f, 0.40912648f, 4.0f, 0.0f, 4.0f, 0.0f},
    {0.258417463f, 0.620172448f, 0.462203864f, 0.218266847f, 14.0f, 6.0f, 4.0f, 1.0f},
    {0.368684486f, 0.388546404f, 0.232305027f, 0.401187986f, 6.0f, 0.0f, 4.0f, 0.0f},
    {0.211916742f, 0.0932213954f, 0.243186368f, 0.455124097f, 16.0f, 1.0f, 4.0f, 0.0f},
    {0.0f, 0.454893492f, 0.257014843f, 0.222864847f, 1.0f, 3.0f, 4.0f, 0.0f},
    {0.509672698f, 0.893818367f, 0.583855471f, 0.29644738f, 3.0f, 6.0f, 4.0f, 1.0f},
};
constexpr float TEST_ACTUAL_NORMALIZED[TEST_VECTOR_COUNT] = {0.424540712f, 0.766512631f, 0.0f, 0.202155654f, 0.773061999f, 0.834202957f, 0.799834951f, 0.233655734f};
constexpr float TEST_EXPECTED_PREDICTION_NORMALIZED[TEST_VECTOR_COUNT] = {0.373556148f, 0.370375686f, 0.357344816f, 0.372110572f, 0.365956204f, 0.37015472f, 0.372791735f, 0.363537631f};
constexpr uint8_t TEST_EXPECTED_ANOMALY[TEST_VECTOR_COUNT] = {0, 1, 0, 0, 1, 1, 1, 0};

inline float predictNormalized(const float features[FEATURE_COUNT]) {
  float prediction = INTERCEPT;
  for (size_t index = 0; index < FEATURE_COUNT; ++index) {
    const float standardized =
        (features[index] - FEATURE_MEAN[index]) / FEATURE_SCALE[index];
    prediction += standardized * COEFFICIENTS[index];
  }
  return prediction;
}

inline bool isAnomaly(float actualNormalized, float predictedNormalized) {
  return fabsf(actualNormalized - predictedNormalized) > RESIDUAL_THRESHOLD_NORMALIZED;
}
}  // namespace tinyml_model
