#pragma once
#include <Arduino.h>
#include "risk_classifier.h"

// Gerenciador de alertas local: não transmite dados pela rede.
inline void emitRiskAlert(const char* municipality, const RiskAssessment& assessment) {
  Serial.printf(
    "[ALERTA] municipio=%s | Gold=%s | mockdata=%s | consolidado=%s\n",
    municipality,
    riskLevelName(assessment.regional),
    riskLevelName(assessment.local),
    riskLevelName(assessment.consolidated)
  );
  if (assessment.consolidated == RISK_HIGH) {
    Serial.println("[ALERTA] Nivel alto: redobre a atencao e siga orientacoes da Defesa Civil.");
  } else if (assessment.consolidated == RISK_MEDIUM) {
    Serial.println("[ALERTA] Nivel medio: acompanhe as condicoes locais.");
  } else if (assessment.consolidated == RISK_LOW) {
    Serial.println("[INFO] Nivel baixo no conjunto de dados consultado.");
  } else {
    Serial.println("[AVISO] Nivel regional indisponivel ou nao reconhecido.");
  }
}
