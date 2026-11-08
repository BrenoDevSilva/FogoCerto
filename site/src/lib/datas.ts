/** Dia anterior a "AAAA-MM-DD", no mesmo formato. */
export function diaAnterior(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!m) return iso
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3] - 1))
  return d.toISOString().slice(0, 10)
}
