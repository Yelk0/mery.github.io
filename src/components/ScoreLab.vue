<script setup lang="ts">
import { computed, reactive, ref } from "vue"
import { useI18n } from "vue-i18n"
import type { Sources } from "../domain"
import { numberLocale, plainAmount, roundHalfUp, tone, burden } from "../format"
import WorkedExample from "./WorkedExample.vue"

const props = defineProps<{ sources: Sources }>()
const { t, locale } = useI18n()

const example = { real: 8, debt: 4, schools: 2, care: -4, health: -10 }
const dials = ["real", "debt", "schools", "care", "health"] as const
type Dial = (typeof dials)[number]
const values = reactive({ ...example })
const hot = ref<Dial | "">("")

const worst = computed(() => ({
  schools: props.sources.schoolsWorst,
  care: props.sources.careWorst,
  health: props.sources.healthWorst,
}))

const parts = computed(() => ({
  real: values.real,
  debt: -props.sources.debtWeight * values.debt,
  schools: -values.schools,
  care: -values.care,
  health: -values.health / props.sources.healthDaysPerPoint,
}))

const score = computed(() => roundHalfUp(parts.value.real + parts.value.debt + parts.value.schools + parts.value.care + parts.value.health, 1))

const limits: Record<Dial, { min: number; max: number; step: number }> = {
  real: { min: -20, max: 20, step: 0.1 },
  debt: { min: -25, max: 25, step: 0.1 },
  schools: { min: -12, max: 12, step: 0.1 },
  care: { min: -12, max: 16, step: 0.1 },
  health: { min: -50, max: 70, step: 1 },
}

function near(left: number, right: number) {
  return Math.abs(left - right) < 0.001
}

function words(points: number, plural = false) {
  const text = plainAmount(points, numberLocale(locale.value))
  if (points > 0) return t(plural ? "addPlural" : "adds", { n: text })
  if (points < 0) return t(plural ? "takeOffPlural" : "takesOff", { n: text })
  return t(plural ? "changeNothing" : "changesNothing")
}

function say(key: Dial) {
  const text = plainAmount(values[key], numberLocale(locale.value))
  const part = plainAmount(parts.value[key], numberLocale(locale.value))
  if (key === "real") return values.real > 0 ? t("labRealUp", { n: text }) : values.real < 0 ? t("labRealDown", { n: text }) : t("labRealZero")
  if (key === "debt") return values.debt > 0 ? t("labDebtUp", { n: text, half: part }) : values.debt < 0 ? t("labDebtDown", { n: text, half: part }) : t("labDebtZero")
  if (key === "schools") return values.schools > 0 ? t("labSchoolsUp", { n: text }) : values.schools < 0 ? t("labSchoolsDown", { n: text }) : t("labSchoolsZero")
  if (key === "care") return values.care > 0 ? t("labCareUp", { n: text }) : values.care < 0 ? t("labCareDown", { n: text }) : t("labCareZero")
  return values.health > 0
    ? t("labHealthUp", { n: text, days: props.sources.healthDaysPerPoint, points: part })
    : values.health < 0
      ? t("labHealthDown", { n: text, days: props.sources.healthDaysPerPoint, points: part })
      : t("labHealthZero")
}

function headline(key: Dial) {
  const text = plainAmount(values[key], numberLocale(locale.value))
  if (key === "real") return values.real > 0 ? t("realBigger", { n: text }) : values.real < 0 ? t("realSmaller", { n: text }) : t("realSame")
  if (key === "debt") return values.debt > 0 ? t("debtMore", { n: text }) : values.debt < 0 ? t("debtLess", { n: text }) : t("debtSame")
  if (key === "health") return values.health > 0 ? t("waitLonger", { n: text }) : values.health < 0 ? t("waitShorter", { n: text }) : t("waitSame")
  return values[key] > 0 ? t("gapWorse", { n: text }) : values[key] < 0 ? t("gapBetter", { n: text }) : t("gapSame")
}

function headlineTone(key: Dial) {
  return key === "real" ? tone(values[key]) : burden(values[key])
}

function meter(key: Dial) {
  const points = parts.value[key]
  const width = Math.min(100, (Math.abs(points) / 12) * 100)
  return { positive: points > 0 ? width : 0, negative: points < 0 ? width : 0 }
}

function percent(key: Dial) {
  const limit = limits[key]
  return `${((values[key] - limit.min) / (limit.max - limit.min)) * 100}%`
}

const summary = computed(() => dials.map((key) => `${t(partName(key))} ${words(parts.value[key], key === "schools")}.`).join(" "))

const exampleOn = computed(() => dials.every((key) => near(values[key], example[key])))
const missingOn = computed(() => near(values.real, example.real) && near(values.debt, example.debt) && near(values.schools, worst.value.schools) && near(values.care, worst.value.care) && near(values.health, worst.value.health))

function partName(key: Dial) {
  if (key === "real") return "partEconomy"
  if (key === "debt") return "partDebt"
  if (key === "schools") return "partSchools"
  if (key === "care") return "partCare"
  return "partSurgery"
}

function label(key: Dial) {
  if (key === "real") return "dialReal"
  if (key === "debt") return "dialDebt"
  if (key === "schools") return "dialSchools"
  if (key === "care") return "dialCare"
  return "dialHealth"
}

function useExample() {
  Object.assign(values, example)
}

function useMissing() {
  Object.assign(values, { real: example.real, debt: example.debt, ...worst.value })
}

function isWorst(key: Dial) {
  if (key === "real" || key === "debt") return false
  return near(values[key], worst.value[key])
}

function fill(key: Dial) {
  if (key === "real" || key === "debt") return
  values[key] = worst.value[key]
}
</script>

<template>
  <div class="lab">
    <div class="lab-board">
      <div class="lab-sticky">
        <p class="kicker">{{ t("labScore") }}</p>
        <p class="lab-total" :class="tone(score)" aria-live="polite">{{ score >= 0 ? "+" : "" }}{{ score.toLocaleString(locale === "en" ? "en-GB" : "es-ES", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) }}</p>
        <p class="lab-sum">{{ summary }}</p>
      </div>
      <p class="lab-key">{{ t("labKey") }}</p>
      <ol class="lab-parts">
        <li v-for="key in dials" :key="key" class="lab-part" :class="{ 'is-hot': hot === key, 'is-worst': isWorst(key) }">
          <span>{{ t(partName(key)) }}</span>
          <b :class="tone(parts[key])">{{ words(parts[key], key === "schools") }}</b>
          <span class="meter" aria-hidden="true">
            <span class="meter-neg"><i :style="{ width: `${meter(key).negative}%` }"></i></span>
            <span class="meter-zero"></span>
            <span class="meter-pos"><i :style="{ width: `${meter(key).positive}%` }"></i></span>
          </span>
        </li>
      </ol>
    </div>
    <div class="lab-controls">
      <div class="lab-presets">
        <v-btn :variant="exampleOn ? 'flat' : 'outlined'" :color="exampleOn ? 'primary' : undefined" @click="useExample">{{ t("presetExample") }}</v-btn>
        <v-btn :variant="missingOn ? 'flat' : 'outlined'" :color="missingOn ? 'primary' : undefined" @click="useMissing">{{ t("presetMissing") }}</v-btn>
      </div>
      <div v-for="key in dials" :key="key" class="dial">
        <div class="dial-top">
          <label :for="`lab-${key}`">{{ t(label(key)) }}</label>
          <output :class="headlineTone(key)">{{ headline(key) }}</output>
        </div>
        <WorkedExample v-if="key === 'real'" :year="sources.lastYear" />
        <p v-if="key === 'care'" class="lab-alert"><strong>{{ t("careAlertTitle") }}</strong> {{ t("careAlert") }}</p>
        <input
          :id="`lab-${key}`"
          v-model.number="values[key]"
          type="range"
          :min="limits[key].min"
          :max="limits[key].max"
          :step="limits[key].step"
          :style="{ '--pct': percent(key) }"
          @input="hot = key"
        >
        <p class="dial-hint">{{ say(key) }}</p>
        <v-btn v-if="key !== 'real' && key !== 'debt'" variant="outlined" :color="near(values[key], worst[key]) ? 'primary' : undefined" @click="fill(key)">{{ t("fillWorst") }}</v-btn>
      </div>
    </div>
  </div>
</template>
