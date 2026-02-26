import { RouteRecordRaw } from "vue-router";
import CdSearchResults from "@/components/search-results/cd.search-results.vue";

export const routes: RouteRecordRaw[] = [
  {
    name: "search",
    path: "/",
    components: {
      content: CdSearchResults,
    }
  },
  /** @see https://router.vuejs.org/guide/migration/#removed-star-or-catch-all-routes */
  { path: "/:pathMatch(.*)*", name: "not-found", redirect: { name: "search" } },
  {
    path: "/:pathMatch(.*)",
    name: "bad-not-found",
    redirect: { name: "search" },
  },
];
