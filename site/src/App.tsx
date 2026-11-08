import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { getRiscoAtual, type RiscoMunicipio } from './data/risco'
import { Inicio } from './pages/Inicio'
import { Panorama } from './pages/Panorama'
import { ComoCalculamos } from './pages/ComoCalculamos'
import { EmBreve } from './pages/EmBreve'
import { AvisoLegal } from './components/AvisoLegal'
import {
  IconeBalao,
  IconeCamera,
  IconeChama,
  IconeInicio,
  IconeLista,
  IconeRecarregar,
  IconeRegua,
} from './components/Icones'

type Rota = 'inicio' | 'panorama' | 'como-calculamos' | 'assistente' | 'foto'

const MENU: { rota: Rota; rotulo: string; curto: string; icone: ReactNode }[] = [
  { rota: 'inicio', rotulo: 'Início', curto: 'Início', icone: <IconeInicio /> },
  { rota: 'panorama', rotulo: 'Panorama', curto: 'Panorama', icone: <IconeLista /> },
  { rota: 'como-calculamos', rotulo: 'Como calculamos', curto: 'Cálculo', icone: <IconeRegua /> },
  { rota: 'assistente', rotulo: 'Assistente', curto: 'Assistente', icone: <IconeBalao /> },
  { rota: 'foto', rotulo: 'Enviar foto', curto: 'Foto', icone: <IconeCamera /> },
]

const TITULOS: Record<Rota, string> = {
  inicio: 'Risco de fogo hoje',
  panorama: 'Panorama',
  'como-calculamos': 'Como calculamos',
  assistente: 'Pergunte ao assistente',
  foto: 'Enviar foto de fumaça',
}

// Rotas por "#/": funcionam em qualquer servidor estático, sem configuração extra.
function lerRota(): Rota {
  const r = window.location.hash.replace(/^#\/?/, '').split(/[?/]/)[0]
  return (MENU.some((m) => m.rota === r) ? r : 'inicio') as Rota
}

function hrefDe(rota: Rota) {
  return rota === 'inicio' ? '#/' : `#/${rota}`
}

const CHAVE_MUNICIPIO = 'fogocerto:municipio'

function lerMunicipioSalvo(): number | null {
  try {
    const v = Number(localStorage.getItem(CHAVE_MUNICIPIO))
    return Number.isFinite(v) && v > 0 ? v : null
  } catch {
    return null
  }
}

function salvarMunicipio(id: number) {
  try {
    localStorage.setItem(CHAVE_MUNICIPIO, String(id))
  } catch {
    /* modo privado: segue sem lembrar */
  }
}

type Estado =
  | { tipo: 'carregando' }
  | { tipo: 'erro' }
  | { tipo: 'ok'; lista: RiscoMunicipio[] }

export default function App() {
  const [rota, setRota] = useState<Rota>(lerRota)
  const [estado, setEstado] = useState<Estado>({ tipo: 'carregando' })
  const [selecionado, setSelecionado] = useState<number | null>(lerMunicipioSalvo)
  const primeiraRender = useRef(true)

  const carregar = useCallback(() => {
    setEstado({ tipo: 'carregando' })
    getRiscoAtual()
      .then((lista) => setEstado({ tipo: 'ok', lista }))
      .catch(() => setEstado({ tipo: 'erro' }))
  }, [])

  useEffect(carregar, [carregar])

  useEffect(() => {
    const aoMudar = () => setRota(lerRota())
    window.addEventListener('hashchange', aoMudar)
    return () => window.removeEventListener('hashchange', aoMudar)
  }, [])

  // A cada troca de tela: título da aba, topo da página e foco no título (leitor de tela).
  useEffect(() => {
    document.title = `${TITULOS[rota]} · FogoCerto`
    if (primeiraRender.current) {
      primeiraRender.current = false
      return
    }
    window.scrollTo(0, 0)
    document.querySelector<HTMLElement>('main h1')?.focus()
  }, [rota])

  const escolher = (id: number) => {
    setSelecionado(id)
    salvarMunicipio(id)
  }

  const abrirMunicipio = (id: number) => {
    escolher(id)
    window.location.hash = '#/'
  }

  let conteudo: ReactNode
  if (rota === 'como-calculamos') {
    conteudo = <ComoCalculamos />
  } else if (rota === 'assistente') {
    conteudo = (
      <EmBreve
        titulo="Pergunte ao assistente"
        icone={<IconeBalao width={40} height={40} />}
        descricao={
          <p>
            Em breve você vai poder perguntar, com suas palavras, sobre queima controlada e a lei. O assistente responde
            citando a fonte, avisa quando não sabe e sempre indica o órgão ambiental. Ele não dá parecer jurídico.
          </p>
        }
        previa={
          <div className="previa-chat">
            <span className="previa-chat__balao previa-chat__balao--eu">Preciso de autorização para queimar o pasto?</span>
            <span className="previa-chat__balao">Sim. A Lei 14.944/2024 diz que…</span>
            <span className="previa-chat__campo">Escreva sua pergunta</span>
          </div>
        }
      />
    )
  } else if (rota === 'foto') {
    conteudo = (
      <EmBreve
        titulo="Enviar foto de fumaça"
        icone={<IconeCamera width={40} height={40} />}
        descricao={
          <p>
            Em breve você vai poder tirar uma foto de fumaça ou fogo, e o FogoCerto vai dizer se parece mesmo fogo. A
            foto não será guardada. Em caso de fogo, ligue já para a Defesa Civil (199) ou os Bombeiros (193).
          </p>
        }
        previa={
          <div className="previa-foto">
            <IconeCamera width={32} height={32} />
            <span>Tirar ou escolher foto</span>
          </div>
        }
      />
    )
  } else if (estado.tipo === 'carregando') {
    conteudo = (
      <div className="estado" role="status" aria-live="polite">
        <span className="estado__chama" aria-hidden="true">
          <IconeChama width={40} height={40} />
        </span>
        <p>Carregando o risco de hoje…</p>
      </div>
    )
  } else if (estado.tipo === 'erro') {
    conteudo = (
      <div className="estado estado--erro" role="alert">
        <h1 className="titulo-pagina" tabIndex={-1}>
          Não foi possível carregar o risco
        </h1>
        <p>Pode ser a internet fraca ou o sistema fora do ar. Confira sua conexão e tente de novo em instantes.</p>
        <button type="button" className="botao" onClick={carregar}>
          <IconeRecarregar width={20} height={20} /> Tentar de novo
        </button>
        <p className="estado__dica">
          Em caso de fogo, não espere: ligue para a Defesa Civil (<a href="tel:199">199</a>) ou os Bombeiros (
          <a href="tel:193">193</a>).
        </p>
      </div>
    )
  } else if (rota === 'panorama') {
    conteudo = <Panorama lista={estado.lista} onAbrir={abrirMunicipio} />
  } else {
    conteudo = (
      <Inicio lista={estado.lista} selecionadoId={selecionado ?? estado.lista[0].id_ibge} onSelecionar={escolher} />
    )
  }

  return (
    <>
      <a href="#conteudo" className="pular" onClick={(e) => {
        e.preventDefault()
        document.getElementById('conteudo')?.focus()
      }}>
        Pular para o conteúdo
      </a>

      <header className="topo">
        <div className="topo__dentro">
          <a href="#/" className="marca" aria-label="FogoCerto, página inicial">
            <span className="marca__icone" aria-hidden="true">
              <IconeChama width={22} height={22} />
            </span>
            <span className="marca__nome">
              Fogo<b>Certo</b>
            </span>
          </a>
          <p className="topo__lema">Risco de fogo diário · Pará</p>
        </div>
        <nav className="menu" aria-label="Principal">
          <ul>
            {MENU.map((m) => (
              <li key={m.rota}>
                <a href={hrefDe(m.rota)} aria-current={rota === m.rota ? 'page' : undefined} className="menu__item">
                  {m.icone}
                  <span className="menu__longo">{m.rotulo}</span>
                  <span className="menu__curto">{m.curto}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <main id="conteudo" className="conteudo" tabIndex={-1}>
        {conteudo}
      </main>

      <footer className="rodape">
        <AvisoLegal compacto />
        <p>
          FogoCerto · Global Solution FIAP 2026 · dados abertos do INPE e do Open-Meteo.{' '}
          <a href={hrefDe('como-calculamos')}>Como calculamos</a>
        </p>
      </footer>
    </>
  )
}
