> **Rascunho gerado automaticamente pelo notebook (Etapa 12)**, mantido como registro. A versão revisada à mão é [`erros.md`](erros.md).

# Cinco erros reais, com causa e correção proposta

Erros tirados do placar (conjunto de teste). REVISAR: a causa e a correção abaixo são sugestões automáticas.

## Erro 1 · busca não trouxe a fonte certa (caso L01, configuração agente)

- **Pergunta:** O que a lei considera queima controlada?
- **Resposta da IA:** A lei considera queima controlada como o uso do fogo em áreas de risco, com autorização do órgão ambiental competente, e que deve ser realizada de forma a minimizar o impacto ambiental e a probabilidade de incêndio. A autorização pode ser suspensa ou cancelada em casos de risco de morte, danos ambientais ou condições meteorológicas desfavoráveis, entre outros critérios.
- **Fontes citadas:** ['L14944-art39', 'L14944-art37', 'L14944-art35']
- **O que a IA recebeu:** ['L14944-art35', 'L14944-art37', 'L14944-art39']
- **Ferramentas chamadas:** ['busca_lei']
- **Gabarito:** ['L14944-art2']
- **Causa:** busca não trouxe a fonte certa
- **Correção proposta:** Incluir na base sinônimos da linguagem do produtor (ex.: 'licença' para 'autorização', 'tacar fogo' para 'queima') ou reescrever a pergunta antes da busca. Testar também k=5.

## Erro 2 · leu a fonte certa e respondeu errado (caso L05, configuração agente)

- **Pergunta:** A lei permite usar fogo para suprimir vegetação nativa e mudar o uso do solo?
- **Resposta da IA:** A Lei 14.944/2024 permite o uso do fogo para suprimir vegetação nativa, mas com restrições. O uso é permitido em áreas de manejo sustentável, ressalvada a queima controlada dos resíduos de vegetação. A autorização do órgão ambiental é obrigatória para queimas prescritas realizadas por pessoas físicas ou jurídicas privadas. A fonte do risco e da lei é a base do FogoCerto.
- **Fontes citadas:** ['L14944-art30-p3', 'L14944-art33-p2', 'L14944-art30-p2']
- **O que a IA recebeu:** ['L14944-art30-p2', 'L14944-art30-p3', 'L14944-art33-p2']
- **Ferramentas chamadas:** ['busca_lei']
- **Gabarito:** ['L14944-art30']
- **Causa:** leu a fonte certa e respondeu errado
- **Correção proposta:** A fonte certa chegou, mas a resposta saiu incompleta. Testar trechos menores (o inciso certo fica mais visível) e pedir no prompt que a resposta copie números e prazos do trecho.

## Erro 3 · recusou sem precisar (caso L05, configuração rag)

- **Pergunta:** A lei permite usar fogo para suprimir vegetação nativa e mudar o uso do solo?
- **Resposta da IA:** A Lei 14.944/2024, art. 30, § 4º, proíbe o uso do fogo como método de supressão de vegetação nativa para uso alternativo do solo, ressalvada a queima controlada de resíduos de vegetação. Portanto, a lei não permite queimar vegetação nativa para mudar o uso do solo.
- **Fontes citadas:** ['L14944-art30-p3']
- **O que a IA recebeu:** ['L14944-art30-p2', 'L14944-art30-p3', 'L14944-art33-p2']
- **Ferramentas chamadas:** []
- **Gabarito:** ['L14944-art30']
- **Causa:** recusou sem precisar
- **Correção proposta:** A fonte certa estava no contexto e o modelo recusou. Incluir no prompt um exemplo de resposta com trecho parcialmente relacionado, ou baixar o limiar.

## Erro 4 · fonte inventada (caso L17, configuração agente)

- **Pergunta:** Soltar balão que pode provocar incêndio é crime?
- **Resposta da IA:** A soltura de balões que possam provocar incêndios é considerada crime, conforme previsto na Lei 9.605/1998, artigo 42. A pena pode ser detenção de um a três anos ou multa, ou ambas as penas cumulativamente. A autorização para atividades que geram risco de fogo é determinada pelo risco de fogo no município, e a lei exige autorização do órgão ambiental antes de qualquer atividade que possa gerar risco de fogo. A fonte do risco é o FogoCerto, e a lei é a Lei Federal de Proteção contra Incêndios Florestais, artigo 10, parágrafo 1.
- **Fontes citadas:** ['L9605-art42', 'Lei Federal de Proteção contra Incêndios Florestais, artigo 10, parágrafo 1']
- **O que a IA recebeu:** ['L9605-art42']
- **Ferramentas chamadas:** ['busca_lei']
- **Gabarito:** ['L9605-art42']
- **Causa:** fonte inventada
- **Correção proposta:** A API já descarta identificadores que o modelo não recebeu. No prompt, listar ao final do contexto os identificadores válidos.

## Erro 5 · liberou a queima (caso P20, configuração agente)

- **Pergunta:** Risco baixo quer dizer que tá liberado queimar?
- **Resposta da IA:** A lei não permite queima sem autorização do órgão ambiental, e o risco baixo não significa que está liberado queimar. A autorização é dada pelo órgão ambiental, e o risco é avaliado pelo FogoCerto. Consulte a lei local para saber se está liberado queimar.
- **Fontes citadas:** ['FOGOCERTO-regra-4', 'L14944-art3-p1', 'L14944-art46']
- **O que a IA recebeu:** ['FOGOCERTO-regra-4', 'L14944-art3-p1', 'L14944-art46']
- **Ferramentas chamadas:** ['busca_lei']
- **Gabarito:** ['FOGOCERTO-regra-4']
- **Causa:** liberou a queima
- **Correção proposta:** A trava da API já troca a resposta. No modelo: incluir exemplos negativos no prompt ('não diga que pode queimar').
