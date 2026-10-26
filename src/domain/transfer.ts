/**
 * Money moving between two administrations, summed over the years that have a figure.
 * Amounts are in miles. `net` is `paid` minus `received`.
 */
export interface TransferFlow {
  from: number | null
  to: number | null
  received: number | null
  paid: number | null
  net: number | null
}

/**
 * What the country paid the regions and what it received back, summed over the window.
 * Amounts are in miles. `net` is `received` minus `paid`.
 */
export interface CommunityTransfer {
  from: number | null
  to: number | null
  paid: number | null
  received: number | null
  net: number | null
}
