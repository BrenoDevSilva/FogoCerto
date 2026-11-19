#pragma once
#include <Arduino.h>

// Valores demonstrativos para validar o fluxo de classificação local.
struct MockObservation {
  const char* label;
  float temperatureC;
  float humidityPct;
  bool smokeDetected;
};

static const MockObservation MOCK_SCENARIOS[] = {
  {"BAIXO", 27.0f, 58.0f, false},
  {"MEDIO", 32.0f, 38.0f, false},
  {"ALTO", 39.0f, 24.0f, true}
};
static constexpr size_t MOCK_SCENARIO_COUNT =
  sizeof(MOCK_SCENARIOS) / sizeof(MOCK_SCENARIOS[0]);
