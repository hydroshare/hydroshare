import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import Vue from "@vitejs/plugin-vue";
import generateSitemap from "vite-ssg-sitemap";
import Components from "unplugin-vue-components/vite";
import AutoImport from "unplugin-auto-import/vite";
import VueMacros from "unplugin-vue-macros/vite";
import vuetify from "vite-plugin-vuetify";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const base = env.VITE_APP_BASE;
  return {
    // TODO: verify that these paths are correct!
    // root: "./",
    base: base,
    // envDir: "./",
    resolve: {
      alias: {
        "@/": `${path.resolve(__dirname, "src")}/`,
      },
      // Dedupe deps shared with cznet-vue-core so a single copy is used — two
      // Vue / Vuetify runtimes side by side would break reactivity.
      dedupe: [
        "vue",
        "vuetify",
        "@jsonforms/core",
        "@jsonforms/vue",
        "vue-facing-decorator",
        // ajv keeps generated `Name` objects in module-level state; two copies
        // exchange Names and the receiver serializes them as `{"str":"..."}`,
        // producing invalid generated code. Keep a single ajv copy.
        "ajv",
        "ajv-formats",
        "ajv-keywords",
        "ajv-errors",
      ],
    },

    define: {
      VITE_APP_VERSION: JSON.stringify(process.env.npm_package_version),
    },

    // https://vitejs.dev/config/dep-optimization-options#optimizedeps-include
    optimizeDeps: {
      include: [
        "@fortawesome/fontawesome-free",
        "vuetify",
        // Because cznet-vue-core is excluded (below), Vite's scanner doesn't
        // walk into it to discover its transitive deps. These are the
        // CJS-shaped packages it reaches that need interop shimming — list
        // them explicitly so Vite pre-bundles them with a synthetic default
        // export. Symptom of a missing entry here: "does not provide an
        // export named 'default'" at runtime.
        "@jsonforms/core",
        "@jsonforms/vue",
        "ajv",
        "ajv-errors",
        "ajv-keywords",
        "markdown-it",
        "dayjs",
        "lodash-es",
        "sprintf-js",
        "v-mask",
        "buefy",
      ],
    },

    plugins: [
      VueMacros({
        plugins: {
          vue: Vue({
            include: [/\.vue$/, /\.md$/],
          }),
        },
      }),

      // https://github.com/antfu/unplugin-auto-import
      AutoImport({
        imports: [
          "vue",
          "@vueuse/head",
          "@vueuse/core",
          {
            // add any other imports you were relying on
            "vue-router/auto": ["useLink"],
          },
        ],
        dts: "src/auto-imports.d.ts",
        dirs: ["src/composables", "src/stores"],
        vueTemplate: true,
      }),

      // https://github.com/antfu/unplugin-vue-components
      Components({
        // allow auto load components under `./src/components/`
        extensions: ["vue"],
        // allow auto import and register components
        include: [/\.vue$/, /\.vue\?vue/],
        dts: "src/components.d.ts",
      }),

      // https://github.com/feat-agency/vite-plugin-webfont-dl
      // WebfontDownload(),

      vuetify({
        styles: { configFile: "src/assets/css/settings.scss" },
      }),
    ],

    // https://github.com/vitest-dev/vitest
    test: {
      include: ["test/**/*.test.ts"],
      environment: "jsdom",
    },

    // https://github.com/antfu/vite-ssg
    ssgOptions: {
      script: "async",
      formatting: "minify",
      onFinished() {
        generateSitemap();
      },
      format: "esm", // default
    },

    ssr: {
      // TODO: workaround until they support native ESM
      noExternal: ["workbox-window"],
    },

    build: {
      outDir: "./dist",
      rollupOptions: {
        output: {
          // Assets will use relative paths like assets/file.js
          assetFileNames: 'assets/[name]-[hash][extname]',
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
        }
      },
      // Ensure assets use relative paths
      assetsDir: 'assets',
    },

    server: {
      host: '0.0.0.0',
      port: 5004,
      strictPort: true,
      hmr: {
        host: 'localhost',
        port: 5004, // Same as dev server
        clientPort: 80, // Browser connects through nginx on port 80
      },
    },
  };
});
