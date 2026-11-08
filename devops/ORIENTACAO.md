# Orientação para a parte de Secure DevOps Tools & Cloud Computing

Documento para quem fará a disciplina de DevOps e Cloud no FogoCerto. Pode ser lido por uma pessoa ou colado como contexto numa ferramenta de IA. Leia antes: `README.md`, `docs/PROJETO-FogoCerto.md` (seção 6.5) e `site/README.md`.

## Contexto do projeto

FogoCerto avisa produtores rurais e defesa civil, a cada manhã, o risco de fogo no município (15 municípios do Pará). O produto **nunca autoriza queima**: informa o risco e encaminha ao órgão ambiental. O avaliador de todas as matérias vai **abrir o site por uma URL pública**, sem ajuda. Se a URL não abrir, perdemos nota em várias disciplinas ao mesmo tempo.

## Qual é o papel de DevOps

Colocar o produto no ar, com segurança e com monitoramento. Em termos práticos: **empacotar, publicar e vigiar** o site (e a API, quando existir). É a disciplina que sustenta a entrega das outras: o link do MVP no README principal ainda diz "a definir".

## O que a disciplina exige (e o que vale nota)

Conferir o enunciado para a estrutura exata (o projeto levantou 14 pontos nesta disciplina). Do que já está levantado:

- **Docker:** imagem com **usuário não root** e **sem segredo dentro da imagem**; `docker compose` para subir localmente.
- **Terraform:** infraestrutura como código. `state` e `.tfvars` **fora do repositório** (o `.gitignore` já bloqueia). **Nenhuma porta de administração aberta para `0.0.0.0/0`.**
- **GitHub Actions** a cada push: build, **Gitleaks** (segredos), **Semgrep** (código) e **Trivy** (imagem e dependências), segredos em **GitHub Secrets** e **deploy automático**.
- Mostrar **uma execução barrada e a corrigida** (o pipeline pegando um problema de verdade e depois passando).
- **Dashboard** com as 4 métricas de ouro e **um alerta disparado**.
- Diagrama, responsabilidade compartilhada, onde ficam os dados pessoais (LGPD), custo estimado e **Ficha Técnica no `devops/README.md`** (hoje "a preencher").
- Pergunta em aberto do projeto: **AWS ou Azure?** Decidir cedo, porque o Terraform depende disso.

## O que o site precisa para ser publicado

O site já está pronto na `main`, em `site/`. É um **site estático**: não tem servidor próprio.

| Item | Valor |
|---|---|
| Stack | React 18 + Vite 8 + TypeScript |
| Node para o build | **20.19 ou mais novo** (ou 22.12+) |
| Instalar | `cd site && npm ci` |
| Gerar | `npm run build` (já checa os tipos e falha se houver erro) |
| Saída | `site/dist/`: HTML, CSS, JS, fontes e o JSON. **É só isso que vai para o servidor** |
| Testar local | `npm run preview` (http://localhost:4173) |
| Vulnerabilidades | `npm audit` está em **0** |

Sugestão de Dockerfile em dois estágios: estágio 1 com Node (`npm ci` e `npm run build`), estágio 2 com um servidor estático **que rode sem root** (por exemplo nginx "unprivileged", na porta 8080) copiando só o `dist/`.

### Cuidados de servidor (importantes)

- **HTTPS é obrigatório em produção.** O site funciona offline e pode ser instalado no celular (PWA), e isso só funciona em HTTPS (o `localhost` é exceção). Sem HTTPS, o site abre normalmente, mas perde essas duas funções.
- **Cache:** `index.html` e `sw.js` devem ter `Cache-Control: no-cache`, para o navegador sempre pegar a versão nova. Arquivos em `assets/` têm o hash no nome e podem ficar em cache por muito tempo (`immutable`).
- **`data/risco_atual.json`:** não deve ficar em cache longo. O site já o pede com `no-cache` e o service worker busca na rede primeiro, mas um cache agressivo do servidor ou de CDN atrasaria o dado novo.
- **Rotas:** o site usa `#/` (por exemplo `#/panorama`), então **não precisa de regra de reescrita** no servidor.
- **Subpasta:** o build usa caminhos relativos, então funciona também fora da raiz do domínio.
- **Cabeçalhos de segurança** são bem-vindos (CSP, `X-Content-Type-Options`, etc.). O site carrega tudo do próprio domínio (fontes locais, sem CDN), o que facilita uma CSP restrita.

## Como o dado chega ao ar

O site lê **`site/public/data/risco_atual.json`**, gerado pelo Databricks. O time de Big Data **atualiza esse arquivo por pull request**, e o pipeline coleta o dia anterior todo dia às 10:30 (Brasília). Isso gera um pedido para o deploy:

- **Redeploy automático quando esse arquivo mudar na `main`** (por exemplo, um gatilho do workflow por `paths: site/public/data/**`). Sem isso, o site publicado mostra dado velho e acende o aviso "A atualização mais recente ainda não chegou".
- Mais adiante, o JSON pode ser trocado pela API `GET /risco`. Só o módulo `site/src/data/risco.ts` muda; o resto do site não.

## Monitoramento: o que vale vigiar

As 4 métricas de ouro, aplicadas ao FogoCerto:

| Métrica | Exemplo no FogoCerto |
|---|---|
| Latência | tempo de resposta do site (e da API, quando existir) |
| Tráfego | acessos por minuto |
| Erros | respostas 5xx e 404 em `data/risco_atual.json` |
| Saturação | uso de CPU e memória do contêiner |

E um alerta de negócio que faz sentido aqui: **"o `risco_atual.json` está velho"**. O campo `data` do arquivo deveria ser sempre ontem (último dia fechado); se for mais antigo que isso, a coleta diária parou. É um alerta fácil de demonstrar e que importa de verdade.

## Dados pessoais e LGPD

O site **não coleta nem guarda dado pessoal**. O único dado guardado no aparelho é o município escolhido (`localStorage`). O JSON de risco não tem dado pessoal. Os dados pessoais do projeto (contato de quem recebe alerta) ficam no Big Data, com hash, e são **fictícios** por enquanto. No diagrama, mostre onde cada coisa fica.

## Contrato com o resto do produto

Endereços previstos para a API (ainda não existem; combinem com o dono da API):

- `GET /risco?municipio_id=` → nível, fatores, focos, horário da atualização.
- `POST /sensor/eventos` → robô do Maker Lab.
- `POST /visao/classificar` → imagem; devolve classe e confiança (a imagem não é guardada).
- `POST /assistente/perguntar` → pergunta e município; devolve resposta, fontes e indicação de recusa.

Cada uma pode virar um contêiner. Planeje as portas, a rede e a publicação (só o necessário para fora).

## O que não fazer

- Não subir senha, token, chave de nuvem, `.tfstate` ou `.tfvars` (o `.gitignore` já bloqueia, mas confira antes de cada commit).
- Não colocar segredo na imagem Docker nem no workflow (use GitHub Secrets).
- Não abrir porta de administração (SSH, banco, painel) para `0.0.0.0/0`.
- Não rodar o contêiner como root.
- Não deixar o repositório privado nem a URL fora do ar durante a correção (até uma semana após a entrega).

## Estrutura da pasta (sugestão)

```
devops/
  README.md          Ficha Técnica, diagrama, custo, responsabilidade compartilhada
  docker/            Dockerfiles e docker-compose
  terraform/         infraestrutura (sem state nem .tfvars)
  monitoramento/     dashboard, alertas e prints
.github/workflows/   pipeline (build, Gitleaks, Semgrep, Trivy, deploy)
```

## Prazos

Entrega final: 19/11/2026 às 23h55, no portal da disciplina (PDF único com links clicáveis). Meta interna: 18/11. **O site publicado precisa estar no ar antes da gravação do pitch e do vídeo do MVP.** Trabalhe em uma branch curta (`devops/docker`, `devops/pipeline`), abra pull request e peça 1 aprovação antes de juntar na `main`.
