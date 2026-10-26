import { createI18n } from "vue-i18n"
import { languageFromAddress, type Language } from "../route"
import en from "./en.json"
import es from "./es.json"

export type { Language }
export type MessageSchema = { [Key in keyof typeof es]: string }

const messages = { es, en } satisfies Record<Language, MessageSchema>

export const i18n = createI18n<[MessageSchema], Language>({
  legacy: false,
  locale: languageFromAddress(),
  fallbackLocale: "es",
  messages,
})
