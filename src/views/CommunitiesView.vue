<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { useRoute } from "vue-router"
import { chosenWindow } from "../data/load"
import type { Dataset } from "../domain"
import { pageHref, queryText } from "../route"
import AccountsTable from "../components/AccountsTable.vue"

const props = defineProps<{ dataset: Dataset }>()
const route = useRoute()
const { t } = useI18n()
const windowId = computed(() => queryText(route.query.window))

const chosen = computed(() => chosenWindow(props.dataset, windowId.value))
</script>

<template>
  <p>{{ t("commKicker") }}</p>
  <h1>{{ t("commTitle") }}</h1>
  <p class="deck">{{ t("commDeck") }}</p>
  <p class="note">{{ t("commNote") }}</p>
  <div v-if="chosen" class="filters">
    <v-chip
      v-for="item in dataset.windows"
      :key="item.id"
      :href="pageHref('communities', {}, { window: item.id })"
      :color="item.id === chosen.id ? 'primary' : undefined"
      label
    >
      {{ item.start }}–{{ item.end }}<template v-if="item.open"> · {{ t("commOpen") }}</template>
    </v-chip>
  </div>
  <template v-if="chosen">
    <h2>{{ dataset.country.name }}</h2>
    <AccountsTable :places="[dataset.country]" :window-id="chosen.id" />
    <AccountsTable :places="dataset.regions" :window-id="chosen.id" />
  </template>
  <p class="note">{{ t("commScaleNote") }}</p>
  <p class="note">{{ t("commFlowNote") }}</p>
</template>
