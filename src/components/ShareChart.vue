<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { sharePlot } from "../chart"
import type { Term, YearlyEconomy } from "../domain"

const props = defineProps<{
  firstYear: number
  lastYear: number
  economy: YearlyEconomy[]
  terms: Term[]
}>()

const { t } = useI18n()
const plot = computed(() => sharePlot(props.firstYear, props.lastYear, props.economy, props.terms))
</script>

<template>
  <figure v-if="plot" class="chart">
    <svg :viewBox="`0 0 ${plot.width} ${plot.height}`" role="img" :aria-label="t('chartLabel')">
      <rect
        v-for="(band, index) in plot.bands"
        :key="index"
        :class="`band band-${band.tone}`"
        :x="band.x"
        y="16"
        :width="band.width"
        height="196"
      />
      <text class="axis" x="4" y="27">{{ plot.top }}</text>
      <text class="axis" x="4" y="212">{{ plot.bottom }}</text>
      <polyline class="series" :points="plot.line" />
      <text v-for="label in plot.labels" :key="label.year" class="axis" :x="label.x" y="232" text-anchor="middle">{{ label.year }}</text>
    </svg>
  </figure>
</template>
