import { ViteSSG } from "vite-ssg";
import App from "./App.vue";
import type { UserModule } from "./types";

import "./assets/css/global.scss";
// Imported here (not via SCSS @use) so Vite tracks dist/index.css of the
// linked cznet-vue-core through HMR. Library rebuilds propagate without
// re-running the SCSS compile step.
import "@cznethub/cznet-vue-core/styles";
import { routes } from "./routes";
import { APP_BASE } from "./constants";

// https://github.com/antfu/vite-ssg
export const createApp = ViteSSG(
  App,
  {
    routes,
    // scrollBehavior(_to, _from, _savedPosition) {
    //   document.getElementsByTagName("html")[0]?.scrollTo({ left: 0, top: 0 });
    // },
    base: APP_BASE,
  },
  (ctx) => {
    // install all modules under `modules/`
    Object.values(
      import.meta.glob<{ install: UserModule }>("./modules/*.ts", {
        eager: true,
      }),
    ).forEach((i) => i.install?.(ctx));
  },
);
