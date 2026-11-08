/**
 * Único ponto de leitura do risco de fogo.
 *
 * Hoje lê o arquivo oficial `public/data/risco_atual.json`, exportado pelo
 * Databricks (camada Ouro, visão `vw_risco_atual`). Quando a API existir,
 * basta trocar a URL abaixo por `GET /risco` (ou `/risco?municipio_id=`)
 * mantendo o mesmo formato: as telas não precisam mudar.
 */

import { situacaoData } from '../lib/datas'

export type NivelRisco = 'baixo' | 'medio' | 'alto'

export interface RiscoMunicipio {
  id_ibge: number
  nome: string
  uf: string
  /** Dia a que o risco se refere (AAAA-MM-DD). É o último dia fechado, ou seja, ontem. */
  data: string
  nivel_risco: NivelRisco
  pontos: number
  /** Motivos em texto, separados por ";". Pode vir vazio. */
  fatores: string
  focos_ontem: number
  umidade_min: number | null
  vento_max: number | null
  temp_max: number | null
  chuva_3d: number | null
  /** Posição do município (graus). Opcional: o Big Data ainda vai incluir no JSON. Sem isso, não há mapa. */
  lat: number | null
  lon: number | null
  /** Quando o dado foi gerado (AAAA-MM-DDTHH:MM:SS). */
  atualizado_em: string
}

const URL_RISCO = `${import.meta.env.BASE_URL}data/risco_atual.json`

const NIVEIS: readonly NivelRisco[] = ['baixo', 'medio', 'alto']

function numeroOuNulo(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

function validar(item: unknown): RiscoMunicipio | null {
  if (!item || typeof item !== 'object') return null
  const o = item as Record<string, unknown>
  if (typeof o.id_ibge !== 'number' || typeof o.nome !== 'string') return null
  if (!NIVEIS.includes(o.nivel_risco as NivelRisco)) return null
  if (typeof o.data !== 'string') return null
  return {
    id_ibge: o.id_ibge,
    nome: o.nome,
    uf: typeof o.uf === 'string' ? o.uf : '',
    data: o.data,
    nivel_risco: o.nivel_risco as NivelRisco,
    pontos: numeroOuNulo(o.pontos) ?? 0,
    fatores: typeof o.fatores === 'string' ? o.fatores : '',
    focos_ontem: numeroOuNulo(o.focos_ontem) ?? 0,
    umidade_min: numeroOuNulo(o.umidade_min),
    vento_max: numeroOuNulo(o.vento_max),
    temp_max: numeroOuNulo(o.temp_max),
    chuva_3d: numeroOuNulo(o.chuva_3d),
    lat: numeroOuNulo(o.lat),
    lon: numeroOuNulo(o.lon),
    atualizado_em: typeof o.atualizado_em === 'string' ? o.atualizado_em : '',
  }
}

/** O arquivo carregou, mas o conteúdo não serve (formato errado, vazio ou com data futura). */
export class ErroDado extends Error {}

export interface RiscoAtual {
  /** Municípios, do maior para o menor risco. */
  lista: RiscoMunicipio[]
  /** true quando não havia internet e o dado veio da última cópia salva no aparelho. */
  offline: boolean
}

/** Cabeçalho que o service worker (public/sw.js) põe na resposta servida do cache. */
const CABECALHO_OFFLINE = 'x-fogocerto-offline'

/** Lê o risco atual. Lança erro se não carregar (nem da rede, nem do cache). */
export async function getRiscoAtual(): Promise<RiscoAtual> {
  const resposta = await fetch(URL_RISCO, { cache: 'no-cache' })
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`)
  const offline = resposta.headers.get(CABECALHO_OFFLINE) === '1'
  const bruto: unknown = await resposta.json()
  if (!Array.isArray(bruto)) throw new ErroDado('Formato inesperado')
  const lidos = bruto.map(validar).filter((m): m is RiscoMunicipio => m !== null)
  // Data depois de hoje não existe: é dado inválido e não pode ser mostrado como se fosse risco.
  const lista = lidos.filter((m) => situacaoData(m.data) !== 'futuro')
  if (lista.length === 0) throw new ErroDado(lidos.length ? 'Data futura no arquivo' : 'Arquivo sem municípios')
  lista.sort((a, b) => b.pontos - a.pontos || b.focos_ontem - a.focos_ontem)
  return { lista, offline }
}
