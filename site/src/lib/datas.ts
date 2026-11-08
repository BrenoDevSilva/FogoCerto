/** Dia anterior a "AAAA-MM-DD", no mesmo formato. */
export function diaAnterior(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!m) return iso
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3] - 1))
  return d.toISOString().slice(0, 10)
}

/** Fuso em que o Big Data fecha o dia (a coleta roda às 10:30 de Brasília). */
const FUSO = 'America/Sao_Paulo'

/**
 * Data de hoje em São Paulo ("AAAA-MM-DD"), não a do aparelho: assim um celular com o fuso
 * errado, ou aberto de outro país, continua comparando com o mesmo dia do pipeline.
 */
export function hojeISO(agora = new Date()): string {
  // O locale en-CA formata como AAAA-MM-DD.
  return new Intl.DateTimeFormat('en-CA', { timeZone: FUSO, year: 'numeric', month: '2-digit', day: '2-digit' }).format(
    agora,
  )
}

/** Ontem em São Paulo ("AAAA-MM-DD"): o último dia fechado, que é o `data` esperado do arquivo. */
export function ontemISO(agora = new Date()): string {
  return diaAnterior(hojeISO(agora))
}

/**
 * Como a `data` do arquivo se compara com o calendário de hoje:
 * - `fechado`: é ontem, o último dia completo (o esperado, sem aviso);
 * - `antigo`: é mais velha que ontem (a atualização mais recente ainda não chegou);
 * - `futuro`: é depois de hoje, o que não pode acontecer (dado inválido).
 * Um dia igual a hoje é aceito como `fechado`: não é o esperado, mas também não é erro.
 */
export type SituacaoData = 'fechado' | 'antigo' | 'futuro'

export function situacaoData(data: string, agora = new Date()): SituacaoData {
  const dia = data.slice(0, 10)
  if (dia > hojeISO(agora)) return 'futuro'
  return dia >= ontemISO(agora) ? 'fechado' : 'antigo'
}
