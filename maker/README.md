# FogoCerto — Maker Lab

Firmware e materiais de demonstração do carrinho CP4 integrados ao projeto FogoCerto.

## Integrantes

| Nome completo | RM |
|---|---|
| Breno Silva | RM99275 |
| Eduardo Araujo | RM99758 |
| Gabriela Trevisan | RM99500 |
| Gustavo Akio | RM550241 |
| Rafael Franck | RM550875 |

## Objetivo
Apresentar o risco municipal calculado pelo pipeline Big Data (Gold), combinar esse nível com cenários locais de `mockdata` e registrar alertas no Monitor Serial. O carrinho mantém a função original de desvio de obstáculos usando o modelo Edge Impulse do CP4.

## Arquitetura adotada
- **Big Data:** exportação da view `workspace.fogocerto.vw_risco_atual` para CSV.
- **Snapshot:** `simulation/export_gold.py` converte o CSV em `firmware/gold_snapshot.h`.
- **Execução offline:** o ESP32 consulta o snapshot gravado na flash; não consulta API, Databricks ou Wi-Fi.
- **Município:** seleção manual pelo Monitor Serial; nenhum município é pré-selecionado.
- **Mockdata:** cenários controlados para demonstração da classificação local.
- **Eventos:** alertas e decisões registrados localmente no Monitor Serial via USB.
- **Navegação:** o desvio de obstáculos continua usando a inferência Edge Impulse do firmware original CP4.

## Estrutura
```text
maker/
├── README.md
├── firmware/
├── simulation/
├── tests/
└── docs/
└── tinyml/
```

## Hardware e pinagem
Hardware original: ESP32 DevKit V1, L298N, dois motores DC, HC-SR04 e alimentação original do carrinho.

| Sinal | GPIO |
|---|---:|
| L298N IN1 | 32 |
| L298N IN2 | 33 |
| L298N IN3 | 25 |
| L298N IN4 | 26 |
| HC-SR04 TRIG | 22 |
| HC-SR04 ECHO | 23 |

## Como preparar
1. Exporte a view `workspace.fogocerto.vw_risco_atual` como CSV.
2. Na raiz `maker/`, execute:
   ```bash
   python simulation/export_gold.py caminho/para/vw_risco_atual.csv
   ```
3. O script atualiza `firmware/gold_snapshot.h`.
4. Disponibilize no ambiente Arduino a biblioteca Edge Impulse original do CP4, incluindo `carrinho-tinyml_inferencing.h` e os arquivos auxiliares gerados pelo Edge Impulse.
5. Abra `firmware/FogoCerto.ino` na Arduino IDE, selecione ESP32 Dev Module e compile.
6. Abra o Monitor Serial em 115200 e selecione o município digitando o número.

## Comandos do Monitor Serial
- Número: seleciona o município correspondente ao snapshot.
- `m`: alterna entre os cenários mockdata baixo, médio e alto.
- `r`: imprime novamente a lista de municípios.
- `s`: imprime o resumo do risco e os fatores.

## Consolidação do risco
O nível consolidado é o maior entre o risco regional Gold e a classificação local de mockdata. Não somamos pontos Gold aos pontos locais, evitando dupla contagem de variáveis ambientais que já participam do cálculo regional.

## Limitações e transparência
- O snapshot é estático: representa os dados disponíveis no momento da exportação, não dados em tempo real.
- O cabeçalho incluído inicialmente é um modelo vazio. É necessário gerar o snapshot com o CSV real antes da demonstração.
- A biblioteca/modelo Edge Impulse original não é redistribuída neste pacote; é uma dependência já pertencente ao projeto CP4 da disciplina de Maker-Lab.
- A compilação final foi validada na Arduino IDE com a biblioteca Edge Impulse disponível e a placa ESP32 selecionada.
- O risco é informativo/preventivo e não é usado como comando de navegação nem como autorização para realizar queimadas.
