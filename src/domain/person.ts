import type { Score } from "./score"

export interface Person {
  slug: string
  name: string
  party: string
  /** Region shown beside the person on the ranking. Each term names its own region. */
  regionSlug: string
  /** Null when this person is not in the ranking. */
  score: Score | null
}
