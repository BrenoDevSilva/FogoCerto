# Casos de teste dos cenários

| Cenário | Temperatura | Umidade | Indicação de fumaça | Resultado esperado |
|---|---:|---:|---|---|
| BAIXO | 27 °C | 58% | Não | BAIXO |
| MÉDIO | 32 °C | 38% | Não | MÉDIO |
| ALTO | 39 °C | 24% | Sim | ALTO |

## Consolidação
- Gold ALTO + local BAIXO → ALTO.
- Gold MÉDIO + local BAIXO → MÉDIO.
- Gold BAIXO + local ALTO → ALTO.
- Gold desconhecido + local MÉDIO → MÉDIO.

Executar os testes com `python -m unittest discover -s tests -v`.
