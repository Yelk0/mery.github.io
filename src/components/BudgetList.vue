<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import {
  BUDGET_POLICIES,
  FOREIGN_PARTS,
  GENERAL_PARTS,
  JUSTICE_PARTS,
  LEADERSHIP_PARTS,
  type Budget,
  type BudgetPolicy,
} from "../domain"
import { formatNumber, numberLocale } from "../format"
import { foreignLabel, generalLabel, justiceLabel, leadershipLabel, policyLabel } from "../i18n/labels"

const props = defineProps<{ budget: Budget | null }>()
const { t, locale } = useI18n()

const always: BudgetPolicy[] = ["health", "education", "care", "housing", "transport", "interest"]

const rows = computed(() => {
  const budget = props.budget
  if (!budget) return []
  return policies(budget).flatMap((policy) => {
    const share = budget.share[policy]
    if (share === undefined) return []
    return [{
      key: policy,
      label: text(policyLabel[policy]),
      share,
      gdp: budget.gdp[policy] ?? null,
      parts: partsOf(budget, policy),
    }]
  })
})

const spainParts = computed(() => Boolean(props.budget?.parts.leadership))
const span = computed(() => {
  const budget = props.budget
  if (!budget) return ""
  return budget.from === budget.to ? `${budget.from}` : `${budget.from}–${budget.to}`
})

function policies(budget: Budget): BudgetPolicy[] {
  const shown: BudgetPolicy[] = []
  for (const policy of always) {
    if (budget.share[policy] !== undefined) shown.push(policy)
  }
  for (const policy of BUDGET_POLICIES) {
    if (always.includes(policy) || policy === "rest" || policy === "pensions") continue
    const share = budget.share[policy]
    if (share !== undefined && share > 0) shown.push(policy)
  }
  const pensions = budget.share.pensions
  if (pensions !== undefined && pensions > 0) {
    const interest = shown.indexOf("interest")
    shown.splice(interest + 1, 0, "pensions")
  }
  const rest = budget.share.rest
  if (rest !== undefined && rest > 0) shown.push("rest")
  return shown
}

function partsOf(budget: Budget, policy: BudgetPolicy) {
  if (policy === "general") return listed(budget.parts.general, budget.partsGdp.general, GENERAL_PARTS, generalLabel)
  if (policy === "leadership") return listed(budget.parts.leadership, budget.partsGdp.leadership, LEADERSHIP_PARTS, leadershipLabel)
  if (policy === "justice") return listed(budget.parts.justice, budget.partsGdp.justice, JUSTICE_PARTS, justiceLabel)
  if (policy === "foreign") return listed(budget.parts.foreign, budget.partsGdp.foreign, FOREIGN_PARTS, foreignLabel)
  return []
}

function listed<Key extends string>(
  shares: Partial<Record<Key, number>> | undefined,
  gdp: Partial<Record<Key, number>> | undefined,
  order: readonly Key[],
  labels: Record<Key, string>,
) {
  if (!shares) return []
  return order.flatMap((key) => {
    const share = shares[key]
    if (share === undefined || share <= 0) return []
    return [{ key, label: text(labels[key]), share, gdp: gdp?.[key] ?? null }]
  })
}

function text(key: string) {
  return t(key as "commHealth")
}

function percent(value: number, digits: number) {
  return formatNumber(value, digits, numberLocale(locale.value))
}
</script>

<template>
  <p v-if="!budget">{{ t("commBudgetMissing") }}</p>
  <template v-else>
    <p v-if="!budget.complete" class="note">{{ t("commBudgetPartial", { span }) }}</p>
    <p v-if="rows.some((row) => row.parts.length)" class="note">{{ t(spainParts ? "commBudgetPartsSpain" : "commBudgetParts") }}</p>
    <ul class="budget" :class="{ 'budget-gdp': Object.keys(budget.gdp).length }">
      <li v-for="row in rows" :key="row.key">
        <span>{{ row.label }}</span>
        <b>
          <small v-if="row.gdp !== null" class="of-gdp">{{ t("commBudgetGdp", { n: percent(row.gdp, 2) }) }}</small>
          {{ percent(row.share, 1) }}%
        </b>
        <i><em :style="{ width: `${Math.max(0, row.share)}%` }"></em></i>
        <ul v-if="row.parts.length" class="parts">
          <li v-for="part in row.parts" :key="part.key">
            <span>{{ part.label }}</span>
            <b>
              <small v-if="part.gdp !== null" class="of-gdp">{{ t("commBudgetGdp", { n: percent(part.gdp, 2) }) }}</small>
              {{ percent(part.share, 2) }}%
            </b>
            <i><em :style="{ width: `${Math.max(0, part.share)}%` }"></em></i>
          </li>
        </ul>
      </li>
    </ul>
  </template>
</template>
