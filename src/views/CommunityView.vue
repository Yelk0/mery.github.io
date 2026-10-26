<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue"
import { useI18n } from "vue-i18n"
import { useRoute } from "vue-router"
import { useWords } from "../copy/words"
import { chosenWindow, placeBySlug } from "../data/load"
import type { CountryWindow, Dataset, Law, RegionWindow } from "../domain"
import { burden, communityBalance, euBalance, millions, numberLocale, signedMillions, signedPercent, signedPoints, tone } from "../format"
import { pageHref, param, queryText } from "../route"
import BudgetList from "../components/BudgetList.vue"
import VolumeChart from "../components/VolumeChart.vue"

const props = defineProps<{ dataset: Dataset }>()
const route = useRoute()
const { t, locale } = useI18n()
const words = useWords()
const openLaw = ref<string | null>(null)
const slug = computed(() => param(route.params.slug))
const windowId = computed(() => queryText(route.query.window))

const place = computed(() => placeBySlug(props.dataset, slug.value))
const country = computed(() => place.value?.kind === "country")
const laws = computed(() => (place.value?.kind === "region" ? [...place.value.laws].sort((left, right) => left.votedOn.localeCompare(right.votedOn)) : []))
const selected = computed(() => laws.value.find((law) => law.id === openLaw.value) ?? null)
const unit = computed(() => t("commMillionUnit"))
const loc = computed(() => numberLocale(locale.value))

function show(id: string) {
  openLaw.value = openLaw.value === id ? null : id
  if (openLaw.value) document.getElementById("vote")?.scrollIntoView({ block: "nearest" })
}

function kindLabel(kind: Law["kind"]) {
  return t(kind === "presupuestos" ? "commKindBudget" : "commKindLey")
}

function money(value: number | null) {
  return millions(value, loc.value, unit.value)
}

function signedMoney(value: number | null) {
  return signedMillions(value, loc.value, unit.value)
}

function shareOf(part: number | null, total: number | null) {
  if (part === null || !total) return null
  return Math.round((part / total) * 1000) / 10
}

function span(from: number | null, to: number | null) {
  if (from === null || to === null) return ""
  return from === to ? `${from}` : `${from}–${to}`
}

function countryAccount(account: RegionWindow | CountryWindow): CountryWindow | null {
  return account.baseline === "european-union" ? account : null
}

async function focusWindow() {
  const id = windowId.value
  if (!id) return
  await nextTick()
  document.getElementById(`block-${id}`)?.scrollIntoView()
}

onMounted(focusWindow)
watch(windowId, focusWindow)
</script>

<template>
  <p v-if="!place">{{ t("commNoRegion") }}</p>
  <template v-else>
    <p class="kicker"><a :href="pageHref('communities', {}, { window: chosenWindow(dataset, windowId)?.id ?? '' })">{{ t("commTitle") }}</a></p>
    <h1>{{ place.name }}</h1>
    <p v-if="country" class="note">{{ t("commSpain") }}</p>
    <p v-else-if="place.kind === 'region' && place.foral" class="note">{{ t("commForal") }}</p>
    <p class="note">{{ t(country ? "commChartEu" : "commChart") }} {{ t("commNote") }}</p>
    <VolumeChart :points="place.volume" :laws="laws" :country="country" :open-id="openLaw" @open="show" />

    <section v-if="selected" id="vote" class="vote is-on">
      <p class="kicker">{{ kindLabel(selected.kind) }} · {{ selected.votedOn }}</p>
      <h2>{{ selected.title }}</h2>
      <p>{{ selected.sentence }}</p>
      <p class="note">{{ t("commNote") }}</p>
      <div class="vote-sides">
        <div>
          <h3>{{ t("commVoteFor") }}</h3>
          <ul class="votes">
            <li v-for="vote in selected.votes.filter((item) => item.side === 'for')" :key="vote.group">
              <span>{{ vote.group }}</span>
              <i><em :style="{ width: `${(100 * vote.count) / Math.max(...selected.votes.map((item) => item.count), 1)}%` }"></em></i>
              <b>{{ vote.count.toLocaleString(loc) }}</b>
            </li>
            <li v-if="!selected.votes.some((item) => item.side === 'for')"><p>{{ t("commVoteNone") }}</p></li>
          </ul>
        </div>
        <div>
          <h3>{{ t("commVoteAgainst") }}</h3>
          <ul class="votes against">
            <li v-for="vote in selected.votes.filter((item) => item.side === 'against')" :key="vote.group">
              <span>{{ vote.group }}</span>
              <i><em :style="{ width: `${(100 * vote.count) / Math.max(...selected.votes.map((item) => item.count), 1)}%` }"></em></i>
              <b>{{ vote.count.toLocaleString(loc) }}</b>
            </li>
            <li v-if="!selected.votes.some((item) => item.side === 'against')"><p>{{ t("commVoteNone") }}</p></li>
          </ul>
        </div>
      </div>
      <h3>{{ t("commVoteAbstain") }}</h3>
      <ul class="votes abstain">
        <li v-for="vote in selected.votes.filter((item) => item.side === 'abstain')" :key="vote.group" class="is-thin">
          <span>{{ vote.group }}</span>
          <i><em :style="{ width: `${(100 * vote.count) / Math.max(...selected.votes.map((item) => item.count), 1)}%` }"></em></i>
          <b>{{ vote.count.toLocaleString(loc) }}</b>
        </li>
        <li v-if="!selected.votes.some((item) => item.side === 'abstain')"><p>{{ t("commVoteNone") }}</p></li>
      </ul>
      <p><a :href="selected.url" target="_blank" rel="noopener">{{ t("commGazette") }}</a></p>
      <v-btn variant="outlined" @click="openLaw = null">{{ t("commClose") }}</v-btn>
    </section>

    <template v-if="!country">
      <h2>{{ t("commLaws") }}</h2>
      <ul v-if="laws.length" class="law-list">
        <li v-for="law in laws" :key="law.id">
          <button type="button" :class="{ 'is-on': law.id === openLaw }" @click="show(law.id)">
            <strong>{{ law.votedOn.slice(0, 4) }}</strong>
            <span>{{ kindLabel(law.kind) }}. {{ law.title }}</span>
          </button>
        </li>
      </ul>
      <p v-else>{{ t("commLawsEmpty") }}</p>
    </template>

    <article v-for="account in place.windows" :id="`block-${account.window.id}`" :key="account.window.id" class="block">
      <h2>{{ account.window.start }}–{{ account.window.end }}<template v-if="account.window.open"> · {{ t("commOpen") }}</template></h2>
      <p v-if="account.window.open" class="note">{{ t("commBlockOpen") }}</p>
      <div class="pair">
        <div>
          <span>{{ t(country ? "commGrowthSpain" : "commGrowth") }}</span>
          <strong :class="tone(account.growth)">{{ signedPercent(account.growth, loc) }}</strong>
        </div>
        <div>
          <span>{{ t(country ? "commDuringEu" : "commDuring") }}</span>
          <strong :class="tone(account.againstBaseline)">{{ signedPercent(account.againstBaseline, loc) }}</strong>
        </div>
        <div>
          <span>{{ t(country ? "commLaterGrowthSpain" : "commLaterGrowth") }}<template v-if="account.window.laterReady"> · {{ account.window.laterStart }}–{{ account.window.laterEnd }}</template></span>
          <strong :class="tone(account.laterGrowth)">{{ account.window.laterReady ? signedPercent(account.laterGrowth, loc) : t("commSoon") }}</strong>
        </div>
        <div>
          <span>{{ t(country ? "commLaterEu" : "commLater") }}<template v-if="account.window.laterReady"> · {{ account.window.laterStart }}–{{ account.window.laterEnd }}</template></span>
          <strong :class="tone(account.laterAgainstBaseline)">{{ account.window.laterReady ? signedPercent(account.laterAgainstBaseline, loc) : t("commSoon") }}</strong>
        </div>
      </div>
      <p v-if="!account.window.open && !account.window.laterReady" class="note">{{ t("commBlockSoon") }}</p>

      <h3>{{ t("commBudget") }}</h3>
      <p class="note">{{ t(country ? "commBudgetHelpSpain" : "commBudgetHelp") }}</p>
      <BudgetList :budget="account.budget" />

      <h3>{{ t("commBalanceTitle") }}</h3>
      <div class="pair">
        <div>
          <span>{{ t("commBalance") }}</span>
          <strong :class="tone(account.balance)">{{ signedPercent(account.balance, loc) }}</strong>
        </div>
        <div>
          <span>{{ t("commBalanceEnd") }}<template v-if="account.scale"> · {{ account.scale.year }}</template></span>
          <strong :class="tone(account.balanceEnd)">{{ signedMoney(account.balanceEnd) }}</strong>
        </div>
      </div>
      <p class="note">{{ t("commBalanceHelp") }}</p>

      <h3>{{ t("commDebtTitle") }}</h3>
      <p class="note">{{ t("commDebtHelp") }}</p>
      <p v-if="!account.debt">{{ t("commNoDebt") }}</p>
      <template v-else>
        <p class="deck"><strong :class="burden(account.debt.change)">{{ signedMoney(account.debt.change) }}</strong></p>
        <ul class="budget">
          <li>
            <span>{{ t("commBonds") }}</span>
            <b>{{ shareOf(account.debt.bonds, account.debt.total) === null ? "—" : `${words.number(shareOf(account.debt.bonds, account.debt.total))}%` }}</b>
            <i><em :style="{ width: `${Math.max(0, shareOf(account.debt.bonds, account.debt.total) ?? 0)}%` }"></em></i>
          </li>
          <li>
            <span>{{ t("commLoans") }}</span>
            <b>{{ shareOf(account.debt.loans, account.debt.total) === null ? "—" : `${words.number(shareOf(account.debt.loans, account.debt.total))}%` }}</b>
            <i><em :style="{ width: `${Math.max(0, shareOf(account.debt.loans, account.debt.total) ?? 0)}%` }"></em></i>
          </li>
        </ul>
        <p class="note">{{ t("commBonds") }} {{ money(account.debt.bonds) }}. {{ t("commLoans") }} {{ money(account.debt.loans) }}.</p>
        <p v-if="(account.debt.fund ?? 0) > 0" class="note">{{ t("commFund", { n: money(account.debt.fund) }) }}</p>
      </template>

      <template v-if="account.baseline === 'spain' && account.stateTransfer">
        <h3>{{ t("commFlowTitle") }}</h3>
        <div class="pair">
          <div><span>{{ t("commReceived") }} · {{ span(account.stateTransfer.from, account.stateTransfer.to) }}</span><strong>{{ money(account.stateTransfer.received) }}</strong></div>
          <div><span>{{ t("commReturned") }} · {{ span(account.stateTransfer.from, account.stateTransfer.to) }}</span><strong>{{ money(account.stateTransfer.paid) }}</strong></div>
        </div>
        <p class="note">{{ t("commFlowHelp") }}</p>
      </template>
      <template v-if="countryAccount(account)?.euTransfer">
        <h3>{{ t("commFlowTitleEu") }}</h3>
        <div class="pair">
          <div><span>{{ t("commReceivedEu") }} · {{ span(countryAccount(account)!.euTransfer!.from, countryAccount(account)!.euTransfer!.to) }}</span><strong>{{ money(countryAccount(account)!.euTransfer!.received) }}</strong></div>
          <div><span>{{ t("commReturnedEu") }} · {{ span(countryAccount(account)!.euTransfer!.from, countryAccount(account)!.euTransfer!.to) }}</span><strong>{{ money(countryAccount(account)!.euTransfer!.paid) }}</strong></div>
          <div><span>{{ t("commEuNet") }} · {{ span(countryAccount(account)!.euTransfer!.from, countryAccount(account)!.euTransfer!.to) }}</span><strong :class="euBalance(countryAccount(account)!.euTransfer!.net)">{{ signedMoney(countryAccount(account)!.euTransfer!.net) }}</strong></div>
        </div>
        <p class="note">{{ t("commFlowHelpEu") }}</p>
      </template>
      <template v-if="countryAccount(account)?.communityTransfer">
        <h3>{{ t("commStateTitle") }}</h3>
        <div class="pair">
          <div><span>{{ t("commStateGiven") }} · {{ span(countryAccount(account)!.communityTransfer!.from, countryAccount(account)!.communityTransfer!.to) }}</span><strong>{{ money(countryAccount(account)!.communityTransfer!.paid) }}</strong></div>
          <div><span>{{ t("commStateBack") }} · {{ span(countryAccount(account)!.communityTransfer!.from, countryAccount(account)!.communityTransfer!.to) }}</span><strong>{{ money(countryAccount(account)!.communityTransfer!.received) }}</strong></div>
          <div><span>{{ t("commStateNet") }} · {{ span(countryAccount(account)!.communityTransfer!.from, countryAccount(account)!.communityTransfer!.to) }}</span><strong :class="communityBalance(countryAccount(account)!.communityTransfer!.net)">{{ signedMoney(countryAccount(account)!.communityTransfer!.net) }}</strong></div>
        </div>
        <p class="note">{{ t("commStateHelp") }}</p>
      </template>
      <p v-if="account.scale" class="note">
        <template v-if="account.scale.gdp !== null">{{ t("commScaleLine", { year: account.scale.year, gdp: money(account.scale.gdp) }) }} </template>
        <template v-if="account.debt && account.scale.debtShare !== null">{{ t(country ? "commScaleDebtSpain" : "commScaleDebt", { debt: money(account.debt.total), share: `${words.number(account.scale.debtShare)}%` }) }} </template>
        <template v-if="account.scale.spent !== null">{{ t(country ? "commScaleSpentSpain" : "commScaleSpent", { spent: money(account.scale.spent) }) }} </template>
        <template v-if="countryAccount(account)?.centralSpending !== null && countryAccount(account)?.centralSpending !== undefined">{{ t("commScaleState", { spent: money(countryAccount(account)!.centralSpending) }) }} </template>
        <template v-if="account.scale.debtShareChange !== null">{{ t("commBurdenChangeLine", { change: signedPoints(account.scale.debtShareChange, loc) }) }}</template>
      </p>
    </article>
    <p v-if="place.kind === 'region'" class="note"><a :href="pageHref('region', { slug: place.slug })">{{ t("commPresidents") }}</a></p>
  </template>
</template>
