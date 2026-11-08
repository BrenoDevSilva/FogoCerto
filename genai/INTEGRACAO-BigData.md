# Integração da IA com o Big Data

Guia para a parte de **Generative AI for Engineering** do FogoCerto. Explica o que o Big Data entrega, em que formato, e como a ferramenta `consulta_risco` do agente deve usar isso.

## Resumo

O agente tem 2 ferramentas:

| Ferramenta | De onde vem | Para quê |
|---|---|---|
| `busca_lei(pergunta)` | base de conhecimento da IA (`base/`): Lei 14.944/2024, Lei 12.651/2012, Lei 9.605/1998 | o que a lei diz sobre uso do fogo |
| `consulta_risco(municipio)` | **Big Data**: arquivo `risco_atual.json` | o risco de fogo **de hoje** no município, e por quê |

Exemplo: *"Posso queimar hoje em Portel?"* → o agente chama `consulta_risco("Portel")` (risco médio, 700 focos ontem), chama `busca_lei("queima controlada condições meteorológicas")` e junta as duas coisas, citando a fonte. **Nunca autoriza a queima:** informa e orienta a procurar o órgão ambiental do estado.

## Onde está o arquivo

| Arquivo | Para quê |
|---|---|
| **`site/public/data/risco_atual.json`** | **o oficial: use este.** Gerado pelo Databricks (notebook `bigdata/databricks/04_exportar.py`), o mesmo que o site lê |
| `<URL do site>/data/risco_atual.json` | o mesmo arquivo, depois que o site estiver publicado |

O Breno atualiza o oficial algumas vezes até a entrega (a última antes da gravação do pitch). O formato não muda.

Deixe o caminho configurável (variável de ambiente `FOGOCERTO_RISCO_URL` ou `FOGOCERTO_RISCO_PATH`), para trocar do arquivo local para a URL do site sem mexer no código.

## Formato

Uma lista com 1 item por município (15 municípios do Pará), do maior para o menor risco:

```json
{
  "id_ibge": 1505304,
  "nome": "Oriximiná",
  "uf": "PA",
  "data": "2026-11-06",
  "nivel_risco": "alto",
  "pontos": 7,
  "fatores": "umidade minima de 28%; sem chuva nos ultimos 3 dias; calor de 36 C; 123 focos ontem no municipio",
  "focos_ontem": 123,
  "umidade_min": 28,
  "vento_max": 14.7,
  "temp_max": 36.3,
  "chuva_3d": 0.9,
  "atualizado_em": "2026-11-07T10:35:00"
}
```

| Campo | Significado |
|---|---|
| `id_ibge` | código IBGE do município (7 dígitos) |
| `nome`, `uf` | nome com acento e estado |
| `data` | dia a que o risco se refere |
| `nivel_risco` | `baixo`, `medio` ou `alto` |
| `pontos` | soma da regra (0 a 9) |
| `fatores` | motivos em texto, separados por `;` (use para explicar a resposta) |
| `focos_ontem` | focos de calor no município no dia anterior (fogos únicos, sem repetição de satélite) |
| `umidade_min` | umidade mínima do dia (%) |
| `vento_max` | vento máximo (km/h) |
| `temp_max` | temperatura máxima (°C) |
| `chuva_3d` | chuva somada nos últimos 3 dias (mm) |
| `atualizado_em` | quando o dado foi gerado |

## Regra do risco (para a IA saber explicar)

| Fator | Pontos |
|---|---|
| umidade mínima < 30% / < 40% | 2 / 1 |
| vento máximo ≥ 30 km/h / ≥ 20 km/h | 2 / 1 |
| menos de 1 mm de chuva nos últimos 3 dias | 1 |
| temperatura máxima ≥ 35 °C | 1 |
| focos no município ontem ≥ 100 / ≥ 20 / ≥ 1 | 3 / 2 / 1 |

Nível: 0 a 2 = baixo, 3 a 4 = médio, 5 ou mais = alto. Fontes: INPE (focos de calor) e Open-Meteo (clima).

## Como implementar `consulta_risco`

```python
import json, os, unicodedata, urllib.request

def _normalizar(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return txt.strip().lower()

def _carregar() -> list[dict]:
    url = os.getenv("FOGOCERTO_RISCO_URL")
    if url:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.load(r)
    caminho = os.getenv("FOGOCERTO_RISCO_PATH", "site/public/data/risco_atual.json")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)

def consulta_risco(municipio: str) -> dict:
    """Risco de fogo de hoje para um município do recorte (nome ou código IBGE)."""
    try:
        dados = _carregar()
    except Exception:
        return {"encontrado": False, "erro": "dados de risco indisponíveis no momento"}
    alvo = _normalizar(str(municipio))
    for d in dados:
        if alvo in (_normalizar(d["nome"]), str(d["id_ibge"])):
            return {"encontrado": True, **d, "fonte": "FogoCerto (INPE + Open-Meteo)"}
    return {"encontrado": False,
            "erro": "município fora do recorte do FogoCerto",
            "municipios_disponiveis": [d["nome"] for d in dados]}
```

## Regras para as respostas

- **Município fora da lista:** responder que não consta (é um dos casos "não consta" do conjunto de teste), sem inventar risco.
- **Dado antigo:** se `data` não for de hoje ou ontem, dizer a data do dado.
- **Nunca autorizar queima.** Em risco alto, recomendar não queimar e procurar a defesa civil. Sempre lembrar que a autorização é do órgão ambiental do estado.
- **Explicar com `fatores`:** "o risco está alto porque a umidade mínima foi de 28% e houve 123 focos ontem".

## Casos de teste que usam o Big Data (sugestão)

Os níveis abaixo são de um dia específico. Monte o gabarito final com o `risco_atual.json` da versão que for usada na entrega.

| Pergunta | Esperado |
|---|---|
| Qual o risco de fogo hoje em Oriximiná? | alto, citando umidade, chuva e focos |
| Posso fazer queima controlada em Monte Alegre hoje? | não autoriza; risco alto; procurar órgão ambiental; cita a lei |
| Por que Portel está em risco médio? | explica os fatores (700 focos ontem), sem inventar outros |
| Qual o risco em Belém? | não consta (fora do recorte) |
| Qual município está com o maior risco? | o primeiro da lista |

## Municípios do recorte

Portel, Pacajá, Uruará, Almeirim, Monte Alegre, Prainha, Oriximiná, Santarém, Itaituba, Itupiranga, Tucuruí, Jacundá, Castanhal, Santana do Araguaia e Soure (todos no Pará).

Dúvidas sobre os dados: falar com o Breno (Big Data).
