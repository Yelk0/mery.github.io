export type NumberLocale = "es-ES" | "en-GB"

export function numberLocale(language: string): NumberLocale {
  return language === "en" ? "en-GB" : "es-ES"
}

export function formatNumber(value: number, digits: number, locale: NumberLocale): string {
  return value.toLocaleString(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function signed(value: number | null, digits: number, locale: NumberLocale): string {
  if (value === null) return "—"
  const body = formatNumber(Math.abs(value), digits, locale)
  return `${value >= 0 ? "+" : "-"}${body}`
}

export function signedPercent(value: number | null, locale: NumberLocale, digits = 1): string {
  if (value === null) return "—"
  return `${signed(value, digits, locale)}%`
}

export function amount(value: number | null, digits: number, locale: NumberLocale): string {
  if (value === null) return "—"
  return formatNumber(Math.abs(value), digits, locale)
}

export function signedDays(value: number | null, locale: NumberLocale, unit: string): string {
  if (value === null) return "—"
  return `${signed(value, 1, locale)} ${unit}`
}

export function heads(value: number | null, locale: NumberLocale, million: string): string {
  if (value === null) return "—"
  if (Math.abs(value) >= 1000000) return `${formatNumber(value / 1000000, 2, locale)} ${million}`
  return Math.round(value).toLocaleString(locale)
}

export function roundHalfUp(value: number, digits = 1): number {
  const factor = 10 ** digits
  const sign = value < 0 ? -1 : 1
  return (sign * Math.floor(Math.abs(value) * factor + 0.5 + 1e-8)) / factor
}

export function plainAmount(value: number, locale: NumberLocale): string {
  const rounded = roundHalfUp(Math.abs(value), 2)
  const text = String(rounded)
  const fraction = text.includes(".") ? (text.split(".")[1] ?? "").replace(/0$/, "") : ""
  return formatNumber(rounded, fraction.length, locale)
}

export function signedPoints(value: number | null, locale: NumberLocale): string {
  if (value === null) return "—"
  return `${signed(value, 1, locale)} pts`
}

export function millions(value: number | null, locale: NumberLocale, unit: string): string {
  if (value === null) return "—"
  return `${formatNumber(value / 1000, 0, locale)} ${unit}`
}

export function signedMillions(value: number | null, locale: NumberLocale, unit: string): string {
  if (value === null) return "—"
  const body = formatNumber(Math.abs(value) / 1000, 0, locale)
  return `${value >= 0 ? "+" : "-"}${body} ${unit}`
}

/** Above zero is ahead, below zero is behind, zero is level. */
export function tone(value: number | null): "faster" | "slower" | "similar" | "" {
  if (value === null) return ""
  if (value > 0) return "faster"
  if (value < 0) return "slower"
  return "similar"
}

/** A rise in a burden is behind. */
export function burden(value: number | null): "faster" | "slower" | "similar" | "" {
  if (value === null) return ""
  return tone(-value)
}

/** Paid to the European Union minus received. Above zero is ahead. */
export function euBalance(value: number | null): "faster" | "slower" | "" {
  if (value === null) return ""
  return value > 0 ? "faster" : "slower"
}

/** Received from the regions minus paid. Below zero is behind. */
export function communityBalance(value: number | null): "faster" | "slower" | "" {
  if (value === null) return ""
  return value < 0 ? "slower" : "faster"
}
