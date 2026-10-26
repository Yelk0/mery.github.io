import type { IsoDate, Pace, TermVerdict } from "./common"

/** A person holding one office inside a cabinet. */
export interface OfficeHolder {
  name: string
  office: string
  startedOn: IsoDate
  endedOn: IsoDate | null
}

/** One calendar year inside a term, and whether it counted toward the score. */
export interface ScoreYear {
  year: number
  days: number
  counted: boolean
  /** Current-price growth of the region, in percent. */
  regionGrowth: number | null
  /** Current-price growth of Spain, in percent. */
  spainGrowth: number | null
  /** Region growth minus Spain growth. Null when the year is not counted. */
  excess: number | null
  /** Index of GDP per person. 100 is Spain in 2000. */
  index: number | null
  /** Region GDP as a percent of Spain's GDP. */
  shareOfCountry: number | null
}

/** The result of one term, before several terms are combined into a career score. */
export interface TermMeasure {
  countedYears: number
  firstYear: number | null
  lastYear: number | null
  result: number | null
  verdict: TermVerdict
  /** Pace of this term against Spain's real growth. */
  versusSpain: Pace | null
  peerRank: number | null
  peerCount: number | null
  averageRegionGrowth: number | null
  averageSpainGrowth: number | null
  excessGrowth: number | null
  /** Change in the current-price size of the economy, in percent. */
  outputChange: number | null
  /** Change in GDP per person relative to Spain, in index points. */
  indexChange: number | null
  /** Change in the region's share of Spain's GDP, in percentage points. */
  peopleChange: number | null
  shareBefore: number | null
  shareAfter: number | null
  indexBefore: number | null
  indexAfter: number | null
  populationBefore: number | null
  populationAfter: number | null
  /** Real growth of the region minus real growth of Spain, in percent. */
  realChange: number | null
  publicJobsChange: number | null
  privateJobsChange: number | null
  /** Debt as a percent of GDP. */
  debtBefore: number | null
  debtAfter: number | null
  debtChange: number | null
  /** Surgical waiting time, in days. */
  healthBefore: number | null
  healthAfter: number | null
  healthChange: number | null
  /** Early school leaving, in percent. */
  schoolsBefore: number | null
  schoolsAfter: number | null
  schoolsChange: number | null
  /** People waiting for a care plan, in percent of those entitled. */
  careBefore: number | null
  careAfter: number | null
  careChange: number | null
  healthSeriesBreak: boolean
  healthStartsOnBreak: boolean
  healthBreakOpenDays: number | null
  healthOldDays: number | null
}

/** One continuous time as president of one region. */
export interface Term {
  personSlug: string
  personName: string
  party: string
  regionSlug: string
  startedOn: IsoDate
  /** Null while the person is still in office. */
  endedOn: IsoDate | null
  cabinet: OfficeHolder[]
  years: ScoreYear[]
  /** Null when this term has no measured result of its own. */
  measure: TermMeasure | null
}
