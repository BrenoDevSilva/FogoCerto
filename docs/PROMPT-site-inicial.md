# Tarefa: criar o site inicial (MVP) do FogoCerto

Contexto: leia `README.md`, `docs/PROJETO-FogoCerto.md` e `bigdata/README.md` antes de começar.

## O que é
Site do FogoCerto: mostra, a cada manhã, o risco de fogo de hoje em 15 municípios do Pará, explicando o porquê, para produtores rurais e defesa civil. Público com celular simples e internet ruim. Português do Brasil, linguagem simples.

## Stack
- React + Vite + TypeScript, dentro da pasta `site/`.
- CSS simples ou Tailwind; sem bibliotecas pesadas.
- `npm run build` precisa gerar um site estático (o time de DevOps vai empacotar em Docker depois).

## Dados
O arquivo **oficial já existe**: `site/public/data/risco_atual.json`. Ele foi gerado pelo Databricks (camada Ouro, visão `vw_risco_atual`). Use ele, **não crie dado de exemplo** e não o edite à mão: o time de Big Data o atualiza por pull request.

Formato (lista com 1 item por município, 15 municípios do Pará, do maior para o menor risco):

```json
{"id_ibge":1504802,"nome":"Monte Alegre","uf":"PA","data":"2026-11-03","nivel_risco":"alto","pontos":7,
 "fatores":"umidade minima de 39%; vento de ate 22 km/h; sem chuva nos ultimos 3 dias; calor de 36 C; 349 focos ontem no municipio",
 "focos_ontem":349,"umidade_min":39.0,"vento_max":22.0,"temp_max":35.8,"chuva_3d":0.4,
 "atualizado_em":"2026-11-08T02:14:21.403011"}
```

Campos: `nivel_risco` é `baixo`, `medio` ou `alto`; `fatores` são os motivos em texto separados por `;` (mostre como lista); `data` é o dia a que o risco se refere (mostre sempre, o dado pode não ser de hoje); `atualizado_em` é quando foi gerado.

Isole a leitura num único módulo (`src/data/risco.ts`, função `getRiscoAtual()`), usando `fetch` do arquivo em `/data/risco_atual.json`. Assim, depois, dá para trocar pela API `GET /risco?municipio_id=` sem mexer nas telas.

## Telas
1. **Início:** escolher o município (lista ou busca) e ver um cartão grande com o nível (baixo, médio ou alto, com cor **e** texto/ícone, não só cor), os motivos em lista simples, focos de ontem, umidade, vento, chuva e a hora da atualização.
2. **Panorama:** os 15 municípios ordenados do maior para o menor risco.
3. **Como calculamos:** a regra de pontos explicada em linguagem simples (está em `bigdata/README.md`) e as fontes (INPE e Open-Meteo).
4. **Espaços reservados** (só a casca, com "em breve"): "Pergunte ao assistente" (GenAI) e "Enviar foto de fumaça" (Visão).

## Regras do produto (obrigatórias)
- O site **nunca autoriza queima**. Sempre mostrar: "O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado." Em risco alto, recomendar não queimar e procurar a defesa civil.
- Acessível: contraste bom, funciona com teclado, textos alternativos, fonte legível, funciona bem no celular.
- Se o dado não carregar, mostrar uma mensagem clara, nunca tela em branco. Se a `data` do arquivo não for de hoje, avisar "dados de DD/MM".
- Nada de chave, senha ou dado pessoal no código.

## Git
- Trabalhe na branch `site/inicial`, faça commits pequenos e, no fim, abra um pull request para `main` (não faça merge sozinho).
- Atualize `site/README.md` com: como rodar (`npm install`, `npm run dev`), como gerar o build e de onde vêm os dados.

## Antes de terminar
Rode `npm run build` sem erro, abra o site no navegador, teste no tamanho de celular e me mostre prints das telas.
