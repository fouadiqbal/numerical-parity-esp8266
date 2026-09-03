#pragma once

#include <Arduino.h>

namespace tinyml_fused_fp32 {
constexpr size_t FEATURE_COUNT = 8;
constexpr float BIAS = 0.40581334f;
constexpr float RESIDUAL_THRESHOLD_NORMALIZED = 0.383026056f;
constexpr float WEIGHTS[FEATURE_COUNT] = {-0.0122173465f, -0.00781282981f, -0.0136342566f, -0.0139993205f, 5.56560252e-05f, 0.000322773626f, -0.00596685345f, 0.00480869049f};

inline float predictNormalized(const float features[FEATURE_COUNT]) {
  float prediction = BIAS;
  for (size_t index = 0; index < FEATURE_COUNT; ++index) {
    prediction += features[index] * WEIGHTS[index];
  }
  return prediction;
}

inline bool isAnomaly(float actualNormalized, float predictedNormalized) {
  return fabsf(actualNormalized - predictedNormalized) >
      RESIDUAL_THRESHOLD_NORMALIZED;
}
}  // namespace tinyml_fused_fp32
