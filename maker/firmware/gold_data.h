#pragma once
#include <Arduino.h>

// Estrutura correspondente aos campos exportados da view Gold.
struct GoldRiskRecord {
  const char* id_ibge;
  const char* nome;
  const char* uf;
  const char* data;
  const char* nivel_risco;
  int pontos;
  int focos_ontem;
  float umidade_min;
  float vento_max;
  float temp_max;
  float chuva_3d;
  const char* fatores;
  const char* atualizado_em;
};
