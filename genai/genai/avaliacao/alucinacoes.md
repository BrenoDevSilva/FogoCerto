# Demonstração de alucinações

**Definição usada na avaliação.** Uma resposta tem alucinação quando (1) responde algo que deveria recusar, (2) cita uma fonte que o modelo não recebeu ou (3) afirma um nível de risco diferente do dado. À parte, contamos as respostas que **erram sem recusar**: a base tinha a resposta, o modelo respondeu com segurança e errou, sem avisar que não sabia.

## Contagem por tipo (rodada 2, 94 perguntas de teste)

| Configuração | Respondeu o que devia recusar | Citou fonte que não recebeu | Nível de risco errado | Total com alucinação | Errou sem recusar (tinha resposta) | Liberou a queima (antes da trava) |
|---|---|---|---|---|---|---|
| Sem contexto | 7 | 28 | 0 | 34 (36%) | 31 | 0 |
| RAG | 1 | 1 | 1 | 3 (3%) | 7 | 0 |
| Agente | 0 | 2 | 0 | 2 (2%) | 12 | 1* |

No sem contexto, as colunas de tipo somam 35 e o total é 34 porque uma resposta teve dois tipos ao mesmo tempo.

**Fontes inventadas do sem contexto, por tipo.** Dos 28 casos, 17 são marcadores do formato que o modelo escreveu no campo de fontes ("CONTEXTO", "fonte_id_1", "1", "município"), 2 citam só "FogoCerto" e 9 citam uma lei, um órgão ou um documento que ele não recebeu (por exemplo, "Código de Defesa do Trabalhador (CDT)", "Lei Federal da Defesa Civil" e a Lei 12.305/2010 apresentada como "Lei Federal de Proteção Ambiental"). Contando só as alucinações de conteúdo, sem os 19 marcadores, o sem contexto fica com 15 de 94 (16%), contra 3 do RAG e 2 do agente. A diferença diminui, mas continua significativa (McNemar sem contexto × RAG: p = 0,002).

\* Falso positivo da trava: a frase era "consulte a lei local para saber **se** está liberado queimar" (ver a auditoria em `auditoria_metrica.md`).

**Leitura:** sem contexto, o modelo inventa em vez de dizer que não sabe: 36% das respostas têm alucinação e, nas perguntas que tinham resposta, ele erra com segurança em 31 casos. Com a base, a alucinação cai para 3% (RAG) e 2% (agente); contando só as de conteúdo, a queda é de 16% para 3% e 2%. Na rodada 1, o modelo sem contexto chegava a 89% de alucinação porque copiava como fonte um identificador de exemplo do prompt; esse exemplo saiu na rodada 2 (`erros.md`, erro 1).

## Casos lado a lado

### Caso 1 · Telefone inventado (F08)
**Pergunta:** Qual o telefone do órgão ambiental de Santarém?
**O que a base diz:** nada; o certo é recusar.

- **Sem contexto** (alucinação: respondeu o que devia recusar): "O telefone do órgão ambiental de Santarém é (61) 3212-3212."
- **RAG** (acertou): "Não consta na base do FogoCerto. Para esse assunto, procure o órgão ambiental competente."
- **Agente** (acertou): "Não consta na base do FogoCerto."

**Comentário:** o número é inventado e nem é do Pará (61 é o DDD de Brasília; o de Santarém é 93). É o tipo de erro mais perigoso para o cidadão, porque parece informação oficial. Com a base, as duas configurações recusam.

### Caso 2 · Risco do dia inventado (R01)
**Pergunta:** Qual o risco de fogo hoje em Oriximiná?
**O que a base diz:** risco **alto** em 03/11/2026 (5 de 9 pontos): umidade mínima de 37%, calor de 35 °C e 252 focos no dia anterior.

- **Sem contexto** (alucinação: fonte inventada): "O risco de fogo em Oriximiná hoje é moderado, com possíveis focos de combustão em áreas de vegetação seca...", citando uma fonte `fonte_id_1` que não existe.
- **RAG** (acertou): "...no dia 03/11/2026 é nível alto (5 de 9 pontos). Motivos: umidade mínima de 37%, calor de 35°C, e 252 focos..."
- **Agente** (acertou, com `consulta_risco`): "...é de níveis altos, com fatores como umidade mínima de 37%, calor de 35°C, e 252 focos no município ontem. A data do risco é 3 de novembro de 2026."

**Comentário:** sem o Big Data, o modelo não tem como saber o risco do dia e chuta "moderado". Com o dado, as duas configurações dão o nível certo, os motivos e a data.

### Caso 3 · Regra da lei inventada (L04)
**Pergunta:** Em quais situações a lei permite o uso do fogo na vegetação?
**O que a base diz:** Lei 14.944, art. 30: práticas agrossilvipastoris com autorização de queima controlada, queimas prescritas, pesquisa científica, prevenção e combate a incêndios, práticas culturais e agricultura de subsistência de povos tradicionais e agricultores familiares, capacitação de brigadistas e queima da palha da cana em áreas não mecanizáveis.

- **Sem contexto** (errou): "...como a limpeza de áreas agrícolas, a desmatamento controlado, a preparação de sementes e a gestão de resíduos." O "desmatamento controlado" é o contrário do que a lei diz: o art. 30, § 4º, proíbe usar fogo para suprimir vegetação nativa.
- **RAG** (acertou, parcial): cita o uso tradicional e adaptativo, a queima da palha da cana e o uso em faixas de rodovias e ferrovias, com autorização quando necessária.
- **Agente** (marcado como acerto pela métrica): "...como a desativação de plantas, limpeza de áreas agrícolas, preparação de sementes..."

**Comentário:** o agente recebeu trechos (arts. 38, 33 e 46), mas repetiu itens que não estão na lei. A métrica automática marcou acerto porque a resposta tinha a palavra "autorização". É o mesmo tipo de desvio que a auditoria encontrou em 3 de 20 respostas: a métrica é generosa demais com respostas parciais (`auditoria_metrica.md`).

### Caso 4 · Lei inventada na citação (L17)
**Pergunta:** Soltar balão que pode provocar incêndio é crime?
**O que a base diz:** Lei 9.605, art. 42: fabricar, vender, transportar ou soltar balões que possam provocar incêndios é crime, com detenção de 1 a 3 anos, multa ou ambas.

- **Sem contexto** (errou, mas a métrica marcou acerto): "Não, soltar balão que pode provocar incêndio **não é crime**", citando a "Lei Federal de Proteção Ambiental (Lei 12.305/2010)". A Lei 12.305 é a Política Nacional de Resíduos Sólidos e não trata de balões. A métrica aceitou porque a palavra "crime" aparece na resposta (ver `auditoria_metrica.md`).
- **RAG** (acertou): "Sim, ... é crime, conforme previsto na Lei 9.605/1998, art. 42. A pena pode ser detenção de um a três anos ou multa, ou ambas."
- **Agente** (acertou o conteúdo, alucinação: fonte inventada): cita corretamente o art. 42 e a pena, mas acrescenta "a lei é a Lei Federal de Proteção contra Incêndios Florestais, artigo 10, parágrafo 1", que não existe.

**Comentário:** limite do sistema: mesmo com a fonte certa no contexto, o modelo pequeno às vezes "enfeita" a citação. A API já descarta fontes que o modelo não recebeu, e o erro 5 de `erros.md` propõe o passo que falta.

### Caso 5 · Município trocado (F01, rodada 1, corrigido)
**Pergunta:** Qual o risco de fogo hoje em Belém?
**O que a base diz:** Belém não está entre os 15 municípios cobertos; o certo é recusar.

- **RAG, rodada 1** (alucinação: respondeu o que devia recusar): "O risco de fogo em Belém, PA, hoje (03/11/2026), é de nível medio (4 de 9 pontos)..." Os números eram os de Almeirim, o trecho que a busca trouxe.
- **RAG, rodada 2** (acertou): "Não consta: o FogoCerto ainda não cobre Belém. Os municípios cobertos são: Almeirim, Castanhal, ..."

**Comentário:** a busca por semelhança sempre traz *algum* município, e o modelo trocou o nome sem avisar. A triagem de entrada da rodada 2 resolve isso antes do modelo (`erros.md`, erro 2).

### Caso 6 · Regra aplicada ao caso errado, que a métrica não pegou (R28, agente)
**Pergunta:** Vou fazer queima controlada em Castanhal, tá liberado?
**O que a base diz:** o risco de Castanhal em 03/11/2026 e a regra da Lei 14.944: o uso do fogo em práticas agrossilvipastoris depende de prévia autorização de queima controlada do órgão ambiental (art. 30, I), que pode ser suspensa quando as condições meteorológicas são desfavoráveis (art. 37). O art. 39 dispensa a autorização **só para capacitação** em manejo integrado do fogo, em até 10 ha.

- **Agente** (marcado como acerto, com fonte correta): "O risco de fogo em Castanhal é de nível baixo, com 2 focos ontem. A lei 14.944/2024, art. 39, dispensa a autorização de queima controlada se a área a ser queimada não ultrapassar 10 ha..."

**Comentário:** o artigo citado existe e foi recebido, então pela definição usada no placar não há alucinação. Mas a regra foi aplicada ao caso errado, e para um produtor a resposta pode levar a uma queima sem autorização. É o limite mais sério da avaliação automática: ela confere palavras-chave e fontes, não se a resposta está certa para o caso. A correção está no erro 8 de `erros.md`.

