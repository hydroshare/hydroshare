<template>
  <v-card class="cd-login">
    <v-card-title>Log In</v-card-title>
    <v-card-text>
      <p class="text-body-1">
        User accounts in the IGUIDE Catalog are managed using your ORCID® iD.
        An ORCID iD is a persistent digital identifier that you own and control
        and that distinguishes you from every other researcher.
      </p>
      <p class="text-body-1">
        If you have an ORCID already, click the button below to get started. If
        you don't have an ORCID yet, getting one is easy. Visit
        <a href="https://orcid.org" target="_blank">https://orcid.org</a> to
        register and get your unique ORCID iD.
      </p>
      <img :src="require('@/assets/img/orcid.png')" alt="ORCID" />
    </v-card-text>
    <v-divider></v-divider>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="onCancel">Cancel</v-btn>
      <v-btn
        id="orcid_login_continue"
        @click="openLogInDialog()"
        color="primary"
      >
        <v-icon class="mr-2">fab fa-orcid</v-icon>
        <span>Log In Using ORCID</span>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import User from "@/models/user.model";

const emit = defineEmits<{
  cancel: [];
  "logged-in": [];
}>();

async function openLogInDialog() {
  User.logIn(onLoggedIn);
}

function onCancel() {
  emit("cancel");
}

function onLoggedIn() {
  emit("logged-in");
}
</script>

<style lang="scss" scoped>
:deep(.v-card__text img) {
  max-width: 12rem;
}
</style>
