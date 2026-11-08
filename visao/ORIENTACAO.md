# Orientação para a parte de Applied Computer Vision

Documento para quem fará a disciplina de Visão no FogoCerto. Pode ser lido por uma pessoa ou colado como contexto numa ferramenta de IA. Leia antes: `README.md` e `docs/PROJETO-FogoCerto.md` (seção 6.3).

## Contexto do projeto

FogoCerto avisa produtores rurais e defesa civil, a cada manhã, o risco de fogo no município (15 municípios do Pará) e orienta sobre queima controlada. O risco vem de dados abertos (focos de calor do INPE e clima do Open-Meteo), processados em `bigdata/`. O produto **nunca autoriza queima**: informa o risco e encaminha ao órgão ambiental.

## Qual é o papel da Visão

O satélite só detecta um foco depois que passa sobre o local, e fogo pequeno nem sempre aparece. A Visão entra como **confirmação em campo**: o usuário envia uma imagem e o modelo diz se há fumaça ou fogo, com a confiança. O FogoCerto trata isso como uma **ocorrência** para a defesa civil e a cruza com o resto: há foco de satélite por perto? O risco do município hoje é alto?

Não prometa que o modelo substitui o olho humano. Ele ajuda a triar: imagem com fumaça, em município de risco alto e com foco de satélite próximo, sobe na fila de atenção.

## Visão de futuro (para o pitch, não para construir agora)

O mesmo modelo poderia analisar imagens de **câmeras fixas** em fazendas e torres, que é como funciona o monitoramento comercial de fogo. No MVP, a entrada é a foto enviada. No relatório e no vídeo, apresente isso como **próximo passo**, nunca como algo já feito. Não construa integração com câmera.

## O que a disciplina exige (e o que vale nota)

Treinar um modelo de detecção ou classificação de fumaça e fogo, medir com métricas reais (mAP, precisão, recall, matriz de confusão) e entregar: PDF (resumo de 250 palavras, objetivo de 50 palavras, metodologia, resultados), repositório e vídeo. Conferir o enunciado para a estrutura exata. O grosso da nota está no modelo, nas métricas e no relatório. A integração com o produto pesa menos.

## Ajustes pedidos (pequenos)

1. **Entrada do modelo = "uma imagem", venha de onde vier.** A API recebe imagem e devolve classe e confiança. Assim, foto do produtor e câmera fixa são duas origens da mesma entrada.
2. **Conjunto de dados com os dois cenários:** fumaça vista de perto (foto de celular) e vista de longe (estilo câmera de torre ou de propriedade). Confira a licença de cada conjunto público e registre a fonte. Separe um conjunto de teste que o modelo nunca viu, preferencialmente com imagens próprias (do grupo).
3. **Relatório honesto sobre erros.** Mostre os erros reais: o modelo vai confundir nuvem, neblina, poeira e pôr do sol com fumaça. Matriz de confusão com esses casos vale mais do que prometer acurácia alta.
4. **Objetivo e conclusão** descrevem o uso como confirmação em campo hoje e monitoramento por câmera como próximo passo.

## Contrato com o resto do produto

`POST /visao/classificar` com uma imagem. Resposta:

```json
{
  "classe": "fumaca",
  "confianca": 0.87,
  "mensagem": "Possível fumaça detectada. Procure a defesa civil."
}
```

- `classe`: `fumaca`, `fogo` ou `nada`.
- Abaixo de um limiar de confiança (justifique o valor), responder com dúvida: "não foi possível confirmar; se houver perigo, procure a defesa civil".
- Não guardar a imagem (LGPD): processar e descartar. Sem rosto, placa ou dado pessoal no repositório.
- Se alguém do grupo conectar isso ao FogoCerto, o município vem do usuário, e o risco do dia vem de `site/public/data/risco_atual.json`.

## O que não fazer

- Não construir integração com câmeras, painel de monitoramento nem app móvel. Não pontua e coloca a entrega em risco.
- Não citar usuários, mercado, preço ou clientes que o grupo não validou.
- Não subir imagens grandes, modelos (`.pt`, `.onnx`) nem vídeos para o GitHub (o `.gitignore` já bloqueia). Guarde o modelo e os dados em outro lugar e documente como baixar.
- Não subir chaves, tokens ou dados pessoais.

## Estrutura da pasta (sugestão)

```
visao/
  README.md          como reproduzir, resultados, links
  notebooks/         treino e avaliação com as saídas salvas
  src/               código da API de classificação
  amostras/          poucas imagens de teste (leves)
```

## Prazos

Entrega final: 19/11/2026 às 23h55, no Teams da disciplina. Meta interna: 18/11. Trabalhe em uma branch curta (`visao/treino`, `visao/api`), abra pull request e peça 1 aprovação antes de juntar na `main`.
