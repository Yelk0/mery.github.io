<script setup lang="ts">
import { computed } from "vue"
import { useI18n } from "vue-i18n"
import type { Place } from "../domain"
import { pageHref } from "../route"
import {
  burden,
  communityBalance,
  euBalance,
  millions,
  numberLocale,
  signedMillions,
  signedPercent,
  signedPoints,
  tone,
} from "../format"

const props = defineProps<{
  places: Place[]
  windowId: string
}>()

const { t, locale } = useI18n()

const country = computed(() => props.places[0]?.kind === "country")

const headers = computed(() => {
  const keys = country.value
    ? [
        "commGrowthSpain",
        "commDuringEu",
        "commLaterGrowthSpain",
        "commLaterEu",
        "commBalance",
        "commBalanceEnd",
        "commReceivedEu",
        "commReturnedEu",
        "commEuNet",
        "commStateSpent",
        "commStateGiven",
        "commStateBack",
        "commStateNet",
        "commGdp",
        "commSpentAll",
        "commDebt",
        "commDebtLevel",
        "commBurden",
        "commBurdenChange",
      ] as const
    : [
        "commGrowth",
        "commDuring",
        "commLaterGrowth",
        "commLater",
        "commBalance",
        "commBalanceEnd",
        "commReceived",
        "commReturned",
        "commGdp",
        "commSpent",
        "commDebt",
        "commDebtLevel",
        "commBurden",
        "commBurdenChange",
      ] as const
  return keys.map((key) => t(key).replaceAll("<br>", " "))
})

const rows = computed(() => props.places.map((place) => ({
  slug: place.slug,
  name: place.name,
  href: pageHref("community", { slug: place.slug }, { window: props.windowId }),
  cells: cellsOf(place),
})))

function cellsOf(place: Place): { text: string; tone: string }[] {
  const found = place.windows.find((item) => item.window.id === props.windowId)
  if (!found) return headers.value.map(() => ({ text: "—", tone: "" }))
  if (found.baseline === "european-union") return countryCells(found)
  return regionCells(found)
}

function countryCells(account: Extract<Place["windows"][number], { baseline: "european-union" }>) {
  const flow = account.euTransfer
  const communities = account.communityTransfer
  return [
    percent(account.growth),
    percent(account.againstBaseline),
    later(account.window.laterReady, account.laterGrowth),
    later(account.window.laterReady, account.laterAgainstBaseline),
    percent(account.balance),
    signedMoney(account.balanceEnd, tone(account.balanceEnd)),
    money(flow?.received ?? null),
    money(flow?.paid ?? null),
    signedMoney(flow?.net ?? null, euBalance(flow?.net ?? null)),
    money(account.centralSpending),
    money(communities?.paid ?? null),
    money(communities?.received ?? null),
    signedMoney(communities?.net ?? null, communityBalance(communities?.net ?? null)),
    money(account.scale?.gdp ?? null),
    money(account.scale?.spent ?? null),
    signedMoney(account.debt?.change ?? null, burden(account.debt?.change ?? null)),
    money(account.debt?.total ?? null),
    share(account.scale?.debtShare ?? null),
    points(account.scale?.debtShareChange ?? null, burden(account.scale?.debtShareChange ?? null)),
  ]
}

function regionCells(account: Extract<Place["windows"][number], { baseline: "spain" }>) {
  const flow = account.stateTransfer
  return [
    percent(account.growth),
    percent(account.againstBaseline),
    later(account.window.laterReady, account.laterGrowth),
    later(account.window.laterReady, account.laterAgainstBaseline),
    percent(account.balance),
    signedMoney(account.balanceEnd, tone(account.balanceEnd)),
    money(flow?.received ?? null),
    money(flow?.paid ?? null),
    money(account.scale?.gdp ?? null),
    money(account.scale?.spent ?? null),
    signedMoney(account.debt?.change ?? null, burden(account.debt?.change ?? null)),
    money(account.debt?.total ?? null),
    share(account.scale?.debtShare ?? null),
    points(account.scale?.debtShareChange ?? null, burden(account.scale?.debtShareChange ?? null)),
  ]
}

function percent(value: number | null) {
  return { text: signedPercent(value, loc()), tone: tone(value) }
}

function later(ready: boolean, value: number | null) {
  if (!ready) return { text: t("commSoon"), tone: "" }
  return percent(value)
}

function money(value: number | null) {
  return { text: millions(value, loc(), t("commMillionUnit")), tone: "" }
}

function signedMoney(value: number | null, toneName: string) {
  return { text: signedMillions(value, loc(), t("commMillionUnit")), tone: toneName }
}

function share(value: number | null) {
  if (value === null) return { text: "—", tone: "" }
  return { text: `${formatShare(value)}%`, tone: "" }
}

function points(value: number | null, toneName: string) {
  return { text: signedPoints(value, loc()), tone: toneName }
}

function formatShare(value: number) {
  return value.toLocaleString(loc(), { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

function loc() {
  return numberLocale(locale.value)
}
</script>

<template>
  <v-table density="compact" class="sheet">
    <thead>
      <tr>
        <th></th>
        <th v-for="header in headers" :key="header" class="num">{{ header }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.slug">
        <td><a :href="row.href">{{ row.name }}</a></td>
        <td v-for="(cell, index) in row.cells" :key="index" class="num" :class="cell.tone">{{ cell.text }}</td>
      </tr>
    </tbody>
  </v-table>
</template>
