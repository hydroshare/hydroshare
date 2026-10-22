<template>
  <v-dialog v-model="isOpen" max-width="640">
    <v-card>
      <v-card-title class="text-h6">Get file URL</v-card-title>
      <v-card-text>
        <v-alert
          v-if="accessNotice"
          type="warning"
          variant="tonal"
          density="compact"
          class="mb-4 text-body-2"
        >
          {{ accessNotice }}
        </v-alert>
        <v-text-field
          :model-value="url"
          readonly
          variant="outlined"
          density="compact"
          hide-details
          @focus="($event.target as HTMLInputElement).select()"
        >
          <template #append-inner>
            <v-btn
              size="small"
              variant="text"
              :prepend-icon="isCopied ? 'mdi-check' : 'mdi-content-copy'"
              @click="copy"
            >
              {{ isCopied ? "Copied" : "Copy" }}
            </v-btn>
          </template>
        </v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="isOpen = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { Notifications } from "@cznethub/cznet-vue-core";

const props = defineProps<{
  url: string;
  /** Sharing status name, e.g. "Private" or "Public". */
  status?: string | null;
}>();

const isOpen = defineModel<boolean>({ default: false });
const isCopied = ref(false);

const accessNotice = computed(() => {
  switch ((props.status || "").toLowerCase()) {
    case "private":
      return "This file is within a Private resource. Only users who have been granted at least \"view\" permission, or anyone with the link if Private Link Sharing is enabled, can access this URL. To make it publicly available, make the resource public.";
    case "discoverable":
      return "This file is within a Discoverable resource. Only users who have been granted at least \"view\" permission, or anyone with the link if Private Link Sharing is enabled, can access this URL. To make it publicly available, make the resource public.";
    default:
      return "";
  }
});

watch(isOpen, (open) => {
  if (open) isCopied.value = false;
});

async function copy() {
  try {
    await navigator.clipboard.writeText(props.url);
    isCopied.value = true;
  } catch {
    Notifications.toast({
      message: "Could not copy to the clipboard. Select the URL and copy it manually.",
      type: "error",
    });
  }
}
</script>
