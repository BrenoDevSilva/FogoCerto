#pragma once
#include "gold_data.h"
#include "risk_rules.h"

struct RiskAssessment {
  RiskLevel regional;
  RiskLevel local;
  RiskLevel consolidated;
};

inline RiskAssessment assessRisk(const GoldRiskRecord& gold,
                                 const MockObservation& localObservation) {
  RiskAssessment result;
  result.regional = riskLevelFromGold(gold.nivel_risco);
  result.local = classifyLocalMockdata(localObservation);
  result.consolidated = maximumRiskLevel(result.regional, result.local);
  return result;
}
