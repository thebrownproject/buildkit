import { defineConfig } from "vite";

export default defineConfig({
  base: "/buildkit/",
  esbuild: {
    supported: { "top-level-await": true },
  },
});
