import { useId, type ReactNode } from 'react'
import type { NivelRisco, RiscoMunicipio } from '../data/risco'
import { AvisoLegal } from '../components/AvisoLegal'
import { AvisoData } from '../components/AvisoData'
import { AvisoOffline } from '../components/AvisoOffline'
import { Medidor } from '../components/Medidor'
import { BarrasNivel } from '../components/SeloNivel'
import {
  IconeChama,
  IconeChuva,
  IconeGota,
  IconeRelogio,
  IconeTelefone,
  IconeTermometro,
  IconeVento,
} from '../components/Icones'
import { NIVEL, PONTOS_MAX, fatoresEmLista, fmtData, fmtDataHora, fmtNumero } from '../lib/formato'
import { diaAnterior } from '../lib/datas'

const ORIENTACAO: Record<NivelRisco, { titulo: string; texto: ReactNode }> = {
  alto: {
    titulo: 'Não faça queima.',
    texto: (
      <>
        O tempo e os focos por perto favorecem o fogo. Se vir fogo ou fumaça, procure a defesa civil:{' '}
        <a href="tel:199" className="tel">
          <IconeTelefone width={16} height={16} /> Defesa Civil 199
        </a>{' '}
        <a href="tel:193" className="tel">
          <IconeTelefone width={16} height={16} /> Bombeiros 193
        </a>
      </>
    ),
  },
  medio: {
    titulo: 'Evite queimar.',
    texto:
      'As condições pedem atenção. Qualquer queima só com autorização do órgão ambiental e com gente acompanhando o tempo todo.',
  },
  baixo: {
    titulo: 'Risco baixo, mas fique atento.',
    texto:
      'As condições do último dia ajudam pouco o fogo. Mesmo assim, queimar exige autorização do órgão ambiental, e o tempo pode mudar.',
  },
}

interface Props {
  lista: RiscoMunicipio[]
  offline: boolean
  selecionadoId: number
  onSelecionar: (id: number) => void
}

export function Inicio({ lista, offline, selecionadoId, onSelecionar }: Props) {
  const idSelect = useId()
  const m = lista.find((x) => x.id_ibge === selecionadoId) ?? lista[0]
  const fatores = fatoresEmLista(m.fatores)
  const orientacao = ORIENTACAO[m.nivel_risco]
  const ordemAlfabetica = [...lista].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))

  return (
    <>
      <h1 className="titulo-pagina" tabIndex={-1}>
        Risco de fogo <span className="titulo-pagina__destaque">mais recente</span>
      </h1>

      <div className="escolha">
        <label htmlFor={idSelect} className="escolha__rotulo">
          Seu município
        </label>
        <div className="escolha__campo">
          <select id={idSelect} value={m.id_ibge} onChange={(e) => onSelecionar(Number(e.target.value))}>
            {ordemAlfabetica.map((x) => (
              <option key={x.id_ibge} value={x.id_ibge}>
                {x.nome} ({x.uf})
              </option>
            ))}
          </select>
        </div>
      </div>

      {offline && <AvisoOffline />}

      <AvisoData data={m.data} />

      <article className={`cartao cartao--${m.nivel_risco}`} aria-labelledby="cartao-nivel">
        <header className="cartao__topo">
          <p className="cartao__local">
            {m.nome} <span>· {m.uf}</span>
          </p>
          <p className="cartao__dia">Risco para {fmtData(m.data)}</p>
        </header>

        <div className="cartao__nivel">
          <Medidor nivel={m.nivel_risco} pontos={m.pontos} />
          <div className="cartao__nivel-texto">
            <h2 id="cartao-nivel" className="cartao__rotulo">
              <BarrasNivel nivel={m.nivel_risco} tamanho={28} />
              {NIVEL[m.nivel_risco].rotulo}
            </h2>
            <p className="cartao__pontos">
              {m.pontos} de {PONTOS_MAX} pontos
            </p>
          </div>
        </div>

        <div className="cartao__orientacao">
          <p className="cartao__orientacao-titulo">{orientacao.titulo}</p>
          <p>{orientacao.texto}</p>
        </div>

        <section className="cartao__motivos" aria-labelledby="titulo-motivos">
          <h3 id="titulo-motivos">Por que este nível?</h3>
          {fatores.length > 0 ? (
            <ul>
              {fatores.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          ) : (
            <p>Nenhum fator de risco passou dos limites neste dia.</p>
          )}
        </section>

        <section aria-labelledby="titulo-medidas">
          <h3 id="titulo-medidas" className="visualmente-oculto">
            Medidas do dia
          </h3>
          <dl className="medidas">
            <Medida icone={<IconeChama />} nome={`Focos de calor em ${fmtData(diaAnterior(m.data), false)}`} valor={fmtNumero(m.focos_ontem)} />
            <Medida icone={<IconeGota />} nome="Umidade mínima" valor={fmtNumero(m.umidade_min, '%')} />
            <Medida icone={<IconeVento />} nome="Vento máximo" valor={fmtNumero(m.vento_max, ' km/h')} />
            <Medida icone={<IconeChuva />} nome="Chuva em 3 dias" valor={fmtNumero(m.chuva_3d, ' mm')} />
            <Medida icone={<IconeTermometro />} nome="Temperatura máxima" valor={fmtNumero(m.temp_max, ' °C')} />
          </dl>
        </section>

        <p className="cartao__atualizado">
          <IconeRelogio width={18} height={18} />
          Atualizado em {fmtDataHora(m.atualizado_em)}
        </p>
      </article>

      <AvisoLegal />
    </>
  )
}

function Medida({ icone, nome, valor }: { icone: ReactNode; nome: string; valor: string }) {
  return (
    <div className="medida">
      <dt>
        <span className="medida__icone">{icone}</span>
        {nome}
      </dt>
      <dd>{valor}</dd>
    </div>
  )
}
