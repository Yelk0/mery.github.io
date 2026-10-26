import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { amount, formatNumber, heads, numberLocale, signed, signedDays, signedPercent, signedPoints } from "../format"

export interface Words {
  t: (key: string, vars?: Record<string, string | number>) => string
  amount: (value: number | null, digits?: number) => string
  signed: (value: number | null, digits?: number) => string
  signedPercent: (value: number | null) => string
  signedPoints: (value: number | null) => string
  signedDays: (value: number | null) => string
  number: (value: number | null, digits?: number) => string
  heads: (value: number | null) => string
}

export function useWords(): Words {
  const { t, locale } = useI18n()
  const loc = computed(() => numberLocale(locale.value))
  const say = (key: string, vars?: Record<string, string | number>) =>
    vars === undefined ? t(key as "now") : t(key as "now", vars)
  return {
    t: say,
    amount: (value, digits = 1) => amount(value, digits, loc.value),
    signed: (value, digits = 1) => signed(value, digits, loc.value),
    signedPercent: (value) => signedPercent(value, loc.value),
    signedPoints: (value) => signedPoints(value, loc.value),
    signedDays: (value) => signedDays(value, loc.value, say("dayCompact")),
    number: (value, digits = 1) => (value === null ? "—" : formatNumber(value, digits, loc.value)),
    heads: (value) => heads(value, loc.value, say("million")),
  }
}
