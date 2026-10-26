import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { defineConfig, type Plugin } from "vite"
import vue from "@vitejs/plugin-vue"

const root = path.dirname(fileURLToPath(import.meta.url))

function serveData(): Plugin {
  return {
    name: "serve-data",
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const url = request.url?.split("?")[0] ?? ""
        if (!url.startsWith("/data/")) {
          next()
          return
        }
        const file = path.normalize(path.join(root, decodeURIComponent(url)))
        const dataRoot = path.join(root, "data") + path.sep
        if (!file.startsWith(dataRoot) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
          next()
          return
        }
        response.setHeader("Content-Type", "application/json; charset=utf-8")
        fs.createReadStream(file).pipe(response)
      })
    },
  }
}

export default defineConfig({
  plugins: [vue(), serveData()],
  server: { port: 5173, strictPort: true },
})
