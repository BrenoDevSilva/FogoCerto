# Check Point 02 - TinyML Aplicado ao Carrinho-Robô

Este diretório contém os arquivos, datasets, documentação e artefatos de Machine Learning embarcado (TinyML) desenvolvidos para os checkpoints e Global Solution da disciplina Project-based Maker Lab.

---

## 1. Dataset e Coleta de Dados

* **Sensor Utilizado:** Sensor Ultrassônico HC-SR04 (Pinos: TRIG -> GPIO 5, ECHO -> GPIO 18).
* **Dados Coletados:** Leitura de distância em centímetros tratada via Média Móvel de 5 amostras e normalizada no intervalo $[0, 1]$.
* **Classes Definidas:**
  1. `LIVRE`: Distância $> 25\text{ cm}$. O carrinho prossegue na velocidade máxima nominal.
  2. `OBSTACULO_PROXIMO`: Distância entre $10\text{ cm}$ e $25\text{ cm}$. O carrinho reduz a velocidade para $50\%$.
  3. `COLISAO_IMINENTE`: Distância $< 10\text{ cm}$. Parada de emergência imediata e manobra de recuo.
* **Quantidade de Amostras:** 300 amostras exportadas e organizadas no arquivo `dataset/dataset_tinyml.csv`.

---

## 2. Pipeline no Edge Impulse

1. **Data Acquisition:** Importação do dataset via CSV com divisão automática de **80% para Treinamento** e **20% para Teste**.
2. **Impulse Design:**
   * **Processing Block:** *Raw Data* (entrada de 1 feature normalizada).
   * **Learning Block:** *Classification* (Rede Neural / Keras).
3. **Parâmetros de Treinamento:**
   * Épocas: `20`
   * Taxa de Aprendizado (Learning Rate): `0.005`
   * Arquitetura: Camada densa de entrada, camada oculta (8 neurônios) e camada de saída Softmax para 3 classes.
4. **Métricas do Modelo:**
   * Acurácia em Teste: ~96.5%
   * Loss: 0.12
5. **Deployment:** Modelo quantizado em `int8` exportado como biblioteca C++ para Arduino / ESP32.

---

## 3. Evidências do Processo (Edge Impulse)

As capturas de tela do pipeline de treinamento e teste estão salvas na pasta `tinyml/edge_impulse/`:

* `01_data_acquisition.png` — Visualização da distribuição dos dados coletados.
* `02_impulse_design.png` — Bloco de processamento e aprendizado.
* `03_feature_generation.png` — Mapeamento das *features* das 3 classes.
* `04_training_results.png` — Matriz de confusão e acurácia do modelo.
* `05_model_testing.png` — Resultado das validações com o conjunto de testes.

---

## 4. Integração Hardware + TinyML

A biblioteca gerada foi embarcada no ESP32 (`tinyml/lib/carrinho_tinyml_inferencing`). O código principal localizado em `src/codigo.ino` lê continuamente o sensor ultrassônico, executa a função `run_classifier()` do Edge Impulse e aciona a ponte H L298N dinamicamente conforme a classe predita.