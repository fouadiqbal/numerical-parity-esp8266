#include "tinyml_fixed_model.h"

volatile int64_t resultSink = 0;
float inputFeatures[tinyml_fixed_q15::FEATURE_COUNT] = {
    0.4f, 0.3f, 0.5f, 0.2f, 12.0f, 2.0f, 3.0f, 0.0f};
int16_t quantizedFeatures[tinyml_fixed_q15::FEATURE_COUNT];

void setup() {
  for (size_t index = 0; index < tinyml_fixed_q15::FEATURE_COUNT; ++index) {
    quantizedFeatures[index] =
        tinyml_fixed_q15::quantizeFeature(inputFeatures[index], index);
  }
  resultSink = tinyml_fixed_q15::predictQ30(quantizedFeatures);
}

void loop() {
  yield();
}
