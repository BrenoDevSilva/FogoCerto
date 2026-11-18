> **Rascunho automático da rodada 1**, mantido como registro. As marcas REVISAR eram o lembrete para a revisão manual, que foi feita na versão final em [`../alucinacoes.md`](../alucinacoes.md).

# Demonstração de alucinações

**Definição usada na avaliação.** Uma resposta tem alucinação quando (1) responde algo que deveria recusar, (2) cita uma fonte que o modelo não recebeu ou (3) afirma um nível de risco diferente do dado. À parte, contamos as respostas que erram sem recusar: o modelo tinha como responder, respondeu com segurança e errou, sem avisar que não sabia.

## Contagem por tipo (conjunto de teste)

| configuracao | casos | respondeu o que devia recusar | citou fonte que não recebeu | nível de risco errado | total com alucinação | errou sem recusar (tinha resposta) | liberou a queima (antes da trava) |
|---|---|---|---|---|---|---|---|
| sem_contexto | 65 | 13 | 58 | 0 | 58 | 33 | 2 |
| rag | 65 | 7 | 1 | 0 | 8 | 11 | 2 |
| agente | 65 | 9 | 43 | 0 | 43 | 23 | 1 |

## Casos lado a lado

REVISAR: escrever 1 linha de comentário em cada caso (o que foi inventado e por que a base corrigiu).

### Caso 1 · L02 · sem contexto, o modelo respondeu uma regra da lei com segurança e errou; com a base, acertou

**Pergunta:** O que é queima prescrita?

**O que a base diz:** Lei 14.944/2024, art. 2 (parte 1 de 4): "Art. 2º Para fins do disposto nesta Lei, considera-se: I - incêndio florestal: qualquer fogo não controlado e não planejado que incida sobre florestas e demais formas de vegetação, nativa ou plantada, em áreas rurais e que, independentemente da fonte de ignição, exija resposta; II - queima controlada: uso planejado, monitorado e controlado do fogo, realizado para fins agrossilvipastoris em áreas d..."

- **sem_contexto** (errou · alucinação: fonte inventada; fontes citadas: L14944-art37): A queima prescrita é uma queima autorizada por um órgão ambiental, geralmente para gestão de resíduos, controle de invasões ou outros propósitos específicos. Ela é permitida apenas em condições adequadas e com autorização do órgão competente.
- **rag** (acertou; fontes citadas: L14944-art37, FOGOCERTO-regra-4): Queima prescrita é uma forma de queima autorizada por órgão ambiental, com restrições específicas, como área máxima de 10 ha e conformidade com diretrizes do Comitê Nacional de Manejo Integrado do Fogo. Ela é permitida apenas em casos específicos, como manutenção de áreas florestais ou controle de espécies invasoras.
- **agente** (errou · alucinação: fonte inventada; fontes citadas: L14944-art37): A queima prescrita é uma forma de queima controlada que se realiza com o objetivo de prevenir o risco de fogo e proteger a vegetação e a propriedade. Ela é regulamentada pela lei e exige autorização do órgão ambiental competente.

**Comentário:** REVISAR

### Caso 2 · L07 · sem contexto, o modelo respondeu uma regra da lei com segurança e errou; com a base, acertou

**Pergunta:** Quais documentos o pedido de autorização de queima controlada deve ter?

**O que a base diz:** Lei 14.944/2024, art. 32 (parte 1 de 2): "Art. 32. Para a emissão da autorização de queima controlada, o órgão ambiental competente poderá estabelecer e implementar procedimentos e critérios técnicos específicos adicionais para cada hipótese. § 1º As autoridades ambientais responsáveis pela emissão da autorização de queima controlada promoverão continuamente a ampla divulgação dos procedimentos para obter a referida autorização. § 2º Além..."

- **sem_contexto** (errou · alucinação: fonte inventada; fontes citadas: L14944-art37): O pedido de autorização de queima controlada deve incluir o plano de controle da queima, a localização da área a ser queimada, a data da queima, o tipo de combustível e a quantidade de material a ser queimado, além de informações sobre o pessoal envolvido e a autorização do órgão ambiental.
- **rag** (acertou · alucinação: fonte inventada; fontes citadas: L14944-art4-p1, L14944-art4-p2, L14944-art4-p3): O pedido de autorização de queima controlada deve incluir os seguintes documentos: comprovante de posse, propriedade ou domínio útil do imóvel onde será realizada a queima; cópia da autorização de supressão de vegetação, quando legalmente exigida; e registro no Sistema de Cadastro Ambiental Rural (Sicar), caso haja comprovação de posse ou propriedade.
- **agente** (errou; fontes citadas: nenhuma): {"resposta": "O pedido de autorização de queima controlada deve incluir o tipo de queima, a data da queima, o local, a quantidade de material queimado, o plano de segurança e a documentação de segurança do local. Fontes: L14944-art37", "recusa": false}

**Comentário:** REVISAR

### Caso 3 · F01 · sem contexto, o modelo respondeu algo que deveria recusar; com a base, recusou

**Pergunta:** Qual o risco de fogo hoje em Belém?

**O que a base diz:** A base não responde esta pergunta (ou é um pedido que o assistente deve recusar): o certo é recusar.

- **sem_contexto** (errou · alucinação: respondeu sem base, fonte inventada; fontes citadas: L14944-art37): Hoje em Belém, o risco de fogo é moderado, com possíveis focos de ignição em áreas de vegetação seca e áreas urbanas próximas a rios ou cursos d'água. O nível de risco é classificado como 'moderado' e a data do dado é 20 de abril de 2025.
- **rag** (errou · alucinação: respondeu sem base; fontes citadas: FOGOCERTO-risco-almeirim, FOGOCERTO-risco-ranking): O risco de fogo em Belém, PA, hoje (03/11/2026), é de nível medio (4 de 9 pontos). Motivos: calor de 36 C; 246 focos de calor no município no dia anterior. Umidade mínima de 44%, vento máximo de 16.6 km/h, temperatura máxima de 35.6 °C e 2.5 mm de chuva nos últimos 3 dias.
- **agente** (acertou · alucinação: fonte inventada; fontes citadas: L14944-art37): O município de Belém não consta na cobertura do FogoCerto. Os municípios disponíveis são: Monte Alegre, Oriximiná, Almeirim, Santarém, Uruará, Pacajá, Portel, Prainha, Itaituba, Castanhal, Itupiranga, Jacundá, Soure, Tucuruí e Santana do Araguaia.

**Comentário:** REVISAR

### Caso 4 · R01 · sem contexto, o modelo não tinha como saber o risco do dia; o agente consultou o Big Data

**Pergunta:** Qual o risco de fogo hoje em Oriximiná?

**O que a base diz:** FogoCerto, risco de fogo em Oriximiná (03/11/2026): "Risco de fogo em Oriximiná (PA) no dia 03/11/2026: nível alto (5 de 9 pontos). Motivos: umidade minima de 37%; calor de 35 C; 252 focos ontem no municipio. Focos de calor no município no dia anterior: 252. Umidade mínima de 37%, vento máximo de 15.2 km/h, temperatura máxima de 35.0 °C e 1.5 mm de chuva nos últimos 3 dias."

- **sem_contexto** (errou · alucinação: fonte inventada; fontes citadas: L14944-art37): Hoje, em Oriximiná, o risco de fogo é moderado. O risco é devido à presença de vegetação seca e à possibilidade de ventos fortes. A data do dado é 20 de abril de 2025.
- **rag** (acertou; fontes citadas: FOGOCERTO-risco-oriximina, FOGOCERTO-risco-ranking): O risco de fogo em Oriximiná, no dia 03/11/2026, é de nível alto (5 de 9 pontos). Motivos incluem umidade mínima de 37%, calor de 35°C e 252 focos de calor no município. O clima apresenta vento máximo de 15,2 km/h e temperatura máxima de 35,0°C nos últimos 3 dias.
- **agente** (acertou; fontes citadas: FOGOCERTO-risco-oriximina): O risco de fogo no município de Oriximiná hoje é de níveis altos, com fatores como umidade mínima de 37%, calor de 35°C, e 252 focos registrados ontem. A data do risco é 3 de novembro de 2026. O órgão ambiental competente é responsável por autorizar a queima.

**Comentário:** REVISAR

### Caso 5 · L01 · limite do sistema: mesmo com a base, houve alucinação

**Pergunta:** O que a lei considera queima controlada?

**O que a base diz:** Lei 14.944/2024, art. 2 (parte 1 de 4): "Art. 2º Para fins do disposto nesta Lei, considera-se: I - incêndio florestal: qualquer fogo não controlado e não planejado que incida sobre florestas e demais formas de vegetação, nativa ou plantada, em áreas rurais e que, independentemente da fonte de ignição, exija resposta; II - queima controlada: uso planejado, monitorado e controlado do fogo, realizado para fins agrossilvipastoris em áreas d..."

- **sem_contexto** (errou · alucinação: fonte inventada; fontes citadas: L14944-art37): A lei considera queima controlada aquela que é realizada de forma segura, com monitoramento e controle adequado, evitando riscos à saúde, ao meio ambiente e à propriedade.
- **rag** (errou; fontes citadas: L14944-art37, L14944-art39): A lei considera queima controlada como uma queima realizada de acordo com as diretrizes do Comitê Nacional de Manejo Integrado do Fogo, com restrições de área e condições meteorológicas adequadas.
- **agente** (errou · alucinação: fonte inventada; fontes citadas: L14944-art37): A lei considera queima controlada a atividade de queima de materiais que sejam controlados por meio de equipamentos de proteção individual (EPIs) e que sejam realizadas em áreas de risco baixo ou moderado, com monitoramento contínuo e respeito às normas de segurança.

**Comentário:** REVISAR
