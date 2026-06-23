<template>
  <v-app>
    <v-container id="main-container">
      <div class="app-shell">
        <router-view name="toc" />
        <div class="app-content">
          <router-view name="content" :key="$route.fullPath" />
        </div>
      </div>
    </v-container>

    <cz-notifications/>

    <link
      href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900"
      rel="stylesheet"
    />
    <link
      href="https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css"
      rel="stylesheet"
    />
  </v-app>
</template>

<script lang="ts">
import { Component, Vue, toNative } from "vue-facing-decorator";
import { CzNotifications } from "@cznethub/cznet-vue-core";

@Component({
  name: "app",
  components: { CzNotifications },
})
class App extends Vue {
  created() {}
}
export default toNative(App);
</script>

<style lang="scss" scoped>
.app-shell {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
}

// Tighten the TOC ↔ content gap on smaller laptops so the saved space goes to
// the content area, not the gutter.
@media (max-width: 1439px) {
  .app-shell {
    gap: 1rem;
  }
}

.app-content {
  flex: 1 1 auto;
  min-width: 0;
}
</style>
