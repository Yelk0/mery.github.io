import type { Law, Term, VolumePoint, YearlyEconomy } from "./domain"

export interface ChartLabel {
  x: number
  year: number
}

export interface ShareBand {
  x: number
  width: number
  tone: "ahead" | "mid" | "behind"
}

export interface SharePlot {
  width: number
  height: number
  line: string
  labels: ChartLabel[]
  top: string
  bottom: string
  bands: ShareBand[]
}

export interface LawDot {
  id: string
  title: string
  x: number
  anchor: number
  lane: number
}

export interface VolumePlot {
  width: number
  height: number
  line: string
  labels: ChartLabel[]
  top: string
  bottom: string
  baseline: number | null
  dots: LawDot[]
  room: number
}

export function sharePlot(start: number, end: number, economy: YearlyEconomy[], terms: Term[]): SharePlot | null {
  const byYear = new Map(economy.map((year) => [year.year, year.shareOfCountry]))
  const years = range(start, end)
  const values = years.map((year) => byYear.get(year) ?? null)
  const known = values.filter((value): value is number => value !== null)
  if (!known.length || years.length < 2) return null
  const min = Math.min(...known)
  const max = Math.max(...known)
  const pad = Math.max((max - min) * 0.35, min * 0.08, 0.05)
  const low = Math.max(0, min - pad)
  const high = max + pad
  const width = 760
  const height = 240
  const left = 52
  const right = 44
  const top = 16
  const bottom = 28
  const plotW = width - left - right
  const plotH = height - top - bottom
  const xOf = (index: number) => left + (plotW * index) / (years.length - 1)
  const yOf = (value: number) => top + (plotH * (high - value)) / (high - low)
  const owner = new Map<number, { days: number; tone: ShareBand["tone"] }>()
  for (const term of terms) {
    for (const year of term.years) {
      if (!year.counted || year.excess === null) continue
      const current = owner.get(year.year)
      if (current && year.days <= current.days) continue
      const tone = year.excess > 0 ? "ahead" : year.excess < 0 ? "behind" : "mid"
      owner.set(year.year, { days: year.days, tone })
    }
  }
  const bandWidth = plotW / (years.length - 1)
  const bands = years.flatMap((year, index) => {
    const held = owner.get(year)
    if (!held) return []
    return [{ x: xOf(index) - bandWidth / 2, width: bandWidth, tone: held.tone }]
  })
  return {
    width,
    height,
    line: values.flatMap((value, index) => (value === null ? [] : [`${xOf(index).toFixed(1)},${yOf(value).toFixed(1)}`])).join(" "),
    labels: years.filter((year) => year % 5 === 0).map((year) => ({ x: xOf(years.indexOf(year)), year })),
    top: `${max.toFixed(2)}%`,
    bottom: `${min.toFixed(2)}%`,
    bands,
  }
}

export function volumePlot(points: VolumePoint[], laws: Law[]): VolumePlot | null {
  const known = points.flatMap((point) => (point.level === null ? [] : [point.level]))
  if (!known.length || points.length < 2) return null
  const min = Math.min(...known)
  const max = Math.max(...known)
  const pad = Math.max((max - min) * 0.28, 1)
  const low = min - pad
  const high = max + pad
  const width = 760
  const height = 280
  const left = 46
  const right = 16
  const top = 18
  const bottom = 28
  const plotW = width - left - right
  const plotH = height - top - bottom
  const xOf = (index: number) => left + (plotW * index) / (points.length - 1)
  const yOf = (value: number) => top + (plotH * (high - value)) / (high - low)
  const spain = yOf(100)
  const layouts = laws.flatMap((law) => {
    const index = points.findIndex((point) => point.year === law.year)
    const point = points[index]
    if (!point || point.level === null) return []
    return [{ law, x: (xOf(index) / width) * 100, y: (yOf(point.level) / height) * 100 }]
  })
  const parent = layouts.map((_, index) => index)
  const find = (index: number): number => {
    const current = parent[index]
    if (current === undefined || current === index) return index
    const root = find(current)
    parent[index] = root
    return root
  }
  for (let i = 0; i < layouts.length; i += 1) {
    for (let j = i + 1; j < layouts.length; j += 1) {
      const leftLaw = layouts[i]
      const rightLaw = layouts[j]
      if (leftLaw && rightLaw && Math.abs(leftLaw.law.year - rightLaw.law.year) <= 3) parent[find(i)] = find(j)
    }
  }
  const groups = new Map<number, typeof layouts>()
  layouts.forEach((item, index) => {
    const key = find(index)
    const group = groups.get(key) ?? []
    group.push(item)
    groups.set(key, group)
  })
  const dots: LawDot[] = []
  let maxLane = 0
  for (const group of groups.values()) {
    const anchor = Math.min(...group.map((item) => item.y))
    group.forEach((item, lane) => {
      dots.push({ id: item.law.id, title: item.law.title, x: item.x, anchor, lane })
      maxLane = Math.max(maxLane, lane)
    })
  }
  return {
    width,
    height,
    line: points.flatMap((point, index) => (point.level === null ? [] : [`${xOf(index).toFixed(1)},${yOf(point.level).toFixed(1)}`])).join(" "),
    labels: points.filter((point) => point.year % 5 === 0).map((point) => ({ x: xOf(points.indexOf(point)), year: point.year })),
    top: max.toFixed(0),
    bottom: min.toFixed(0),
    baseline: spain >= top && spain <= top + plotH ? spain : null,
    dots,
    room: maxLane ? maxLane * 46 + 22 : 0,
  }
}

function range(start: number, end: number): number[] {
  const years = []
  for (let year = start; year <= end; year += 1) years.push(year)
  return years
}
