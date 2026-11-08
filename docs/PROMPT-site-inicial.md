# Tarefa: criar o site inicial (MVP) do FogoCerto

Contexto: leia `README.md`, `docs/PROJETO-FogoCerto.md` e `bigdata/README.md` antes de começar.

## O que é
Site do FogoCerto: mostra, a cada manhã, o risco de fogo de hoje em 15 municípios do Pará, explicando o porquê, para produtores rurais e defesa civil. Público com celular simples e internet ruim. Português do Brasil, linguagem simples.

## Stack
- React + Vite + TypeScript, dentro da pasta `site/`.
- CSS simples ou Tailwind; sem bibliotecas pesadas.
- `npm run build` precisa gerar um site estático (o time de DevOps vai empacotar em Docker depois).

## Dados
Nesta primeira versão, o site lê um arquivo `site/public/data/risco_atual.json` com o mesmo formato da visão `vw_risco_atual` da camada Ouro:

```json
[{"id_ibge":1505809,"nome":"Portel","uf":"PA","data":"2026-11-06","nivel_risco":"alto","pontos":5,
  "fatores":"umidade minima de 28%; sem chuva nos ultimos 3 dias; 15 focos ontem no municipio",
  "focos_ontem":15,"umidade_min":28,"vento_max":21.0,"temp_max":36.2,"chuva_3d":0.0,
  "atualizado_em":"2026-11-07T10:35:00"}]
```

Crie um JSON de exemplo com os 15 municípios de `bigdata/config/municipios.json` (valores plausíveis, misturando alto, médio e baixo) e marque no README do site que é dado de exemplo até ligarmos a API.
Isole a leitura num único módulo (`src/data/risco.ts`, função `getRiscoAtual()`), para depois trocar o JSON pela API `GET /risco?municipio_id=` sem mexer nas telas.

## Telas
1. **Início:** escolher o município (lista ou busca) e ver um cartão grande com o nível (baixo, médio ou alto, com cor **e** texto/ícone, não só cor), os motivos em lista simples, focos de ontem, umidade, vento, chuva e a hora da atualização.
2. **Panorama:** os 15 municípios ordenados do maior para o menor risco.
3. **Como calculamos:** a regra de pontos explicada em linguagem simples (está em `bigdata/README.md`) e as fontes (INPE e Open-Meteo).
4. **Espaços reservados** (só a casca, com "em breve"): "Pergunte ao assistente" (GenAI) e "Enviar foto de fumaça" (Visão).

## Regras do produto (obrigatórias)
- O site **nunca autoriza queima**. Sempre mostrar: "O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado." Em risco alto, recomendar não queimar e procurar a defesa civil.
- Acessível: contraste bom, funciona com teclado, textos alternativos, fonte legível, funciona bem no celular.
- Se o dado não carregar, mostrar a última informação disponível ou uma mensagem clara, nunca tela em branco.
- Nada de chave, senha ou dado pessoal no código.

## Git
- Trabalhe na branch `site/inicial`, faça commits pequenos e, no fim, abra um pull request para `main` (não faça merge sozinho).
- Atualize `site/README.md` com: como rodar (`npm install`, `npm run dev`), como gerar o build e de onde vêm os dados.

## Antes de terminar
Rode `npm run build` sem erro, abra o site no navegador, teste no tamanho de celular e me mostre prints das telas.
