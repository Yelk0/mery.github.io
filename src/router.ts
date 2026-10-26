import { createRouter, createWebHashHistory } from "vue-router"
import { storedLanguage } from "./route"
import CommunitiesView from "./views/CommunitiesView.vue"
import CommunityView from "./views/CommunityView.vue"
import DataView from "./views/DataView.vue"
import MethodView from "./views/MethodView.vue"
import MissingView from "./views/MissingView.vue"
import PersonView from "./views/PersonView.vue"
import PresidentsView from "./views/PresidentsView.vue"
import RegionView from "./views/RegionView.vue"

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/:lang(es|en)", name: "presidents", component: PresidentsView },
    { path: "/:lang(es|en)/communities", name: "communities", component: CommunitiesView },
    { path: "/:lang(es|en)/communities/:slug", name: "community", component: CommunityView },
    { path: "/:lang(es|en)/region/:slug", name: "region", component: RegionView },
    { path: "/:lang(es|en)/person/:slug", name: "person", component: PersonView },
    { path: "/:lang(es|en)/method", name: "method", component: MethodView },
    { path: "/:lang(es|en)/data", name: "data", component: DataView },
    { path: "/:lang(es|en)/missing", name: "missing", component: MissingView },
    {
      path: "/:pathMatch(.*)*",
      redirect: (to) => {
        const head = to.path.split("/").filter(Boolean)[0]
        if (head === "es" || head === "en") return { name: "presidents", params: { lang: head } }
        const suffix = to.path === "/" ? "" : to.path
        return { path: `/${storedLanguage()}${suffix}`, query: to.query }
      },
    },
  ],
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    if (to.name === from.name && to.params.lang !== from.params.lang) return false
    if (to.name === "community" && to.query.window) return false
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const lang = to.params.lang
  if (lang === "es" || lang === "en") localStorage.setItem("plan-mery-lang", lang)
})
