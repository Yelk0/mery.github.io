import {
  BUDGET_POLICIES,
  FOREIGN_PARTS,
  GENERAL_PARTS,
  JUSTICE_PARTS,
  LEADERSHIP_PARTS,
  type AccountingWindow,
  type Budget,
  type BudgetParts,
  type BudgetShares,
  type CommunityTransfer,
  type Country,
  type CountryWindow,
  type Dataset,
  type DebtStock,
  type EconomyScale,
  type Law,
  type LawKind,
  type Pace,
  type Person,
  type Region,
  type RegionWindow,
  type Score,
  type Sources,
  type Term,
  type TermMeasure,
  type TermVerdict,
  type TransferFlow,
  type VoteSide,
  type YearlyEconomy,
} from "../domain"
import type { RawBlock, RawFlow, RawLaw, RawLeader, RawMeta, RawRegionSeries, RawStore, RawTerm, RawWindow, RawYear } from "./raw"

export function dataFile(name: string): string {
  return `${import.meta.env.BASE_URL}data/${name}`
}

export async function loadDataset(): Promise<Dataset> {
  const [storeResponse, lawsResponse] = await Promise.all([
    fetch(dataFile("store.json")),
    fetch(dataFile("laws.json")),
  ])
  if (!storeResponse.ok) throw new Error(`HTTP ${storeResponse.status}`)
  const store = (await storeResponse.json()) as RawStore
  const laws = lawsResponse.ok ? ((await lawsResponse.json()) as RawLaw[]) : []
  return toDataset(store, laws.map(lawOf))
}

export function toDataset(store: RawStore, laws: Law[]): Dataset {
  const terms = store.terms.map(termOf)
  const countrySource = store.communities.regions.find((region) => region.reference)
  if (!countrySource) throw new Error("store has no country")
  const profiles = new Map(store.regions.map((region) => [region.slug, region]))
  return {
    minimumYears: store.meta.min_career_years,
    sources: sourcesOf(store.meta),
    windows: store.communities.windows.map(windowOf),
    country: countryOf(countrySource, store.spain),
    regions: store.communities.regions
      .filter((region) => !region.reference)
      .map((region) => regionOf(region, profiles.get(region.slug), terms, laws)),
    people: store.leaders.map(personOf),
  }
}

function sourcesOf(meta: RawMeta): Sources {
  const [firstYear, lastYear] = meta.years
  return {
    firstYear,
    lastYear,
    minimumYears: meta.min_career_years,
    debtWeight: meta.debt_weight,
    healthDaysPerPoint: meta.health_days_per_point,
    healthBreakYear: meta.health_break_year,
    healthWorst: meta.health_worst,
    schoolsWorst: meta.schools_worst,
    careWorst: meta.care_worst,
    jobsFirstYear: meta.jobs_first_year,
    healthFirstYear: meta.health_first_year,
    schoolsFirstYear: meta.schools_first_year,
    careFirstYear: meta.care_first_year,
    gdpTable: meta.gdp_table,
    gdpUrl: meta.gdp_url,
    gdpTitle: meta.gdp_title,
    perCapitaTable: meta.per_capita_table,
    perCapitaUrl: meta.per_capita_url,
    perCapitaTitle: meta.per_capita_title,
    volumeUrl: meta.volume_url,
    volumeTitle: meta.volume_title,
    jobsTable: meta.jobs_table,
    jobsUrl: meta.jobs_url,
    jobsTitle: meta.jobs_title,
    debtUrl: meta.debt_url,
    debtFile: meta.debt_file,
    debtTitle: meta.debt_title,
    healthUrl: meta.health_url,
    healthTitle: meta.health_title,
    schoolsUrl: meta.schools_url,
    schoolsTitle: meta.schools_title,
    careUrl: meta.care_url,
    careTitle: meta.care_title,
    balanceUrl: meta.balance_url,
    balanceTitle: meta.balance_title,
    budgetUrl: meta.budget_url,
    budgetTitle: meta.budget_title,
    stateBudgetUrl: meta.state_budget_url,
    stateBudgetTitle: meta.state_budget_title,
    stateBudgetFrom: meta.state_budget_from,
    stateBudgetTo: meta.state_budget_to,
    spainUrl: meta.spain_url,
    spainTitle: meta.spain_title,
    centralUrl: meta.central_url,
    centralTitle: meta.central_title,
    centralFrom: meta.central_from,
    centralTo: meta.central_to,
    flowUrl: meta.flow_url,
    flowTitle: meta.flow_title,
    flowLastYear: meta.flow_last_year,
    spainDebtUrl: meta.spain_debt_url,
    spainDebtFile: meta.spain_debt_file,
    spainDebtTitle: meta.spain_debt_title,
    euUrl: meta.eu_url,
    euTitle: meta.eu_title,
    euVolumeUrl: meta.eu_volume_url,
    euVolumeTitle: meta.eu_volume_title,
    euVolumeFrom: meta.eu_volume_from,
    euVolumeTo: meta.eu_volume_to,
  }
}

function countryOf(source: RawStore["communities"]["regions"][number], spain: Record<string, RawYear>): Country {
  return {
    kind: "country",
    slug: source.slug,
    name: source.name,
    economy: economyOf(spain),
    volume: source.volume.map((point) => ({ year: point.year, level: point.level })),
    windows: source.blocks.map(countryWindowOf),
  }
}

function regionOf(
  source: RawStore["communities"]["regions"][number],
  profile: RawRegionSeries | undefined,
  terms: Term[],
  laws: Law[],
): Region {
  return {
    kind: "region",
    slug: source.slug,
    name: source.name,
    ineLabel: profile?.ine_label ?? source.name,
    foral: source.foral,
    economy: economyOf(profile?.series ?? {}),
    volume: source.volume.map((point) => ({ year: point.year, level: point.level })),
    terms: terms.filter((term) => term.regionSlug === source.slug),
    members: (profile?.members ?? []).map((member) => ({
      name: member.name,
      office: member.office,
      startedOn: member.started_on,
      endedOn: member.ended_on || null,
    })),
    laws: laws.filter((law) => law.regionSlug === source.slug),
    windows: source.blocks.map(regionWindowOf),
  }
}

function economyOf(series: Record<string, RawYear>): YearlyEconomy[] {
  return Object.entries(series)
    .map(([year, row]) => ({
      year: Number(year),
      gdpPerPerson: row.valor,
      index: row.index,
      gdp: row.gdp,
      growth: row.growth,
      shareOfCountry: row.share,
      population: row.population,
    }))
    .sort((left, right) => left.year - right.year)
}

function windowOf(window: RawWindow): AccountingWindow {
  return {
    id: window.id,
    start: window.start,
    end: window.end,
    open: window.open,
    laterStart: window.later_start,
    laterEnd: window.later_end,
    laterReady: window.later_ready,
  }
}

function sharedWindow(block: RawBlock) {
  return {
    window: {
      id: block.id,
      start: block.start,
      end: block.end,
      open: block.open,
      laterStart: block.later_start,
      laterEnd: block.later_end,
      laterReady: block.later_ready,
    },
    growth: block.growth,
    againstBaseline: block.during,
    laterGrowth: block.later_growth,
    laterAgainstBaseline: block.later,
    balance: block.balance,
    balanceEnd: block.balance_end,
    budget: block.budget ? budgetOf(block.budget) : null,
    debt: block.debt ? debtOf(block.debt) : null,
    scale: block.scale ? scaleOf(block.scale) : null,
  }
}

function regionWindowOf(block: RawBlock): RegionWindow {
  return {
    ...sharedWindow(block),
    baseline: "spain",
    stateTransfer: block.flow ? flowOf(block.flow) : null,
  }
}

function countryWindowOf(block: RawBlock): CountryWindow {
  const state = block.state
  const communityTransfer: CommunityTransfer | null = state
    ? {
        from: state.from,
        to: state.to,
        paid: state.given,
        received: state.back,
        net: state.net,
      }
    : null
  return {
    ...sharedWindow(block),
    baseline: "european-union",
    euTransfer: block.flow ? flowOf(block.flow) : null,
    communityTransfer,
    centralSpending: state ? state.spent : null,
  }
}

function flowOf(flow: RawFlow): TransferFlow {
  return {
    from: flow.from,
    to: flow.to,
    received: flow.received,
    paid: flow.paid,
    net: flow.net,
  }
}

function debtOf(debt: NonNullable<RawBlock["debt"]>): DebtStock {
  return {
    change: debt.change,
    total: debt.total,
    bonds: debt.bonds,
    bondsShort: debt.bonds_short,
    bondsLong: debt.bonds_long,
    loans: debt.loans,
    fund: debt.fund,
  }
}

function scaleOf(scale: NonNullable<RawBlock["scale"]>): EconomyScale {
  return {
    year: scale.year,
    gdp: scale.gdp,
    spent: scale.spent,
    debtShare: scale.share,
    debtShareChange: scale.share_change,
  }
}

function budgetOf(raw: Record<string, unknown>): Budget {
  const share: BudgetShares = {}
  for (const policy of BUDGET_POLICIES) {
    const value = raw[policy]
    if (typeof value === "number") share[policy] = value
  }
  return {
    from: numberField(raw.from),
    to: numberField(raw.to),
    complete: raw.complete === true,
    share,
    gdp: sharesOf(raw.of_gdp),
    parts: partsOf(raw.parts),
    partsGdp: partsOf(raw.parts_gdp),
  }
}

function sharesOf(value: unknown): BudgetShares {
  const share: BudgetShares = {}
  if (typeof value !== "object" || value === null) return share
  const record = value as Record<string, unknown>
  for (const policy of BUDGET_POLICIES) {
    const amount = record[policy]
    if (typeof amount === "number") share[policy] = amount
  }
  return share
}

function partsOf(value: unknown): BudgetParts {
  const parts: BudgetParts = {}
  if (typeof value !== "object" || value === null) return parts
  const record = value as Record<string, unknown>
  const general = namedParts(record.general, GENERAL_PARTS)
  const leadership = namedParts(record.leadership, LEADERSHIP_PARTS)
  const justice = namedParts(record.justice, JUSTICE_PARTS)
  const foreign = namedParts(record.foreign, FOREIGN_PARTS)
  if (general) parts.general = general
  if (leadership) parts.leadership = leadership
  if (justice) parts.justice = justice
  if (foreign) parts.foreign = foreign
  return parts
}

function namedParts<Key extends string>(value: unknown, keys: readonly Key[]): Partial<Record<Key, number>> | null {
  if (typeof value !== "object" || value === null) return null
  const record = value as Record<string, unknown>
  const parts: Partial<Record<Key, number>> = {}
  for (const key of keys) {
    const amount = record[key]
    if (typeof amount === "number") parts[key] = amount
  }
  return Object.keys(parts).length > 0 ? parts : null
}

function numberField(value: unknown): number {
  return typeof value === "number" ? value : 0
}

function personOf(leader: RawLeader): Person {
  const score: Score = {
    result: leader.result,
    countedYears: leader.counted_years,
    eligible: leader.eligible,
    rank: leader.rank,
    rankedCount: leader.ranked_count,
    outputChange: leader.output_gained,
    realChange: leader.real_gained,
    indexChange: leader.index_gained,
    peopleChange: leader.people_change,
    publicJobsChange: leader.public_jobs_change,
    privateJobsChange: leader.private_jobs_change,
    debtChange: leader.debt_change,
    health: { measured: leader.health_change, used: leader.health_for_score, filled: leader.health_filled },
    schools: { measured: leader.schools_change, used: leader.schools_for_score, filled: leader.schools_filled },
    care: { measured: leader.care_change, used: leader.care_for_score, filled: leader.care_filled },
    excessSum: leader.excess_sum,
    worstYear: leader.worst_year,
    worstExcess: leader.worst_excess,
    healthStartsOnBreak: leader.health_starts_on_break,
    healthBreakOpenDays: leader.health_break_open_days,
    healthOldDays: leader.health_old_days,
  }
  return {
    slug: leader.slug,
    name: leader.name,
    party: leader.party,
    regionSlug: leader.region_slug,
    score,
  }
}

function termOf(raw: RawTerm): Term {
  return {
    personSlug: raw.slug,
    personName: raw.name,
    party: raw.party,
    regionSlug: raw.region_slug,
    startedOn: raw.started_on,
    endedOn: raw.ended_on,
    cabinet: raw.cabinet.map((member) => ({
      name: member.name,
      office: member.office,
      startedOn: member.started_on,
      endedOn: member.ended_on,
    })),
    years: raw.score.years.map((year) => ({
      year: year.year,
      days: year.days,
      counted: year.counted,
      regionGrowth: year.region_growth,
      spainGrowth: year.spain_growth,
      excess: year.excess,
      index: year.index,
      shareOfCountry: year.share,
    })),
    measure: measureOf(raw.score),
  }
}

function measureOf(raw: RawTerm["score"]): TermMeasure {
  return {
    countedYears: raw.scored_years,
    firstYear: raw.first_year,
    lastYear: raw.last_year,
    result: raw.result,
    verdict: verdictOf(raw.verdict),
    versusSpain: paceOf(raw.versus_spain),
    peerRank: raw.peer_rank,
    peerCount: raw.peer_count,
    averageRegionGrowth: raw.avg_region_growth,
    averageSpainGrowth: raw.avg_spain_growth,
    excessGrowth: raw.excess_growth,
    outputChange: raw.output_change,
    indexChange: raw.index_change,
    peopleChange: raw.people_change,
    shareBefore: raw.share_before,
    shareAfter: raw.share_after,
    indexBefore: raw.index_before,
    indexAfter: raw.index_after,
    populationBefore: raw.population_before,
    populationAfter: raw.population_after,
    realChange: raw.real_change,
    publicJobsChange: raw.public_jobs_change,
    privateJobsChange: raw.private_jobs_change,
    debtBefore: raw.debt_before,
    debtAfter: raw.debt_after,
    debtChange: raw.debt_change,
    healthBefore: raw.health_before,
    healthAfter: raw.health_after,
    healthChange: raw.health_change,
    schoolsBefore: raw.schools_before,
    schoolsAfter: raw.schools_after,
    schoolsChange: raw.schools_change,
    careBefore: raw.care_before,
    careAfter: raw.care_after,
    careChange: raw.care_change,
    healthSeriesBreak: raw.health_break,
    healthStartsOnBreak: raw.health_starts_on_break,
    healthBreakOpenDays: raw.health_break_open_days,
    healthOldDays: raw.health_old_days,
  }
}

function verdictOf(value: string): TermVerdict {
  if (value === "ahead" || value === "behind" || value === "similar" || value === "short") return value
  return "short"
}

function paceOf(value: string | null): Pace | null {
  if (value === "ahead" || value === "behind" || value === "similar") return value
  return null
}

function lawOf(raw: RawLaw): Law {
  return {
    id: raw.id,
    regionSlug: raw.region,
    votedOn: raw.voted_on,
    year: raw.year,
    title: raw.title,
    sentence: raw.sentence,
    url: raw.url,
    kind: kindOf(raw.kind),
    votes: raw.votes.map((vote) => ({
      group: vote.group,
      side: sideOf(vote.side),
      count: vote.count,
    })),
  }
}

function kindOf(value: string): LawKind {
  if (value === "ley" || value === "presupuestos") return value
  return "ley"
}

function sideOf(value: string): VoteSide {
  if (value === "for" || value === "against" || value === "abstain") return value
  return "abstain"
}

export function placeBySlug(dataset: Dataset, slug: string): Country | Region | null {
  if (dataset.country.slug === slug) return dataset.country
  return dataset.regions.find((region) => region.slug === slug) ?? null
}

export function regionName(dataset: Dataset, slug: string): string {
  return dataset.regions.find((region) => region.slug === slug)?.name ?? slug
}

export function termsOf(dataset: Dataset, personSlug: string): Term[] {
  return dataset.regions
    .flatMap((region) => region.terms)
    .filter((term) => term.personSlug === personSlug)
    .sort((left, right) => left.startedOn.localeCompare(right.startedOn))
}

export function chosenWindow(dataset: Dataset, id: string | null): AccountingWindow | null {
  const found = id ? dataset.windows.find((window) => window.id === id) : undefined
  if (found) return found
  const ready = [...dataset.windows].reverse().find((window) => window.laterReady)
  return ready ?? dataset.windows.at(-1) ?? null
}
