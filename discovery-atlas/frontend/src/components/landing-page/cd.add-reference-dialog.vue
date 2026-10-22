<template>
  <v-dialog v-model="isOpen" max-width="560" :persistent="isSubmitting">
    <v-card>
      <v-card-title class="text-h6">Add Content From The Web</v-card-title>
      <v-card-text>
        <div v-if="folderPath" class="text-body-2 text-medium-emphasis mb-4">
          Adding to <span class="font-weight-medium">{{ folderPath }}</span>
        </div>
        <v-text-field
          v-model="name"
          label="Name *"
          hint="Create a name for the referenced content. This name will be displayed in the file content area of the resource."
          persistent-hint
          placeholder="Untitled"
          variant="outlined"
          density="compact"
          class="mb-4"
          autofocus
        />
        <v-text-field
          v-model="url"
          label="URL *"
          hint="Specify the HTTP or FTP URL of a file or website."
          persistent-hint
          placeholder="HTTP or FTP URL"
          variant="outlined"
          density="compact"
          @keydown.enter="onSubmit"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :disabled="isSubmitting" @click="isOpen = false">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          :disabled="!canSubmit"
          :loading="isSubmitting"
          @click="onSubmit"
        >
          Add Content
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
const props = defineProps<{
  folderPath: string;
  /** Resolves `true` when the content was added, which closes the dialog. */
  submit: (_name: string, _url: string) => Promise<boolean>;
}>();

const isOpen = defineModel<boolean>({ default: false });

const name = ref("");
const url = ref("");
const isSubmitting = ref(false);

const canSubmit = computed(
  () => !isSubmitting.value && !!name.value.trim() && !!url.value.trim(),
);

watch(isOpen, (open) => {
  if (open) {
    name.value = "";
    url.value = "";
  }
});

async function onSubmit() {
  if (!canSubmit.value) return;
  isSubmitting.value = true;
  try {
    if (await props.submit(name.value.trim(), url.value.trim())) {
      isOpen.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>
