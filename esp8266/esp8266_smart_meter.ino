#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>

#include "secrets.h"
#include "tinyml_fixed_model.h"
#include "tinyml_fused_model.h"
#include "tinyml_model.h"

#ifndef SMART_METER_ENABLE_FULL_VALIDATION
#define SMART_METER_ENABLE_FULL_VALIDATION 0
#endif

#if SMART_METER_ENABLE_FULL_VALIDATION
#include "tinyml_validation_data.h"
#endif

namespace {

constexpr unsigned long SERIAL_BAUD = 115200;
constexpr unsigned long SEND_INTERVAL_MS = 20000;
constexpr unsigned long WIFI_RETRY_INTERVAL_MS = 10000;
constexpr unsigned long DELAYED_TINYML_REPORT_MS = 30000;

constexpr int ADC_MAX_COUNTS = 1023;
constexpr float PROTOTYPE_MAX_LOAD_KW = 2.0f;
constexpr float ANOMALY_THRESHOLD_KW = 1.8f;

// The local workflow may temporarily change this in its private build copy.
constexpr bool TEST_MODE = false;
constexpr int TEST_RAW_ADC_VALUES[] = {100, 500, 900, 1000};
constexpr size_t TEST_RAW_ADC_COUNT =
    sizeof(TEST_RAW_ADC_VALUES) / sizeof(TEST_RAW_ADC_VALUES[0]);

WiFiClient networkClient;
unsigned long lastSendMs = 0;
unsigned long lastWifiAttemptMs = 0;
bool delayedTinyMlReportDone = false;

void runTinyMlSelfTest() {
  // Retain per-batch timings so a future hardware capture can report a
  // distribution instead of only one aggregate value.
  constexpr size_t BENCHMARK_BATCH_COUNT = 30;
  constexpr uint32_t BENCHMARK_REPETITIONS_PER_BATCH = 250;
  size_t parityPassCount = 0;

  Serial.println("TINYML_SELF_TEST_BEGIN");
  for (size_t vectorIndex = 0;
       vectorIndex < tinyml_model::TEST_VECTOR_COUNT;
       ++vectorIndex) {
    const float prediction = tinyml_model::predictNormalized(
        tinyml_model::TEST_FEATURES[vectorIndex]);
    const float actual = tinyml_model::TEST_ACTUAL_NORMALIZED[vectorIndex];
    const float residual = fabsf(actual - prediction);
    const bool anomaly = tinyml_model::isAnomaly(actual, prediction);
    const bool predictionMatches =
        fabsf(prediction -
              tinyml_model::TEST_EXPECTED_PREDICTION_NORMALIZED[vectorIndex]) < 0.0001f;
    const bool anomalyMatches =
        anomaly == static_cast<bool>(
            tinyml_model::TEST_EXPECTED_ANOMALY[vectorIndex]);
    const bool parityOk = predictionMatches && anomalyMatches;
    parityPassCount += parityOk ? 1 : 0;

    Serial.print("{\"tinyml_vector\":");
    Serial.print(vectorIndex);
    Serial.print(",\"actual_normalized\":");
    Serial.print(actual, 6);
    Serial.print(",\"predicted_normalized\":");
    Serial.print(prediction, 6);
    Serial.print(",\"residual_normalized\":");
    Serial.print(residual, 6);
    Serial.print(",\"anomaly\":");
    Serial.print(anomaly ? 1 : 0);
    Serial.print(",\"parity_ok\":");
    Serial.print(parityOk ? 1 : 0);
    Serial.println("}");
  }

  volatile float benchmarkSink = 0.0f;
  float benchmarkMeanSumUs = 0.0f;
  float benchmarkMinimumUs = 1.0e9f;
  float benchmarkMaximumUs = 0.0f;
  const uint32_t inferenceCountPerBatch =
      BENCHMARK_REPETITIONS_PER_BATCH * tinyml_model::TEST_VECTOR_COUNT;

  for (size_t batchIndex = 0;
       batchIndex < BENCHMARK_BATCH_COUNT;
       ++batchIndex) {
    const uint32_t benchmarkStartUs = micros();
    for (uint32_t repetition = 0;
         repetition < BENCHMARK_REPETITIONS_PER_BATCH;
         ++repetition) {
      for (size_t vectorIndex = 0;
           vectorIndex < tinyml_model::TEST_VECTOR_COUNT;
           ++vectorIndex) {
        benchmarkSink += tinyml_model::predictNormalized(
            tinyml_model::TEST_FEATURES[vectorIndex]);
      }
      if ((repetition % 100) == 0) {
        yield();
      }
    }
    const uint32_t benchmarkElapsedUs = micros() - benchmarkStartUs;
    const float averageInferenceUs =
        static_cast<float>(benchmarkElapsedUs) / inferenceCountPerBatch;
    benchmarkMeanSumUs += averageInferenceUs;
    if (averageInferenceUs < benchmarkMinimumUs) {
      benchmarkMinimumUs = averageInferenceUs;
    }
    if (averageInferenceUs > benchmarkMaximumUs) {
      benchmarkMaximumUs = averageInferenceUs;
    }

    Serial.print("{\"tinyml_benchmark_batch\":");
    Serial.print(batchIndex);
    Serial.print(",\"inferences\":");
    Serial.print(inferenceCountPerBatch);
    Serial.print(",\"elapsed_us\":");
    Serial.print(benchmarkElapsedUs);
    Serial.print(",\"average_inference_us\":");
    Serial.print(averageInferenceUs, 6);
    Serial.println("}");
  }

  const float averageInferenceUs =
      benchmarkMeanSumUs / BENCHMARK_BATCH_COUNT;

  Serial.print("{\"tinyml_summary\":1,\"parity_passed\":");
  Serial.print(parityPassCount);
  Serial.print(",\"parity_total\":");
  Serial.print(tinyml_model::TEST_VECTOR_COUNT);
  Serial.print(",\"residual_threshold_normalized\":");
  Serial.print(tinyml_model::RESIDUAL_THRESHOLD_NORMALIZED, 6);
  Serial.print(",\"benchmark_batches\":");
  Serial.print(BENCHMARK_BATCH_COUNT);
  Serial.print(",\"inferences_per_batch\":");
  Serial.print(inferenceCountPerBatch);
  Serial.print(",\"average_inference_us_across_batches\":");
  Serial.print(averageInferenceUs, 3);
  Serial.print(",\"minimum_batch_average_us\":");
  Serial.print(benchmarkMinimumUs, 3);
  Serial.print(",\"maximum_batch_average_us\":");
  Serial.print(benchmarkMaximumUs, 3);
  Serial.print(",\"benchmark_guard\":");
  Serial.print(benchmarkSink, 3);
  Serial.println("}");
  Serial.println("TINYML_SELF_TEST_END");
}

void runFixedPointBenchmark() {
  constexpr size_t BENCHMARK_BATCH_COUNT = 30;
  constexpr uint32_t BENCHMARK_REPETITIONS_PER_BATCH = 250;
  size_t predictionParityPassed = 0;
  size_t anomalyParityPassed = 0;

  Serial.println("TINYML_FIXED_Q15_TEST_BEGIN");
  for (size_t vectorIndex = 0;
       vectorIndex < tinyml_fixed_q15::TEST_VECTOR_COUNT;
       ++vectorIndex) {
    const int64_t predictionQ30 = tinyml_fixed_q15::predictQ30(
        tinyml_fixed_q15::TEST_FEATURES_Q15[vectorIndex]);
    const bool anomaly = tinyml_fixed_q15::isAnomaly(
        tinyml_model::TEST_ACTUAL_NORMALIZED[vectorIndex], predictionQ30);
    const bool predictionMatches =
        predictionQ30 ==
        tinyml_fixed_q15::TEST_EXPECTED_PREDICTION_Q30[vectorIndex];
    const bool anomalyMatches =
        anomaly == static_cast<bool>(
            tinyml_fixed_q15::TEST_EXPECTED_ANOMALY[vectorIndex]);
    predictionParityPassed += predictionMatches ? 1 : 0;
    anomalyParityPassed += anomalyMatches ? 1 : 0;
  }

  volatile int64_t benchmarkSink = 0;
  float benchmarkMeanSumUs = 0.0f;
  float benchmarkMinimumUs = 1.0e9f;
  float benchmarkMaximumUs = 0.0f;
  const uint32_t inferenceCountPerBatch =
      BENCHMARK_REPETITIONS_PER_BATCH *
      tinyml_fixed_q15::TEST_VECTOR_COUNT;

  for (size_t batchIndex = 0;
       batchIndex < BENCHMARK_BATCH_COUNT;
       ++batchIndex) {
    const uint32_t benchmarkStartUs = micros();
    for (uint32_t repetition = 0;
         repetition < BENCHMARK_REPETITIONS_PER_BATCH;
         ++repetition) {
      for (size_t vectorIndex = 0;
           vectorIndex < tinyml_fixed_q15::TEST_VECTOR_COUNT;
           ++vectorIndex) {
        benchmarkSink += tinyml_fixed_q15::predictQ30(
            tinyml_fixed_q15::TEST_FEATURES_Q15[vectorIndex]);
      }
      if ((repetition % 100) == 0) {
        yield();
      }
    }
    const uint32_t benchmarkElapsedUs = micros() - benchmarkStartUs;
    const float averageInferenceUs =
        static_cast<float>(benchmarkElapsedUs) / inferenceCountPerBatch;
    benchmarkMeanSumUs += averageInferenceUs;
    if (averageInferenceUs < benchmarkMinimumUs) {
      benchmarkMinimumUs = averageInferenceUs;
    }
    if (averageInferenceUs > benchmarkMaximumUs) {
      benchmarkMaximumUs = averageInferenceUs;
    }

    Serial.print("{\"fixed_q15_benchmark_batch\":");
    Serial.print(batchIndex);
    Serial.print(",\"inferences\":");
    Serial.print(inferenceCountPerBatch);
    Serial.print(",\"elapsed_us\":");
    Serial.print(benchmarkElapsedUs);
    Serial.print(",\"average_inference_us\":");
    Serial.print(averageInferenceUs, 6);
    Serial.println("}");
  }

  Serial.print("{\"fixed_q15_summary\":1,\"prediction_parity_passed\":");
  Serial.print(predictionParityPassed);
  Serial.print(",\"anomaly_parity_passed\":");
  Serial.print(anomalyParityPassed);
  Serial.print(",\"parity_total\":");
  Serial.print(tinyml_fixed_q15::TEST_VECTOR_COUNT);
  Serial.print(",\"benchmark_batches\":");
  Serial.print(BENCHMARK_BATCH_COUNT);
  Serial.print(",\"inferences_per_batch\":");
  Serial.print(inferenceCountPerBatch);
  Serial.print(",\"average_inference_us_across_batches\":");
  Serial.print(benchmarkMeanSumUs / BENCHMARK_BATCH_COUNT, 6);
  Serial.print(",\"minimum_batch_average_us\":");
  Serial.print(benchmarkMinimumUs, 6);
  Serial.print(",\"maximum_batch_average_us\":");
  Serial.print(benchmarkMaximumUs, 6);
  Serial.print(",\"benchmark_guard\":");
  Serial.print(static_cast<long>(benchmarkSink & 0x7fffffff));
  Serial.println("}");
  Serial.println("TINYML_FIXED_Q15_TEST_END");
}

void runFusedFp32Benchmark() {
  constexpr size_t BENCHMARK_BATCH_COUNT = 30;
  constexpr uint32_t BENCHMARK_REPETITIONS_PER_BATCH = 250;
  size_t predictionParityPassed = 0;
  size_t anomalyParityPassed = 0;

  for (size_t vectorIndex = 0;
       vectorIndex < tinyml_model::TEST_VECTOR_COUNT;
       ++vectorIndex) {
    const float prediction = tinyml_fused_fp32::predictNormalized(
        tinyml_model::TEST_FEATURES[vectorIndex]);
    const bool anomaly = tinyml_fused_fp32::isAnomaly(
        tinyml_model::TEST_ACTUAL_NORMALIZED[vectorIndex], prediction);
    predictionParityPassed +=
        fabsf(prediction -
              tinyml_model::TEST_EXPECTED_PREDICTION_NORMALIZED[vectorIndex]) <
                0.0001f
            ? 1
            : 0;
    anomalyParityPassed +=
        anomaly == static_cast<bool>(
            tinyml_model::TEST_EXPECTED_ANOMALY[vectorIndex])
            ? 1
            : 0;
  }

  volatile float benchmarkSink = 0.0f;
  float benchmarkMeanSumUs = 0.0f;
  float benchmarkMinimumUs = 1.0e9f;
  float benchmarkMaximumUs = 0.0f;
  const uint32_t inferenceCountPerBatch =
      BENCHMARK_REPETITIONS_PER_BATCH * tinyml_model::TEST_VECTOR_COUNT;

  for (size_t batchIndex = 0;
       batchIndex < BENCHMARK_BATCH_COUNT;
       ++batchIndex) {
    const uint32_t benchmarkStartUs = micros();
    for (uint32_t repetition = 0;
         repetition < BENCHMARK_REPETITIONS_PER_BATCH;
         ++repetition) {
      for (size_t vectorIndex = 0;
           vectorIndex < tinyml_model::TEST_VECTOR_COUNT;
           ++vectorIndex) {
        benchmarkSink += tinyml_fused_fp32::predictNormalized(
            tinyml_model::TEST_FEATURES[vectorIndex]);
      }
      if ((repetition % 100) == 0) {
        yield();
      }
    }
    const uint32_t elapsedUs = micros() - benchmarkStartUs;
    const float averageUs =
        static_cast<float>(elapsedUs) / inferenceCountPerBatch;
    benchmarkMeanSumUs += averageUs;
    if (averageUs < benchmarkMinimumUs) {
      benchmarkMinimumUs = averageUs;
    }
    if (averageUs > benchmarkMaximumUs) {
      benchmarkMaximumUs = averageUs;
    }
    Serial.print("{\"fused_fp32_benchmark_batch\":");
    Serial.print(batchIndex);
    Serial.print(",\"inferences\":");
    Serial.print(inferenceCountPerBatch);
    Serial.print(",\"elapsed_us\":");
    Serial.print(elapsedUs);
    Serial.print(",\"average_inference_us\":");
    Serial.print(averageUs, 6);
    Serial.println("}");
  }

  Serial.print("{\"fused_fp32_summary\":1,\"prediction_parity_passed\":");
  Serial.print(predictionParityPassed);
  Serial.print(",\"anomaly_parity_passed\":");
  Serial.print(anomalyParityPassed);
  Serial.print(",\"parity_total\":");
  Serial.print(tinyml_model::TEST_VECTOR_COUNT);
  Serial.print(",\"average_inference_us_across_batches\":");
  Serial.print(benchmarkMeanSumUs / BENCHMARK_BATCH_COUNT, 6);
  Serial.print(",\"minimum_batch_average_us\":");
  Serial.print(benchmarkMinimumUs, 6);
  Serial.print(",\"maximum_batch_average_us\":");
  Serial.print(benchmarkMaximumUs, 6);
  Serial.print(",\"benchmark_guard\":");
  Serial.print(benchmarkSink, 3);
  Serial.println("}");
}

void runFixedPointWithQuantizationBenchmark() {
  constexpr size_t BENCHMARK_BATCH_COUNT = 30;
  constexpr uint32_t BENCHMARK_REPETITIONS_PER_BATCH = 250;
  const uint32_t inferenceCountPerBatch =
      BENCHMARK_REPETITIONS_PER_BATCH * tinyml_model::TEST_VECTOR_COUNT;
  volatile int64_t benchmarkSink = 0;
  float benchmarkMeanSumUs = 0.0f;
  float benchmarkMinimumUs = 1.0e9f;
  float benchmarkMaximumUs = 0.0f;
  int16_t quantized[tinyml_fixed_q15::FEATURE_COUNT];

  for (size_t batchIndex = 0;
       batchIndex < BENCHMARK_BATCH_COUNT;
       ++batchIndex) {
    const uint32_t benchmarkStartUs = micros();
    for (uint32_t repetition = 0;
         repetition < BENCHMARK_REPETITIONS_PER_BATCH;
         ++repetition) {
      for (size_t vectorIndex = 0;
           vectorIndex < tinyml_model::TEST_VECTOR_COUNT;
           ++vectorIndex) {
        for (size_t featureIndex = 0;
             featureIndex < tinyml_fixed_q15::FEATURE_COUNT;
             ++featureIndex) {
          quantized[featureIndex] = tinyml_fixed_q15::quantizeFeature(
              tinyml_model::TEST_FEATURES[vectorIndex][featureIndex],
              featureIndex);
        }
        benchmarkSink += tinyml_fixed_q15::predictQ30(quantized);
      }
      if ((repetition % 100) == 0) {
        yield();
      }
    }
    const uint32_t elapsedUs = micros() - benchmarkStartUs;
    const float averageUs =
        static_cast<float>(elapsedUs) / inferenceCountPerBatch;
    benchmarkMeanSumUs += averageUs;
    if (averageUs < benchmarkMinimumUs) {
      benchmarkMinimumUs = averageUs;
    }
    if (averageUs > benchmarkMaximumUs) {
      benchmarkMaximumUs = averageUs;
    }
    Serial.print("{\"fixed_q15_with_quantization_batch\":");
    Serial.print(batchIndex);
    Serial.print(",\"inferences\":");
    Serial.print(inferenceCountPerBatch);
    Serial.print(",\"elapsed_us\":");
    Serial.print(elapsedUs);
    Serial.print(",\"average_inference_us\":");
    Serial.print(averageUs, 6);
    Serial.println("}");
  }

  Serial.print("{\"fixed_q15_with_quantization_summary\":1,");
  Serial.print("\"average_inference_us_across_batches\":");
  Serial.print(benchmarkMeanSumUs / BENCHMARK_BATCH_COUNT, 6);
  Serial.print(",\"minimum_batch_average_us\":");
  Serial.print(benchmarkMinimumUs, 6);
  Serial.print(",\"maximum_batch_average_us\":");
  Serial.print(benchmarkMaximumUs, 6);
  Serial.print(",\"benchmark_guard\":");
  Serial.print(static_cast<long>(benchmarkSink & 0x7fffffff));
  Serial.println("}");
}

#if SMART_METER_ENABLE_FULL_VALIDATION
void runFullTinyMlValidation() {
  constexpr float PREDICTION_TOLERANCE_NORMALIZED = 0.0001f;
  size_t predictionParityPassed = 0;
  size_t anomalyParityPassed = 0;
  size_t truePositive = 0;
  size_t falsePositive = 0;
  size_t falseNegative = 0;
  size_t trueNegative = 0;
  float maxPredictionDifferenceNormalized = 0.0f;
  float absoluteErrorSumNormalized = 0.0f;
  float squaredErrorSumNormalized = 0.0f;
  size_t fixedDecisionAgreement = 0;
  float fixedMaxDifferenceNormalized = 0.0f;
  float fixedAbsoluteErrorSumNormalized = 0.0f;
  float fixedSquaredErrorSumNormalized = 0.0f;
  size_t fusedDecisionAgreement = 0;
  float fusedMaxDifferenceNormalized = 0.0f;
  float fusedAbsoluteErrorSumNormalized = 0.0f;
  float fusedSquaredErrorSumNormalized = 0.0f;
  float features[tinyml_model::FEATURE_COUNT];
  int16_t fixedFeatures[tinyml_fixed_q15::FEATURE_COUNT];

  Serial.println("TINYML_FULL_VALIDATION_BEGIN");
  const uint32_t validationStartUs = micros();
  for (size_t vectorIndex = 0;
       vectorIndex < tinyml_validation::VECTOR_COUNT;
       ++vectorIndex) {
    tinyml_validation::loadFeatures(vectorIndex, features);
    const float actual = tinyml_validation::actualNormalized(vectorIndex);
    const float expectedPrediction =
        tinyml_validation::expectedPredictionNormalized(vectorIndex);
    const bool expectedAnomaly =
        tinyml_validation::expectedAnomaly(vectorIndex);
    const bool trueAnomaly = tinyml_validation::trueAnomaly(vectorIndex);
    const float prediction = tinyml_model::predictNormalized(features);
    const bool predictedAnomaly =
        tinyml_model::isAnomaly(actual, prediction);

    for (size_t featureIndex = 0;
         featureIndex < tinyml_fixed_q15::FEATURE_COUNT;
         ++featureIndex) {
      fixedFeatures[featureIndex] =
          tinyml_fixed_q15::quantizeFeature(features[featureIndex], featureIndex);
    }
    const int64_t fixedPredictionQ30 =
        tinyml_fixed_q15::predictQ30(fixedFeatures);
    const float fixedPrediction =
        tinyml_fixed_q15::dequantizePrediction(fixedPredictionQ30);
    const bool fixedAnomaly =
        tinyml_fixed_q15::isAnomaly(actual, fixedPredictionQ30);
    fixedDecisionAgreement += fixedAnomaly == expectedAnomaly ? 1 : 0;
    const float fixedDifference = fabsf(fixedPrediction - expectedPrediction);
    if (fixedDifference > fixedMaxDifferenceNormalized) {
      fixedMaxDifferenceNormalized = fixedDifference;
    }
    const float fixedError = actual - fixedPrediction;
    fixedAbsoluteErrorSumNormalized += fabsf(fixedError);
    fixedSquaredErrorSumNormalized += fixedError * fixedError;

    const float fusedPrediction =
        tinyml_fused_fp32::predictNormalized(features);
    const bool fusedAnomaly =
        tinyml_fused_fp32::isAnomaly(actual, fusedPrediction);
    fusedDecisionAgreement += fusedAnomaly == expectedAnomaly ? 1 : 0;
    const float fusedDifference = fabsf(fusedPrediction - expectedPrediction);
    if (fusedDifference > fusedMaxDifferenceNormalized) {
      fusedMaxDifferenceNormalized = fusedDifference;
    }
    const float fusedError = actual - fusedPrediction;
    fusedAbsoluteErrorSumNormalized += fabsf(fusedError);
    fusedSquaredErrorSumNormalized += fusedError * fusedError;

    const float predictionDifference =
        fabsf(prediction - expectedPrediction);
    if (predictionDifference <= PREDICTION_TOLERANCE_NORMALIZED) {
      ++predictionParityPassed;
    }
    if (predictedAnomaly == expectedAnomaly) {
      ++anomalyParityPassed;
    }
    if (predictionDifference > maxPredictionDifferenceNormalized) {
      maxPredictionDifferenceNormalized = predictionDifference;
    }

    const float error = actual - prediction;
    absoluteErrorSumNormalized += fabsf(error);
    squaredErrorSumNormalized += error * error;

    if (trueAnomaly && predictedAnomaly) {
      ++truePositive;
    } else if (!trueAnomaly && predictedAnomaly) {
      ++falsePositive;
    } else if (trueAnomaly && !predictedAnomaly) {
      ++falseNegative;
    } else {
      ++trueNegative;
    }
  }
  const uint32_t validationElapsedUs = micros() - validationStartUs;
  const float deviceMaeNormalized =
      absoluteErrorSumNormalized / tinyml_validation::VECTOR_COUNT;
  const float deviceRmseNormalized = sqrtf(
      squaredErrorSumNormalized / tinyml_validation::VECTOR_COUNT);
  const float fixedDeviceMaeNormalized =
      fixedAbsoluteErrorSumNormalized / tinyml_validation::VECTOR_COUNT;
  const float fixedDeviceRmseNormalized = sqrtf(
      fixedSquaredErrorSumNormalized / tinyml_validation::VECTOR_COUNT);
  const float fusedDeviceMaeNormalized =
      fusedAbsoluteErrorSumNormalized / tinyml_validation::VECTOR_COUNT;
  const float fusedDeviceRmseNormalized = sqrtf(
      fusedSquaredErrorSumNormalized / tinyml_validation::VECTOR_COUNT);

  Serial.print("{\"tinyml_full_validation\":1,\"vectors\":");
  Serial.print(tinyml_validation::VECTOR_COUNT);
  Serial.print(",\"prediction_parity_passed\":");
  Serial.print(predictionParityPassed);
  Serial.print(",\"anomaly_parity_passed\":");
  Serial.print(anomalyParityPassed);
  Serial.print(",\"max_prediction_difference_normalized\":");
  Serial.print(maxPredictionDifferenceNormalized, 9);
  Serial.print(",\"device_mae_normalized\":");
  Serial.print(deviceMaeNormalized, 9);
  Serial.print(",\"device_rmse_normalized\":");
  Serial.print(deviceRmseNormalized, 9);
  Serial.print(",\"true_positive\":");
  Serial.print(truePositive);
  Serial.print(",\"false_positive\":");
  Serial.print(falsePositive);
  Serial.print(",\"false_negative\":");
  Serial.print(falseNegative);
  Serial.print(",\"true_negative\":");
  Serial.print(trueNegative);
  Serial.print(",\"validation_elapsed_us\":");
  Serial.print(validationElapsedUs);
  Serial.print(",\"fixed_q15_decision_agreement\":");
  Serial.print(fixedDecisionAgreement);
  Serial.print(",\"fixed_q15_max_difference_normalized\":");
  Serial.print(fixedMaxDifferenceNormalized, 9);
  Serial.print(",\"fixed_q15_device_mae_normalized\":");
  Serial.print(fixedDeviceMaeNormalized, 9);
  Serial.print(",\"fixed_q15_device_rmse_normalized\":");
  Serial.print(fixedDeviceRmseNormalized, 9);
  Serial.print(",\"fused_fp32_decision_agreement\":");
  Serial.print(fusedDecisionAgreement);
  Serial.print(",\"fused_fp32_max_difference_normalized\":");
  Serial.print(fusedMaxDifferenceNormalized, 9);
  Serial.print(",\"fused_fp32_device_mae_normalized\":");
  Serial.print(fusedDeviceMaeNormalized, 9);
  Serial.print(",\"fused_fp32_device_rmse_normalized\":");
  Serial.print(fusedDeviceRmseNormalized, 9);
  Serial.println("}");
  Serial.println("TINYML_FULL_VALIDATION_END");
}
#endif

void setAlertLed(bool anomaly) {
  // The NodeMCU onboard LED is active-low.
  digitalWrite(LED_BUILTIN, anomaly ? LOW : HIGH);
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  const unsigned long now = millis();
  if (lastWifiAttemptMs != 0 && now - lastWifiAttemptMs < WIFI_RETRY_INTERVAL_MS) {
    return;
  }

  lastWifiAttemptMs = now;
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  WiFi.begin(SMART_METER_WIFI_SSID, SMART_METER_WIFI_PASSWORD);
  Serial.println("Wi-Fi connection attempt started");
}

int readRawAdc() {
  if (!TEST_MODE) {
    return analogRead(A0);
  }

  const size_t sequenceIndex =
      ((millis() / SEND_INTERVAL_MS) - 1) % TEST_RAW_ADC_COUNT;
  return TEST_RAW_ADC_VALUES[sequenceIndex];
}

float estimatePrototypeLoadKw(int rawAdc) {
  return static_cast<float>(rawAdc) / ADC_MAX_COUNTS * PROTOTYPE_MAX_LOAD_KW;
}

long sendToThingSpeak(int rawAdc, float loadKw, bool anomaly, int& httpCode) {
  HTTPClient http;

  String url = "http://api.thingspeak.com/update?api_key=";
  url += SMART_METER_THINGSPEAK_WRITE_KEY;
  url += "&field1=" + String(rawAdc);
  url += "&field2=" + String(loadKw, 3);
  url += "&field3=" + String(anomaly ? 1 : 0);

  if (!http.begin(networkClient, url)) {
    httpCode = -1;
    return 0;
  }

  httpCode = http.GET();
  const String responseBody = httpCode > 0 ? http.getString() : "0";
  http.end();
  return responseBody.toInt();
}

void printStructuredLog(
    int rawAdc,
    float loadKw,
    bool anomaly,
    int httpCode,
    long entryId) {
  Serial.print("{\"uptime_ms\":");
  Serial.print(millis());
  Serial.print(",\"raw_adc\":");
  Serial.print(rawAdc);
  Serial.print(",\"load_kw\":");
  Serial.print(loadKw, 3);
  Serial.print(",\"anomaly\":");
  Serial.print(anomaly ? 1 : 0);
  Serial.print(",\"wifi_rssi_dbm\":");
  Serial.print(WiFi.status() == WL_CONNECTED ? WiFi.RSSI() : 0);
  Serial.print(",\"http_code\":");
  Serial.print(httpCode);
  Serial.print(",\"thingspeak_entry_id\":");
  Serial.print(entryId);
  Serial.println("}");
}

}  // namespace

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  setAlertLed(false);

  Serial.begin(SERIAL_BAUD);
  delay(1000);
  Serial.println();
  Serial.println("ESP8266 smart-meter prototype starting");

  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  connectWifi();
}

void loop() {
  connectWifi();

  const unsigned long now = millis();
  if (!delayedTinyMlReportDone && now >= DELAYED_TINYML_REPORT_MS) {
    runTinyMlSelfTest();
    runFusedFp32Benchmark();
    runFixedPointBenchmark();
    runFixedPointWithQuantizationBenchmark();
#if SMART_METER_ENABLE_FULL_VALIDATION
    runFullTinyMlValidation();
#endif
    delayedTinyMlReportDone = true;
  }

  if (now - lastSendMs < SEND_INTERVAL_MS) {
    delay(10);
    return;
  }
  lastSendMs = now;

  const int rawAdc = readRawAdc();
  const float loadKw = estimatePrototypeLoadKw(rawAdc);
  const bool anomaly = loadKw > ANOMALY_THRESHOLD_KW;
  setAlertLed(anomaly);

  int httpCode = 0;
  long entryId = 0;
  if (WiFi.status() == WL_CONNECTED) {
    entryId = sendToThingSpeak(rawAdc, loadKw, anomaly, httpCode);
  }

  printStructuredLog(rawAdc, loadKw, anomaly, httpCode, entryId);
}
