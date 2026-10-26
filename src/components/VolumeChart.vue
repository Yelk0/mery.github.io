<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import { volumePlot } from "../chart"
import type { Law, VolumePoint } from "../domain"

const props = defineProps<{
  points: VolumePoint[]
  laws: Law[]
  country: boolean
  openId: string | null
}>()

const emit = defineEmits<{ open: [id: string] }>()
const { t } = useI18n()
const plot = computed(() => volumePlot(props.points, props.laws))
</script>

<template>
  <div v-if="plot" class="chart volume-chart">
    <div class="plot">
      <div :style="{ height: `${plot.room}px` }"></div>
      <div class="plot-sheet">
        <svg :viewBox="`0 0 ${plot.width} ${plot.height}`" role="img" :aria-label="t(country ? 'commChartEu' : 'commChart')">
          <line v-if="plot.baseline !== null" class="baseline" x1="46" :x2="plot.width - 16" :y1="plot.baseline" :y2="plot.baseline" />
          <text class="axis" x="4" y="29">{{ plot.top }}</text>
          <text class="axis" x="4" :y="plot.height - 28">{{ plot.bottom }}</text>
          <polyline class="series" :points="plot.line" />
          <text v-for="label in plot.labels" :key="label.year" class="axis" :x="label.x" :y="plot.height - 8" text-anchor="middle">{{ label.year }}</text>
        </svg>
        <button
          v-for="dot in plot.dots"
          :key="dot.id"
          type="button"
          class="law-dot"
          :class="{ 'is-on': dot.id === openId }"
          :style="{ left: `${dot.x}%`, top: `calc(${dot.anchor}% - ${dot.lane * 46}px)` }"
          :aria-label="dot.title"
          @click="emit('open', dot.id)"
        ><span></span></button>
      </div>
    </div>
  </div>
</template>
