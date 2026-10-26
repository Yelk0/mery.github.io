<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { useWords } from "../copy/words"
import type { Dataset, Score } from "../domain"
import { pageHref } from "../route"

const props = defineProps<{ dataset: Dataset }>()
const { t } = useI18n()
const words = useWords()

function covered(read: (score: Score) => number | null) {
  const ranked = props.dataset.people.flatMap((person) => (person.score?.eligible ? [person.score] : []))
  return { have: ranked.filter((score) => read(score) !== null).length, total: ranked.length }
}

const schools = computed(() => covered((score) => score.schools.measured))
const health = computed(() => covered((score) => score.health.measured))
const care = computed(() => covered((score) => score.care.measured))
const debt = computed(() => covered((score) => score.debtChange))
const real = computed(() => covered((score) => score.realChange))
const blank = computed(() => health.value.total - health.value.have)
const flagged = computed(() => props.dataset.people.find((person) => person.score?.healthStartsOnBreak) ?? null)
const spell = computed(() => {
  const person = flagged.value
  if (!person) return null
  return props.dataset.regions.flatMap((region) => region.terms).find((term) => term.personSlug === person.slug && term.measure?.healthStartsOnBreak) ?? null
})
const asks = [1, 2, 3, 4, 5, 6] as const
</script>

<template>
  <p class="kicker">{{ t("missingKicker") }}</p>
  <h1>{{ t("missingTitle") }}</h1>
  <p class="deck">{{ t("missingDeck") }}</p>
  <div class="coverage">
    <article class="full">
      <b>{{ t("shareOf", schools) }}</b>
      <p>{{ t("cardSchools", { from: dataset.sources.schoolsFirstYear, to: dataset.sources.lastYear }) }}</p>
    </article>
    <article class="thin">
      <b>{{ t("shareOf", health) }}</b>
      <p>{{ t("cardHealth", { from: dataset.sources.healthFirstYear, to: dataset.sources.lastYear }) }}</p>
    </article>
    <article class="thin">
      <b>{{ t("shareOf", care) }}</b>
      <p>{{ t("cardCare", { from: dataset.sources.careFirstYear, to: dataset.sources.lastYear }) }}</p>
    </article>
  </div>
  <section v-if="flagged?.score && spell?.measure" class="break-story">
    <div class="break-pair">
      <div>
        <span>{{ t("decLabel", { year: dataset.sources.healthBreakYear - 1 }) }}</span>
        <b>{{ words.number(flagged.score.healthOldDays, 0) }}</b>
        <em>{{ t("daysOld") }}</em>
      </div>
      <div>
        <span>{{ t("decLabel", { year: dataset.sources.healthBreakYear }) }}</span>
        <b class="slower">{{ words.number(flagged.score.healthBreakOpenDays, 0) }}</b>
        <em>{{ t("daysNew") }}</em>
      </div>
    </div>
    <p>
      {{ t("breakLead", { old: words.number(flagged.score.healthOldDays, 0), open: words.number(flagged.score.healthBreakOpenDays, 0) }) }}
      <a :href="pageHref('person', { slug: flagged.slug })">{{ flagged.name }}</a>{{ t("breakTail", { open: words.number(flagged.score.healthBreakOpenDays, 0), after: words.number(spell.measure.healthAfter, 0) }) }}
    </p>
  </section>
  <h2>{{ t("asksTitle") }}</h2>
  <ol class="asks">
    <li v-for="item in asks" :key="item">
      <div>
        <strong>{{ t(`ask${item}Title`) }}</strong>
        <span>{{ t(`ask${item}Body`, { blank, total: health.total }) }}</span>
      </div>
    </li>
  </ol>
  <h2>{{ t("coverTitle") }}</h2>
  <ul class="compare">
    <li><div><strong>{{ t("coverSchoolsTitle") }}</strong><span>{{ t("coverSchools", { from: dataset.sources.schoolsFirstYear, to: dataset.sources.lastYear }) }}</span></div><b class="faster">{{ t("shareOf", schools) }}</b></li>
    <li><div><strong>{{ t("coverHealthTitle") }}</strong><span>{{ t("coverHealth", { from: dataset.sources.healthFirstYear, to: dataset.sources.lastYear }) }}</span></div><b class="slower">{{ t("shareOf", health) }}</b></li>
    <li><div><strong>{{ t("coverCareTitle") }}</strong><span>{{ t("coverCare", { from: dataset.sources.careFirstYear, to: dataset.sources.lastYear }) }}</span></div><b class="slower">{{ t("shareOf", care) }}</b></li>
    <li><div><strong>{{ t("coverDebtTitle") }}</strong><span>{{ t("coverDebt", { from: dataset.sources.firstYear, to: dataset.sources.lastYear }) }}</span></div><b class="faster">{{ t("shareOf", debt) }}</b></li>
    <li><div><strong>{{ t("coverRealTitle") }}</strong><span>{{ t("coverReal", { from: dataset.sources.firstYear, to: dataset.sources.lastYear }) }}</span></div><b>{{ t("shareOf", real) }}</b></li>
  </ul>
  <p class="note">{{ t("missingFoot") }}<a :href="pageHref('method')">{{ t("missingMethod") }}</a>.</p>
</template>
