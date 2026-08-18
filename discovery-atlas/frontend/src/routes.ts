import { RouteRecordRaw } from "vue-router";
import CdSearchResults from "@/components/search-results/cd.search-results.vue";
import LandingPage from "@/components/landing-page/landing-page.vue";
import EditDataset from "@/components/landing-page/edit-dataset.vue";
import Toc from "@/components/base/toc.vue";
import CdFooter from "@/components/base/cd.footer.vue";
import AuthRedirect from "@/components/account/auth-redirect.vue";

export const routes: RouteRecordRaw[] = [
  {
    name: "search",
    path: "/",
    components: {
      content: CdSearchResults,
      footer: CdFooter,
    },
    meta: {
      title: "Search",
    },
    beforeEnter(to) {
      // If no query parameters are provided, default the sort order — but
      // DON'T pre-apply the `a=Published` filter, which silently hid every
      // non-published resource and surprised users on a fresh visit.
      if (Object.keys(to.query).length === 0) {
        return { name: "search", query: { sortBy: "datePublished", order: "desc" } };
      }
    },
  },
  {
    name: "landing",
    path: "/resource-v2/:resourceId?",
    props: true,
    components: {
      content: LandingPage,
      toc: Toc,
      footer: CdFooter,
    },
    meta: {
      title: "Landing Page",
    },
  },
  {
    name: "edit-dataset",
    path: "/resource-v2/:resourceId/edit",
    props: true,
    components: {
      content: EditDataset,
      toc: Toc,
      footer: CdFooter,
    },
    meta: {
      title: "Edit Dataset",
    },
  },
  {
    name: "auth-redirect",
    path: "/auth-redirect",
    components: {
      content: AuthRedirect,
    },
    meta: {
      hideNavigation: true,
    },
  },
  /** @see https://router.vuejs.org/guide/migration/#removed-star-or-catch-all-routes */
  { path: "/:pathMatch(.*)*", name: "not-found", redirect: { name: "search" } },
  {
    path: "/:pathMatch(.*)",
    name: "bad-not-found",
    redirect: { name: "search" },
  },
];
