import type { NivelRisco } from '../data/risco'

const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })

export function fmtNumero(v: number | null, sufixo = ''): string {
  return v === null ? 'sem dado' : `${numero.format(v)}${sufixo}`
}

/** "2026-11-03" -> "03/11/2026" (sem fuso: é só o dia). */
export function fmtData(iso: string, comAno = true): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!m) return iso
  return comAno ? `${m[3]}/${m[2]}/${m[1]}` : `${m[3]}/${m[2]}`
}

/** "2026-11-08T02:14:21.403011" -> "08/11/2026 às 02:14" (mostra o horário do arquivo, sem converter fuso). */
export function fmtDataHora(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso)
  if (!m) return iso || 'sem dado'
  return `${m[3]}/${m[2]}/${m[1]} às ${m[4]}:${m[5]}`
}

/**
 * Os fatores vêm do Databricks sem acento ("umidade minima de 39%").
 * Aqui só ajustamos a escrita para a tela; o conteúdo não muda.
 */
export function fatoresEmLista(fatores: string): string[] {
  return fatores
    .split(';')
    .map((f) => f.trim())
    .filter(Boolean)
    .map((f) =>
      f
        .replace(/\bminima\b/gi, 'mínima')
        .replace(/\bate\b/gi, 'até')
        .replace(/\bultimos\b/gi, 'últimos')
        .replace(/\bmunicipio\b/gi, 'município')
        .replace(/(\d)\s?C\b/g, '$1 °C')
        .replace(/^1 focos\b/, '1 foco')
        .replace(/^./, (c) => c.toUpperCase()),
    )
}

export const NIVEL: Record<NivelRisco, { rotulo: string; curto: string; barras: number }> = {
  baixo: { rotulo: 'Risco baixo', curto: 'Baixo', barras: 1 },
  medio: { rotulo: 'Risco médio', curto: 'Médio', barras: 2 },
  alto: { rotulo: 'Risco alto', curto: 'Alto', barras: 3 },
}

/** Pontuação máxima possível pela regra da camada Ouro (2+2+1+1+3). */
export const PONTOS_MAX = 9
