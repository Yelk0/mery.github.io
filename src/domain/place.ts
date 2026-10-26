import type { YearlyEconomy, VolumePoint } from "./economy"
import type { Law } from "./law"
import type { OfficeHolder, Term } from "./term"
import type { CountryWindow, RegionWindow } from "./window"

interface PlaceBase {
  slug: string
  name: string
  economy: YearlyEconomy[]
  volume: VolumePoint[]
}

export interface Region extends PlaceBase {
  kind: "region"
  /** Statistical name, as published. */
  ineLabel: string
  /** True for the foral regimes, which keep their own tax arrangement. */
  foral: boolean
  terms: Term[]
  /** People who held an office in a cabinet of this region. */
  members: OfficeHolder[]
  laws: Law[]
  windows: RegionWindow[]
}

export interface Country extends PlaceBase {
  kind: "country"
  windows: CountryWindow[]
}

export type Place = Country | Region
