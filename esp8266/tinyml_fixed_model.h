#pragma once

#include <Arduino.h>

namespace tinyml_fixed_q15 {
constexpr size_t FEATURE_COUNT = 8;
constexpr size_t TEST_VECTOR_COUNT = 8;
constexpr int Q_BITS = 30;
constexpr int64_t Q_SCALE = 1073741824LL;
constexpr int32_t INPUT_MAXIMUM = 32767;
constexpr int64_t BIAS_Q30 = 435738756LL;
constexpr int64_t THRESHOLD_Q30 = 411271096LL;
constexpr int32_t MULTIPLIER_Q30[FEATURE_COUNT] = {-400, -256, -447, -459, 42, 63, -2346, 158};
constexpr float FEATURE_MAXIMUM[FEATURE_COUNT] = {1.0f, 1.0f, 1.0f, 1.0f, 23.0f, 6.0f, 12.0f, 1.0f};
constexpr int16_t TEST_FEATURES_Q15[TEST_VECTOR_COUNT][FEATURE_COUNT] = {
    {13322, 8831, 11807, 7765, 24219, 0, 8192, 0},
    {14251, 9673, 17155, 9422, 7123, 16384, 8192, 0},
    {15816, 17718, 21569, 13406, 5699, 0, 10922, 0},
    {8468, 20321, 15145, 7152, 19945, 32767, 10922, 32767},
    {12081, 12732, 7612, 13146, 8548, 0, 10922, 0},
    {6944, 3055, 7968, 14913, 22794, 5461, 10922, 0},
    {0, 14905, 8422, 7303, 1425, 16384, 10922, 0},
    {16700, 29288, 19131, 9714, 4274, 32767, 10922, 32767},
};
constexpr int64_t TEST_EXPECTED_PREDICTION_Q30[TEST_VECTOR_COUNT] = {401106122, 397682011, 383698197, 399552982, 392946390, 397450692, 400275395, 390348748};
constexpr uint8_t TEST_EXPECTED_ANOMALY[TEST_VECTOR_COUNT] = {0, 1, 0, 0, 1, 1, 1, 0};

inline int16_t quantizeFeature(float value, size_t index) {
  const float clipped = constrain(value, 0.0f, FEATURE_MAXIMUM[index]);
  return static_cast<int16_t>(lroundf(
      clipped / FEATURE_MAXIMUM[index] * INPUT_MAXIMUM));
}

inline int64_t predictQ30(const int16_t featuresQ15[FEATURE_COUNT]) {
  int64_t prediction = BIAS_Q30;
  for (size_t index = 0; index < FEATURE_COUNT; ++index) {
    prediction += static_cast<int64_t>(featuresQ15[index]) *
                  MULTIPLIER_Q30[index];
  }
  return prediction;
}

inline float dequantizePrediction(int64_t predictionQ30) {
  return static_cast<float>(predictionQ30) / static_cast<float>(Q_SCALE);
}

inline bool isAnomaly(float actualNormalized, int64_t predictionQ30) {
  const int64_t actualQ30 = static_cast<int64_t>(
      llroundf(actualNormalized * static_cast<float>(Q_SCALE)));
  const int64_t difference = actualQ30 >= predictionQ30
      ? actualQ30 - predictionQ30
      : predictionQ30 - actualQ30;
  return difference > THRESHOLD_Q30;
}
}  // namespace tinyml_fixed_q15
