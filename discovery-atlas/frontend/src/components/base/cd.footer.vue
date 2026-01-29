<template>
  <v-container
    flat
    class="footer text--secondary d-flex flex-column align-center full-width text-body-2"
  >
    <div class="d-lg-flex justify-space-between full-width">
      <div class="mb-4">
        <div class="mb-4 text-h6 mb-1">Contact Us</div>
        <!-- <p><router-link to="/contact">Contact</router-link></p> -->
        <p>
          <a href="mailto:{{$t('footer.supportEmail')}}">Email Support</a>
        </p>
        <p>
          Learn more about
          <a href="https://www.hydroshare.org/" target="_blank">HydroShare</a>
        </p>
        <p>
          Visit
          <a href="https://www.hydroshare.org/" target="_blank"
            >hydroshare.org</a
          >
        </p>
      </div>

      <div>
        <div class="mb-4 text-h6">Open Source</div>
        <p>
          The HydroShare Catalog and Discover system are Open Source. Find us on
          <a href="https://github.com/I-GUIDE/catalogapi" target="_blank"
            >GitHub</a
          >.
        </p>
        <p>
          Report a bug
          <a href="https://github.com/I-GUIDE/catalogapi/issues" target="_blank"
            >here</a
          >
        </p>
        <p>This is Version {{ version }} of the HydroShare catalog</p>
      </div>
    </div>

    <v-divider></v-divider>

    <div class="text-center d-flex flex-column align-center mt-4">
      <p>
        (c) {{ year }} CUAHSI. ﻿This material is based upon work supported by
        the National Science Foundation (NSF).<br />
        Any opinions, findings, conclusions, or recommendations expressed in
        this material are those of the authors and do not necessarily reflect
        the views of the NSF.
      </p>
    </div>
  </v-container>
</template>

<script lang="ts">
import { Component, Vue } from "vue-facing-decorator";

@Component({
  name: "cd-footer",
  components: {},
})
export default class CdFooter extends Vue {
  get version() {
    return VITE_APP_VERSION;
  }

  protected get year() {
    return new Date().getFullYear();
  }
}
</script>

<style lang="scss" scoped>
.footer {
  padding: 2rem 0;
}

p {
  margin-bottom: 0.75rem;
}
</style>
