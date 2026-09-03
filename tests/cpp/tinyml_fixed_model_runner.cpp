#include <iomanip>
#include <iostream>

#include "tinyml_fixed_model.h"

int main() {
  float features[tinyml_fixed_q15::FEATURE_COUNT];
  int16_t quantized[tinyml_fixed_q15::FEATURE_COUNT];
  float actualNormalized = 0.0f;
  while (true) {
    for (size_t index = 0; index < tinyml_fixed_q15::FEATURE_COUNT; ++index) {
      if (!(std::cin >> features[index])) {
        return 0;
      }
      quantized[index] = tinyml_fixed_q15::quantizeFeature(features[index], index);
    }
    if (!(std::cin >> actualNormalized)) {
      return 2;
    }
    const int64_t predictionQ30 = tinyml_fixed_q15::predictQ30(quantized);
    const float prediction =
        tinyml_fixed_q15::dequantizePrediction(predictionQ30);
    const bool anomaly =
        tinyml_fixed_q15::isAnomaly(actualNormalized, predictionQ30);
    std::cout << std::setprecision(10) << prediction << ' '
              << static_cast<int>(anomaly) << ' ' << predictionQ30 << '\n';
  }
}
