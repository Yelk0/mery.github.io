<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { useRoute } from "vue-router"
import { useWords } from "../copy/words"
import { peopleSentence, pictureSentence, scoreSentence, servicesSentence, spellBody, spellYears } from "../copy/sentences"
import { termsOf, regionName } from "../data/load"
import type { Dataset } from "../domain"
import { pageHref, param } from "../route"
import { tone } from "../format"

const props = defineProps<{ dataset: Dataset }>()
const route = useRoute()
const { t } = useI18n()
const words = useWords()
const slug = computed(() => param(route.params.slug))

const person = computed(() => props.dataset.people.find((item) => item.slug === slug.value) ?? null)
const terms = computed(() => (person.value ? termsOf(props.dataset, person.value.slug) : []))
const score = computed(() => person.value?.score ?? null)

const rank = computed(() => {
  const current = person.value
  const result = score.value
  if (!current || !result || result.rank === null) return ""
  const key = terms.value.length > 1 ? "rankMany" : "rankOne"
  return t(key, { rank: result.rank, total: result.rankedCount ?? 0, years: result.countedYears, spells: terms.value.length })
})
</script>

<template>
  <p v-if="!person">{{ t("noPerson") }}</p>
  <template v-else-if="score">
    <p class="kicker"><a :href="pageHref('region', { slug: person.regionSlug })">{{ regionName(dataset, person.regionSlug) }}</a></p>
    <h1>{{ person.name }}</h1>
    <p class="when">
      {{ terms.map((term) => `${term.startedOn} – ${term.endedOn || t("inOffice")}`).join(" · ") }}
      <template v-if="person.party"> · {{ person.party }}</template>
    </p>
    <template v-if="score.eligible">
      <p class="deck">{{ t("scoreIs") }} <strong :class="tone(score.result)">{{ words.signed(score.result) }}</strong>. {{ rank }}</p>
      <p class="note">{{ scoreSentence(score, words) }}</p>
      <p class="note">{{ peopleSentence(score, words) }}</p>
      <p class="note">{{ pictureSentence(score, words) }}</p>
      <p class="note">{{ servicesSentence(score, person.regionSlug, dataset.sources, words) }}</p>
    </template>
    <template v-else-if="score.countedYears >= dataset.minimumYears">
      <p class="deck">{{ t("noDebtDeck", { years: score.countedYears }) }}</p>
      <p class="note">{{ pictureSentence(score, words) }} {{ score.realChange === null ? t("realMissingRecord") : t(score.realChange >= 0 ? "realUp" : "realDown", { n: words.amount(score.realChange) }) }}</p>
      <p class="note">{{ servicesSentence(score, person.regionSlug, dataset.sources, words) }}</p>
    </template>
    <template v-else>
      <p class="deck">{{ t("earlyDeck", { years: t(score.countedYears === 1 ? "oneCountedYear" : "manyCountedYears", { n: score.countedYears }), minimum: dataset.minimumYears }) }}</p>
      <p v-if="score.countedYears" class="note">{{ scoreSentence(score, words) }} {{ pictureSentence(score, words) }} {{ servicesSentence(score, person.regionSlug, dataset.sources, words) }}</p>
    </template>
    <p v-if="terms.length > 1" class="note">{{ t("between") }}</p>
    <p v-if="score.worstYear !== null" class="note">{{ t("worstYear", { year: score.worstYear, gap: words.signed(score.worstExcess) }) }}</p>
    <p class="note">{{ t("yearRowsNote") }}</p>
    <template v-for="term in terms" :key="term.startedOn">
      <h2>{{ spellYears(term, t("now")) }}</h2>
      <p class="note">{{ spellBody(term, person.regionSlug, dataset.sources, words) }}</p>
      <v-table density="compact">
        <thead>
          <tr>
            <th>{{ t("colYear") }}</th>
            <th class="num">{{ t("colDays") }}</th>
            <th class="num">{{ t("colRegion") }}</th>
            <th class="num">{{ t("colSpain") }}</th>
            <th class="num">{{ t("colDiff") }}</th>
            <th>{{ t("colCounted") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="year in term.years" :key="year.year">
            <td>{{ year.year }}</td>
            <td class="num">{{ year.days }}</td>
            <td class="num">{{ words.number(year.regionGrowth) }}%</td>
            <td class="num">{{ words.number(year.spainGrowth) }}%</td>
            <td class="num" :class="year.excess === null ? '' : year.excess < 0 ? 'slower' : year.excess > 0 ? 'faster' : 'similar'">{{ words.signed(year.excess) }}</td>
            <td>{{ year.counted ? t("yes") : t("no") }}</td>
          </tr>
        </tbody>
      </v-table>
      <h2>{{ t("spellCabinet") }}</h2>
      <ul v-if="term.cabinet.length" class="short-list">
        <li v-for="member in term.cabinet" :key="`${member.name}-${member.startedOn}`">
          <strong>{{ member.name }}</strong>
          <span>{{ member.office }} · {{ member.startedOn }} – {{ member.endedOn || t("openEnded") }}</span>
        </li>
      </ul>
      <p v-else>{{ t("spellCabinetEmpty") }}</p>
    </template>
  </template>
</template>
