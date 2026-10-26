/**
 * What changed between the December before a term and the December it ended.
 * `measured` is the published change. `used` is the value that entered the
 * score after a missing service figure was replaced by the worst measured one.
 */
export interface ServiceChange {
  measured: number | null
  used: number | null
  filled: boolean
}

/**
 * The career result shown on the presidents list.
 * A person with several terms has one score that combines them.
 * `result` is null when the career is too short or the region has no debt series.
 */
export interface Score {
  result: number | null
  countedYears: number
  eligible: boolean
  rank: number | null
  rankedCount: number | null
  /** Change in the current-price size of the economy, in percent. */
  outputChange: number | null
  /** Real growth against Spain, in percent. */
  realChange: number | null
  /** Change in GDP per person relative to Spain, in index points. */
  indexChange: number | null
  /** Change in the region's share of Spain, in percentage points. */
  peopleChange: number | null
  /** Change in public and private employment, in percent. */
  publicJobsChange: number | null
  privateJobsChange: number | null
  /** Change in debt as a percent of GDP, in percentage points. */
  debtChange: number | null
  health: ServiceChange
  schools: ServiceChange
  care: ServiceChange
  /** Sum of the counted yearly excesses, before the other parts of the formula. */
  excessSum: number | null
  worstYear: number | null
  worstExcess: number | null
  healthStartsOnBreak: boolean
  healthBreakOpenDays: number | null
  healthOldDays: number | null
}
