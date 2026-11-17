#include <Arduino.h>
#include <string.h>
#include <carrinho-tinyml_inferencing.h>

#include "config.h"
#include "gold_data.h"
#include "gold_snapshot.h"
#include "mock_sensors.h"
#include "ultrasonic_sensor.h"
#include "robot_control.h"
#include "risk_rules.h"
#include "risk_classifier.h"
#include "alert_manager.h"
#include "event_logger.h"

// Buffer e inferência mantidos conforme o firmware original.
static float eiFeatures[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];
static int selectedMunicipality = -1;
static size_t mockScenarioIndex = 0;

static bool runOriginalObstacleClassifier(float* obstacleConfidence) {
  for (size_t ix = 0; ix < EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE; ix++) {
    eiFeatures[ix] = readUltrasonicDistanceCm();
    delay(EI_CLASSIFIER_INTERVAL_MS);
  }

  signal_t signal;
  int error = numpy::signal_from_buffer(
    eiFeatures, EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, &signal
  );
  if (error != 0) {
    Serial.printf("[ERRO] signal_from_buffer: %d\n", error);
    return false;
  }

  ei_impulse_result_t result = {0};
  error = run_classifier(&signal, &result, false);
  if (error != EI_IMPULSE_OK) {
    Serial.printf("[ERRO] run_classifier: %d\n", error);
    return false;
  }

  float probability = 0.0f;
  for (size_t ix = 0; ix < EI_CLASSIFIER_LABEL_COUNT; ix++) {
    if (strcmp(result.classification[ix].label, "OBSTACULO") == 0) {
      probability = result.classification[ix].value;
    }
  }
  *obstacleConfidence = probability;
  return true;
}

static const GoldRiskRecord* getSelectedGoldRecord() {
  if (selectedMunicipality < 0 ||
      static_cast<size_t>(selectedMunicipality) >= GOLD_RECORD_COUNT) {
    return nullptr;
  }
  return &GOLD_RECORDS[selectedMunicipality];
}

static void printMunicipalityList() {
  Serial.println("\n=== MUNICIPIOS NO SNAPSHOT GOLD ===");
  if (GOLD_RECORD_COUNT == 0) {
    Serial.println("Snapshot vazio. Gere gold_snapshot.h usando simulation/export_gold.py.");
    return;
  }
  for (size_t i = 0; i < GOLD_RECORD_COUNT; i++) {
    Serial.printf("%u) %s - %s | data=%s | risco=%s\n",
      static_cast<unsigned>(i + 1),
      GOLD_RECORDS[i].nome,
      GOLD_RECORDS[i].uf,
      GOLD_RECORDS[i].data,
      GOLD_RECORDS[i].nivel_risco
    );
  }
  Serial.printf("Snapshot atualizado em: %s\n", GOLD_SNAPSHOT_GENERATED_AT);
  Serial.println("Digite o numero do municipio. Comandos: m, r, s");
}

static void printRiskSummary() {
  const GoldRiskRecord* gold = getSelectedGoldRecord();
  if (gold == nullptr) {
    Serial.println("[INFO] Primeiro selecione um municipio pelo numero.");
    return;
  }

  const MockObservation& observation = MOCK_SCENARIOS[mockScenarioIndex];
  const RiskAssessment assessment = assessRisk(*gold, observation);

  Serial.printf("\nMunicipio: %s (%s)\n", gold->nome, gold->uf);
  Serial.printf("Data do dado Gold: %s | atualizado_em: %s\n",
                gold->data, gold->atualizado_em);
  Serial.printf("Pontos Gold: %d | focos ontem: %d\n",
                gold->pontos, gold->focos_ontem);
  Serial.printf("Fatores Gold: %s\n", gold->fatores);
  Serial.printf("Mockdata %s: temperatura=%.1f C, umidade=%.1f%%, fumaça=%s\n",
                observation.label, observation.temperatureC,
                observation.humidityPct, observation.smokeDetected ? "SIM" : "NAO");
  emitRiskAlert(gold->nome, assessment);
  Serial.println("Consolidacao: maior severidade entre Gold e mockdata; sem soma de pontos.");
}

static void handleSerialCommands() {
  while (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.equalsIgnoreCase("r")) {
      printMunicipalityList();
    } else if (command.equalsIgnoreCase("m")) {
      mockScenarioIndex = (mockScenarioIndex + 1) % MOCK_SCENARIO_COUNT;
      Serial.printf("[MOCKDATA] Cenário ativo: %s\n",
                    MOCK_SCENARIOS[mockScenarioIndex].label);
      printRiskSummary();
    } else if (command.equalsIgnoreCase("s")) {
      printRiskSummary();
    } else if (command.length() > 0) {
      const int number = command.toInt();
      if (number >= 1 && static_cast<size_t>(number) <= GOLD_RECORD_COUNT) {
        selectedMunicipality = number - 1;
        Serial.printf("[SELECAO] Municipio: %s\n",
                      GOLD_RECORDS[selectedMunicipality].nome);
        logMakerEvent("MUNICIPIO_SELECIONADO", GOLD_RECORDS[selectedMunicipality].nome);
        printRiskSummary();
      } else {
        Serial.println("[INFO] Comando invalido. Use numero, m, r ou s.");
      }
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  setupRobotMotors();
  setupUltrasonicSensor();
  stopRobot();
  delay(300);

  Serial.println("\nFogoCerto Maker iniciado — funcionamento offline.");
  Serial.println("Desvio de obstaculos: classificador Edge Impulse original do CP4.");
  printMunicipalityList();
}

void loop() {
  handleSerialCommands();

  // O risco de incêndio não comanda a navegação. A movimentação depende exclusivamente do classificador de obstáculos original
  float obstacleConfidence = 0.0f;
  if (runOriginalObstacleClassifier(&obstacleConfidence)) {
    if (obstacleConfidence > OBSTACLE_CONFIDENCE_THRESHOLD) {
      Serial.printf("[TINYML] Obstaculo detectado: %.2f. Desviando.\n", obstacleConfidence);
      logMakerEvent("OBSTACULO", "Desvio acionado pelo modelo Edge Impulse");
      stopRobot();
      delay(200);
      turnRobotRight();
    } else {
      Serial.printf("[TINYML] Caminho livre. Confianca OBSTACULO=%.2f\n",
                    obstacleConfidence);
      moveRobotForward(180);
    }
  } else {
    stopRobot();
  }
  delay(50);
}
