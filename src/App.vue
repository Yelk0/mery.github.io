<script setup lang="ts">
import { onMounted, ref, watch } from "vue"
import { useI18n } from "vue-i18n"
import { useRoute } from "vue-router"
import { loadDataset, placeBySlug } from "./data/load"
import type { Dataset } from "./domain"
import { languageHref, pageHref, param, titleKey } from "./route"

const route = useRoute()
const { t, locale } = useI18n()
const dataset = ref<Dataset | null>(null)
const error = ref("")

onMounted(async () => {
  try {
    dataset.value = await loadDataset()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
  }
})

watch([() => route.fullPath, dataset], () => {
  const code = route.params.lang === "en" ? "en" : "es"
  locale.value = code
  localStorage.setItem("plan-mery-lang", code)
  document.documentElement.lang = code
  const data = dataset.value
  const slug = param(route.params.slug)
  if (data && route.name === "person") {
    const person = data.people.find((item) => item.slug === slug)
    if (person) {
      document.title = person.name
      return
    }
  }
  if (data && (route.name === "region" || route.name === "community")) {
    const place = placeBySlug(data, slug)
    if (place) {
      document.title = place.name
      return
    }
  }
  document.title = t(titleKey(route.name))
}, { immediate: true })

function on(page: string) {
  const name = route.name
  return name === page
    || (page === "presidents" && (name === "person" || name === "region"))
    || (page === "communities" && name === "community")
}
</script>

<template>
  <v-app>
    <v-sheet class="top" border>
      <a class="brand" :href="pageHref('presidents')">Plan Mery</a>
      <nav>
        <v-btn variant="text" :href="pageHref('presidents')" :active="on('presidents')">{{ t("navHome") }}</v-btn>
        <v-btn variant="text" :href="pageHref('communities')" :active="on('communities')">{{ t("navCommunities") }}</v-btn>
        <v-btn variant="text" :href="pageHref('method')" :active="on('method')">{{ t("navMethod") }}</v-btn>
        <v-btn variant="text" :href="pageHref('data')" :active="on('data')">{{ t("navData") }}</v-btn>
        <v-btn variant="text" :href="pageHref('missing')" :active="on('missing')">{{ t("navMissing") }}</v-btn>
      </nav>
      <v-spacer />
      <v-btn :href="languageHref('es')" :variant="route.params.lang === 'es' ? 'flat' : 'text'" :aria-pressed="route.params.lang === 'es'">ES</v-btn>
      <v-btn :href="languageHref('en')" :variant="route.params.lang === 'en' ? 'flat' : 'text'" :aria-pressed="route.params.lang === 'en'">EN</v-btn>
    </v-sheet>
    <v-main>
      <v-container>
        <v-progress-circular v-if="!dataset && !error" indeterminate color="primary" />
        <v-alert v-else-if="error" type="error">{{ t("loadError", { error }) }}</v-alert>
        <router-view v-else-if="dataset" v-slot="{ Component }">
          <component :is="Component" :dataset="dataset" />
        </router-view>
      </v-container>
    </v-main>
  </v-app>
</template>
