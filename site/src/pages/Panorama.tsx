import { useId, useState } from 'react'
import type { NivelRisco, RiscoMunicipio } from '../data/risco'
import { listarEstados, nomeUF, ufsDaLista } from '../lib/estados'
import { SeloNivel } from '../components/SeloNivel'
import { IconeAlerta, IconeChama, IconeSeta } from '../components/Icones'
import { AvisoLegal } from '../components/AvisoLegal'
import { PONTOS_MAX, fmtData, fmtNumero, hojeISO } from '../lib/formato'

interface Props {
  lista: RiscoMunicipio[]
  onAbrir: (id: number) => void
}

const ORDEM: NivelRisco[] = ['alto', 'medio', 'baixo']
const PLURAL: Record<NivelRisco, string> = { alto: 'em risco alto', medio: 'em risco médio', baixo: 'em risco baixo' }

export function Panorama({ lista: todos, onAbrir }: Props) {
  const idFiltro = useId()
  const ufs = ufsDaLista(todos)
  const [uf, setUf] = useState('')
  const lista = uf ? todos.filter((m) => m.uf === uf) : todos
  const contagem = ORDEM.map((n) => ({ nivel: n, total: lista.filter((m) => m.nivel_risco === n).length }))
  const datas = [...new Set(lista.map((m) => m.data))]
  const dataRef = datas.length === 1 ? datas[0] : null
  const desatualizado = dataRef !== null && dataRef !== hojeISO()

  return (
    <>
      <h1 className="titulo-pagina" tabIndex={-1}>
        Panorama
      </h1>
      <p className="lead">
        Todos os {todos.length} municípios acompanhados ({listarEstados(ufs)}), do maior para o menor risco
        {dataRef ? <> em {fmtData(dataRef)}</> : null}.
      </p>

      {ufs.length > 1 && (
        <div className="filtro-uf">
          <label htmlFor={idFiltro}>Estado</label>
          <select id={idFiltro} value={uf} onChange={(e) => setUf(e.target.value)}>
            <option value="">Todos</option>
            {ufs.map((u) => (
              <option key={u} value={u}>
                {nomeUF(u)}
              </option>
            ))}
          </select>
        </div>
      )}

      {desatualizado && dataRef && (
        <p className="aviso-data" role="status">
          <IconeAlerta className="aviso-data__icone" />
          <span>
            <strong>Dados de {fmtData(dataRef, false)}.</strong> O cálculo de hoje ainda não chegou.
          </span>
        </p>
      )}

      <ul className="resumo" aria-label="Resumo por nível">
        {contagem.map((c) => (
          <li key={c.nivel} className={`resumo__item resumo__item--${c.nivel}`}>
            <span className="resumo__numero">{c.total}</span>
            <span className="resumo__texto">{PLURAL[c.nivel]}</span>
          </li>
        ))}
      </ul>

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
                <span className="ranking__nome">
                  {m.nome} <span className="ranking__uf">· {m.uf}</span>
                </span>
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
