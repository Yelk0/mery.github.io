<script setup lang="ts">
import { useI18n } from "vue-i18n"
import type { Dataset } from "../domain"
import { pageHref } from "../route"
import ScoreLab from "../components/ScoreLab.vue"

defineProps<{ dataset: Dataset }>()
const { t } = useI18n()
</script>

<template>
  <p class="kicker">{{ t("methodKicker") }}</p>
  <h1>{{ t("methodTitle") }}</h1>
  <p class="deck">{{ t("methodDeck") }}</p>
  <ScoreLab :sources="dataset.sources" />
  <p class="note">{{ t("methodNote", { n: dataset.minimumYears }) }}</p>
  <p class="note">
    {{ t("sources") }}
    <a :href="dataset.sources.volumeUrl">{{ t("sourceReal") }}</a>,
    <a :href="dataset.sources.debtUrl">{{ t("sourceDebt") }}</a>,
    <a :href="dataset.sources.schoolsUrl">{{ t("sourceSchools") }}</a>,
    <a :href="dataset.sources.careUrl">{{ t("sourceCare") }}</a>,
    <a :href="dataset.sources.healthUrl">{{ t("sourceHealth") }}</a>.
    <a :href="pageHref('data')">{{ t("dataLink") }}</a>.
    <a :href="pageHref('missing')">{{ t("sourceMissing") }}</a>.
  </p>
</template>
