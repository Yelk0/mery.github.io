/** Debt stock at the end of a window. Amounts are in miles. */
export interface DebtStock {
  /** Rise, or fall, from the December before the window to the December at the end. */
  change: number | null
  total: number | null
  bonds: number | null
  bondsShort: number | null
  bondsLong: number | null
  loans: number | null
  /** Part of the loans that comes from the State financing fund. Null for the country. */
  fund: number | null
}

/**
 * The economy and the debt ratio at the end of a window.
 * For a region, `spent` is that region's settled budget.
 * For the country, `spent` is the spending of all public administrations,
 * which is wider than the State budget.
 */
export interface EconomyScale {
  year: number
  /** GDP, in miles. */
  gdp: number | null
  /** Spending, in miles. */
  spent: number | null
  /** Debt as a percent of GDP. */
  debtShare: number | null
  /** Change in that percent since the December before the window. */
  debtShareChange: number | null
}
