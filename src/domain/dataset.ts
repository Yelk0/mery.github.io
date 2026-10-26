import type { Country, Region } from "./place"
import type { Person } from "./person"
import type { Sources } from "./sources"
import type { AccountingWindow } from "./window"

/** The document the page loads. People are separate because a career can cross regions. */
export interface Dataset {
  /** Counted years a career needs before it can be ranked. */
  minimumYears: number
  sources: Sources
  windows: AccountingWindow[]
  country: Country
  regions: Region[]
  people: Person[]
}
