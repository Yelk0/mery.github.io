/** One calendar year of the economy at current prices. */
export interface YearlyEconomy {
  year: number
  /** GDP per person, in euros. */
  gdpPerPerson: number | null
  /** Index of GDP per person. 100 is Spain in 2000. */
  index: number | null
  /** GDP, in miles. */
  gdp: number | null
  /** Current-price growth over the previous year, in percent. */
  growth: number | null
  /** This place's GDP as a percent of the country's GDP. The country itself is 100. */
  shareOfCountry: number | null
  population: number | null
}

/** Real output compared with the place's baseline. 100 is that baseline in 2000. */
export interface VolumePoint {
  year: number
  level: number | null
}
