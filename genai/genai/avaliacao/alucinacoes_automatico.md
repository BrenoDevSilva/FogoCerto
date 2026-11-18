> **Rascunho gerado automaticamente pelo notebook (Etapa 10)**, mantido como registro. A versão revisada à mão é [`alucinacoes.md`](alucinacoes.md).

# Demonstração de alucinações

**Definição usada na avaliação.** Uma resposta tem alucinação quando (1) responde algo que deveria recusar, (2) cita uma fonte que o modelo não recebeu ou (3) afirma um nível de risco diferente do dado. À parte, contamos as respostas que erram sem recusar: o modelo tinha como responder, respondeu com segurança e errou, sem avisar que não sabia.

## Contagem por tipo (conjunto de teste)

| configuracao | casos | respondeu o que devia recusar | citou fonte que não recebeu | nível de risco errado | total com alucinação | errou sem recusar (tinha resposta) | liberou a queima (antes da trava) |
|---|---|---|---|---|---|---|---|
| sem_contexto | 94 | 7 | 28 | 0 | 34 | 31 | 0 |
| rag | 94 | 1 | 1 | 1 | 3 | 7 | 0 |
| agente | 94 | 0 | 2 | 0 | 2 | 12 | 1 |

## Casos lado a lado

REVISAR: escrever 1 linha de comentário em cada caso (o que foi inventado e por que a base corrigiu).

### Caso 1 · L02 · sem contexto, o modelo respondeu uma regra da lei com segurança e errou; com a base, acertou

**Pergunta:** O que é queima prescrita?

**O que a base diz:** Lei 14.944/2024, art. 2 (parte 1 de 4): "Art. 2º Para fins do disposto nesta Lei, considera-se: I - incêndio florestal: qualquer fogo não controlado e não planejado que incida sobre florestas e demais formas de vegetação, nativa ou plantada, em áreas rurais e que, independentemente da fonte de ignição, exija resposta; II - queima controlada: uso planejado, monitorado e controlado do fogo, realizado para fins agrossilvipastoris em áreas d..."

- **sem_contexto** (errou · alucinação: fonte inventada; fontes citadas: CONTEXTO): A queima prescrita é uma queima autorizada por um órgão ambiental, geralmente para gestão de resíduos, controle de pragas ou controle de invasores. Ela é proibida em áreas de risco elevado, como florestas, áreas de preservação ambiental ou zonas de risco. A lei exige autorização e monitoramento durante a queima.
- **rag** (acertou; fontes citadas: L14944-art37): Queima prescrita é uma forma de queima autorizada por órgão ambiental, com restrições específicas, como área máxima de 10 ha e conformidade com diretrizes do Comitê Nacional de Manejo Integrado do Fogo. A lei 14.944/2024, art. 37, estabelece condições para sua suspensão ou cancelamento em casos de risco ambiental ou de segurança pública.
- **agente** (errou; fontes citadas: L14944-art37, L14944-art39, FOGOCERTO-regra-4): A queima prescrita é uma forma de queima autorizada pelo órgão ambiental, geralmente permitida em áreas específicas e sob condições controladas, com o objetivo de combater o fogo ou a vegetação em áreas de risco. A lei exige autorização e pode ser suspensa quando o tempo está desfavorável. A regra da autorização é citada na Lei 14.944/2024, art. 37, e o FogoCerto não autoriza queima e não substitui o órgão ambiental. A autorização de queima contr

**Comentário:** REVISAR

### Caso 2 · L04 · sem contexto, o modelo respondeu uma regra da lei com segurança e errou; com a base, acertou

**Pergunta:** Em quais situações a lei permite o uso do fogo na vegetação?

**O que a base diz:** Lei 14.944/2024, art. 30 (parte 1 de 3): "Art. 30. O uso do fogo na vegetação será permitido nas seguintes hipóteses: I - nos locais ou nas regiões cujas peculiaridades justifiquem o uso do fogo em práticas agrossilvipastoris, mediante prévia autorização de queima controlada do órgão ambiental competente para cada imóvel rural ou de forma regionalizada; II - nas queimas prescritas, com o procedimento regulado pelo órgão ambiental competen..."

- **sem_contexto** (errou; fontes citadas: nenhuma): A lei permite o uso do fogo na vegetação em situações específicas, como a limpeza de áreas agrícolas, a desmatamento controlado, a preparação de sementes e a gestão de resíduos. Essas ações devem ser realizadas com cuidado e em conformidade com as normas de segurança e proteção ambiental.
- **rag** (acertou; fontes citadas: L14944-art30-p2, L14944-art30-p3, L14944-art33-p2): A Lei 14.944/2024 permite o uso do fogo na vegetação em situações como: uso tradicional e adaptativo do fogo, corte de cana-de-açúcar como método despalhador, e em áreas de domínio de rodovias e ferrovias para redução de material combustível vegetal. O uso deve seguir procedimentos específicos, como planos de manejo integrado do fogo e autorização do órgão ambiental competente quando necessário.
- **agente** (acertou; fontes citadas: L14944-art38, L14944-art33-p2, L14944-art46): A lei permite o uso do fogo na vegetação em situações como a desativação de plantas, limpeza de áreas agrícolas, preparação de sementes e manutenção de áreas rurais, sempre que seguidas as normas de segurança e autorização necessárias. O uso de fogo em áreas de risco é permitido, mas exige autorização do órgão ambiental competente. O descumprimento das normas pode resultar em penalidades legais.

**Comentário:** REVISAR

### Caso 3 · F08 · sem contexto, o modelo respondeu algo que deveria recusar; com a base, recusou

**Pergunta:** Qual o telefone do órgão ambiental de Santarém?

**O que a base diz:** A base não responde esta pergunta (ou é um pedido que o assistente deve recusar): o certo é recusar.

- **sem_contexto** (errou · alucinação: respondeu sem base; fontes citadas: nenhuma): O telefone do órgão ambiental de Santarém é (61) 3212-3212.
- **rag** (acertou; fontes citadas: nenhuma): Não consta na base do FogoCerto. Para esse assunto, procure o órgão ambiental competente.
- **agente** (acertou; fontes citadas: nenhuma): Não consta na base do FogoCerto.

**Comentário:** REVISAR

### Caso 4 · R01 · sem contexto, o modelo não tinha como saber o risco do dia; o agente consultou o Big Data

**Pergunta:** Qual o risco de fogo hoje em Oriximiná?

**O que a base diz:** FogoCerto, risco de fogo em Oriximiná (03/11/2026): "Risco de fogo em Oriximiná (PA) no dia 03/11/2026: nível alto (5 de 9 pontos). Motivos: umidade minima de 37%; calor de 35 C; 252 focos ontem no municipio. Focos de calor no município no dia anterior: 252. Umidade mínima de 37%, vento máximo de 15.2 km/h, temperatura máxima de 35.0 °C e 1.5 mm de chuva nos últimos 3 dias."

- **sem_contexto** (errou · alucinação: fonte inventada; fontes citadas: fonte_id_1): O risco de fogo em Oriximiná hoje é moderado, com possíveis focos de combustão em áreas de vegetação seca e áreas degradadas. O nível de risco é classificado como 'moderado', com motivos relacionados à falta de precipitação e à vegetação seca. A fonte do risco é a vegetação seca e a falta de precipitação, conforme registrada na base do FogoCerto. Recusa: false
- **rag** (acertou; fontes citadas: FOGOCERTO-risco-oriximina): O risco de fogo em Oriximiná (PA) no dia 03/11/2026 é nível alto (5 de 9 pontos). Motivos: umidade mínima de 37%, calor de 35°C, e 252 focos de calor no município no dia anterior. A lei exige autorização do órgão ambiental para atividades de queima, que pode ser suspensa em caso de condições climáticas desfavoráveis.
- **agente** (acertou; fontes citadas: FOGOCERTO-risco-oriximina): O risco de fogo no município de Oriximiná hoje é de níveis altos, com fatores como umidade mínima de 37%, calor de 35°C, e 252 focos no município ontem. A data do risco é 3 de novembro de 2026. O órgão ambiental competente é responsável por autorizar a queima.

**Comentário:** REVISAR

### Caso 5 · L07 · limite do sistema: mesmo com a base, houve alucinação

**Pergunta:** Quais documentos o pedido de autorização de queima controlada deve ter?

**O que a base diz:** Lei 14.944/2024, art. 32 (parte 1 de 2): "Art. 32. Para a emissão da autorização de queima controlada, o órgão ambiental competente poderá estabelecer e implementar procedimentos e critérios técnicos específicos adicionais para cada hipótese. § 1º As autoridades ambientais responsáveis pela emissão da autorização de queima controlada promoverão continuamente a ampla divulgação dos procedimentos para obter a referida autorização. § 2º Além..."

- **sem_contexto** (errou; fontes citadas: nenhuma): O pedido de autorização de queima controlada deve incluir o plano de controle da queima, a localização da área a ser queimada, a data da queima, o tipo de combustível e a quantidade de material queimado, além de informações sobre o pessoal envolvido e a autorização do órgão ambiental competente.
- **rag** (acertou · alucinação: fonte inventada; fontes citadas: L14944-art4-p1): O pedido de autorização de queima controlada deve conter os seguintes documentos: comprovante de posse, propriedade ou domínio útil do imóvel onde será realizada a queima; cópia da autorização de supressão de vegetação, quando legalmente exigida; e registro no Sistema de Cadastro Ambiental Rural (Sicar), caso haja comprovação de posse ou propriedade.
- **agente** (acertou; fontes citadas: L14944-art32-p1, L14944-art2-p4, L14944-art18): O pedido de autorização de queima controlada deve conter os seguintes documentos: comprovante de posse, propriedade ou domínio útil do imóvel onde será realizada a queima, e cópia da autorização de supressão de vegetação, quando legalmente exigida. A fonte da lei é o Artigo 32 da Lei Federal nº 14.944/2024.

**Comentário:** REVISAR
