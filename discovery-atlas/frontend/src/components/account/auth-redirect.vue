<template>
  <v-container>
    <div class="text-h5">You have signed in!</div>
    <p class="font-weight-regular text-body-1 mt-4">
      You can return to the main page. This window will be closed
      automatically...
    </p>
  </v-container>
</template>

<script lang="ts">
import { APP_URL } from "@/constants";
import { Component, Vue, toNative } from "vue-facing-decorator";

@Component({
  name: "auth-redirect",
  components: {},
})
class AuthRedirect extends Vue {
  mounted() {
    // Get a dictionary of parameters in the redirect response URL
    const dict: any = {};
    this.$route.hash.split("&").reduce((acc, curr) => {
      const [key, val] = curr.split("=");
      acc[key] = val;
      return acc;
    }, dict);

    // window.opener references our original window from where the login popup was opened
    window.opener.postMessage(
      { accessToken: dict["#access_token"] || "" },
      APP_URL // Important security measure: https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy
    );
    window.close();
  }
}

export default toNative(AuthRedirect);
</script>

<style lang="scss" scoped></style>
