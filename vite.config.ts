import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { defineConfig, type Plugin } from "vite"
import vue from "@vitejs/plugin-vue"

const root = path.dirname(fileURLToPath(import.meta.url))
const siteBase = "/mery.github.io/"
const publishedData = ["store.json", "laws.json", "people.json", "office-corrections.json"]

function dataRequest(url: string): string | null {
  const pathOnly = decodeURIComponent(url.split("?")[0] ?? "")
  const marker = "/data/"
  const at = pathOnly.indexOf(marker)
  if (at < 0) return null
  const prefix = pathOnly.slice(0, at)
  if (prefix !== "" && prefix !== siteBase.slice(0, -1)) return null
  return pathOnly.slice(at)
}

function serveData(): Plugin {
  return {
    name: "serve-data",
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const url = dataRequest(request.url ?? "")
        if (!url) {
          next()
          return
        }
        const file = path.normalize(path.join(root, url))
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

function publishData(): Plugin {
  return {
    name: "publish-data",
    apply: "build",
    closeBundle() {
      const destination = path.join(root, "docs", "data")
      fs.mkdirSync(destination, { recursive: true })
      for (const name of publishedData) {
        const source = path.join(root, "data", name)
        if (!fs.existsSync(source)) throw new Error(`Missing data/${name}, needed for the published site`)
        fs.copyFileSync(source, path.join(destination, name))
      }
      fs.writeFileSync(path.join(root, "docs", ".nojekyll"), "")
    },
  }
}

export default defineConfig({
  base: siteBase,
  plugins: [vue(), serveData(), publishData()],
  build: { outDir: "docs", emptyOutDir: true },
  server: { port: 5173, strictPort: true },
})
