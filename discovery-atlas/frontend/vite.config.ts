import path from "node:path";
import { defineConfig, loadEnv } from "vite";
import Vue from "@vitejs/plugin-vue";
import generateSitemap from "vite-ssg-sitemap";
import Components from "unplugin-vue-components/vite";
import AutoImport from "unplugin-auto-import/vite";
import VueMacros from "unplugin-vue-macros/vite";
import { VitePWA } from "vite-plugin-pwa";
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
    },

    define: {
      VITE_APP_VERSION: JSON.stringify(process.env.npm_package_version),
    },

    // https://vitejs.dev/config/dep-optimization-options#optimizedeps-include
    optimizeDeps: {
      include: ["@fortawesome/fontawesome-free", "vuetify"],
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

      // https://github.com/antfu/vite-plugin-pwa
      VitePWA({
        registerType: "autoUpdate",
        includeAssets: ["favicon.svg", "safari-pinned-tab.svg"],
        manifest: {
          name: "Vitesse",
          short_name: "Vitesse",
          theme_color: "#ffffff",
          icons: [
            {
              src: "/pwa-192x192.png",
              sizes: "192x192",
              type: "image/png",
            },
            {
              src: "/pwa-512x512.png",
              sizes: "512x512",
              type: "image/png",
            },
            {
              src: "/pwa-512x512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "any maskable",
            },
          ],
        },
        workbox: {
          maximumFileSizeToCacheInBytes: 4000000,
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        }
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
