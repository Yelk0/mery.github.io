<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import type { Dataset } from "../domain"
import { dataFile } from "../data/load"
import { pageHref } from "../route"

const props = defineProps<{ dataset: Dataset }>()
const { t, locale } = useI18n()

function row(title: string, body: string, links: { href: string; label: string; outside: boolean }[], inScore: boolean) {
  return { title, body, links, inScore }
}

function open(href: string, label: string, outside = true) {
  return { href, label, outside }
}

const scored = computed(() => {
  locale.value
  const sources = props.dataset.sources
  const from = sources.firstYear
  const to = sources.lastYear
  return [
  row(t("dataRealTitle"), t("dataReal", { title: sources.volumeTitle, from, to }), [open(sources.volumeUrl, t("dataOpen"))], true),
  row(t("dataDebtTitle"), t("dataDebt", { title: sources.debtTitle, from, to }), [open(sources.debtUrl, t("dataOpen")), open(sources.debtFile, t("dataCsv"))], true),
  row(t("dataSchoolsTitle"), t("dataSchools", { title: sources.schoolsTitle, from: sources.schoolsFirstYear, to }), [open(sources.schoolsUrl, t("dataOpen"))], true),
  row(t("dataCareTitle"), t("dataCare", { title: sources.careTitle, from: sources.careFirstYear, to }), [open(sources.careUrl, t("dataOpen"))], true),
  row(t("dataHealthTitle"), t("dataHealth", { title: sources.healthTitle, from: sources.healthFirstYear, to }), [open(sources.healthUrl, t("dataOpen")), open(pageHref("missing"), t("dataBreak"), false)], true),
  ]
})

const beside = computed(() => {
  locale.value
  const sources = props.dataset.sources
  const from = sources.firstYear
  const to = sources.lastYear
  return [
  row(t("dataGdpTitle"), t("dataGdp", { table: sources.gdpTable, title: sources.gdpTitle, from, to }), [open(sources.gdpUrl, t("dataOpen"))], false),
  row(t("dataPersonTitle"), t("dataPerson", { table: sources.perCapitaTable, title: sources.perCapitaTitle, from, to }), [open(sources.perCapitaUrl, t("dataOpen"))], false),
  row(t("dataPopTitle"), t("dataPop"), [open(sources.gdpUrl, `${t("dataTable")} ${sources.gdpTable}`), open(sources.perCapitaUrl, `${t("dataTable")} ${sources.perCapitaTable}`)], false),
  row(t("dataJobsTitle"), t("dataJobs", { table: sources.jobsTable, title: sources.jobsTitle, from: sources.jobsFirstYear }), [open(sources.jobsUrl, t("dataOpen"))], false),
  row(t("dataBalanceTitle"), t("dataBalance", { title: sources.balanceTitle, from, to }), [open(sources.balanceUrl, t("dataOpen"))], false),
  row(t("dataSpainTitle"), t("dataSpain", { title: sources.spainTitle, from, to }), [open(sources.spainUrl, t("dataOpen"))], false),
  row(t("dataCentralTitle"), t("dataCentral", { title: sources.centralTitle, from: sources.centralFrom, to: sources.centralTo }), [open(sources.centralUrl, t("dataOpen"))], false),
  row(t("dataSpainDebtTitle"), t("dataSpainDebt", { title: sources.spainDebtTitle }), [open(sources.spainDebtUrl, t("dataOpen")), open(sources.spainDebtFile, t("dataCsv"))], false),
  row(t("dataEuTitle"), t("dataEu", { title: sources.euTitle }), [open(sources.euUrl, t("dataOpen"))], false),
  row(t("dataEuVolumeTitle"), t("dataEuVolume", { title: sources.euVolumeTitle, from: sources.euVolumeFrom, to: sources.euVolumeTo }), [open(sources.euVolumeUrl, t("dataOpen"))], false),
  row(t("dataBudgetTitle"), t("dataBudget", { title: sources.budgetTitle, to }), [open(sources.budgetUrl, t("dataOpen"))], false),
  row(t("dataStateBudgetTitle"), t("dataStateBudget", { title: sources.stateBudgetTitle, from: sources.stateBudgetFrom, to: sources.stateBudgetTo }), [open(sources.stateBudgetUrl, t("dataOpen"))], false),
  row(t("dataFlowTitle"), t("dataFlow", { title: sources.flowTitle, to: sources.flowLastYear }), [open(sources.flowUrl, t("dataOpen"))], false),
  ]
})
</script>

<template>
  <p class="kicker">{{ t("dataKicker") }}</p>
  <h1>{{ t("dataTitle") }}</h1>
  <p class="deck">{{ t("dataDeck") }}</p>
  <h2>{{ t("dataInTitle") }}</h2>
  <p class="note">{{ t("dataInDeck") }}</p>
  <ul class="compare sources">
    <li v-for="item in scored" :key="item.title">
      <div>
        <strong>{{ item.title }}</strong>
        <span>{{ item.body }}</span>
        <p class="source-links">
          <a v-for="link in item.links" :key="link.href" :href="link.href" :target="link.outside ? '_blank' : undefined" :rel="link.outside ? 'noopener' : undefined">{{ link.label }}</a>
        </p>
      </div>
      <b class="faster">{{ t("dataInBadge") }}</b>
    </li>
  </ul>
  <h2>{{ t("dataBesideTitle") }}</h2>
  <p class="note">{{ t("dataBesideDeck") }}</p>
  <ul class="compare sources">
    <li v-for="item in beside" :key="item.title">
      <div>
        <strong>{{ item.title }}</strong>
        <span>{{ item.body }}</span>
        <p class="source-links">
          <a v-for="link in item.links" :key="link.href + link.label" :href="link.href" target="_blank" rel="noopener">{{ link.label }}</a>
        </p>
      </div>
      <b>{{ t("dataOutBadge") }}</b>
    </li>
  </ul>
  <h2>{{ t("dataPeopleTitle") }}</h2>
  <p class="note">{{ t("dataPeopleDeck") }}</p>
  <ul class="compare sources">
    <li>
      <div>
        <strong>{{ t("dataPeopleTitle") }}</strong>
        <span>{{ t("dataOffice", { from: dataset.sources.firstYear, to: dataset.sources.lastYear }) }}</span>
        <p class="source-links">
          <a href="https://www.wikidata.org/wiki/Property:P39" target="_blank" rel="noopener">Wikidata P39</a>
          <a href="https://es.wikipedia.org/" target="_blank" rel="noopener">Wikipedia</a>
          <a :href="dataFile('people.json')">{{ t("dataList") }}</a>
          <a :href="dataFile('office-corrections.json')">{{ t("dataFixes") }}</a>
        </p>
      </div>
    </li>
  </ul>
</template>
