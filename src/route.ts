import type { LocationQueryValue, RouteLocationRaw } from "vue-router"
import { router } from "./router"

export type Language = "es" | "en"
export type PageName = "presidents" | "communities" | "community" | "region" | "person" | "method" | "data" | "missing"
export type VerdictFilter = "all" | "gained" | "lost" | "early"

const storedKey = "plan-mery-lang"

export function storedLanguage(): Language {
  return localStorage.getItem(storedKey) === "en" ? "en" : "es"
}

export function languageFromAddress(): Language {
  const path = (location.hash.replace(/^#/, "") || "/").split("?")[0] ?? "/"
  const head = path.split("/").filter(Boolean)[0]
  if (head === "en" || head === "es") return head
  return storedLanguage()
}

export function param(value: string | string[] | undefined): string {
  return typeof value === "string" ? value : ""
}

export function queryText(value: LocationQueryValue | LocationQueryValue[] | undefined): string | null {
  return typeof value === "string" && value ? value : null
}

export function verdictOf(value: LocationQueryValue | LocationQueryValue[] | undefined): VerdictFilter {
  const text = queryText(value)
  if (text === "gained" || text === "lost" || text === "early") return text
  return "all"
}

function language(): Language {
  const value = router.currentRoute.value.params.lang
  return value === "en" ? "en" : "es"
}

export function toPage(name: PageName, params: Record<string, string> = {}, query: Record<string, string> = {}): RouteLocationRaw {
  const search: Record<string, string> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value) search[key] = value
  }
  return { name, params: { lang: language(), ...params }, query: search }
}

export function pageHref(name: PageName, params: Record<string, string> = {}, query: Record<string, string> = {}): string {
  return router.resolve(toPage(name, params, query)).href
}

export function languageHref(lang: Language): string {
  const current = router.currentRoute.value
  const params: Record<string, string> = { lang }
  for (const [key, value] of Object.entries(current.params)) {
    if (typeof value === "string") params[key] = value
  }
  params.lang = lang
  const name = typeof current.name === "string" ? current.name : "presidents"
  return router.resolve({ name, params, query: current.query }).href
}

export function titleKey(name: unknown): "titleHome" | "titleCommunities" | "titleMethod" | "titleData" | "titleMissing" {
  if (name === "communities" || name === "community") return "titleCommunities"
  if (name === "method") return "titleMethod"
  if (name === "data") return "titleData"
  if (name === "missing") return "titleMissing"
  return "titleHome"
}
