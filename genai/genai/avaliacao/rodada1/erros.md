> **Rascunho automático da rodada 1**, mantido como registro. As marcas REVISAR eram o lembrete para a revisão manual, que foi feita na versão final em [`../erros.md`](../erros.md).

# Cinco erros reais, com causa e correção proposta

Erros tirados do placar (conjunto de teste). REVISAR: a causa e a correção abaixo são sugestões automáticas.

## Erro 1 · fonte inventada (caso L01, configuração agente)

- **Pergunta:** O que a lei considera queima controlada?
- **Resposta da IA:** A lei considera queima controlada a atividade de queima de materiais que sejam controlados por meio de equipamentos de proteção individual (EPIs) e que sejam realizadas em áreas de risco baixo ou moderado, com monitoramento contínuo e respeito às normas de segurança.
- **Fontes citadas:** ['L14944-art37']
- **O que a IA recebeu:** []
- **Ferramentas chamadas:** []
- **Gabarito:** ['L14944-art2']
- **Causa:** fonte inventada
- **Correção proposta:** A API já descarta identificadores que o modelo não recebeu. No prompt, listar ao final do contexto os identificadores válidos.

## Erro 2 · JSON inválido (caso L07, configuração agente)

- **Pergunta:** Quais documentos o pedido de autorização de queima controlada deve ter?
- **Resposta da IA:** {"resposta": "O pedido de autorização de queima controlada deve incluir o tipo de queima, a data da queima, o local, a quantidade de material queimado, o plano de segurança e a documentação de segurança do local. Fontes: L14944-art37", "recusa": false}
- **Fontes citadas:** []
- **O que a IA recebeu:** []
- **Ferramentas chamadas:** []
- **Gabarito:** ['L14944-art32']
- **Causa:** JSON inválido
- **Correção proposta:** Usar geração guiada por esquema (JSON schema) ou fazer uma nova tentativa com o lembrete do formato. Enquanto isso, a API devolve uma recusa padrão quando o JSON falha.

## Erro 3 · busca não trouxe a fonte certa (caso P16, configuração agente)

- **Pergunta:** Quem trabalha de brigadista tem direito a seguro?
- **Resposta da IA:** Não consta na base do FogoCerto informações sobre seguro para trabalhadores de brigadista. Recusa: true
- **Fontes citadas:** []
- **O que a IA recebeu:** []
- **Ferramentas chamadas:** []
- **Gabarito:** ['L14944-art14']
- **Causa:** busca não trouxe a fonte certa
- **Correção proposta:** Incluir na base sinônimos da linguagem do produtor (ex.: 'licença' para 'autorização', 'tacar fogo' para 'queima') ou reescrever a pergunta antes da busca. Testar também k=5.

## Erro 4 · não recusou (caso F01, configuração rag)

- **Pergunta:** Qual o risco de fogo hoje em Belém?
- **Resposta da IA:** O risco de fogo em Belém, PA, hoje (03/11/2026), é de nível medio (4 de 9 pontos). Motivos: calor de 36 C; 246 focos de calor no município no dia anterior. Umidade mínima de 44%, vento máximo de 16.6 km/h, temperatura máxima de 35.6 °C e 2.5 mm de chuva nos últimos 3 dias.
- **Fontes citadas:** ['FOGOCERTO-risco-almeirim', 'FOGOCERTO-risco-ranking']
- **O que a IA recebeu:** ['FOGOCERTO-regra-3', 'FOGOCERTO-risco-almeirim', 'FOGOCERTO-risco-ranking']
- **Ferramentas chamadas:** []
- **Gabarito:** recusar
- **Causa:** não recusou
- **Correção proposta:** A pergunta parece com o tema, mas a base não tem a resposta. Reforçar no prompt, com um exemplo, que valor de multa, taxa, prazo e telefone não constam na base, e incluir essas fontes (o Decreto 6.514/2008, de multas) numa próxima versão.

## Erro 5 · leu a fonte certa e respondeu errado (caso L04, configuração rag)

- **Pergunta:** Em quais situações a lei permite o uso do fogo na vegetação?
- **Resposta da IA:** A Lei 14.944/2024 permite o uso do fogo na vegetação em situações como: uso tradicional e adaptativo do fogo, corte de cana-de-açúcar como método despalhador, e em áreas de domínio de rodovias e ferrovias para redução de material combustível vegetal e prevenção de incêndios, conforme regulamentado.
- **Fontes citadas:** ['L14944-art30-p2', 'L14944-art30-p3', 'L14944-art33-p2']
- **O que a IA recebeu:** ['L14944-art30-p2', 'L14944-art30-p3', 'L14944-art33-p2']
- **Ferramentas chamadas:** []
- **Gabarito:** ['L14944-art30', 'L12651-art38']
- **Causa:** leu a fonte certa e respondeu errado
- **Correção proposta:** A fonte certa chegou, mas a resposta saiu incompleta. Testar trechos menores (o inciso certo fica mais visível) e pedir no prompt que a resposta copie números e prazos do trecho.
