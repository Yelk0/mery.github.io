import type { BudgetPolicy, ForeignPart, GeneralPart, JusticePart, LeadershipPart } from "../domain"

export const policyLabel = {
  health: "commHealth",
  education: "commEducation",
  care: "commCare",
  housing: "commHousing",
  transport: "commTransport",
  interest: "commInterest",
  pensions: "commPensions",
  justice: "commJustice",
  defence: "commDefence",
  security: "commSecurity",
  foreign: "commForeign",
  employment: "commEmployment",
  unemployment: "commUnemployment",
  benefits: "commBenefits",
  labour: "commLabour",
  social_security: "commSocialSecurity",
  culture: "commCulture",
  agriculture: "commAgriculture",
  farm_works: "commFarmWorks",
  industry: "commIndustry",
  energy: "commEnergy",
  commerce: "commCommerce",
  tourism: "commTourism",
  research: "commResearch",
  economic: "commEconomic",
  leadership: "commLeadership",
  general: "commGeneral",
  statistics: "commStatistics",
  tax: "commTax",
  transfers: "commTransfersAdmin",
  eu_transfers: "commEuBudget",
  communications: "commCommunications",
  community: "commCommunity",
  other_social: "commOtherSocial",
  resilient: "commResilient",
  rest: "commRest",
} as const satisfies Record<BudgetPolicy, string>

export const generalLabel = {
  general_territory: "partTerritory",
  general_mutual: "partMutual",
  general_finance: "partFinance",
  general_purchase: "partPurchase",
  general_elections: "partElections",
  general_admin: "partGeneralAdmin",
  general_contingency: "partContingency",
  general_memory: "partMemory",
  general_other: "partGeneralOther",
  staff: "partStaff",
  goods: "partGoods",
  current_transfers: "partCurrentTransfers",
  capital_transfers: "partCapitalTransfers",
  investment: "partInvestment",
  assets: "partAssets",
  contingency: "partFund",
} as const satisfies Record<GeneralPart, string>

export const leadershipLabel = {
  crown: "partCrown",
  parliament: "partParliament",
  constitutional: "partConstitutional",
  audit: "partAudit",
  council: "partCouncil",
  government: "partGovernment",
  leadership_other: "partLeadershipOther",
} as const satisfies Record<LeadershipPart, string>

export const justiceLabel = {
  courts: "partCourts",
  judicial_council: "partJudicialCouncil",
  justice_other: "partJusticeOther",
} as const satisfies Record<JusticePart, string>

export const foreignLabel = {
  embassies: "partEmbassies",
  cooperation: "partCooperation",
  foreign_other: "partForeignOther",
} as const satisfies Record<ForeignPart, string>
