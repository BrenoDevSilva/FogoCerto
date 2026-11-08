import type { RiscoMunicipio } from '../data/risco'

/** Nome de cada estado pela sigla (UF). */
export const NOME_UF: Record<string, string> = {
  AC: 'Acre',
  AL: 'Alagoas',
  AP: 'Amapá',
  AM: 'Amazonas',
  BA: 'Bahia',
  CE: 'Ceará',
  DF: 'Distrito Federal',
  ES: 'Espírito Santo',
  GO: 'Goiás',
  MA: 'Maranhão',
  MT: 'Mato Grosso',
  MS: 'Mato Grosso do Sul',
  MG: 'Minas Gerais',
  PA: 'Pará',
  PB: 'Paraíba',
  PR: 'Paraná',
  PE: 'Pernambuco',
  PI: 'Piauí',
  RJ: 'Rio de Janeiro',
  RN: 'Rio Grande do Norte',
  RS: 'Rio Grande do Sul',
  RO: 'Rondônia',
  RR: 'Roraima',
  SC: 'Santa Catarina',
  SP: 'São Paulo',
  SE: 'Sergipe',
  TO: 'Tocantins',
}

export function nomeUF(uf: string): string {
  return NOME_UF[uf] ?? uf
}

/** Siglas dos estados presentes nos dados, em ordem alfabética do nome. */
export function ufsDaLista(lista: RiscoMunicipio[]): string[] {
  return [...new Set(lista.map((m) => m.uf).filter(Boolean))].sort((a, b) =>
    nomeUF(a).localeCompare(nomeUF(b), 'pt-BR'),
  )
}

/** "Pará", "Pará e Tocantins", "Mato Grosso, Pará e Tocantins". */
export function listarEstados(ufs: string[]): string {
  const nomes = ufs.map(nomeUF)
  if (nomes.length <= 1) return nomes[0] ?? ''
  return `${nomes.slice(0, -1).join(', ')} e ${nomes[nomes.length - 1]}`
}

/**
 * Órgão estadual que autoriza queima, quando já conferido pelo time.
 * Estados fora da tabela recebem a orientação genérica.
 */
export const ORGAO_AMBIENTAL: Record<string, string> = {
  PA: 'a SEMAS (Secretaria de Meio Ambiente e Sustentabilidade do Pará)',
}
