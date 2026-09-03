#include "tinyml_model.h"

volatile float resultSink = 0.0f;
float features[tinyml_model::FEATURE_COUNT] = {
    0.4f, 0.3f, 0.5f, 0.2f, 12.0f, 2.0f, 3.0f, 0.0f};

void setup() {
  resultSink = tinyml_model::predictNormalized(features);
}

void loop() {
  yield();
}
