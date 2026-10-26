/**
 * Shared names for the domain.
 *
 * Money is stored in miles: thousands of euros. A percent is already a
 * percent, so 33.6 means 33.6%. A missing measure is null. Zero means the
 * measure was published and came out at zero.
 */

export type IsoDate = string

export type PlaceKind = "country" | "region"

/** A region is compared with Spain. The country is compared with the European Union. */
export type ComparisonBaseline = "spain" | "european-union"

export type VoteSide = "for" | "against" | "abstain"

export type LawKind = "ley" | "presupuestos"

/** `short` means the term has too few counted years to rank. */
export type TermVerdict = "ahead" | "behind" | "similar" | "short"

export type Pace = "ahead" | "behind" | "similar"
