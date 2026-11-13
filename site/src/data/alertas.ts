/**
 * Alertas enviados pela automação (RPA, pasta `rpa/`).
 *
 * O robô lê o mesmo `risco_atual.json` que o site, decide quem avisar, envia por
 * Telegram ou e-mail e publica aqui o que fez (sem nenhum contato pessoal). O site
 * mostra no cartão do município que os assinantes já foram avisados.
 * É informação complementar: se o arquivo faltar ou vier quebrado, nada aparece.
 */

export interface AlertaEnviado {
  id_ibge: number
  /** Dia do dado que gerou o alerta (AAAA-MM-DD). */
  data_dado: string
  motivo: string
  /** Quando o alerta saiu (AAAA-MM-DDTHH:MM:SS-03:00). */
  enviado_em: string
  assinantes_avisados: number
  /** true quando a automação rodou em modo de teste, sem envio real. */
  simulado: boolean
}

const URL_ALERTAS = `${import.meta.env.BASE_URL}data/alertas.json`

function validar(item: unknown): AlertaEnviado | null {
  if (!item || typeof item !== 'object') return null
  const o = item as Record<string, unknown>
  if (typeof o.id_ibge !== 'number' || typeof o.data_dado !== 'string' || typeof o.enviado_em !== 'string') return null
  return {
    id_ibge: o.id_ibge,
    data_dado: o.data_dado,
    motivo: typeof o.motivo === 'string' ? o.motivo : '',
    enviado_em: o.enviado_em,
    assinantes_avisados: typeof o.assinantes_avisados === 'number' ? o.assinantes_avisados : 0,
    simulado: o.simulado === true,
  }
}

export async function getAlertas(): Promise<AlertaEnviado[]> {
  try {
    const resposta = await fetch(URL_ALERTAS, { cache: 'no-cache' })
    if (!resposta.ok) return []
    const bruto: unknown = await resposta.json()
    const lista = (bruto as { alertas?: unknown })?.alertas
    if (!Array.isArray(lista)) return []
    return lista.map(validar).filter((a): a is AlertaEnviado => a !== null)
  } catch {
    return []
  }
}

/** Alerta mais recente do município para o mesmo dia de dado que o cartão mostra. */
export function alertaDoDia(lista: AlertaEnviado[], idIbge: number, data: string): AlertaEnviado | undefined {
  return lista
    .filter((a) => a.id_ibge === idIbge && a.data_dado === data.slice(0, 10))
    .sort((a, b) => b.enviado_em.localeCompare(a.enviado_em))[0]
}
