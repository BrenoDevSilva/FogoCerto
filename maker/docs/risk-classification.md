# Classificação e consolidação do risco

## Classificação local mockdata
- ALTO se houver indicação de fumaça, temperatura ≥ 38 °C ou umidade < 25%.
- MÉDIO se temperatura ≥ 32 °C ou umidade < 40%.
- BAIXO nos demais casos.

## Integração com Gold
O nível regional é lido de `nivel_risco` no snapshot. O nível consolidado é a maior severidade entre Gold e mockdata. Não se somam os pontos Gold aos pontos locais, pois isso poderia contar novamente fatores ambientais já considerados no pipeline regional.

Se o nível Gold não for reconhecido, o firmware sinaliza `INDEFINIDO`; a consolidação usa o nível local disponível.

A classificação local serve para demonstração do fluxo e não substitui o cálculo Gold ou alertas oficiais.
