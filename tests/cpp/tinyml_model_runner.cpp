#include <iomanip>
#include <iostream>

#include "tinyml_model.h"

int main() {
  float features[tinyml_model::FEATURE_COUNT];
  float actualNormalized = 0.0f;
  while (true) {
    for (size_t index = 0; index < tinyml_model::FEATURE_COUNT; ++index) {
      if (!(std::cin >> features[index])) {
        return 0;
      }
    }
    if (!(std::cin >> actualNormalized)) {
      return 2;
    }
    const float prediction = tinyml_model::predictNormalized(features);
    const bool anomaly = tinyml_model::isAnomaly(actualNormalized, prediction);
    std::cout << std::setprecision(10) << prediction << ' '
              << static_cast<int>(anomaly) << '\n';
  }
}
