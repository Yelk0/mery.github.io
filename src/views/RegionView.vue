<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { useRoute } from "vue-router"
import { useWords } from "../copy/words"
import type { Dataset } from "../domain"
import { pageHref, param } from "../route"
import { tone } from "../format"
import ShareChart from "../components/ShareChart.vue"

const props = defineProps<{ dataset: Dataset }>()
const route = useRoute()
const { t } = useI18n()
const words = useWords()
const slug = computed(() => param(route.params.slug))

const region = computed(() => props.dataset.regions.find((item) => item.slug === slug.value) ?? null)
const terms = computed(() => [...(region.value?.terms ?? [])].sort((left, right) => left.startedOn.localeCompare(right.startedOn)))
</script>

<template>
  <p v-if="!region">{{ t("noRegion", { name: slug }) }}</p>
  <template v-else>
    <p class="kicker"><a :href="pageHref('presidents')">{{ t("navHome") }}</a> · {{ region.ineLabel }}</p>
    <h1>{{ region.name }}</h1>
    <p class="deck">{{ t("chartDeck") }}</p>
    <ShareChart :first-year="dataset.sources.firstYear" :last-year="dataset.sources.lastYear" :economy="region.economy" :terms="terms" />
    <ol class="timeline">
      <li v-for="term in terms" :key="term.startedOn">
        <div>
          <a :href="pageHref('person', { slug: term.personSlug })">{{ term.personName }}</a>
          <span v-if="term.party" class="party">{{ term.party }}</span>
          <p class="when">{{ term.startedOn }} – {{ term.endedOn || t("inOffice") }}</p>
        </div>
        <div class="result">
          <strong :class="tone(term.measure?.result ?? null)">{{ words.signed(term.measure?.result ?? null) }}</strong>
          <span>{{ t("timelineLine", {
            real: words.signedPercent(term.measure?.realChange ?? null),
            debt: words.signedPoints(term.measure?.debtChange ?? null),
            economy: words.signedPercent(term.measure?.outputChange ?? null),
            person: words.signed(term.measure?.indexChange ?? null),
            people: words.signedPercent(term.measure?.peopleChange ?? null),
            publicJobs: words.signedPercent(term.measure?.publicJobsChange ?? null),
            privateJobs: words.signedPercent(term.measure?.privateJobsChange ?? null),
            health: words.signedDays(term.measure?.healthChange ?? null),
            flag: term.measure?.healthStartsOnBreak ? t("newCountInline") : "",
            schools: words.signedPoints(term.measure?.schoolsChange ?? null),
            care: words.signedPoints(term.measure?.careChange ?? null),
          }) }}</span>
        </div>
      </li>
    </ol>
    <h2>{{ t("cabinetTitle") }}</h2>
    <p class="note">{{ t("cabinetNote") }}</p>
    <v-table v-if="region.members.length" density="compact">
      <thead>
        <tr>
          <th>{{ t("colName") }}</th>
          <th>{{ t("colPost") }}</th>
          <th>{{ t("colFrom") }}</th>
          <th>{{ t("colUntil") }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in region.members" :key="`${member.name}-${member.startedOn}`">
          <td>{{ member.name }}</td>
          <td>{{ member.office }}</td>
          <td>{{ member.startedOn || "—" }}</td>
          <td>{{ member.endedOn || "—" }}</td>
        </tr>
      </tbody>
    </v-table>
    <p v-else>{{ t("cabinetEmpty", { name: region.name }) }}</p>
  </template>
</template>
