# Cinco erros reais, com causa e correção

Erros tirados das respostas guardadas em `avaliacao/` (rodada 2, conjunto de teste) e em `avaliacao/rodada1/`. Cada erro aponta a etapa do caminho em que a resposta falhou. Os dois primeiros foram corrigidos e medidos de novo; os outros três ficam com a correção proposta. No fim, três achados da conferência final (6 a 8), também com correção proposta.

| # | Erro | Etapa que falhou | Situação |
|---|---|---|---|
| 1 | O agente respondia de memória e inventava fontes | decisão do agente + prompt | corrigido e medido de novo |
| 2 | O RAG inventou o risco de um município fora da cobertura | geração (modelo misturou contexto) | corrigido e medido de novo |
| 3 | O agente recusa sem consultar as ferramentas | decisão do agente | correção proposta |
| 4 | A consulta reescrita pelo agente perde a palavra-chave | busca do agente | correção proposta |
| 5 | Fonte inventada ou trocada mesmo com o conteúdo certo | citação | correção proposta |
| 6 | O RAG recusa o "posso queimar hoje?" mesmo dando a resposta | prompt (regras em conflito) | correção proposta |
| 7 | O agente escreve o nome do município errado na ferramenta | chamada da ferramenta | correção proposta |
| 8 | Resposta perigosa contada como acerto | métrica e trava | correção proposta |

## Erro 1 · O agente respondia de memória e inventava fontes (rodada 1, corrigido)

- **Exemplo (L01, rodada 1):** *"O que a lei considera queima controlada?"* O agente não chamou nenhuma ferramenta e respondeu que queima controlada é a "queima de materiais controlados por meio de equipamentos de proteção individual (EPIs)", citando `L14944-art37`. A lei define queima controlada como uso planejado, monitorado e controlado do fogo para fins agrossilvipastoris (Lei 14.944, art. 2º, II).
- **Tamanho do problema:** na rodada 1, o agente usou ferramenta em só 15 de 64 perguntas. O identificador `L14944-art37` aparecia como exemplo no prompt, e o modelo sem contexto o copiou como fonte 56 vezes.
- **Causa:** o modelo pequeno prefere responder do que chamar uma ferramenta, e o exemplo do prompt virou "a fonte padrão".
- **Correção aplicada:** saiu o identificador de exemplo do prompt; quando o agente responde sem consultar nada, recebe um lembrete, uma vez só; a regra 8 passou a dizer que responder "não pode" não é recusa.
- **Medido de novo** (mesma régua, 64 perguntas que existiam nas duas rodadas): uso de ferramenta de 15/64 para 41/64; acertos de 27/64 para 45/64; alucinação de 65,6% para 3,1% (`avaliacao/comparacao_rodadas.csv`).
- **Separando as duas mudanças:** entre as rodadas também entrou a triagem do erro 2. Nos 57 casos comuns que não passaram pela triagem, os acertos do agente foram de 24 para 38 e as alucinações de 36 para 2 (de 63% para 3,5%). Os outros 4 acertos ganhos vêm da triagem.

## Erro 2 · O RAG inventou o risco de um município fora da cobertura (rodada 1, corrigido)

- **Exemplo (F01, rodada 1):** *"Qual o risco de fogo hoje em Belém?"* Belém não está entre os 15 municípios. A busca trouxe o trecho de risco de **Almeirim**, e o modelo respondeu: "O risco de fogo em Belém, PA, hoje (03/11/2026), é de nível medio (4 de 9 pontos). Motivos: calor de 36 C; 246 focos...". Os números são os de Almeirim.
- **Causa:** a busca por semelhança sempre devolve *algum* município, e o modelo trocou o nome sem avisar.
- **Correção aplicada:** triagem de entrada que recusa, antes do modelo, o município citado que não esteja na cobertura, e uma regra no prompt ("se o município perguntado não aparecer no contexto, recuse").
- **Medido de novo:** na rodada 2, F01 e as perguntas novas sobre Paragominas e Redenção (F25 e F26, escritas depois da correção) foram recusadas corretamente nas três configurações. A triagem não barrou nenhuma pergunta que devia ser respondida.
- **Limite da correção:** a triagem procura um nome com inicial maiúscula logo depois de "em", "de", "no" ou "na" (em minúsculas). Ela pega nomes compostos ("em São Félix do Xingu"), mas testamos frases que passam direto para o modelo: "qual o risco de fogo em belem hoje?" (nome em minúsculas), "Em Belém tem risco de fogo hoje?" (preposição no começo da frase, com maiúscula) e o formato que a própria API monta, "(município: Belém)". Nesses casos, a regra do prompt e a `consulta_risco` (que responde "não consta" para município fora da lista) são as camadas que sobram. Correção proposta: comparar o texto, sem acento e em minúsculas, com a lista dos 144 municípios do Pará (IBGE), em qualquer posição da frase.

## Erro 3 · O agente recusa sem consultar as ferramentas (rodada 2)

- **Exemplo (L10):** *"Qual é o limite de área queimada no uso do fogo de forma solidária?"* O agente respondeu "Não consta na base do FogoCerto..." sem chamar a `busca_lei`. O RAG, com a mesma base, acertou: 500 hectares (Lei 14.944, art. 38, parágrafo único).
- **Tamanho do problema:** em 16 das 51 perguntas de lei, o agente recusou sem consultar nenhuma ferramenta. O RAG acertou 12 dessas 16. Isso explica 12 das 15 perguntas de diferença entre o agente (22/51 nas perguntas de lei) e o RAG (37/51); a diferença é estatisticamente significativa (McNemar, p = 0,004).
- **Causa:** o lembrete da correção 1 só dispara quando o agente *responde* de memória, não quando ele *recusa* de memória.
- **Correção proposta:** disparar o lembrete também quando o agente recusa sem ter consultado nada (exceto nas perguntas já recusadas pela triagem), ou chamar a `busca_lei` automaticamente no primeiro passo e deixar o agente decidir só as consultas seguintes.

## Erro 4 · A consulta reescrita pelo agente perde a palavra-chave (rodada 2)

- **Exemplo (P04):** *"Preciso abrir aceiro antes de fazer a queima controlada?"* O agente buscou "regra sobre autorização para queima controlada": a palavra "aceiro" sumiu. Recebeu os arts. 18, 2 e 32 e respondeu sobre autorização, sem falar de aceiro. O RAG, buscando com a pergunta original, recebeu o art. 31 e acertou ("é necessário abrir aceiro... art. 31").
- **Causa:** a busca do agente junta a consulta dele com a pergunta original e fica com a maior nota de cada trecho. Mesmo assim, os trechos da consulta genérica tiveram notas maiores e ocuparam as 3 vagas.
- **Correção proposta:** combinar as duas listas por posição (por exemplo, intercalando os primeiros resultados de cada consulta), em vez de pela maior nota, para garantir vaga aos trechos que a pergunta original encontrou.

## Erro 5 · Fonte inventada ou trocada mesmo com o conteúdo certo (rodada 2)

- **Exemplo A (L17, agente):** *"Soltar balão que pode provocar incêndio é crime?"* O conteúdo está certo (Lei 9.605, art. 42, detenção de 1 a 3 anos), mas a resposta também cita uma "Lei Federal de Proteção contra Incêndios Florestais, artigo 10, parágrafo 1", que não existe na base nem foi recebida.
- **Exemplo B (L07, RAG):** *"Quais documentos o pedido de autorização de queima controlada deve ter?"* O conteúdo está certo (comprovante de posse ou propriedade, autorização de supressão quando exigida e registro no Sicar, art. 32), mas a fonte citada foi `L14944-art4-p1`, que não estava entre os trechos recebidos (`art2-p4`, `art32-p1` e `art32-p2`).
- **Causa:** o modelo escreve a fonte "de cabeça" em vez de copiar o identificador do trecho que usou.
- **Correção proposta:** a API já descarta fontes que o modelo não recebeu. Falta um passo depois da geração: se a lista de fontes ficar vazia ou tiver uma fonte não recebida, escolher entre os trechos recebidos o que mais se parece com a resposta (pela mesma busca e5) e usá-lo como fonte, ou pedir uma nova resposta só com os identificadores válidos listados.

## Achados da conferência final (rodada 2)

Ao conferir de novo todas as respostas salvas, encontramos mais três erros. Eles não mudam o placar, mas atingem a pergunta central do produto, "posso queimar hoje?", e por isso ficam registrados com a correção proposta.

## Erro 6 · O RAG recusa o "posso queimar hoje?" mesmo dando a resposta

- **Exemplo (R11):** *"Quero queimar o pasto hoje em Uruará, pode?"* O RAG respondeu: "O risco de fogo em Uruará (PA) no dia 03/11/2026 é nível medio (4 de 9 pontos). A lei exige autorização do órgão ambiental, que pode ser suspensa quando o tempo está desfavorável. Recusa: true", e marcou `recusa: true`. A resposta está certa, mas a marcação de recusa faz a métrica contar erro.
- **Tamanho do problema:** são 5 perguntas "posso queimar" no teste e o RAG acertou só 1. Em 3 delas (R10, R11 e R20), deu o risco e a lei e marcou recusa. Em 8 respostas do RAG, o modelo escreveu "Recusa: true" dentro do texto.
- **Causa:** duas regras do prompt se contradizem para essa pergunta. A regra 4 manda recusar pedidos de autorização ("Nesses pedidos, recuse") e a regra 6 manda responder quando perguntam se podem queimar. O modelo cumpre as duas: responde e marca recusa.
- **Correção proposta:** limitar a regra 4 a pedidos de autorização ou de parecer ("me autoriza", "analise meu caso") e dizer na regra 6 que "posso queimar hoje em X?" se responde com o risco e a lei, com `recusa: false`. Depois da geração, apagar "Recusa: true/false" do texto da resposta. Medir de novo nos 5 casos e em casos novos desse tipo.

## Erro 7 · O agente escreve o nome do município errado na ferramenta

- **Exemplo (R05 e R27):** *"O risco de fogo em Soure está alto?"* O agente chamou `consulta_risco` com o município "Sourde"; no R27, com "Sour". A ferramenta não achou o município e o agente respondeu que "Soure não consta na base do FogoCerto", o que é falso.
- **Tamanho do problema:** são os 2 erros do agente nas 20 perguntas de risco do dia.
- **Causa:** a ferramenta só aceita o nome exato. O modelo pequeno às vezes escreve o nome com erro.
- **Correção proposta:** na `consulta_risco`, comparar o nome sem acento e em minúsculas e aceitar o mais parecido da lista (por exemplo, com `difflib.get_close_matches`), devolvendo o nome encontrado; ou usar o município detectado na pergunta original quando o argumento do modelo não for encontrado.

## Erro 8 · Resposta perigosa contada como acerto

- **Exemplo (R28, agente):** *"Vou fazer queima controlada em Castanhal, tá liberado?"* O agente respondeu que "a Lei 14.944/2024, art. 39, dispensa a autorização de queima controlada se a área a ser queimada não ultrapassar 10 ha". O art. 39 dispensa a autorização só para capacitação em manejo integrado do fogo. Para um produtor, essa resposta pode levar a uma queima sem autorização. A métrica contou acerto, e com fonte correta. No R10, o agente também escreveu "é possível queimar a roça, mas a autorização do órgão ambiental competente é necessária".
- **Causa:** a métrica confere palavras-chave e fontes, não se a regra foi aplicada ao caso certo. A trava procura frases como "pode queimar" e "está liberada" e não pega paráfrases como "dispensa a autorização" ou "é possível queimar".
- **Correção proposta:** (1) incluir na trava as paráfrases de liberação ("dispensa a autorização", "é possível queimar", "pode sim", "pode tacar fogo") e aplicá-la também no placar; (2) nos casos "posso queimar", acrescentar ao gabarito palavras proibidas ("dispensa", "liberado", "pode queimar"), que fazem a resposta contar como erro; (3) aumentar esses casos de 5 para pelo menos 20, porque é a pergunta mais importante do produto.

