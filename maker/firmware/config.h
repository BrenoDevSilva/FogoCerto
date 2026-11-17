#pragma once
#include <Arduino.h>

// Pinagem original do projeto de checkpoint. Não alterar.
static constexpr uint8_t IN1 = 32;
static constexpr uint8_t IN2 = 33;
static constexpr uint8_t IN3 = 25;
static constexpr uint8_t IN4 = 26;
static constexpr uint8_t TRIG_PIN = 22;
static constexpr uint8_t ECHO_PIN = 23;

static constexpr uint32_t SERIAL_BAUD = 115200;
static constexpr float OBSTACLE_CONFIDENCE_THRESHOLD = 0.70f;
