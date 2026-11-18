# Auditoria da métrica automática

A conferência automática compara a resposta com palavras-chave e fontes do gabarito. Para saber o quanto confiar nela, lemos à mão uma amostra de respostas e comparamos com o veredito da métrica.

## Rodada 1: correções na régua

Lendo as respostas da rodada 1, achamos falhas na própria métrica, corrigidas antes da rodada 2:
- 4 casos com palavras-chave incompletas no gabarito (L05, L18, P05 e P10). Exemplo: "proíbe" não casava com "proibid".
- A trava contra "pode queimar" marcava como liberação a frase "não significa que a queima está liberada". Passou a ignorar frases com negação antes do trecho.
- O leitor de JSON falhava quando o modelo repetia o objeto ou escrevia algo depois. Passou a ler o primeiro objeto completo.

A rodada 1 foi recalculada com a régua corrigida (`comparacao_rodadas.csv`), para a comparação entre rodadas medir só a mudança no sistema.

## Rodada 2: amostra de 20 respostas

Amostra aleatória (semente 7) de 20 respostas do RAG e do agente nas perguntas de lei (grupos 1 e 2) que não foram recusadas. Cada uma foi lida junto com o artigo do gabarito. O sorteio pode ser refeito com `python avaliacao/amostra_auditoria.py`, que mostra as mesmas 20 respostas e o veredito da métrica. A amostra não inclui o risco do dia, as recusas nem o sem contexto; esses recortes foram conferidos à parte, nas seções abaixo.

| # | Config. | Caso | Métrica | Leitura humana | Concorda? |
|---|---|---|---|---|---|
| 1 | RAG | P29 | acerto | certa (responsabilidade civil com nexo causal, art. 45) | sim |
| 2 | RAG | P07 | erro | errada (a lei não se aplica à queima de resíduos, art. 48) | sim |
| 3 | Agente | L13 | acerto | certa (administrativa, civil e criminal) | sim |
| 4 | RAG | L11 | acerto | certa (dispensa até 10 ha, art. 39) | sim |
| 5 | RAG | L16 | acerto | certa (detenção de 6 meses a 1 ano) | sim |
| 6 | Agente | P19 | acerto | errada (descreve a ferramenta, não a regra de pontos) | **não** |
| 7 | RAG | L20 | erro | errada (troca "dar ciência" por "autorização") | sim |
| 8 | Agente | L05 | erro | errada (diz que a lei permite) | sim |
| 9 | RAG | L13 | acerto | certa | sim |
| 10 | Agente | P08 | acerto | certa (culposo: detenção de 6 meses a 1 ano) | sim |
| 11 | RAG | P22 | erro | incompleta (não cita o Ibama, art. 34) | sim |
| 12 | RAG | L08 | acerto | certa (as hipóteses do art. 37) | sim |
| 13 | RAG | L19 | acerto | parcial (cita o órgão gestor, não os órgãos do Sisnama) | **parcial** |
| 14 | Agente | L23 | acerto | certa (coordenado pelo Ibama) | sim |
| 15 | Agente | L19 | acerto | parcial (mesmo caso do 13) | **parcial** |
| 16 | Agente | P13 | erro | errada (não diz que o responsável deve combater, art. 45, § 1º) | sim |
| 17 | RAG | L26 | acerto | certa (agravante em época de seca, art. 53) | sim |
| 18 | RAG | L10 | acerto | certa (500 ha, art. 38) | sim |
| 19 | RAG | L41 | acerto | certa (agravantes do art. 53) | sim |
| 20 | Agente | P17 | acerto | certa, mas vaga (a autorização traz orientações de horário, art. 32) | sim |

**Resultado:** a métrica concordou com a leitura humana em **17 de 20** respostas (85%). Nas outras 3, ela foi **generosa**: marcou acerto em respostas parciais ou erradas. Ela não marcou como erro nenhuma resposta certa nesta amostra.

**O que isso muda no placar:** os acertos reais devem ser um pouco menores que os reportados, nas configurações com base. As diferenças entre as configurações (30% sem contexto contra 80% no RAG) são muito maiores que esse desvio, então as conclusões se mantêm. Também na rodada 2, a trava marcou como liberação a frase condicional "para saber **se** está liberado queimar" (P20, agente). Correção proposta: tratar "se" antes do trecho como condição, não como afirmação.

## Rodada 2: os acertos do modelo sem contexto

Lemos também os 10 acertos do modelo sem contexto nas perguntas de lei. Em 3 deles a resposta está **errada** e a métrica marcou acerto, porque a palavra-chave aparece mesmo numa negação ou numa afirmação falsa:

| Caso | Resposta sem contexto | O que a lei diz |
|---|---|---|
| L17 | "soltar balão que pode provocar incêndio **não é crime**" | é crime (Lei 9.605, art. 42) |
| P13 | "você **não é obrigado** a combater o fogo" | o responsável deve agir (Lei 14.944, art. 45) |
| L38 | "a Lei 14.944, também conhecida como Lei dos Resíduos Sólidos, **aplica-se**" | não se aplica a resíduos sólidos (art. 48) |

Outros 2 estão parciais (L08 cita um "Decreto nº 6.344/2015" que não existe; L19 é o mesmo caso parcial do RAG e do agente). Ou seja, o acerto real do modelo sem contexto é ainda menor que os 30% do placar, e a diferença para o RAG é maior do que a tabela mostra.

## Palavra-chave que já está na pergunta

A causa desses falsos acertos é um limite do gabarito: em **12 dos 72 casos com resposta**, a palavra-chave exigida já aparece na própria pergunta (L17, L32, L34, L38, L40, P02, P04, P05, P13, P16, P24 e P30). Nesses casos, uma resposta que só repete a pergunta passa na métrica.

Para medir o efeito, recalculamos o acerto sem esses 12 casos, com as respostas já salvas:

| Configuração | Placar oficial (94) | Sem os 12 casos (82) |
|---|---|---|
| Sem contexto | 28/94 (29,8%) | 21/82 (25,6%) |
| RAG | 75/94 (79,8%) | 64/82 (78,0%) |
| Agente | 62/94 (66,0%) | 57/82 (69,5%) |

A ordem e as conclusões não mudam. Correção proposta para a próxima versão do gabarito: trocar a palavra-chave desses 12 casos por uma informação que só aparece na resposta certa (por exemplo, a pena ou o artigo) e tratar negação antes da palavra-chave, como já é feito na trava.

## Outros falsos acertos, fora da amostra

Na conferência final, lendo as respostas que a amostra não cobria, achamos mais respostas erradas que a métrica contou como acerto:

| Caso | Config. | Resposta | O que a lei diz |
|---|---|---|---|
| R28 | Agente | "o art. 39 dispensa a autorização de queima controlada se a área não ultrapassar 10 ha" | o art. 39 vale só para capacitação em manejo integrado do fogo (erro 8 de `erros.md`) |
| L38 | Agente | a Lei 14.944 "se aplica à queima de resíduos sólidos" | não se aplica (art. 48) |
| P13 | RAG | "você não é obrigado a combater" | o responsável implementa ações de prevenção e combate (art. 45, § 1º) |
| L02 | RAG | a queima prescrita tem "área máxima de 10 ha" | a lei não traz esse limite para a queima prescrita |

L38 e P13 estão entre os 12 casos com a palavra-chave na pergunta, cujo efeito foi medido acima. R28 e L02 não estão; com eles, os acertos reais do RAG e do agente ficam mais uma ou duas perguntas abaixo do placar. As conclusões não mudam.

## Recusa medida pelo campo `recusa`

A métrica de recusa olha só o campo `recusa` do JSON, não o texto. Isso deixou passar três casos do agente:
- **F13** (ração para gado) e **F17** (receita de bolo de milho): o agente respondeu a pergunta fora do tema e marcou `recusa: true`. Contou como "recusa correta".
- **L22** (garantias do brigadista): o agente afirmou que "a lei não oferece garantias específicas ao brigadista florestal", o que é falso (art. 14), e marcou `recusa: true`. Como recusou, a resposta não entrou como alucinação.

O caminho inverso também acontece: o RAG deu a resposta certa e marcou `recusa: true` em 3 perguntas "posso queimar hoje?" (erro 6 de `erros.md`). Correção proposta: conferir também o texto, contando como recusa só a resposta que diz que não consta ou encaminha ao órgão sem dar informação.

