/**
 * Único ponto de leitura do risco de fogo.
 *
 * Hoje lê o arquivo oficial `public/data/risco_atual.json`, exportado pelo
 * Databricks (camada Ouro, visão `vw_risco_atual`). Quando a API existir,
 * basta trocar a URL abaixo por `GET /risco` (ou `/risco?municipio_id=`)
 * mantendo o mesmo formato: as telas não precisam mudar.
 */

export type NivelRisco = 'baixo' | 'medio' | 'alto'

export interface RiscoMunicipio {
  id_ibge: number
  nome: string
  uf: string
  /** Dia a que o risco se refere (AAAA-MM-DD). Pode não ser hoje. */
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
    atualizado_em: typeof o.atualizado_em === 'string' ? o.atualizado_em : '',
  }
}

/** Lista de municípios, do maior para o menor risco. Lança erro se não carregar. */
export async function getRiscoAtual(): Promise<RiscoMunicipio[]> {
  const resposta = await fetch(URL_RISCO, { cache: 'no-cache' })
  if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`)
  const bruto: unknown = await resposta.json()
  if (!Array.isArray(bruto)) throw new Error('Formato inesperado')
  const lista = bruto.map(validar).filter((m): m is RiscoMunicipio => m !== null)
  if (lista.length === 0) throw new Error('Arquivo sem municípios')
  return lista.sort((a, b) => b.pontos - a.pontos || b.focos_ontem - a.focos_ontem)
}
