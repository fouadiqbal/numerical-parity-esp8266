#include "tinyml_fused_model.h"

volatile float resultSink = 0.0f;
float features[tinyml_fused_fp32::FEATURE_COUNT] = {
    0.4f, 0.3f, 0.5f, 0.2f, 12.0f, 2.0f, 3.0f, 0.0f};

void setup() {
  resultSink = tinyml_fused_fp32::predictNormalized(features);
}

void loop() {
  yield();
}
