<template>
  <v-container id="main-container">
    <router-view name="content" :key="$route.fullPath" />
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

<style lang="scss" scoped></style>