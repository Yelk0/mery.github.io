import type { IsoDate, LawKind, VoteSide } from "./common"

export interface Vote {
  group: string
  side: VoteSide
  count: number
}

/** A law of one region, placed on the year it was voted. */
export interface Law {
  id: string
  regionSlug: string
  votedOn: IsoDate
  year: number
  title: string
  sentence: string
  url: string
  kind: LawKind
  votes: Vote[]
}
