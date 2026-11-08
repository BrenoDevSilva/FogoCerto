import type { NivelRisco, RiscoMunicipio } from '../data/risco'
import { SeloNivel } from '../components/SeloNivel'
import { IconeChama, IconeSeta } from '../components/Icones'
import { AvisoLegal } from '../components/AvisoLegal'
import { AvisoData } from '../components/AvisoData'
import { AvisoOffline } from '../components/AvisoOffline'
import { MapaPara } from '../components/MapaPara'
import { PONTOS_MAX, fmtData, fmtNumero } from '../lib/formato'

interface Props {
  lista: RiscoMunicipio[]
  offline: boolean
  onAbrir: (id: number) => void
}

const ORDEM: NivelRisco[] = ['alto', 'medio', 'baixo']
const PLURAL: Record<NivelRisco, string> = { alto: 'em risco alto', medio: 'em risco médio', baixo: 'em risco baixo' }

export function Panorama({ lista, offline, onAbrir }: Props) {
  const contagem = ORDEM.map((n) => ({ nivel: n, total: lista.filter((m) => m.nivel_risco === n).length }))
  const datas = [...new Set(lista.map((m) => m.data))]
  const dataRef = datas.length === 1 ? datas[0] : null
  // Se houver datas diferentes no arquivo, o aviso usa a mais antiga.
  const dataMaisAntiga = [...datas].sort()[0]

  return (
    <>
      <h1 className="titulo-pagina" tabIndex={-1}>
        Panorama
      </h1>
      <p className="lead">
        Os {lista.length} municípios do Pará acompanhados, do maior para o menor risco
        {dataRef ? <> em {fmtData(dataRef)}</> : null}.
      </p>

      {offline && <AvisoOffline />}

      <AvisoData data={dataMaisAntiga} />

      <ul className="resumo" aria-label="Resumo por nível">
        {contagem.map((c) => (
          <li key={c.nivel} className={`resumo__item resumo__item--${c.nivel}`}>
            <span className="resumo__numero">{c.total}</span>
            <span className="resumo__texto">{PLURAL[c.nivel]}</span>
          </li>
        ))}
      </ul>

      <MapaPara lista={lista} onAbrir={onAbrir} />

      <ol className="ranking">
        {lista.map((m, i) => (
          <li key={m.id_ibge}>
            <a
              href="#/"
              className={`ranking__linha ranking__linha--${m.nivel_risco}`}
              onClick={(e) => {
                e.preventDefault()
                onAbrir(m.id_ibge)
              }}
            >
              <span className="ranking__pos" aria-hidden="true">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="ranking__corpo">
                <span className="ranking__nome">{m.nome}</span>
                <span className="ranking__info">
                  <SeloNivel nivel={m.nivel_risco} curto />
                  <span className="ranking__focos">
                    <IconeChama width={15} height={15} />
                    {fmtNumero(m.focos_ontem)} {m.focos_ontem === 1 ? 'foco' : 'focos'} na véspera
                  </span>
                </span>
                <span className="ranking__barra" aria-hidden="true">
                  <span style={{ width: `${(Math.max(m.pontos, 0.25) / PONTOS_MAX) * 100}%` }} />
                </span>
              </span>
              <span className="ranking__pontos" aria-hidden="true">
                <strong>{m.pontos}</strong>
                <span>pts</span>
              </span>
              <IconeSeta className="ranking__seta" />
              <span className="visualmente-oculto">
                , {m.pontos} de {PONTOS_MAX} pontos. Ver detalhes.
              </span>
            </a>
          </li>
        ))}
      </ol>

      <AvisoLegal compacto />
    </>
  )
}
