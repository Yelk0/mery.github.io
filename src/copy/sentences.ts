import type { Score, Sources, Term, TermMeasure } from "../domain"
import type { Words } from "./words"

export function stateRun(slug: string): boolean {
  return slug === "ceuta" || slug === "melilla"
}

export function period(term: { startedOn: string; endedOn: string | null }, inOffice: string): string {
  return `${term.startedOn} – ${term.endedOn || inOffice}`
}

export function spellYears(term: Term, now: string): string {
  const end = term.endedOn ? term.endedOn.slice(0, 4) : now
  return `${term.startedOn.slice(0, 4)}–${end}`
}

export function scoreSentence(score: Score, words: Words): string {
  if (score.result === null) return words.t("scoreNeedsBoth")
  const real = score.realChange === null
    ? words.t("realMissingRecord")
    : words.t(score.realChange >= 0 ? "realUp" : "realDown", { n: words.amount(score.realChange) })
  let debt = words.t("debtFlat")
  if ((score.debtChange ?? 0) > 0) debt = words.t("debtRose", { n: words.amount(score.debtChange) })
  else if ((score.debtChange ?? 0) < 0) debt = words.t("debtFell", { n: words.amount(score.debtChange) })
  return `${real} ${debt}`
}

export function pictureSentence(score: Score, words: Words): string {
  return [
    moved(score.outputChange, "pricesUp", "pricesDown", "pricesMissing", words),
    moved(score.publicJobsChange, "publicUp", "publicDown", "publicMissing", words),
    moved(score.privateJobsChange, "privateUp", "privateDown", "privateMissing", words),
    words.t("besideScore"),
  ].join(" ")
}

export function servicesSentence(score: Score, regionSlug: string, sources: Sources, words: Words): string {
  if (stateRun(regionSlug)) return words.t("stateBlank")
  return [
    serviceLine(score, "health", "healthName", "days", sources.healthDaysPerPoint, words.signedDays, "tenDays", words),
    breakSentence(score, sources, words),
    serviceLine(score, "schools", "schoolsName", "points", 1, words.signedPoints, "", words),
    serviceLine(score, "care", "careName", "points", 1, words.signedPoints, "", words),
  ].filter(Boolean).join(" ")
}

export function peopleSentence(score: Score, words: Words): string {
  return [
    score.indexChange === null ? "" : words.t(score.indexChange >= 0 ? "indexUp" : "indexDown", { n: words.amount(score.indexChange) }),
    score.peopleChange === null ? "" : words.t(score.peopleChange >= 0 ? "peopleUp" : "peopleDown", { n: words.amount(score.peopleChange) }),
    words.t("peopleHelp"),
  ].filter(Boolean).join(" ")
}

export function spellBody(term: Term, regionSlug: string, sources: Sources, words: Words): string {
  const measure = term.measure
  if (!measure || measure.outputChange === null) return words.t("spellNoYear", { period: period(term, words.t("inOffice")) })
  return words.t(measure.outputChange >= 0 ? "spellUp" : "spellDown", {
    period: period(term, words.t("inOffice")),
    n: words.amount(measure.outputChange),
    shareBefore: words.number(measure.shareBefore, 2),
    shareAfter: words.number(measure.shareAfter, 2),
    indexBefore: words.number(measure.indexBefore),
    indexAfter: words.number(measure.indexAfter),
    indexChange: words.signed(measure.indexChange),
    popBefore: words.heads(measure.populationBefore),
    popAfter: words.heads(measure.populationAfter),
    people: words.signedPercent(measure.peopleChange),
    extras: spellExtras(measure, regionSlug, sources, words),
  })
}

function spellExtras(measure: TermMeasure, regionSlug: string, sources: Sources, words: Words): string {
  const real = measure.realChange === null
    ? words.t("realMissingSpell")
    : words.t(measure.realChange >= 0 ? "realUp" : "realDown", { n: words.amount(measure.realChange) })
  const jobs = measure.publicJobsChange !== null || measure.privateJobsChange !== null
    ? words.t("jobsSpell", { public: words.signedPercent(measure.publicJobsChange), private: words.signedPercent(measure.privateJobsChange) })
    : words.t("jobsNoSpell", { year: sources.jobsFirstYear })
  const debt = measure.debtChange === null
    ? words.t("debtNoSpell")
    : words.t("debtWent", { before: words.number(measure.debtBefore), after: words.number(measure.debtAfter), change: words.signed(measure.debtChange) })
  const services = stateRun(regionSlug) ? words.t("stateSpell") : [
    measure.healthChange !== null
      ? words.t("healthWent", {
        before: words.number(measure.healthBefore, 0),
        after: words.number(measure.healthAfter, 0),
        change: words.signedDays(measure.healthChange),
        extra: breakSentence(measure, sources, words),
      })
      : measure.healthSeriesBreak
        ? words.t("healthCross", { year: sources.healthBreakYear })
        : words.t("healthNoSpell", { year: sources.healthFirstYear }),
    measure.schoolsChange !== null
      ? words.t("schoolsWent", {
        before: words.number(measure.schoolsBefore),
        after: words.number(measure.schoolsAfter),
        change: words.signedPoints(measure.schoolsChange),
      })
      : words.t("schoolsNoSpell"),
    measure.careChange !== null
      ? words.t("careWent", {
        before: words.number(measure.careBefore),
        after: words.number(measure.careAfter),
        change: words.signedPoints(measure.careChange),
      })
      : words.t("careNoSpell", { year: sources.careFirstYear }),
  ].join(" ")
  const result = measure.result === null ? "" : words.t("spellEconomy", { n: words.signed(measure.result) })
  return `${real} ${jobs} ${debt} ${services}${result}`
}

function breakSentence(info: { healthStartsOnBreak: boolean; healthBreakOpenDays: number | null; healthOldDays: number | null }, sources: Sources, words: Words): string {
  if (!info.healthStartsOnBreak) return ""
  const opened = info.healthBreakOpenDays === null
    ? words.t("breakRevised")
    : words.t("breakOpened", { n: words.number(info.healthBreakOpenDays, 0) })
  const before = info.healthOldDays === null ? "" : words.t("breakBefore", { n: words.number(info.healthOldDays, 0) })
  return words.t("breakStart", { year: sources.healthBreakYear, opened, before })
}

function serviceLine(
  score: Score,
  name: "health" | "schools" | "care",
  nameKey: string,
  kind: "days" | "points",
  perPoint: number,
  format: (value: number | null) => string,
  scaleKey: string,
  words: Words,
): string {
  const change = score[name]
  if (change.used === null) return words.t("serviceNoFill", { label: words.t(nameKey) })
  const scale = scaleKey ? `${words.t(scaleKey)} ` : ""
  const effect = effectSentence(change.used, perPoint, words)
  if (change.filled) return `${words.t(`${name}Filled`, { value: format(change.used) })} ${scale}${effect}`
  return `${serviceMove(nameKey, change.measured, kind, words)} ${scale}${effect}`
}

function serviceMove(nameKey: string, value: number | null, kind: "days" | "points", words: Words): string {
  const label = words.t(nameKey)
  if (value === null || value === 0) return words.t(kind === "days" ? "serviceFlatDays" : "serviceFlatPoints", { label })
  const key = value > 0
    ? (kind === "days" ? "serviceRoseDays" : "serviceRosePoints")
    : (kind === "days" ? "serviceFellDays" : "serviceFellPoints")
  return words.t(key, { label, n: words.amount(value) })
}

function effectSentence(used: number, perPoint: number, words: Words): string {
  const points = used / perPoint
  if (points > 0) return words.t("effectOff", { n: words.amount(points) })
  if (points < 0) return words.t("effectOn", { n: words.amount(-points) })
  return words.t("effectStill")
}

function moved(value: number | null, up: string, down: string, missing: string, words: Words): string {
  if (value === null) return words.t(missing)
  return words.t(value >= 0 ? up : down, { n: words.amount(value) })
}
