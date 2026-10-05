<template>
  <v-dialog v-model="dialogOpen" max-width="480">
    <v-card>
      <v-card-title class="text-subtitle-1"> Find HydroShare user </v-card-title>
      <v-card-text>
        <v-autocomplete
          v-model="selected"
          v-model:search="search"
          :items="items"
          :loading="isSearching"
          placeholder="Search by name or username"
          prepend-inner-icon="mdi-account-search"
          item-title="text"
          item-value="id"
          variant="outlined"
          density="compact"
          hide-no-data
          hide-details
          clearable
          no-filter
          return-object
          autofocus
        />
        <v-alert
          v-if="importError"
          type="error"
          variant="tonal"
          density="compact"
          class="mt-3"
        >
          {{ importError }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialogOpen = false">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :disabled="!selected"
          :loading="isImporting"
          @click="importSelected"
        >
          Add
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
// Lets an editor pick an existing HydroShare account (via
// /user-autocomplete/, same pattern as cd.manage-access.vue) to
// pre-populate a new Author or Contributor entry in edit-dataset.vue,
// instead of typing name/email/affiliation by hand. See
// .ai/docs/6442-research-add-hydroshare-user-as-author.md.
import { computed, ref, watch } from "vue";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "select", person: Record<string, any>): void;
}>();

const search = ref("");
const items = ref<{ id: number; text: string }[]>([]);
const selected = ref<{ id: number; text: string } | null>(null);
const isSearching = ref(false);
const isImporting = ref(false);
const importError = ref("");
let searchToken = 0;
let searchDebounce: number | null = null;
// Parent window's scroll position captured right before we recenter it on
// the dialog, so we can put the user back where they were once it closes.
let prevScrollY: number | null = null;

const dialogOpen = computed<boolean>({
  get: () => props.modelValue,
  set: (v: boolean) => emit("update:modelValue", v),
});

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      search.value = "";
      items.value = [];
      selected.value = null;
      importError.value = "";
      // This app runs inside an iframe with scrolling="no" sized to its
      // full content, so Vuetify's position:fixed dialog lands at
      // iframe-center — typically far below the parent viewport. Wait for
      // the dialog to mount, then scroll the parent so iframe-center
      // aligns with its viewport center. Same fix as cd.manage-access.vue's
      // alignDialogToParentViewport.
      try {
        prevScrollY = window.parent?.scrollY ?? null;
      } catch {
        prevScrollY = null;
      }
      setTimeout(alignDialogToParentViewport, 80);
    } else {
      try {
        if (prevScrollY !== null) {
          window.parent?.scrollTo({ top: prevScrollY, behavior: "smooth" });
        }
      } catch {
        // cross-origin access denied — nothing we can do from inside the iframe
      } finally {
        prevScrollY = null;
      }
    }
  },
);

function alignDialogToParentViewport() {
  try {
    const parentWin = window.parent;
    if (!parentWin || parentWin === window) return;
    const iframe = parentWin.document.getElementById(
      "discovery-app-frame",
    ) as HTMLIFrameElement | null;
    if (!iframe) return;
    const iframeRect = iframe.getBoundingClientRect();
    const contentHeight = Math.max(
      iframe.offsetHeight,
      document.documentElement.scrollHeight,
    );
    const dialogYInParent =
      iframeRect.top + parentWin.scrollY + contentHeight / 2;
    // Bias the scroll target up by the HydroShare navbar height so the
    // dialog's top edge isn't clipped by it after the scroll settles.
    const navbarOffset = 80;
    const targetScrollY = Math.max(
      0,
      dialogYInParent - parentWin.innerHeight / 2 - navbarOffset,
    );
    if (Math.abs(parentWin.scrollY - targetScrollY) < 4) return;
    parentWin.scrollTo({ top: targetScrollY, behavior: "smooth" });
  } catch {
    // cross-origin access denied — nothing we can do from inside the iframe
  }
}

watch(search, (q) => {
  if (searchDebounce) {
    window.clearTimeout(searchDebounce);
  }
  if (!q || q.length < 2) {
    items.value = [];
    return;
  }
  searchDebounce = window.setTimeout(() => runAutocomplete(q), 300);
});

async function runAutocomplete(q: string) {
  const token = ++searchToken;
  isSearching.value = true;
  try {
    const resp = await fetch(`/user-autocomplete/?q=${encodeURIComponent(q)}`, {
      credentials: "include",
    });
    if (!resp.ok) return;
    const result = await resp.json();
    if (token !== searchToken) return;
    // django-autocomplete-light Select2 response: { results: [{id, text}], ... }
    items.value = (result.results || []).map((r: any) => ({
      id: Number(r.id),
      text: r.text,
    }));
  } catch (e) {
    // ignore — leave the list empty
  } finally {
    if (token === searchToken) {
      isSearching.value = false;
    }
  }
}

async function importSelected() {
  if (!selected.value) return;
  isImporting.value = true;
  importError.value = "";
  try {
    const resp = await fetch(`/hsapi/userDetails/${selected.value.id}/`, {
      credentials: "include",
    });
    if (!resp.ok) {
      importError.value = `Failed to load user info (${resp.status}).`;
      return;
    }
    const info = await resp.json();

    // Target the PersonIdentifier schema (@type/propertyID/value only);
    // ORCID and the profile URL are both stored as full URIs already.
    const identifier: { "@type": string; propertyID: string; value: string }[] =
      [];
    if (info.identifiers?.ORCID) {
      identifier.push({
        "@type": "PropertyValue",
        propertyID: "ORCID",
        value: info.identifiers.ORCID,
      });
    }
    if (info.url) {
      identifier.push({
        "@type": "PropertyValue",
        propertyID: "HydroShareID",
        value: info.url,
      });
    }

    const person: Record<string, any> = {
      "@type": "Person",
      name: info.name,
    };
    if (info.email) person.email = info.email;
    if (identifier.length) person.identifier = identifier;
    if (info.organization) {
      person.affiliation = { "@type": "Organization", name: info.organization };
    }

    emit("select", person);
    dialogOpen.value = false;
  } catch (e: any) {
    importError.value = `Failed to import user: ${e.message}`;
  } finally {
    isImporting.value = false;
  }
}
</script>
