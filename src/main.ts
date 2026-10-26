import { createApp } from "vue"
import App from "./App.vue"
import { i18n } from "./i18n"
import { router } from "./router"
import { vuetify } from "./plugins/vuetify"
import "./style.css"
import "./features.css"

const app = createApp(App).use(i18n).use(vuetify).use(router)
void router.isReady().then(() => app.mount("#app"))
