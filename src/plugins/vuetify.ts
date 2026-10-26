import { createVuetify } from "vuetify"
import * as components from "vuetify/components"
import * as directives from "vuetify/directives"
import "vuetify/styles"

export const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "light",
    themes: {
      light: {
        colors: {
          primary: "#1f6b45",
          secondary: "#9c3412",
          background: "#f6f1e7",
          surface: "#fffdf8",
        },
      },
    },
  },
})
