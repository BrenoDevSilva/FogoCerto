#pragma once
#include <Arduino.h>

// Eventos são registrados no Monitor Serial/USB.
inline void logMakerEvent(const char* eventType, const char* description) {
  Serial.printf("[EVENTO] tipo=%s | detalhe=%s\n", eventType, description);
}
