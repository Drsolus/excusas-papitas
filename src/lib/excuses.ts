export type Excuse = {
  id: string
  category: string
  text: string
  probability: number
  refs: string[]
}

export type ExcuseDataset = {
  meta: {
    title: string
    count: number
    probability_sum: number
    rule: string
    categories: string[]
    anime_refs: string[]
  }
  excuses: Excuse[]
}

const CATEGORY_LABELS: Record<string, string> = {
  dormir: 'sueño.exe',
  preparar: 'chamba_invisible',
  mente: 'buffer_mental',
  salir: 'irl_quest',
  contenido: 'schedule.patch',
  ridicula: 'glitch_absurdo',
  anime_madoka: 'madoka_ref',
  anime_villana: 'villainess_ref',
  anime_citrus: 'citrus_denied',
}

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category
}

/** Weighted random pick using each excuse's probability (assumes sum ≈ 1). */
export function pickExcuse(excuses: Excuse[]): Excuse {
  if (excuses.length === 0) {
    throw new Error('No hay excusas en el dataset')
  }

  const total = excuses.reduce((sum, item) => sum + item.probability, 0)
  let roll = Math.random() * (total || 1)

  for (const excuse of excuses) {
    roll -= excuse.probability
    if (roll <= 0) return excuse
  }

  return excuses[excuses.length - 1]!
}

export function formatProbability(probability: number): string {
  const pct = probability * 100
  if (pct >= 1) return `${pct.toFixed(2)}%`
  if (pct >= 0.1) return `${pct.toFixed(3)}%`
  return `${pct.toFixed(4)}%`
}
