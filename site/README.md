# FogoCerto · Site (MVP)

Tela que o cidadão usa: o risco de fogo de hoje no seu município, com os motivos explicados, para produtores rurais e defesa civil. Feita para celular simples e internet ruim.

O site é **nacional**: não há estado fixo no código. A cobertura é a que vier no JSON. Hoje são 15 municípios do Pará, o recorte inicial do Big Data; quando entrarem outros estados, o seletor passa a agrupar por estado, o Panorama ganha filtro por estado e os textos de cobertura se ajustam sozinhos.

**Integrantes:** ver [README principal](../README.md#integrantes).

## Telas

| Rota | Tela |
|---|---|
| `#/` | **Início**: escolha do município e cartão com nível (cor + texto + ícone), motivos, focos, umidade, vento, chuva, calor e hora da atualização |
| `#/panorama` | **Panorama**: todos os municípios acompanhados, do maior para o menor risco, com filtro por estado quando houver mais de um (toque abre o município no Início) |
| `#/como-calculamos` | **Como calculamos**: a regra de pontos em linguagem simples e as fontes |
| `#/assistente` | Pergunte ao assistente (GenAI): **em breve** |
| `#/foto` | Enviar foto de fumaça (Visão): **em breve** |

As rotas usam `#/`, então o site funciona em qualquer servidor estático sem configuração extra.

## Como rodar

Requer Node 20.19+ (ou 22.12+).

```bash
cd site
npm install
npm run dev        # http://localhost:5173
```

## Build (site estático)

```bash
npm run build      # gera site/dist/
npm run preview    # serve o dist/ em http://localhost:4173 para conferir
```

`dist/` é só HTML, CSS, JS, fontes e o JSON: qualquer servidor estático (nginx, Docker, GitHub Pages) serve. O build usa caminhos relativos (`base: './'`), então funciona também dentro de uma subpasta.

## De onde vêm os dados

O site lê **`public/data/risco_atual.json`**, o arquivo oficial gerado pelo Databricks (camada Ouro, visão `vw_risco_atual`, ver [`bigdata/`](../bigdata/)). Não há dado de exemplo.

- **Não edite o JSON à mão.** O time de Big Data o atualiza por pull request.
- Toda a leitura está em [`src/data/risco.ts`](src/data/risco.ts), função `getRiscoAtual()`. Para ligar a API `GET /risco?municipio_id=`, troque só esse módulo, mantendo o mesmo formato; as telas não mudam.
- Se a `data` do arquivo não for a de hoje, o site avisa "Dados de DD/MM". Se o arquivo não carregar, mostra uma mensagem clara com botão "Tentar de novo".
- Os `fatores` chegam sem acento ("umidade minima"); o site só ajusta a escrita na tela, sem mudar o conteúdo.
- O horário `atualizado_em` é mostrado como está no arquivo, sem conversão de fuso.

## Regras do produto

- O site **nunca autoriza queima**. Toda tela mostra: "O FogoCerto informa o risco. A autorização de queima é do órgão ambiental do seu estado." Em risco alto, recomenda não queimar e mostra Defesa Civil (199) e Bombeiros (193). O órgão estadual citado vem de `ORGAO_AMBIENTAL` em [`src/lib/estados.ts`](src/lib/estados.ts) (hoje só o Pará, conferido); estados fora da tabela recebem a orientação genérica. Ao incluir um estado novo nos dados, acrescente o órgão dele ali.
- Acessibilidade: nível sempre com texto e ícone de barras (não só cor), navegação por teclado com link "Pular para o conteúdo", foco visível, textos alternativos, fonte Atkinson Hyperlegible (feita para baixa visão), respeita "reduzir movimento".
- Leve: fontes servidas pelo próprio site (só alfabeto latino), sem CDN; ~55 kB de JS comprimido.
- Sem chave, senha ou dado pessoal no código. O único dado guardado no aparelho é o município escolhido (`localStorage`), para abrir direto nele na próxima visita.

## Estrutura

```
public/data/risco_atual.json   dado oficial (Big Data)
src/data/risco.ts              leitura e validação do dado (único ponto a trocar pela API)
src/lib/                       formatação de números, datas e fatores; nomes dos estados e órgãos ambientais
src/components/                medidor, selo de nível, ícones, aviso legal
src/pages/                     Inicio, Panorama, ComoCalculamos, EmBreve
src/App.tsx                    menu, rotas, carregamento e erro
src/styles.css                 estilos
```
