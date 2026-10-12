import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://sachncs.github.io/convexfolio",
  base: "/convexfolio",
  markdown: {
    shikiConfig: { theme: "github-dark" }
  }
});
