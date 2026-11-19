# FogoCerto · Applied Computer Vision

**Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software 4º ano**

| Nome completo | RM |
|---|---|
| Breno Silva | RM99275 |
| Eduardo Araujo | RM99758 |
| Gabriela Trevisan | RM99500 |
| Gustavo Akio | RM550241 |
| Rafael Franck | RM550875 |

Detecção de **fumaça** e **fogo** em imagens com um **YOLO11** treinado sob medida. No FogoCerto, a visão é a **confirmação em campo**: o satélite só vê o foco quando passa e o fogo pequeno escapa, então o produtor envia uma foto e o modelo diz se vê fumaça ou fogo, com a confiança. A foto é cruzada com o risco do município: fumaça confirmada em município de risco alto sobe na fila de atenção. O modelo **ajuda a triar**, não substitui o olhar humano nem a Defesa Civil.

Próximo passo (não construído): a mesma entrada "uma imagem" serve para quadros de **câmeras fixas** em fazendas e torres.

- Vídeo de demonstração: <https://youtu.be/IZauw6l9Onw>
- Relatório técnico (PDF): [`docs/relatorio_visao.pdf`](docs/relatorio_visao.pdf)
- Peso treinado: [`modelos/best.pt`](modelos/best.pt) (YOLO11n treinado no D-Fire, 5,5 MB). Já vem no repositório, então a API e o vídeo rodam sem treinar de novo.

## Como funciona

```
foto (celular) ─┐                         ┌─> classe: fogo | fumaca | nada
quadro de vídeo ┴─> YOLO11n (best.pt) ─> regra de decisão (limiar) ─┤   confiança, dúvida, mensagem
                                                                     └─> + risco do município (risco_atual.json) -> prioridade
```

| Arquivo | O que faz |
|---|---|
| [`notebooks/treino_avaliacao_yolo.ipynb`](notebooks/treino_avaliacao_yolo.ipynb) | Treino no Colab (GPU T4), avaliação por caixa e por imagem, escolha do limiar, erros reais, imagens próprias e velocidade |
| [`src/decisao.py`](src/decisao.py) | Regra única que transforma as caixas na resposta do produto (a mesma usada na avaliação) |
| [`src/modelo.py`](src/modelo.py) | Carrega o `best.pt` e converte a saída do Ultralytics |
| [`src/api.py`](src/api.py) | API `POST /visao/classificar` (FastAPI) e página de demonstração em `/` |
| [`src/detectar_video.py`](src/detectar_video.py) | Detecção em **tempo real** em webcam ou vídeo |
| [`tests/`](tests/) | Testes da regra e da API (sem precisar do modelo) |
| [`resultados/`](resultados/) | Métricas, matrizes de confusão, curvas e erros gerados pelo notebook |
| [`amostras/`](amostras/) | 3 imagens leves do D-Fire (CC0) para testar a API |

## Dataset

**D-Fire** (Venâncio, Lisboa e Barbosa, UFMG), licença **CC0 1.0**, versão do Kaggle `sayedgamal99/smoke-fire-detection-yolo` já dividida em treino (14.122), validação (3.099) e teste (4.306). Mais de 21 mil imagens, 9.838 delas **sem** fogo nem fumaça, o que permite medir o falso alarme. Classes: `0 = fumaca`, `1 = fogo`.

> Venâncio, P. V. A. B.; Lisboa, A. C.; Barbosa, A. V. *An automatic fire detection system based on deep convolutional neural networks for low-power, resource-constrained devices.* Neural Computing and Applications, 2022.

Além do D-Fire, o grupo testa **imagens próprias** (seção 8 do notebook), incluindo casos difíceis: nuvem, neblina, pôr do sol e poeira. Elas não vão para o GitHub (LGPD); só a tabela de resultados.

## Reproduzir

### 1. Treinar (Google Colab)

1. Abra o notebook no Colab: `Arquivo > Fazer upload de notebook` com o `.ipynb`, ou, depois que estiver na `main`, [este link](https://colab.research.google.com/github/BrenoDevSilva/FogoCerto/blob/main/visao/notebooks/treino_avaliacao_yolo.ipynb).
2. `Ambiente de execução > Alterar o tipo > GPU T4`.
3. `Executar tudo`. Tudo é salvo em `MyDrive/FogoCerto_visao/`. Se a sessão cair, rode tudo de novo: o treino continua do último checkpoint.
4. No fim, o Colab baixa `resultados_visao.zip` e `best.pt`. Descompacte os resultados em `visao/resultados/` e coloque o peso em `visao/modelos/best.pt`.

### 2. Rodar a API e a demonstração (Windows, Linux ou Mac, sem GPU)

```bash
cd visao
pip install -r requirements.txt
uvicorn api:app --app-dir src --port 8001
```

Abra <http://localhost:8001> para a página de demonstração ou <http://localhost:8001/docs> para a documentação da API.
A API lê o limiar de `resultados/limiar_recomendado.json` (gerado no notebook). As variáveis `MODELO_PATH`, `LIMIAR_CONFIANCA`, `LIMIAR_DUVIDA`, `RISCO_FONTE` e `CORS_ORIGENS` mudam o padrão.

```bash
curl -F "imagem=@amostras/fogo_dfire_AoF07937.jpg;type=image/jpeg" -F municipio_id=1500503 \
     http://localhost:8001/visao/classificar
```

```json
{
  "classe": "fogo",
  "confianca": 0.777,
  "duvida": false,
  "mensagem": "Possível fogo detectado. Afaste-se e ligue para os Bombeiros (193) ou a Defesa Civil (199).",
  "aviso": "O FogoCerto ajuda a triar. A confirmação é de quem está no local e da Defesa Civil.",
  "deteccoes": [{"classe": "fogo", "confianca": 0.777, "caixa": [392.1, 120.1, 426.5, 151.5]}, …],
  "municipio_id": 1500503,
  "risco_municipio": "alto",
  "prioridade": "alta"
}
```
_(resposta real do modelo treinado para a amostra; a lista de detecções foi encurtada)_

| Campo | Significado |
|---|---|
| `classe` | `fogo`, `fumaca` ou `nada`. Fogo tem prioridade quando aparecem os dois |
| `duvida` | `true` quando a maior confiança está entre `limiar_duvida` e `limiar`: a API não confirma, mas também não descarta |
| `prioridade` | só com `municipio_id`: `alta` (confirmado e risco alto), `media`, `baixa` |

Erros: `400` (não é imagem), `413` (maior que 10 MB), `415` (formato diferente de JPEG, PNG ou WebP), `503` (modelo não carregado).

### 3. Tempo real (webcam ou vídeo)

```bash
python src/detectar_video.py --fonte 0                                   # webcam
python src/detectar_video.py --fonte video.mp4 --saida resultados/demo.mp4
```

### 4. Imagens próprias sem Colab

Coloque as fotos em `visao/imagens_proprias/` (fora do Git) com o nome começando pela resposta certa (`fogo_`, `fumaca_` ou `nada_`) e rode:

```bash
python src/avaliar_proprias.py
```

Gera `resultados/imagens_proprias_resultados.csv` e `resultados/imagens_proprias.png`, igual à seção 8 do notebook.

### 5. Testes

```bash
python -m pytest -q tests
```

## Resultados

YOLO11n, 30 épocas (cerca de 2 h numa GPU T4 do Colab), imagens de 640 px. Números de `resultados/metricas_teste_caixas.json` e `resultados/limiar_recomendado.json`.

| Métrica (teste, 4.306 imagens) | Fumaça | Fogo | Geral |
|---|---|---|---|
| mAP@50 | 0,801 | 0,684 | **0,742** |
| mAP@50-95 | 0,482 | 0,354 | **0,418** |
| Precisão | 0,803 | 0,715 | 0,759 |
| Recall | 0,735 | 0,598 | 0,667 |

| Por imagem (limiar escolhido) | Valor |
|---|---|
| Limiar / limiar de dúvida | 0,15 / 0,10 |
| Sensibilidade (fotos com fogo/fumaça avisadas) | 95,7% |
| Falso alarme (fotos sem nada alarmadas) | 5,0% |
| Acurácia nas 3 respostas (fogo, fumaça, nada) | 93,3% |
| Velocidade em CPU (ms por imagem / FPS) | 76,2 ms / 13,1 FPS |
| Velocidade em GPU T4 (ms por imagem / FPS) | 15,6 ms / 64,2 FPS |

Figuras: `resultados/teste_caixas/confusion_matrix_normalized.png`, `resultados/matriz_confusao_por_imagem.png`, `resultados/curva_limiares.png`, `resultados/erros_falso_alarme.png`, `resultados/erros_perdidos.png`, `resultados/exemplos_deteccao.png`, `resultados/api_demo.png`.

O limiar baixo (0,15) é esperado: o modelo dá confiança moderada para fumaça fina e distante, e a escolha privilegia não perder ocorrências (95,7% avisadas) mantendo o falso alarme em 5%.

## Escolha do limiar

- **`limiar`**: o que dá o maior F1 de "ocorrência" (foto com fogo ou fumaça contra foto sem nada) no teste.
- **`limiar_duvida`**: o maior limiar abaixo dele que ainda avisa 95% das fotos com fogo ou fumaça. Entre os dois, a resposta vem como dúvida.
- Limitação: o limiar foi escolhido no próprio teste, e não numa validação separada.

## Limitações conhecidas

- Nuvens, neblina e luzes à noite são as causas mais comuns de falso alarme entre os 12 casos mais confiantes que anotamos; outra fonte são pontos pequenos no horizonte das câmeras fixas, alguns possivelmente fumaça sem rótulo no dataset. Os casos reais estão em `resultados/erros_*.png` e `resultados/erros_para_anotar.csv`.
- Fumaça fina ou muito distante é a principal fonte de fogo perdido.
- O D-Fire tem muita imagem de câmera de vigilância. Por isso testamos também fotos de celular próprias.

## LGPD e segurança

- A imagem é processada em memória e descartada. Não é gravada em disco nem em log; o log guarda só classe, confiança e município.
- Sem rosto, placa ou endereço nas imagens próprias, que também não vão para o repositório.
- Modelos (`.pt`) e dataset não vão para o GitHub (`.gitignore`).
- Limite de tamanho, checagem de tipo e proteção contra "bomba de descompressão" na API.
