export const BUDGET_POLICIES = [
  "health",
  "education",
  "care",
  "housing",
  "transport",
  "interest",
  "pensions",
  "justice",
  "defence",
  "security",
  "foreign",
  "employment",
  "unemployment",
  "benefits",
  "labour",
  "social_security",
  "culture",
  "agriculture",
  "farm_works",
  "industry",
  "energy",
  "commerce",
  "tourism",
  "research",
  "economic",
  "leadership",
  "general",
  "statistics",
  "tax",
  "transfers",
  "eu_transfers",
  "communications",
  "community",
  "other_social",
  "resilient",
  "rest",
] as const

export type BudgetPolicy = (typeof BUDGET_POLICIES)[number]

export const GENERAL_PARTS = [
  "general_territory",
  "general_mutual",
  "general_finance",
  "general_purchase",
  "general_elections",
  "general_admin",
  "general_contingency",
  "general_memory",
  "general_other",
  "staff",
  "goods",
  "current_transfers",
  "capital_transfers",
  "investment",
  "assets",
  "contingency",
] as const

export const LEADERSHIP_PARTS = [
  "crown",
  "parliament",
  "constitutional",
  "audit",
  "council",
  "government",
  "leadership_other",
] as const

export const JUSTICE_PARTS = ["courts", "judicial_council", "justice_other"] as const

export const FOREIGN_PARTS = ["embassies", "cooperation", "foreign_other"] as const

export type GeneralPart = (typeof GENERAL_PARTS)[number]
export type LeadershipPart = (typeof LEADERSHIP_PARTS)[number]
export type JusticePart = (typeof JUSTICE_PARTS)[number]
export type ForeignPart = (typeof FOREIGN_PARTS)[number]

/** Share of a settled budget, in percent, for the policies that were published. */
export type BudgetShares = Partial<Record<BudgetPolicy, number>>

export interface BudgetParts {
  general?: Partial<Record<GeneralPart, number>>
  leadership?: Partial<Record<LeadershipPart, number>>
  justice?: Partial<Record<JusticePart, number>>
  foreign?: Partial<Record<ForeignPart, number>>
}

/**
 * One settled budget for the years a window actually covers.
 * `share` is the percent of that budget. `gdp` is the same spending as a
 * percent of GDP. `parts` breaks a policy into the pieces underneath it,
 * on the same scale as `share`.
 *
 * The policy `transfers` is the spending line "transfers to other
 * administrations". It is a different figure from the financing-system
 * flow between a region and the State.
 */
export interface Budget {
  from: number
  to: number
  /** True when every year of the window has a liquidation. */
  complete: boolean
  share: BudgetShares
  gdp: BudgetShares
  parts: BudgetParts
  partsGdp: BudgetParts
}
