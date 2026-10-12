<template>
  <!-- The activator is a wrapping <div>, not the button itself: a disabled
       <button> emits no pointer events, so hovering it would never open the
       menu — which is exactly when the user most needs to see why. -->
  <v-menu
    :disabled="!errors.length"
    open-on-hover
    :close-on-content-click="false"
    location="bottom end"
    transition="fade-transition"
  >
    <template #activator="{ props: menuProps }">
      <div v-bind="menuProps" class="d-flex">
        <v-badge
          :model-value="!isValid"
          bordered
          color="error"
          icon="mdi-exclamation-thick"
        >
          <v-btn
            color="primary"
            :variant="variant"
            :size="size"
            prepend-icon="mdi-content-save"
            :disabled="!isValid || isSubmitting"
            :loading="isSubmitting"
            @click="$emit('click')"
          >
            {{ isSubmitting ? busyLabel : label }}
          </v-btn>
        </v-badge>
      </div>
    </template>

    <v-card max-width="420" class="save-errors">
      <div class="save-errors__header text-caption font-weight-bold text-uppercase">
        {{ errors.length }} issue{{ errors.length === 1 ? "" : "s" }} to fix
      </div>
      <v-divider />
      <v-card-text class="py-2 px-3">
        <ul class="save-errors__list">
          <li v-for="(error, index) of errors" :key="index">
            <span class="font-weight-medium">{{ error.title }}</span>
            {{ error.message }}
          </li>
        </ul>
      </v-card-text>
    </v-card>
  </v-menu>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    errors: { title?: string; message?: string }[];
    isValid: boolean;
    isSubmitting?: boolean;
    label?: string;
    busyLabel?: string;
    size?: string;
    variant?: "flat" | "text" | "elevated" | "outlined" | "plain" | "tonal";
  }>(),
  {
    label: "Save Changes",
    busyLabel: "Saving Changes...",
    size: "default",
    variant: "elevated",
  },
);

defineEmits<{ (e: "click"): void }>();
</script>

<style scoped lang="scss">
.save-errors {
  &__header {
    padding: 0.5rem 0.75rem;
    letter-spacing: 0.05em;
    color: rgb(var(--v-theme-error));
  }

  &__list {
    margin: 0;
    padding-left: 1.1rem;
    font-size: 0.8125rem;
    line-height: 1.35rem;

    li + li {
      margin-top: 0.25rem;
    }
  }
}
</style>
