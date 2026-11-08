# FogoCerto: visão geral do projeto (GS FIAP CitizenTech 2026.2, 4ES)

Entrega final: **19/11/2026 às 23h55** (meta interna: 18/11). Um único produto atravessa as 7 disciplinas, publicado em URL pública e usável pelo avaliador sem explicação. Nome provisório. Contexto específico de Big Data em `BigData/CONTEXTO-FogoCerto-BigData.md`.

## 1. Em uma frase
Um sistema que diz ao produtor rural e à defesa civil do município, a cada manhã, se hoje há risco de fogo na região e se é seguro (e permitido) fazer queima controlada.

## 2. Por que este tema
- **Dados fáceis:** fontes abertas, sem cadastro e sem token.
- **Filtro da GenAI** (energia, segurança ou mobilidade): prevenção de incêndio é segurança. Confirmar com o professor Francisco Elanio na mentoria (pendente).
- **As 7 matérias respondem à mesma decisão:** "hoje há risco, e posso queimar?".
- **A lei liga tudo:** a Lei 14.944/2024 permite suspender ou cancelar autorização de queima com condições meteorológicas desfavoráveis. A resposta correta depende de lei + tempo + focos próximos.
- **Reserva** se o tema falhar: janela de pulverização segura (Open-Meteo + lei dos agrotóxicos + NR-31).

## 3. Cidadão e problema
**Cidadão:** pequeno produtor ou pecuarista de um recorte de municípios (a definir) e a defesa civil ou brigada do município.

**Problema:** o fogo na vegetação é detectado por satélite, mas o produtor e o gestor local não têm um aviso simples, diário e local que una risco, regra legal e orientação do que fazer. Muitos não sabem se precisam de autorização, nem que tempo seco e ventoso pode tornar a queima proibida ou perigosa.

**Evidência a levantar antes do pitch:** número de focos de calor no recorte (INPE) e 2 ou 3 conversas curtas com produtores, brigadistas ou defesa civil. O briefing exige "problema real com evidência".

## 4. Visão geral da solução
Fluxo: fontes abertas → Airflow → Bronze, Prata e Ouro (Databricks) → API → MVP web (PWA). Em paralelo: sensor do robô → API; foto do produtor → modelo de visão → API; assistente (agente com LLM local) → API; n8n lê a API e envia alertas.

O MVP mostra: nível de risco do município hoje (baixo, médio ou alto) com os fatores explicados; focos nas últimas 24 horas; assistente que responde sobre queima e lei citando a fonte; envio de foto para checar fumaça; histórico de alertas.

O risco é calculado por **regra transparente** (umidade baixa, vento forte, dias sem chuva, focos próximos), com limiares justificados e validação por backtest no histórico. Sem vender "previsão por IA" sem prova.

## 5. Fontes de dados e status
- **INPE Queimadas** (focos de calor): CSV e GeoJSON das últimas 24 e 48 horas pela API de dados abertos, histórico desde 1998 no BDQueimadas. Sem token. Página: inpe.br/queimadas/dados-abertos. Pelo catálogo, cada foco traz data, satélite, município, estado, precipitação, dias sem chuva e risco de fogo. **A verificar:** URL exata do arquivo diário e colunas reais.
- **Open-Meteo:** umidade, vento, temperatura e chuva (previsão e histórico), sem chave. Adaptar as variáveis ao nosso problema (o enunciado proíbe entregar o exemplo sem adaptar).
- **IBGE:** malha e códigos de municípios.
- **Textos legais (base do RAG):** Lei 14.944/2024 (Manejo Integrado do Fogo), Lei 12.651/2012 (Código Florestal), Lei 9.605/1998 (Crimes Ambientais), com texto oficial no Planalto. Leis federais são texto público, o que simplifica a tabela de licenças.
- **Sensor do robô:** dados reais da maquete, com geração documentada se houver simulação (o enunciado aceita dado simulado com geração justificada).
- **Recorte:** 10 a 20 municípios, escolhido olhando onde há focos nos dias de teste.

## 6. O que cada disciplina entrega

### 6.1 Big Data Architecture & Data Integration (Dados)
- DAG diária no Airflow com 2 tarefas em paralelo (INPE e Open-Meteo) e uma tarefa que confere a chegada. Um arquivo por coleta, com data no nome, em `chegada/`. Chaves e configurações em Variables.
- 2 lotes de dias diferentes no Volume do Databricks. Bronze com Auto Loader, sem duplicar, com contagens antes e depois.
- Prata: tipos, nulos e inválidos tratados, MERGE pela chave, 3 regras de qualidade com total barrado.
- Ouro: 1 fato (risco por município e dia) e 2 ou mais dimensões. 5 consultas SQL com interpretação, 1 de impacto (backtest).
- LGPD: dado pessoal (contato de quem recebe alerta) com hash. O MVP consome a tabela Ouro de risco.
- Entrega: PDF na ordem do enunciado, prints legíveis e legendados, repositório público sem chaves.

### 6.2 Generative AI for Engineering (Inteligência)
- Tarefa: responder perguntas de produtor e gestor sobre uso do fogo no meio rural, em JSON válido com resposta, fonte e recusa.
- Casos de teste com gabarito, incluindo "não consta".
- Base de conhecimento em trechos com fonte (tabela com fonte, formato, licença e nº de trechos), busca medida por recall@1 e recall@3 com limiar justificado.
- Três configurações em placar: modelo sem contexto, RAG simples e RAG com **agente** de duas ferramentas: `consulta_risco(município)` (chama nossa API) e `busca_lei(pergunta)`. Alternativa: LoRA.
- 5 erros reais com causa e correção. README reprodutível.
- Regra de produto: orienta, não dá parecer jurídico, sempre encaminha ao órgão ambiental competente.

### 6.3 Applied Computer Vision (Visão)
- Treino customizado de detecção de fumaça e fogo (ex.: YOLO) com datasets públicos (verificar licença) e imagens próprias para teste.
- No produto: o produtor envia foto e a API devolve classe, confiança e "consulte a defesa civil". Detecção positiva cria alerta local.
- Cuidado: nuvem e poeira geram falso positivo. Reportar métricas reais (mAP, matriz de confusão).
- Entrega: PDF (resumo de 250 palavras, objetivo de 50, metodologia, resultados), vídeo e repositório.

### 6.4 Robotic Process Automation (Automação)
- Fluxo diário em n8n ou Python: lê o risco na API, **decide** por município (risco alto ou foco a menos de X km), **repete** para cada município assinante e envia alerta por Telegram ou e-mail.
- Exceções: API fora do ar, arquivo ausente ou inválido, dado duplicado. Logs com data e hora, itens, sucessos e falhas, sem dados sensíveis.
- Integração verificável com o MVP, testes de sucesso, decisão e falha, fluxo em BPMN, PDF e vídeo de até 3 minutos.

### 6.5 Secure DevOps Tools & Cloud Computing (Produção)
- API e PWA em Docker (usuário não root, sem segredo na imagem), docker compose, infraestrutura em Terraform (state e .tfvars fora do repo, nenhuma porta admin aberta para 0.0.0.0/0).
- GitHub Actions com build, Gitleaks, Semgrep e Trivy a cada push, segredos em GitHub Secrets, deploy automático. Mostrar uma execução barrada e a corrigida.
- Dashboard com as 4 métricas de ouro e um alerta disparado. Diagrama, responsabilidade compartilhada, onde ficam os dados pessoais (LGPD), custo e Ficha Técnica no README. 14 pontos.

### 6.6 Project-Based Maker Lab (Físico)
- Evolução do robô com sensor de temperatura e umidade e sensor de fumaça. Decide localmente (alerta quando a combinação passa do limiar) e envia o evento à API.
- IA: classificação do nível de risco local (regra mais modelo leve), sem depender de comando manual.
- Testes de operação e falha (sem rede, leitura ruim). Teste só com fonte de fumaça segura e supervisionada.
- **Status:** o carrinho não está disponível no momento. Descobrir quem está com ele ou o que falta comprar.
- Entrega só por GitHub (ZIP, PDF e DOC não são aceitos), vídeo de até 6 minutos no README ou YouTube e **nomes de todos os integrantes no README**. Sem os nomes, o grupo fica sem nota na GS.

### 6.7 Business Intelligence & Startup Development (Negócio e pitch)
- Vídeo de até 5 minutos no YouTube (não listado), com demonstração do MVP real na URL pública, sem slides simulando telas.
- Roteiro: problema com dado do INPE; solução; demo; modelo de negócio; indicadores e ODS; viabilidade e pedido.
- Modelo de negócio (hipóteses a validar): prefeituras ou defesas civis (assinatura), cooperativas e sindicatos rurais, seguradoras agrícolas. O produtor usa de graça.
- Indicadores: municípios cobertos, alertas enviados, consultas ao assistente, taxa de focos em dias de risco alto (backtest), tempo entre risco e aviso.

## 7. Contratos entre os componentes (fechar em 1 dia)
- `GET /risco?municipio_id=` → nível, fatores, focos nas últimas 24 horas, horário da atualização.
- `POST /sensor/eventos` → id do dispositivo, horário, temperatura, umidade, leitura de fumaça.
- `POST /visao/classificar` → imagem; devolve classe e confiança (imagem não é guardada).
- `POST /assistente/perguntar` → pergunta e município; devolve resposta, fontes e indicação de recusa.
- Tabela Ouro de risco por município e dia é a fonte de verdade para a API e o n8n.

## 8. IA responsável, LGPD e acessibilidade
- Pessoa no circuito: o sistema nunca autoriza queima. Avisa o risco e encaminha ao órgão competente.
- Transparência: cada alerta mostra por que foi emitido.
- Dados mínimos: sem rosto ou placa, imagens não armazenadas, contato com hash.
- Acessível e resiliente: linguagem simples, contraste, teclado, leitor de tela, celular de entrada e rede ruim (última informação fica visível).

## 9. Riscos
- INPE mudar formato: guardar amostras no repositório e validar o schema no primeiro dia.
- Falso positivo na visão: limiar de confiança, mensagem de dúvida, métricas honestas.
- Pouco histórico para provar impacto: backtest com o histórico de focos do recorte.
- Escopo grande para 12 dias: contratos fechados cedo, dono por disciplina, README mestre com todos os nomes.
- Tema jurídico: o assistente cita a lei e recusa o que a base não cobre.
- Recorte sem focos nos dias de teste: usar o histórico do BDQueimadas.
- Maker Lab sem robô: resolver o hardware nos próximos dias.

## 10. ODS
- **ODS 13** (ação contra a mudança do clima): prevenção de incêndios e redução de emissões.
- **ODS 2** (agricultura sustentável): manejo seguro do fogo na produção.
- **ODS 3** (saúde e bem-estar): fumaça e riscos à vida.

## 11. Divisão (a ajustar)
Equipe de 5, com dono por disciplina:
- Pessoa 1: Big Data e RPA.
- Pessoa 2: GenAI.
- Pessoa 3: Visão e front do MVP.
- Pessoa 4: API, DevOps e Cloud.
- Pessoa 5: Maker Lab, pitch, README mestre e checklist de entregas.

Nomes completos e RMs de todos precisam estar em cada relatório e README.

## 12. Entregas e prazos (tudo até 19/11 às 23h55)
- **Big Data:** PDF com link do repositório, no Teams da disciplina.
- **GenAI:** links do repositório e relatório no GitHub, no Teams.
- **BI e Startup:** link do vídeo no YouTube, com nome completo e RM de todos.
- **Visão:** PDF, repositório e vídeo de demonstração.
- **RPA:** PDF com links do repositório e do vídeo, no Teams.
- **DevOps:** PDF único com links clicáveis, no portal da disciplina.
- **Maker Lab:** somente link do GitHub, com vídeo e nomes no README.
- Links públicos e funcionando durante a correção (até uma semana após o encerramento).
- Possível contradição de pontuação no enunciado (14 pontos no DevOps e 100 pts no Big Data contra "10 por disciplina"): confirmar com os professores na semana de mentoria (05 a 19/11).

## 13. Pendências e próximos passos
1. Confirmar com o professor de GenAI se incêndio rural passa no filtro de segurança.
2. Teste de 30 minutos: baixar o CSV do INPE, chamar o Open-Meteo para um município, ler a Lei 14.944 e anotar 3 perguntas que ela responde e 1 que não responde.
3. Definir o recorte de municípios.
4. Fechar contratos de API e dono de cada disciplina.
5. Colocar a DAG do Airflow para rodar o quanto antes (coleta acumulada é pré-requisito dos 2 lotes).
6. Marcar 2 ou 3 conversas com produtor ou defesa civil.
7. Resolver o hardware do Maker Lab.
8. Perguntas abertas: Telegram ou e-mail para alertas? AWS ou Azure?
