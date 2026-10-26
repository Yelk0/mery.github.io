<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { useRoute, useRouter } from "vue-router"
import { regionName, termsOf } from "../data/load"
import type { Dataset, Person } from "../domain"
import { burden, numberLocale, signed, signedDays, signedPercent, signedPoints, tone } from "../format"
import { pageHref, toPage, verdictOf, type VerdictFilter } from "../route"

const props = defineProps<{ dataset: Dataset }>()
const route = useRoute()
const router = useRouter()
const verdict = computed(() => verdictOf(route.query.verdict))
const query = computed(() => {
  const value = route.query.q
  return typeof value === "string" ? value : ""
})

const { t, locale } = useI18n()

const filters = ["all", "gained", "lost", "early"] as const
const filterLabel = {
  all: "filterAll",
  gained: "filterGained",
  lost: "filterLost",
  early: "filterEarly",
} as const

const needle = computed(() => query.value.trim().toLowerCase())

const matching = computed(() => props.dataset.people.filter((person) => {
  const score = person.score
  if (!score) return false
  if (verdict.value === "gained" && !(score.eligible && (score.result ?? 0) > 0)) return false
  if (verdict.value === "lost" && !(score.eligible && (score.result ?? 0) < 0)) return false
  if (verdict.value === "early" && score.countedYears >= props.dataset.minimumYears) return false
  if (!needle.value) return true
  const region = regionName(props.dataset, person.regionSlug).toLowerCase()
  return person.name.toLowerCase().includes(needle.value)
    || region.includes(needle.value)
    || person.party.toLowerCase().includes(needle.value)
}))

const ranked = computed(() => matching.value
  .flatMap((person) => {
    const score = person.score
    if (!score?.eligible || score.rank === null) return []
    return [{ person, score }]
  })
  .sort((left, right) => (left.score.rank ?? 0) - (right.score.rank ?? 0) || left.person.name.localeCompare(right.person.name)))

const early = computed(() => matching.value
  .filter((person) => (person.score?.countedYears ?? 0) < props.dataset.minimumYears)
  .sort((left, right) => left.name.localeCompare(right.name)))

const uncovered = computed(() => matching.value
  .filter((person) => {
    const score = person.score
    return score !== null && score.countedYears >= props.dataset.minimumYears && !score.eligible
  })
  .sort((left, right) => left.name.localeCompare(right.name)))

function searchQuery(nextVerdict: VerdictFilter, nextQuery: string) {
  return {
    verdict: nextVerdict === "all" ? "" : nextVerdict,
    q: nextQuery,
  }
}

function onQuery(value: string) {
  void router.replace(toPage("presidents", {}, searchQuery(verdict.value, value)))
}

function onVerdict(value: VerdictFilter) {
  void router.push(toPage("presidents", {}, searchQuery(value, query.value)))
}

function office(person: Person) {
  const now = t("now")
  return termsOf(props.dataset, person.slug)
    .map((term) => `${term.startedOn.slice(0, 4)}–${term.endedOn ? term.endedOn.slice(0, 4) : now}`)
    .join(", ")
}

function yearsPhrase(person: Person) {
  const count = person.score?.countedYears ?? 0
  const key = count === 1 ? "oneCountedYear" : "manyCountedYears"
  return t(key, { n: count })
}

function loc() {
  return numberLocale(locale.value)
}
</script>

<template>
  <h1>{{ t("homeTitle") }}</h1>
  <div class="filters">
    <v-text-field
      :model-value="query"
      :label="t('searchLabel')"
      :placeholder="t('searchPlaceholder')"
      density="compact"
      variant="outlined"
      hide-details
      single-line
      @update:model-value="onQuery"
    />
    <v-btn
      v-for="item in filters"
      :key="item"
      :variant="verdict === item ? 'flat' : 'outlined'"
      :color="verdict === item ? 'primary' : undefined"
      @click="onVerdict(item)"
    >{{ t(filterLabel[item]) }}</v-btn>
  </div>

  <v-table v-if="ranked.length" density="compact" class="sheet">
    <thead>
      <tr>
        <th class="num">{{ t("colRank") }}</th>
        <th>{{ t("colPresident") }}</th>
        <th>{{ t("colRegion") }}</th>
        <th>{{ t("colOffice") }}</th>
        <th class="num">{{ t("colYears") }}</th>
        <th class="num">{{ t("colScore") }}</th>
        <th class="num">{{ t("colReal") }}</th>
        <th class="num">{{ t("colDebt") }}</th>
        <th class="num">{{ t("colEconomy") }}</th>
        <th class="num">{{ t("colPerson") }}</th>
        <th class="num">{{ t("colPeople") }}</th>
        <th class="num">{{ t("colPublic").replace("<br>", " ") }}</th>
        <th class="num">{{ t("colPrivate").replace("<br>", " ") }}</th>
        <th class="num">{{ t("colHealth") }}</th>
        <th class="num">{{ t("colSchools") }}</th>
        <th class="num">{{ t("colCare") }}</th>
        <th class="num">{{ t("colWorst") }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in ranked" :key="row.person.slug">
        <td class="num">{{ row.score.rank }}</td>
        <td>
          <a :href="pageHref('person', { slug: row.person.slug })">{{ row.person.name }}</a>
          <span v-if="row.person.party" class="party">{{ row.person.party }}</span>
        </td>
        <td><a :href="pageHref('region', { slug: row.person.regionSlug })">{{ regionName(dataset, row.person.regionSlug) }}</a></td>
        <td>{{ office(row.person) }}</td>
        <td class="num">{{ row.score.countedYears }}</td>
        <td class="num" :class="tone(row.score.result)">{{ signed(row.score.result, 1, loc()) }}</td>
        <td class="num" :class="tone(row.score.realChange)">{{ signedPercent(row.score.realChange, loc()) }}</td>
        <td class="num" :class="burden(row.score.debtChange)">{{ signedPoints(row.score.debtChange, loc()) }}</td>
        <td class="num" :class="tone(row.score.outputChange)">{{ signedPercent(row.score.outputChange, loc()) }}</td>
        <td class="num" :class="tone(row.score.indexChange)">{{ signed(row.score.indexChange, 1, loc()) }}</td>
        <td class="num" :class="tone(row.score.peopleChange)">{{ signedPercent(row.score.peopleChange, loc()) }}</td>
        <td class="num" :class="tone(row.score.publicJobsChange)">{{ signedPercent(row.score.publicJobsChange, loc()) }}</td>
        <td class="num" :class="tone(row.score.privateJobsChange)">{{ signedPercent(row.score.privateJobsChange, loc()) }}</td>
        <td class="num" :class="burden(row.score.health.measured)">
          {{ signedDays(row.score.health.measured, loc(), t("dayCompact")) }}
          <span v-if="row.score.healthStartsOnBreak" class="count-flag">{{ t("newCount") }}</span>
        </td>
        <td class="num" :class="burden(row.score.schools.measured)">{{ signedPoints(row.score.schools.measured, loc()) }}</td>
        <td class="num" :class="burden(row.score.care.measured)">{{ signedPoints(row.score.care.measured, loc()) }}</td>
        <td class="num">
          {{ row.score.worstYear }}
          <span :class="tone(row.score.worstExcess)">{{ signed(row.score.worstExcess, 1, loc()) }}</span>
        </td>
      </tr>
    </tbody>
  </v-table>
  <p v-else-if="verdict !== 'early' && !uncovered.length && !early.length">{{ t("emptyFilter") }}</p>

  <template v-if="uncovered.length && verdict === 'all'">
    <h2>{{ t("noDebtTitle") }}</h2>
    <p class="note">{{ t("noDebtNote") }}</p>
    <ul>
      <li v-for="person in uncovered" :key="person.slug">
        <a :href="pageHref('person', { slug: person.slug })">{{ person.name }}</a>
        {{ t("uncoveredItem", { region: regionName(dataset, person.regionSlug), years: yearsPhrase(person), real: signedPercent(person.score?.realChange ?? null, loc()), debt: signedPoints(person.score?.debtChange ?? null, loc()) }) }}
      </li>
    </ul>
  </template>

  <template v-if="early.length && (verdict === 'all' || verdict === 'early')">
    <h2>{{ t("earlyTitle") }}</h2>
    <p class="note">{{ t("earlyNote", { n: dataset.minimumYears }) }}</p>
    <ul>
      <li v-for="person in early" :key="person.slug">
        <a :href="pageHref('person', { slug: person.slug })">{{ person.name }}</a>
        {{ t("earlyItem", { region: regionName(dataset, person.regionSlug), years: yearsPhrase(person), spells: office(person) }) }}
      </li>
    </ul>
  </template>
</template>
