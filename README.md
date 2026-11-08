# FogoCerto

**Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software 4º ano**

FogoCerto avisa, a cada manhã, produtores rurais e a defesa civil se há risco de fogo hoje no município e se é seguro (e permitido) fazer queima controlada. O risco é calculado com dados abertos de focos de calor do INPE e clima do Open-Meteo, para um recorte de 15 municípios do Pará.

## Integrantes

| Nome completo | RM |
|---|---|
| Breno Silva | RM99275 |
| Eduardo Araujo | RM99758 |
| Gabriela Trevisan | RM99500 |
| Gustavo Akio | RM550241 |
| Rafael Franck | RM550875 |

> Nome completo e RM de todos são obrigatórios aqui e em cada relatório. Sem os nomes no README, o grupo fica sem nota no Maker Lab.

## Links

- MVP (site publicado): _a definir_
- Vídeo pitch (YouTube, não listado): _a definir_
- Vídeo Maker Lab: _a definir_
- Vídeo RPA: _a definir_

## Como o projeto está organizado

| Pasta | Disciplina | Componente |
|---|---|---|
| [`site/`](site/) | MVP | Tela que o cidadão usa |
| [`bigdata/`](bigdata/) | Big Data Architecture & Data Integration | Dados: Airflow + Databricks (Bronze, Prata, Ouro) |
| [`genai/`](genai/) | Generative AI for Engineering | Inteligência: assistente com RAG e agente |
| [`visao/`](visao/) | Applied Computer Vision | Detecção de fumaça e fogo em foto |
| [`rpa/`](rpa/) | Robotic Process Automation | Alertas automáticos aos assinantes |
| [`devops/`](devops/) | Secure DevOps Tools & Cloud Computing | Docker, Terraform, CI/CD, monitoramento |
| [`maker/`](maker/) | Project-Based Maker Lab | Robô com sensores de temperatura, umidade e fumaça |
| [`docs/`](docs/) | Todas | Visão geral do projeto |

Cada pasta tem o próprio README, com a estrutura que a disciplina pede.

## Arquitetura (resumo)

```
INPE (focos) ─┐
              ├─> Airflow ─> chegada/ ─> Databricks: Bronze ─> Prata ─> Ouro ─┐
Open-Meteo ───┘                                                               │
                                                                              v
Robô (sensores) ──> API <── Visão (foto)        Assistente (GenAI) <── API <── tabela de risco
                     │                                                         │
                     v                                                         v
                  site (MVP)  <─────────────────────────────────────── RPA (alertas)
```

## Regras do repositório

- Nunca suba senhas, tokens ou chaves. Use variáveis de ambiente e GitHub Secrets. Uma chave vazada derruba o pipeline de todos.
- Nunca suba dados grandes (CSV do INPE, modelos, vídeos). O `.gitignore` já bloqueia os mais comuns.
- Trabalhe em uma branch curta por tarefa (`bigdata/prata`, `site/tela-risco`...), abra pull request e peça 1 aprovação antes de juntar na `main`.
