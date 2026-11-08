import type { ReactNode } from 'react'
import { AvisoLegal } from '../components/AvisoLegal'
import { BarrasNivel } from '../components/SeloNivel'
import { IconeChama, IconeChuva, IconeGota, IconeTermometro, IconeVento } from '../components/Icones'

// Regra da camada Ouro (ver bigdata/README.md, "Regra de risco").
const REGRAS: { icone: ReactNode; fator: string; faixas: { quando: string; pontos: number }[] }[] = [
  {
    icone: <IconeGota />,
    fator: 'Ar seco (umidade mínima do dia)',
    faixas: [
      { quando: 'abaixo de 30%', pontos: 2 },
      { quando: 'abaixo de 40%', pontos: 1 },
    ],
  },
  {
    icone: <IconeVento />,
    fator: 'Vento forte (máximo do dia)',
    faixas: [
      { quando: '30 km/h ou mais', pontos: 2 },
      { quando: '20 km/h ou mais', pontos: 1 },
    ],
  },
  {
    icone: <IconeChuva />,
    fator: 'Sem chuva',
    faixas: [{ quando: 'menos de 1 mm nos últimos 3 dias', pontos: 1 }],
  },
  {
    icone: <IconeTermometro />,
    fator: 'Calor',
    faixas: [{ quando: 'máxima de 35 °C ou mais', pontos: 1 }],
  },
  {
    icone: <IconeChama />,
    fator: 'Focos de calor no município no dia anterior',
    faixas: [
      { quando: '100 focos ou mais', pontos: 3 },
      { quando: '20 focos ou mais', pontos: 2 },
      { quando: 'pelo menos 1 foco', pontos: 1 },
    ],
  },
]

export function ComoCalculamos() {
  return (
    <>
      <h1 className="titulo-pagina" tabIndex={-1}>
        Como calculamos
      </h1>
      <p className="lead">
        O risco é uma <strong>soma de pontos</strong>, com regras abertas. Não é previsão de inteligência artificial:
        qualquer pessoa pode conferir a conta.
      </p>

      <section className="bloco" aria-labelledby="t-pontos">
        <h2 id="t-pontos">
          <span className="bloco__num">1</span> Cada sinal de perigo soma pontos
        </h2>
        <p>Todo dia, para cada município, olhamos cinco sinais. Em cada sinal conta só a faixa mais alta.</p>
        <ul className="regras">
          {REGRAS.map((r) => (
            <li key={r.fator} className="regra">
              <span className="regra__icone">{r.icone}</span>
              <div className="regra__corpo">
                <h3>{r.fator}</h3>
                <ul>
                  {r.faixas.map((f) => (
                    <li key={f.quando}>
                      <span>{f.quando}</span>
                      <strong>
                        +{f.pontos} {f.pontos === 1 ? 'ponto' : 'pontos'}
                      </strong>
                    </li>
                  ))}
                </ul>
              </div>
            </li>
          ))}
        </ul>
        <p className="nota">No máximo, um dia soma 9 pontos.</p>
      </section>

      <section className="bloco" aria-labelledby="t-nivel">
        <h2 id="t-nivel">
          <span className="bloco__num">2</span> A soma vira um nível
        </h2>
        <ul className="escala">
          <li className="escala__item escala__item--baixo">
            <BarrasNivel nivel="baixo" tamanho={26} />
            <strong>Baixo</strong>
            <span>0 a 2 pontos</span>
          </li>
          <li className="escala__item escala__item--medio">
            <BarrasNivel nivel="medio" tamanho={26} />
            <strong>Médio</strong>
            <span>3 a 4 pontos</span>
          </li>
          <li className="escala__item escala__item--alto">
            <BarrasNivel nivel="alto" tamanho={26} />
            <strong>Alto</strong>
            <span>5 pontos ou mais</span>
          </li>
        </ul>
        <p>
          Usamos os focos do <strong>dia anterior</strong>, nunca os do próprio dia. Assim dá para testar a regra com o
          histórico: conferir se os dias marcados como risco alto foram mesmo os que tiveram mais fogo.
        </p>
      </section>

      <section className="bloco" aria-labelledby="t-fontes">
        <h2 id="t-fontes">
          <span className="bloco__num">3</span> De onde vêm os dados
        </h2>
        <ul className="fontes">
          <li>
            <h3>
              <a href="https://terrabrasilis.dpi.inpe.br/queimadas/portal/" rel="noopener noreferrer" target="_blank">
                INPE · Programa Queimadas
              </a>
            </h3>
            <p>Focos de calor vistos por satélite, em dados abertos, todos os dias.</p>
          </li>
          <li>
            <h3>
              <a href="https://open-meteo.com/" rel="noopener noreferrer" target="_blank">
                Open-Meteo
              </a>
            </h3>
            <p>Umidade do ar, vento, chuva e temperatura, hora a hora, para cada município.</p>
          </li>
          <li>
            <h3>IBGE</h3>
            <p>Códigos e nomes oficiais dos 15 municípios do Pará acompanhados.</p>
          </li>
        </ul>
        <p className="nota">
          Antes de chegar aqui, os dados passam por limpeza e conferência (camadas Bronze, Prata e Ouro no Databricks).
          Foco de calor é um ponto quente visto do espaço: pode ser incêndio, queimada ou outra fonte de calor.
        </p>
      </section>

      <AvisoLegal />
    </>
  )
}
