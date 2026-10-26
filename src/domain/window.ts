import type { Budget } from "./budget"
import type { DebtStock, EconomyScale } from "./debt"
import type { CommunityTransfer, TransferFlow } from "./transfer"

/** The four years a chip on the communities page refers to. */
export interface AccountingWindow {
  id: string
  start: number
  end: number
  /** True when the window is still open because its last year has not arrived. */
  open: boolean
  laterStart: number
  laterEnd: number
  /** True when the following four years are already complete. */
  laterReady: boolean
}

interface WindowBase {
  window: AccountingWindow
  /** Real growth of this place across the window, in percent. */
  growth: number | null
  /** That growth minus the baseline's growth, in percent. */
  againstBaseline: number | null
  /** Real growth across the following window, in percent. */
  laterGrowth: number | null
  /** The following window's growth minus the baseline's, in percent. */
  laterAgainstBaseline: number | null
  /** Surplus or deficit of the whole window, as a percent of GDP. */
  balance: number | null
  /** Surplus or deficit in the last year, in miles. */
  balanceEnd: number | null
  budget: Budget | null
  debt: DebtStock | null
  scale: EconomyScale | null
}

/** One window of a region's accounts. Growth is compared with Spain. */
export interface RegionWindow extends WindowBase {
  baseline: "spain"
  /** What this region received from the State and paid back. */
  stateTransfer: TransferFlow | null
}

/**
 * One window of the country's accounts. Growth is compared with the European Union.
 * `centralSpending` is the central administration in the national accounts.
 * It is neither the State budget in `budget` nor `scale.spent`.
 */
export interface CountryWindow extends WindowBase {
  baseline: "european-union"
  euTransfer: TransferFlow | null
  communityTransfer: CommunityTransfer | null
  /** Central administration spending in the last year, in miles. */
  centralSpending: number | null
}
