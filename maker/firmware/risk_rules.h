#pragma once
#include "mock_sensors.h"

enum RiskLevel : uint8_t {
  RISK_LOW = 0,
  RISK_MEDIUM = 1,
  RISK_HIGH = 2,
  RISK_UNKNOWN = 255
};

// Regras demonstrativas locais aplicadas aos dados mockdata.
inline RiskLevel classifyLocalMockdata(const MockObservation& observation) {
  if (observation.smokeDetected ||
      observation.temperatureC >= 38.0f ||
      observation.humidityPct < 25.0f) {
    return RISK_HIGH;
  }
  if (observation.temperatureC >= 32.0f ||
      observation.humidityPct < 40.0f) {
    return RISK_MEDIUM;
  }
  return RISK_LOW;
}

inline RiskLevel riskLevelFromGold(const char* level) {
  if (level == nullptr) return RISK_UNKNOWN;
  if (strcmp(level, "ALTO") == 0 || strcmp(level, "alto") == 0) return RISK_HIGH;
  if (strcmp(level, "MEDIO") == 0 || strcmp(level, "MÉDIO") == 0 ||
      strcmp(level, "medio") == 0 || strcmp(level, "médio") == 0) return RISK_MEDIUM;
  if (strcmp(level, "BAIXO") == 0 || strcmp(level, "baixo") == 0) return RISK_LOW;
  return RISK_UNKNOWN;
}

inline RiskLevel maximumRiskLevel(RiskLevel a, RiskLevel b) {
  if (a == RISK_UNKNOWN) return b;
  if (b == RISK_UNKNOWN) return a;
  return (a > b) ? a : b;
}

inline const char* riskLevelName(RiskLevel level) {
  switch (level) {
    case RISK_LOW: return "BAIXO";
    case RISK_MEDIUM: return "MEDIO";
    case RISK_HIGH: return "ALTO";
    default: return "INDEFINIDO";
  }
}
