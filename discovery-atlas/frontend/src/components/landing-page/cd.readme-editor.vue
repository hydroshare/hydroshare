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
            auto-grow
            :rows="14"
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

<script lang="ts">
import { Component, Vue, toNative, Prop, Watch } from "vue-facing-decorator";
import { S3Client } from "@aws-sdk/client-s3";
import { Notifications } from "@cznethub/cznet-vue-core";
import { renderMarkdown, isMarkdownFileName } from "./markdown";
import { loadReadme, saveReadme, convertReadmeToMarkdown } from "./readme-s3";
import "github-markdown-css/github-markdown-light.css";

// GitHub-style README editor. Loads/saves/converts its file in S3 directly,
// independent of the metadata form.
@Component({
  name: "cd-readme-editor",
  emits: ["change"],
})
class CdReadmeEditor extends Vue {
  @Prop({ type: String, required: true }) resourceId!: string;
  @Prop({ required: true }) s3Client!: S3Client;
  @Prop({ type: String, required: true }) bucket!: string;
  // README name from the parent's file tree, or null if none exists.
  @Prop({ default: null }) fileName!: string | null;

  tab: "write" | "preview" = "write";
  raw = "";
  savedRaw = "";
  // Local filename; seeded from `fileName`, updated directly on conversion.
  activeName: string | null = null;
  isCreating = false;
  isLoading = false;
  isSaving = false;
  isConverting = false;

  created() {
    this.activeName = this.fileName;
    if (this.activeName) {
      this.load();
    }
  }

  // React to the parent renaming/removing the README, ignoring echoes of a
  // name we set ourselves.
  @Watch("fileName")
  onFileNameChange(value: string | null) {
    if (value === this.activeName) return;
    this.activeName = value;
    this.isCreating = false;
    this.tab = "write";
    if (value) {
      this.load();
    } else {
      this.raw = "";
      this.savedRaw = "";
    }
  }

  get showEditor(): boolean {
    return this.activeName !== null || this.isCreating;
  }

  // The real file name, or the name a new README will be saved under.
  get currentName(): string {
    return this.activeName ?? (this.isCreating ? "readme.md" : "");
  }

  get isMarkdown(): boolean {
    return isMarkdownFileName(this.currentName);
  }

  // Convert is only meaningful for an existing .txt file.
  get canConvert(): boolean {
    return this.activeName !== null && !this.isMarkdown;
  }

  get isDirty(): boolean {
    return this.raw !== this.savedRaw;
  }

  get previewHtml(): string {
    return renderMarkdown(this.raw);
  }

  get placeholder(): string {
    return this.isMarkdown
      ? "Write a README for your dataset in Markdown…"
      : "Write a README for your dataset…";
  }

  startCreate() {
    this.isCreating = true;
    this.raw = "";
    this.savedRaw = "";
    this.tab = "write";
  }

  // Revert to the last saved version.
  discard() {
    this.raw = this.savedRaw;
  }

  async load() {
    const name = this.activeName;
    if (!name) return;
    this.isLoading = true;
    try {
      const text = await loadReadme(this.bucket, this.resourceId, name);
      this.raw = text;
      this.savedRaw = text;
    } catch (e: any) {
      console.error("Failed to load README:", e);
      Notifications.toast({
        title: "Error",
        message: "Failed to load the README file.",
        type: "error",
      });
    } finally {
      this.isLoading = false;
    }
  }

  async save() {
    const name = this.currentName;
    if (!name || this.isSaving) return;
    const wasNew = this.activeName === null;
    // Snapshot so edits typed during the save aren't marked saved.
    const body = this.raw;
    this.isSaving = true;
    try {
      const size = await saveReadme(
        this.s3Client,
        this.bucket,
        this.resourceId,
        name,
        body,
      );
      this.savedRaw = body;
      if (wasNew) {
        this.activeName = name;
        this.isCreating = false;
        this.$emit("change", { action: "created", name, size });
      } else {
        this.$emit("change", { action: "saved", name, size });
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
      this.isSaving = false;
    }
  }

  async convert() {
    const from = this.activeName;
    if (!from || this.isMarkdown || this.isConverting) return;
    // Snapshot so mid-convert edits carry over.
    const body = this.raw;
    this.isConverting = true;
    try {
      const { name: to, size } = await convertReadmeToMarkdown(
        this.s3Client,
        this.bucket,
        this.resourceId,
        from,
        body,
      );
      this.activeName = to;
      this.savedRaw = body;
      this.tab = "write";
      this.$emit("change", {
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
      this.isConverting = false;
    }
  }
}

export default toNative(CdReadmeEditor);
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

.readme-textarea :deep(textarea) {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.85rem;
  line-height: 1.5;
}
</style>
