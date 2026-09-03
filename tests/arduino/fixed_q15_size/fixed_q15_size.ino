#include "tinyml_fixed_model.h"

volatile int64_t resultSink = 0;
int16_t features[tinyml_fixed_q15::FEATURE_COUNT] = {
    13107, 9830, 16384, 6553, 17095, 10922, 8192, 0};

void setup() {
  resultSink = tinyml_fixed_q15::predictQ30(features);
}

void loop() {
  yield();
}
