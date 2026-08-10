<template>
  <div class="readme-editor">
    <!-- No README yet: show "Add README" until the author opts in. -->
    <div v-if="!showEditor" class="readme-add">
      <v-btn
        variant="tonal"
        color="primary"
        prepend-icon="mdi-plus"
        @click="startCreate"
      >
        Add README
      </v-btn>
    </div>

    <v-card
      v-else
      class="readme-editor-card"
      variant="outlined"
      border="grey thin"
    >
      <v-card-title class="readme-editor-header d-flex align-center ga-2">
        <div class="text-overline">README</div>
        <div class="text-caption text-medium-emphasis">{{ currentName }}</div>
        <v-spacer />
        <v-btn
          v-if="canConvert"
          variant="text"
          size="small"
          prepend-icon="mdi-language-markdown-outline"
          :loading="isConverting"
          :disabled="isSaving"
          @click="convert"
        >
          Convert to Markdown
        </v-btn>
        <v-btn
          variant="text"
          size="small"
          :disabled="!isDirty || isSaving || isConverting"
          @click="discard"
        >
          Discard changes
        </v-btn>
        <v-btn
          color="primary"
          size="small"
          variant="flat"
          :loading="isSaving"
          :disabled="!isDirty || isConverting"
          @click="save"
        >
          Save
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-tabs
        v-model="tab"
        density="compact"
        color="primary"
        class="readme-editor-tabs"
      >
        <v-tab value="write">Write</v-tab>
        <v-tab v-if="isMarkdown" value="preview">Preview</v-tab>
      </v-tabs>

      <v-divider />

      <v-card-text>
        <div v-if="isLoading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
        </div>

        <template v-else>
          <!-- Write: raw markdown / text -->
          <v-textarea
            v-show="tab === 'write'"
            v-model="raw"
            class="readme-textarea"
            variant="outlined"
            no-resize
            hide-details
            spellcheck="false"
            :readonly="isSaving || isConverting"
            :placeholder="placeholder"
          />

          <!-- Preview: rendered markdown (markdown mode only) -->
          <div
            v-if="isMarkdown"
            v-show="tab === 'preview'"
            class="markdown-body readme-preview"
            v-html="previewHtml"
          ></div>
        </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { S3Client } from "@aws-sdk/client-s3";
import { Notifications } from "@cznethub/cznet-vue-core";
import { renderMarkdown, isMarkdownFileName } from "./markdown";
import { loadReadme, saveReadme, convertReadmeToMarkdown } from "./readme-s3";
import "github-markdown-css/github-markdown-light.css";

// GitHub-style README editor. Loads/saves/converts its file in S3 directly,
// independent of the metadata form.
const props = withDefaults(
  defineProps<{
    resourceId: string;
    s3Client: S3Client;
    bucket: string;
    // README name from the parent's file tree, or null if none exists.
    fileName?: string | null;
  }>(),
  { fileName: null },
);

const emit = defineEmits(["change", "update:dirty"]);

const tab = ref<"write" | "preview">("write");
const raw = ref("");
const savedRaw = ref("");
// Local filename; seeded from `fileName`, updated directly on conversion.
const activeName = ref<string | null>(null);
const isCreating = ref(false);
const isLoading = ref(false);
const isSaving = ref(false);
const isConverting = ref(false);

activeName.value = props.fileName;
if (activeName.value) {
  load();
}

// React to the parent renaming/removing the README, ignoring echoes of a
// name we set ourselves.
watch(
  () => props.fileName,
  (value) => {
    if (value === activeName.value) return;
    activeName.value = value;
    isCreating.value = false;
    tab.value = "write";
    if (value) {
      load();
    } else {
      raw.value = "";
      savedRaw.value = "";
    }
  },
);

const showEditor = computed<boolean>(
  () => activeName.value !== null || isCreating.value,
);

// The real file name, or the name a new README will be saved under.
const currentName = computed<string>(
  () => activeName.value ?? (isCreating.value ? "readme.md" : ""),
);

const isMarkdown = computed<boolean>(() => isMarkdownFileName(currentName.value));

// Convert is only meaningful for an existing .txt file.
const canConvert = computed<boolean>(
  () => activeName.value !== null && !isMarkdown.value,
);

const isDirty = computed<boolean>(() => raw.value !== savedRaw.value);

// The editor writes to S3 on its own, independent of the metadata form, so
// the parent otherwise has no way to know there are unsaved README edits —
// "Save changes" or "Cancel" would navigate away and discard them silently.
watch(isDirty, (dirty) => emit("update:dirty", dirty), { immediate: true });

const previewHtml = computed<string>(() => renderMarkdown(raw.value));

const placeholder = computed<string>(() =>
  isMarkdown.value
    ? "Write a README for your dataset in Markdown…"
    : "Write a README for your dataset…",
);

function startCreate() {
  isCreating.value = true;
  raw.value = "";
  savedRaw.value = "";
  tab.value = "write";
}

// Revert to the last saved version.
function discard() {
  raw.value = savedRaw.value;
}

async function load() {
  const name = activeName.value;
  if (!name) return;
  isLoading.value = true;
  try {
    const text = await loadReadme(props.bucket, props.resourceId, name);
    raw.value = text;
    savedRaw.value = text;
  } catch (e: any) {
    console.error("Failed to load README:", e);
    Notifications.toast({
      title: "Error",
      message: "Failed to load the README file.",
      type: "error",
    });
  } finally {
    isLoading.value = false;
  }
}

async function save() {
  const name = currentName.value;
  if (!name || isSaving.value) return;
  const wasNew = activeName.value === null;
  // Snapshot so edits typed during the save aren't marked saved.
  const body = raw.value;
  isSaving.value = true;
  try {
    const size = await saveReadme(
      props.s3Client,
      props.bucket,
      props.resourceId,
      name,
      body,
    );
    savedRaw.value = body;
    if (wasNew) {
      activeName.value = name;
      isCreating.value = false;
      emit("change", { action: "created", name, size });
    } else {
      emit("change", { action: "saved", name, size });
    }
    Notifications.toast({ message: "README saved.", type: "success" });
  } catch (e: any) {
    console.error("Failed to save README:", e);
    Notifications.toast({
      title: "Error",
      message: `Failed to save the README. ${e?.message ?? ""}`.trim(),
      type: "error",
    });
  } finally {
    isSaving.value = false;
  }
}

async function convert() {
  const from = activeName.value;
  if (!from || isMarkdown.value || isConverting.value) return;
  // Snapshot so mid-convert edits carry over.
  const body = raw.value;
  isConverting.value = true;
  try {
    const { name: to, size } = await convertReadmeToMarkdown(
      props.s3Client,
      props.bucket,
      props.resourceId,
      from,
      body,
    );
    activeName.value = to;
    savedRaw.value = body;
    tab.value = "write";
    emit("change", {
      action: "converted",
      name: to,
      previousName: from,
      size,
    });
    Notifications.toast({
      message: "README converted to Markdown.",
      type: "success",
    });
  } catch (e: any) {
    console.error("Failed to convert README:", e);
    Notifications.toast({
      title: "Error",
      message: `Failed to convert the README. ${e?.message ?? ""}`.trim(),
      type: "error",
    });
  } finally {
    isConverting.value = false;
  }
}
</script>

<style lang="scss" scoped>
.readme-editor-card {
  border-radius: 8px;

  // Vertically-resizable viewport, mirroring landing-page's README container.
  .v-card-text {
    min-height: 5rem;
    height: 40rem;
    overflow: auto;
    resize: vertical;
    padding: 1rem;
  }

  // Undo github-markdown-css's full-page padding/max-width inside the card.
  .markdown-body {
    box-sizing: border-box;
    min-width: 200px;
    max-width: 100%;
    padding: 0;
    font-family: inherit;
  }
}

.readme-editor-header {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.readme-editor-tabs {
  padding-left: 0.5rem;
}

.readme-textarea {
  height: 100%;

  :deep(.v-input__control),
  :deep(.v-field),
  :deep(.v-field__field) {
    height: 100%;
  }

  :deep(textarea) {
    height: 100%;
    overflow-y: auto;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.85rem;
    line-height: 1.5;
  }
}
</style>
