# Arquitetura

1. O pipeline Big Data calcula os indicadores municipais e disponibiliza a view Gold `workspace.fogocerto.vw_risco_atual`.
2. A view é exportada para CSV antes da demonstração.
3. `simulation/export_gold.py` transforma o CSV em `firmware/gold_snapshot.h`.
4. O ESP32 lê o snapshot gravado na memória flash e funciona offline.
5. O operador seleciona o município no Monitor Serial.
6. A classificação local usa cenários mockdata e pode manter ou elevar a severidade Gold.
7. Eventos são impressos no Monitor Serial via USB.
8. A navegação do carrinho continua baseada no classificador de obstáculos Edge Impulse do CP4.

O nível de risco de incêndio não controla a movimentação do robô.
