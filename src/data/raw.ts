export interface RawYear {
  valor: number | null
  index: number | null
  gdp: number | null
  growth: number | null
  share: number | null
  population: number | null
}

export interface RawOffice {
  name: string
  office: string
  started_on: string
  ended_on: string | null
}

export interface RawScoreYear {
  year: number
  days: number
  counted: boolean
  region_growth: number | null
  spain_growth: number | null
  excess: number | null
  index: number | null
  share: number | null
}

export interface RawTermMeasure {
  years: RawScoreYear[]
  scored_years: number
  first_year: number | null
  last_year: number | null
  avg_region_growth: number | null
  avg_spain_growth: number | null
  excess_growth: number | null
  output_change: number | null
  share_before: number | null
  share_after: number | null
  index_before: number | null
  index_after: number | null
  index_change: number | null
  people_change: number | null
  population_before: number | null
  population_after: number | null
  real_change: number | null
  public_jobs_change: number | null
  private_jobs_change: number | null
  debt_before: number | null
  debt_after: number | null
  debt_change: number | null
  health_before: number | null
  health_after: number | null
  health_change: number | null
  health_break: boolean
  health_starts_on_break: boolean
  health_break_open_days: number | null
  health_old_days: number | null
  schools_before: number | null
  schools_after: number | null
  schools_change: number | null
  care_before: number | null
  care_after: number | null
  care_change: number | null
  result: number | null
  verdict: string
  versus_spain: string | null
  peer_rank: number | null
  peer_count: number | null
}

export interface RawTerm {
  slug: string
  name: string
  party: string
  region_slug: string
  started_on: string
  ended_on: string | null
  cabinet: RawOffice[]
  score: RawTermMeasure
}

export interface RawLeader {
  slug: string
  name: string
  party: string
  region_slug: string
  counted_years: number
  output_gained: number | null
  index_gained: number | null
  people_change: number | null
  real_gained: number | null
  public_jobs_change: number | null
  private_jobs_change: number | null
  debt_change: number | null
  health_change: number | null
  health_for_score: number | null
  health_filled: boolean
  health_starts_on_break: boolean
  health_break_open_days: number | null
  health_old_days: number | null
  schools_change: number | null
  schools_for_score: number | null
  schools_filled: boolean
  care_change: number | null
  care_for_score: number | null
  care_filled: boolean
  result: number | null
  excess_sum: number | null
  worst_year: number | null
  worst_excess: number | null
  eligible: boolean
  rank: number | null
  ranked_count: number | null
}

export interface RawFlow {
  received: number | null
  paid: number | null
  net: number | null
  from: number | null
  to: number | null
}

export interface RawState {
  spent: number | null
  given: number | null
  back: number | null
  net: number | null
  from: number | null
  to: number | null
}

export interface RawDebt {
  change: number | null
  total: number | null
  bonds: number | null
  bonds_short: number | null
  bonds_long: number | null
  loans: number | null
  fund: number | null
}

export interface RawScale {
  year: number
  gdp: number | null
  spent: number | null
  share: number | null
  share_change: number | null
}

export interface RawBlock {
  id: string
  start: number
  end: number
  open: boolean
  during: number | null
  growth: number | null
  later: number | null
  later_growth: number | null
  later_ready: boolean
  later_start: number
  later_end: number
  balance: number | null
  balance_end: number | null
  budget: Record<string, unknown> | null
  debt: RawDebt | null
  flow: RawFlow | null
  state: RawState | null
  scale: RawScale | null
}

export interface RawCommunity {
  slug: string
  name: string
  foral: boolean
  reference: boolean
  volume: { year: number; level: number | null }[]
  blocks: RawBlock[]
}

export interface RawWindow {
  id: string
  start: number
  end: number
  open: boolean
  later_start: number
  later_end: number
  later_ready: boolean
}

export interface RawMember {
  name: string
  office: string
  started_on: string
  ended_on: string | null
}

export interface RawRegionSeries {
  slug: string
  ine_label: string
  series: Record<string, RawYear>
  members: RawMember[]
}

export interface RawMeta {
  min_career_years: number
  years: [number, number]
  debt_weight: number
  health_days_per_point: number
  health_break_year: number
  health_worst: number
  schools_worst: number
  care_worst: number
  jobs_first_year: number
  health_first_year: number
  schools_first_year: number
  care_first_year: number
  gdp_table: string
  gdp_url: string
  gdp_title: string
  per_capita_table: string
  per_capita_url: string
  per_capita_title: string
  volume_url: string
  volume_title: string
  jobs_table: string
  jobs_url: string
  jobs_title: string
  debt_url: string
  debt_file: string
  debt_title: string
  health_url: string
  health_title: string
  schools_url: string
  schools_title: string
  care_url: string
  care_title: string
  balance_url: string
  balance_title: string
  budget_url: string
  budget_title: string
  state_budget_url: string
  state_budget_title: string
  state_budget_from: number
  state_budget_to: number
  spain_url: string
  spain_title: string
  central_url: string
  central_title: string
  central_from: number
  central_to: number
  flow_url: string
  flow_title: string
  flow_last_year: number
  spain_debt_url: string
  spain_debt_file: string
  spain_debt_title: string
  eu_url: string
  eu_title: string
  eu_volume_url: string
  eu_volume_title: string
  eu_volume_from: number
  eu_volume_to: number
}

export interface RawLaw {
  id: string
  region: string
  voted_on: string
  year: number
  title: string
  sentence: string
  url: string
  kind: string
  votes: { group: string; side: string; count: number }[]
}

export interface RawStore {
  meta: RawMeta
  spain: Record<string, RawYear>
  regions: RawRegionSeries[]
  terms: RawTerm[]
  leaders: RawLeader[]
  communities: {
    windows: RawWindow[]
    regions: RawCommunity[]
  }
}
