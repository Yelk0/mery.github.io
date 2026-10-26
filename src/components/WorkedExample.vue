<script setup lang="ts">
import { useI18n } from "vue-i18n"

defineProps<{ year: number }>()
const { t } = useI18n()

const years = [
  {
    title: "exBefore",
    rows: [
      ["exM0", "exStartNum", "exStartDen", "exStartShare", "exStartStep", "exStartPeople", "exGap0", ""],
      ["exC0", "exStartNum", "exStartDen", "exStartShare", "exStartStep", "exStartPeople", "exGap0", ""],
    ],
  },
  {
    title: "exYear1",
    rows: [
      ["exM0", "exM1num", "exStartDen", "exM1share", "exM1step", "exM1people", "exM1Gap", "slower"],
      ["exC0", "exC1num", "exStartDen", "exC1share", "exC1step", "exC1people", "exC1Gap", "faster"],
    ],
  },
  {
    title: "exYear2",
    rows: [
      ["exM0", "exM2num", "exDen2", "exM2share", "exM2step", "exM1people", "exM2Gap", "slower"],
      ["exC0", "exC2num", "exDen2", "exC2share", "exC2step", "exC2people", "exC2Gap", "faster"],
    ],
  },
  {
    title: "exYear3",
    rows: [
      ["exM0", "exM3num", "exDen2", "exM3share", "exM3step", "exM3people", "exM3Gap", "slower"],
      ["exC0", "exC3num", "exDen2", "exC3share", "exC3step", "exC3people", "exC3Gap", "faster"],
    ],
  },
  {
    title: "exYear4",
    rows: [
      ["exM0", "exM3num", "exDen4", "exM4share", "exM4step", "exM3people", "exM4Gap", "slower"],
      ["exC0", "exC4num", "exDen4", "exC4share", "exC4step", "exC4people", "exC4Gap", "faster"],
    ],
  },
] as const
</script>

<template>
  <div class="pile">
    <ol class="pile-years">
      <li>{{ t("pileBefore") }}</li>
      <li>{{ t("pileYear") }}</li>
      <li>{{ t("pileYear") }}</li>
      <li>{{ t("pileYear") }}</li>
      <li>{{ t("pileYear") }}</li>
      <li class="pile-end">{{ t("pileEnd") }}</li>
    </ol>
    <p>{{ t("pileCaption", { year }) }}</p>
    <details class="learn">
      <summary>{{ t("exMore") }}</summary>
      <div class="worked">
        <p class="worked-title">{{ t("exTitle") }}</p>
        <p>{{ t("exIntro") }}</p>
        <p class="formula">
          <span class="over"><b>{{ t("exFormulaNum") }}</b><span>{{ t("exFormulaDen") }}</span></span>
          <span class="eq">− 1</span>
        </p>
        <template v-for="year in years" :key="year.title">
          <p class="worked-year">{{ t(year.title) }}</p>
          <ol class="sums">
            <li v-for="row in year.rows" :key="row[0]" class="sum">
              <b>{{ t(row[0]) }}</b>
              <strong :class="row[7]">{{ t(row[6]) }}</strong>
              <span class="frac">
                <span class="over"><b>{{ t(row[1]) }}</b><span>{{ t(row[2]) }}</span></span>
                <span class="eq">=</span>
                <span class="share">{{ t(row[3]) }}</span>
              </span>
              <em>{{ t(row[4]) }} = <span :class="row[7]">{{ t(row[6]) }}</span></em>
              <i>{{ t(row[5]) }}</i>
            </li>
          </ol>
        </template>
        <p>{{ t("exFoot") }}</p>
      </div>
    </details>
  </div>
</template>
