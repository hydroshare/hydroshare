<template>
  <!-- `hs-host-dialog` pins this to the parent window's visible band when
       embedded; see assets/css/host-dialogs.scss. -->
  <v-dialog
    v-model="dialogOpen"
    max-width="760"
    scrollable
    content-class="hs-host-dialog"
  >
    <v-card class="manage-access-card" :class="{ 'is-processing': isProcessing }">
      <div class="dialog-banner"></div>
      <v-card-title class="dialog-header">
        <div class="d-flex align-center" style="gap: 0.6rem">
          <v-icon color="primary">mdi-account-multiple-outline</v-icon>
          <span class="dialog-title">Manage access</span>
        </div>
        <v-spacer></v-spacer>
        <v-btn icon variant="text" size="small" @click="dialogOpen = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="dialog-body">
        <div v-if="isLoading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
        </div>

        <template v-else-if="loadError">
          <v-alert type="error" variant="tonal" density="compact">
            {{ loadError }}
          </v-alert>
        </template>

        <template v-else>
          <div class="mb-6">
            <p class="text-body-2 text-medium-emphasis mb-2">
              Share this resource with specific HydroShare users or set its
              sharing status. You can give other users the ability to view or
              edit this resource, or add additional owners with full permissions.
            </p>

            <v-expand-transition>
              <ul v-if="showUsageInfo" class="usage-info text-body-2 mt-2">
                <li class="mb-2">
                  <strong>Owners</strong> can perform all operations on a
                  resource and set whether a resource is Public, Discoverable,
                  or Private and Shareable.
                </li>
                <li class="mb-2">
                  <strong>Editors</strong> can edit resource metadata and add
                  or delete resource content files.
                </li>
                <li>
                  <strong>Viewers</strong> can view resource metadata and
                  download resource content files.
                </li>
              </ul>
            </v-expand-transition>

            <v-btn
              size="x-small"
              variant="text"
              color="primary"
              class="ps-0"
              @click="showUsageInfo = !showUsageInfo"
            >
              {{ showUsageInfo ? "Show less" : "Show more" }}
            </v-btn>
          </div>

          <!-- Who has access -->
          <section class="mb-6 field">
            <div class="section-heading">Who has access</div>
            <v-card variant="outlined" border="grey thin">
              <v-table
                density="compact"
                class="access-table"
                :class="{ 'pointer-events-none': isProcessing }"
              >
                <tbody>
                  <tr
                    v-for="(user, index) in users"
                    :key="`${user.user_type}-${user.id}`"
                    :class="{ 'is-loading': user.loading }"
                  >
                    <td>
                      <div class="d-flex align-center" style="gap: 0.75rem">
                        <v-avatar
                          size="40"
                          :color="user.pictureUrl ? undefined : 'grey-lighten-3'"
                          class="user-avatar"
                        >
                          <img v-if="user.pictureUrl" :src="user.pictureUrl" />
                          <v-icon v-else color="grey-darken-1">
                            {{
                              user.user_type === "group"
                                ? "mdi-account-group"
                                : "mdi-account"
                            }}
                          </v-icon>
                        </v-avatar>
                        <div class="user-info">
                          <a
                            :href="
                              user.user_type === 'group'
                                ? `/group/${user.id}`
                                : `/user/${user.id}`
                            "
                            target="_blank"
                            rel="noopener"
                            class="user-name"
                          >
                            {{ user.best_name }}
                          </a>
                          <div
                            v-if="user.user_name"
                            class="user-meta text-caption text-medium-emphasis"
                          >
                            {{ user.user_name }}
                          </div>
                          <div
                            v-else-if="user.user_type === 'group'"
                            class="user-meta text-caption text-medium-emphasis"
                          >
                            Group
                          </div>
                          <div class="d-flex flex-wrap mt-1" style="gap: 0.25rem">
                            <v-chip
                              v-if="user.id === currentUserId"
                              size="x-small"
                              color="primary"
                              variant="flat"
                              label
                            >
                              You
                            </v-chip>
                            <v-chip
                              v-if="
                                user.user_type === 'user' &&
                                quotaHolderId != null &&
                                user.id === quotaHolderId
                              "
                              size="x-small"
                              color="amber-darken-2"
                              variant="tonal"
                              prepend-icon="mdi-chart-pie"
                              label
                            >
                              Quota Holder
                            </v-chip>
                          </div>
                        </div>
                      </div>
                    </td>

                    <td class="text-no-wrap role-cell">
                      <v-menu>
                        <template #activator="{ props: menuProps }">
                          <v-btn
                            v-bind="menuProps"
                            variant="text"
                            size="small"
                            append-icon="mdi-menu-down"
                            class="role-btn"
                            :class="`role-${user.access}`"
                            :disabled="user.loading"
                          >
                            {{ accessLabel[user.access] || user.access }}
                          </v-btn>
                        </template>
                        <v-list density="compact">
                          <v-list-item
                            :active="user.access === 'view'"
                            :disabled="isRoleDisabled(user, 'view')"
                            @click="onChangeAccess(user, index, 'view')"
                          >
                            <v-list-item-title>Can view</v-list-item-title>
                          </v-list-item>
                          <v-list-item
                            :active="user.access === 'edit'"
                            :disabled="isRoleDisabled(user, 'edit')"
                            @click="onChangeAccess(user, index, 'edit')"
                          >
                            <v-list-item-title>Can edit</v-list-item-title>
                          </v-list-item>
                          <v-list-item
                            v-if="user.user_type === 'user'"
                            :active="user.access === 'owner'"
                            :disabled="isRoleDisabled(user, 'owner')"
                            @click="onChangeAccess(user, index, 'owner')"
                          >
                            <v-list-item-title>Is owner</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                    </td>

                    <td class="text-end action-cell">
                      <v-btn
                        v-if="
                          user.can_undo &&
                          (user.user_type === 'group' ||
                            (user.user_type === 'user' &&
                              quotaHolderId !== user.id))
                        "
                        icon
                        size="x-small"
                        variant="text"
                        title="Undo share"
                        @click="undoAccess(user, index)"
                      >
                        <v-icon size="16">mdi-undo</v-icon>
                      </v-btn>

                      <v-btn
                        v-if="canRemoveRow(user)"
                        icon
                        size="x-small"
                        variant="text"
                        color="error"
                        title="Remove"
                        @click="onRemoveAccess(user, index)"
                      >
                        <v-icon size="16">mdi-close</v-icon>
                      </v-btn>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </section>

          <!-- Give access -->
          <section class="mb-6 field">
            <div class="section-heading">Give access</div>
            <v-card variant="outlined" border="grey thin">
              <v-card-text class="pa-5">
                <v-btn-toggle
                  v-model="inviteTarget"
                  density="compact"
                  mandatory
                  color="primary"
                  variant="outlined"
                  divided
                  class="mb-4"
                >
                  <v-btn value="users" size="small" prepend-icon="mdi-account">
                    Users
                  </v-btn>
                  <v-btn
                    value="groups"
                    size="small"
                    prepend-icon="mdi-account-group"
                  >
                    Groups
                  </v-btn>
                </v-btn-toggle>

                <v-autocomplete
                  v-model="grantTargetId"
                  v-model:search="autocompleteSearch"
                  :items="autocompleteItems"
                  :loading="isSearchingAutocomplete"
                  :placeholder="
                    inviteTarget === 'users'
                      ? 'Search by name or username'
                      : 'Search by group name'
                  "
                  :prepend-inner-icon="
                    inviteTarget === 'users' ? 'mdi-account-search' : 'mdi-account-group'
                  "
                  item-title="text"
                  item-value="id"
                  variant="outlined"
                  density="compact"
                  hide-no-data
                  hide-details
                  clearable
                  no-filter
                  return-object
                  class="mb-3"
                />

                <div class="d-flex align-center flex-wrap" style="gap: 0.5rem">
                  <v-select
                    v-model="selectedAccess"
                    :items="roleOptions"
                    variant="outlined"
                    density="compact"
                    hide-details
                    style="max-width: 200px"
                  />
                  <v-spacer></v-spacer>
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-plus"
                    variant="flat"
                    :disabled="!grantTargetId || isProcessing"
                    @click="grantAccess"
                  >
                    Add
                  </v-btn>
                </div>

                <v-alert
                  v-if="grantError"
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mt-3"
                >
                  {{ grantError }}
                </v-alert>
              </v-card-text>
            </v-card>
          </section>

          <!-- Sharing status -->
          <section class="mb-6 field">
            <div class="section-heading">Sharing status</div>
            <v-card variant="outlined" border="grey thin">
              <v-card-text class="pa-5">
                <v-alert
                  v-if="selfAccessLevel === 'owner'"
                  variant="tonal"
                  density="compact"
                  color="primary"
                  icon="mdi-shield-account-outline"
                  class="mb-4"
                >
                  You are the owner of this resource.
                </v-alert>
                <v-alert
                  v-else-if="selfAccessLevel === 'edit'"
                  variant="tonal"
                  density="compact"
                  color="primary"
                  icon="mdi-pencil-outline"
                  class="mb-4"
                >
                  You have been given specific permission to edit this resource.
                </v-alert>
                <v-alert
                  v-else-if="selfAccessLevel === 'view'"
                  variant="tonal"
                  density="compact"
                  color="primary"
                  icon="mdi-eye-outline"
                  class="mb-4"
                >
                  You have been given specific permission to view this resource.
                </v-alert>

                <template v-if="canChangeResourceFlags">
                  <div class="visibility-label mb-2">Visibility</div>
                  <v-btn-toggle
                    :model-value="currentVisibility"
                    density="compact"
                    variant="outlined"
                    mandatory
                    divided
                    class="mb-4 visibility-toggle"
                    @update:model-value="onVisibilityChange"
                  >
                    <v-btn
                      value="public"
                      size="small"
                      prepend-icon="mdi-earth"
                      :disabled="
                        !canBePublicDiscoverable ||
                        !canChangeResourceFlags ||
                        isProcessingAccess
                      "
                      :title="
                        !canChangeResourceFlags
                          ? accessDeniedTitle
                          : 'Can be viewed and downloaded by anyone.'
                      "
                    >
                      Public
                    </v-btn>
                    <v-btn
                      value="discoverable"
                      size="small"
                      prepend-icon="mdi-magnify"
                      :disabled="
                        !canBePublicDiscoverable ||
                        !canChangeResourceFlags ||
                        isProcessingAccess
                      "
                      :title="
                        !canChangeResourceFlags
                          ? accessDeniedTitle
                          : 'Metadata is public but data are protected.'
                      "
                    >
                      Discoverable
                    </v-btn>
                    <v-btn
                      value="private"
                      size="small"
                      prepend-icon="mdi-lock-outline"
                      :disabled="
                        (!resAccess.isPublic && !resAccess.isDiscoverable) ||
                        !canChangeResourceFlags ||
                        isProcessingAccess
                      "
                      :title="
                        !canChangeResourceFlags
                          ? accessDeniedTitle
                          : 'Can be viewed and downloaded only by designated users or research groups.'
                      "
                    >
                      Private
                    </v-btn>
                  </v-btn-toggle>

                  <div v-if="selfAccessLevel === 'owner'" class="sharing-options">
                    <div class="sharing-option">
                      <v-checkbox
                        v-model="resAccess.isShareable"
                        label="Shareable"
                        density="compact"
                        hide-details
                        color="primary"
                        :disabled="isProcessingShareable"
                        @update:model-value="
                          setShareable(
                            resAccess.isShareable
                              ? 'make_shareable'
                              : 'make_not_shareable',
                          )
                        "
                      />
                      <div class="sharing-hint">
                        {{
                          resAccess.isShareable
                            ? "Others with access can share this resource at the same permission level."
                            : "Only the owner can share this resource."
                        }}
                      </div>
                    </div>

                    <div v-if="!resAccess.isPublic" class="sharing-option">
                      <v-checkbox
                        v-model="resAccess.isPrivateLinkSharing"
                        label="Enable private link sharing"
                        density="compact"
                        hide-details
                        color="primary"
                        :disabled="isProcessingPrivateLinkSharing"
                        @update:model-value="
                          setPrivateLinkSharing(
                            resAccess.isPrivateLinkSharing
                              ? 'enable_private_sharing_link'
                              : 'remove_private_sharing_link',
                          )
                        "
                      />
                      <div class="sharing-hint">
                        Anyone with the link (including anonymous users) can
                        access the resource.
                      </div>
                    </div>
                  </div>
                </template>

                <v-alert
                  v-if="sharingError"
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mt-3"
                >
                  {{ sharingError }}
                </v-alert>
              </v-card-text>
            </v-card>
          </section>

          <!-- Storage / quota holder -->
          <section
            v-if="selfAccessLevel === 'owner' && quotaHolder"
            class="mb-2 field"
          >
            <div class="section-heading">Storage</div>
            <v-card variant="outlined" border="grey thin">
              <v-card-text class="pa-5">
                <div class="d-flex align-center flex-wrap" style="gap: 0.5rem">
                  <v-icon color="amber-darken-2" size="18">mdi-chart-pie</v-icon>
                  <span class="text-body-2 text-medium-emphasis">
                    Quota holder:
                  </span>
                  <strong class="text-body-2">{{ quotaHolder.best_name }}</strong>

                  <v-btn
                    v-if="!hasOnlyOneOwner"
                    size="x-small"
                    variant="outlined"
                    class="ms-1"
                    @click="showChangeQuotaHolder = !showChangeQuotaHolder"
                  >
                    Change
                  </v-btn>
                </div>

                <v-expand-transition>
                  <div v-if="showChangeQuotaHolder" class="mt-4">
                    <v-select
                      v-model="newQuotaHolderUsername"
                      :items="quotaHolderCandidates"
                      item-title="best_name"
                      item-value="user_name"
                      label="Change quota holder to another owner"
                      variant="outlined"
                      density="compact"
                      hide-details
                      class="mb-2"
                    />
                    <v-alert
                      v-if="quotaError"
                      type="error"
                      variant="tonal"
                      density="compact"
                      class="mb-2"
                    >
                      {{ quotaError }}
                    </v-alert>
                    <div class="d-flex justify-end" style="gap: 0.5rem">
                      <v-btn
                        size="small"
                        variant="text"
                        :disabled="isChangingQuotaHolder"
                        @click="showChangeQuotaHolder = false"
                      >
                        Cancel
                      </v-btn>
                      <v-btn
                        size="small"
                        color="primary"
                        variant="flat"
                        :loading="isChangingQuotaHolder"
                        :disabled="!newQuotaHolderUsername"
                        @click="setQuotaHolder"
                      >
                        Save changes
                      </v-btn>
                    </div>
                  </div>
                </v-expand-transition>
              </v-card-text>
            </v-card>
          </section>
        </template>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="dialogOpen = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Confirm self-demotion as owner -->
  <v-dialog v-model="confirmDemote.open" max-width="500">
    <v-card class="confirm-card">
      <v-card-title class="d-flex align-center" style="gap: 0.5rem">
        <v-icon color="warning">mdi-alert-outline</v-icon>
        Change your access
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pt-4 text-body-2">
        You are removing your own owner privileges. You may not be able to undo
        this change. Continue?
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="confirmDemote.open = false">Cancel</v-btn>
        <v-btn color="error" variant="flat" @click="confirmDemoteAccept">
          Confirm
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Confirm remove self -->
  <v-dialog v-model="confirmRemoveSelf.open" max-width="500">
    <v-card class="confirm-card">
      <v-card-title class="d-flex align-center" style="gap: 0.5rem">
        <v-icon color="error">mdi-alert-circle-outline</v-icon>
        Remove your own access
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pt-4 text-body-2">
        Are you sure you want to remove your own access from this resource? You
        will lose access immediately.
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="confirmRemoveSelf.open = false">
          Cancel
        </v-btn>
        <v-btn color="error" variant="flat" @click="confirmRemoveSelfAccept">
          Remove
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { Notifications } from "@cznethub/cznet-vue-core";
import User from "@/models/user.model";

interface AccessUser {
  user_type: "user" | "group";
  access: "owner" | "edit" | "view" | "none";
  id: number;
  pictureUrl: string | null;
  best_name: string;
  user_name: string | null;
  can_undo: boolean;
  loading?: boolean;
  [k: string]: any;
}

interface ResAccess {
  isPublic: boolean;
  isDiscoverable: boolean;
  isShareable: boolean;
  isPrivateLinkSharing: boolean;
}

const props = withDefaults(
  defineProps<{
    modelValue?: boolean;
    resourceId: string;
  }>(),
  { modelValue: false },
);

const emit = defineEmits(["update:modelValue", "access-updated"]);

const isLoading = ref(false);
const dataLoaded = ref(false);
const loadError = ref("");

const users = ref<AccessUser[]>([]);
const currentUserId = ref<number | null>(null);
const selfAccessLevel = ref<string | null>(null);
const quotaHolderId = ref<number | null>(null);
const canChangeResourceFlags = ref(false);
const canBePublicDiscoverable = ref(false);
const resAccess = ref<ResAccess>({
  isPublic: false,
  isDiscoverable: false,
  isShareable: false,
  isPrivateLinkSharing: false,
});

const inviteTarget = ref<"users" | "groups">("users");
const selectedAccess = ref<"view" | "edit" | "owner">("view");
const grantTargetId = ref<{ id: number; text: string } | null>(null);
const autocompleteSearch = ref("");
const autocompleteItems = ref<{ id: number; text: string }[]>([]);
const isSearchingAutocomplete = ref(false);
let searchToken = 0;
let searchDebounce: number | null = null;

const isProcessing = ref(false);
const isProcessingAccess = ref(false);
const isProcessingShareable = ref(false);
const isProcessingPrivateLinkSharing = ref(false);
const isChangingQuotaHolder = ref(false);

const grantError = ref("");
const sharingError = ref("");
const quotaError = ref("");

const showUsageInfo = ref(false);
const showChangeQuotaHolder = ref(false);
const newQuotaHolderUsername = ref<string | null>(null);

const confirmDemote = ref({
  open: false,
  user: null as AccessUser | null,
  index: -1,
  accessToGrant: "view" as "view" | "edit" | "owner",
});

const confirmRemoveSelf = ref({
  open: false,
  user: null as AccessUser | null,
  index: -1,
});

const accessDeniedTitle =
  "You do not have permission to change the sharing status.";
const accessLabel: Record<string, string> = {
  view: "Can view",
  edit: "Can edit",
  owner: "Is owner",
};

const dialogOpen = computed<boolean>({
  get: () => props.modelValue,
  set: (value: boolean) => {
    emit("update:modelValue", value);
  },
});

const hasOnlyOneOwner = computed<boolean>(
  () => users.value.filter((u) => u.access === "owner").length === 1,
);

const currentVisibility = computed<"public" | "discoverable" | "private">(
  () => {
    if (resAccess.value.isPublic) return "public";
    if (resAccess.value.isDiscoverable) return "discoverable";
    return "private";
  },
);

const roleOptions = computed(() => {
  const opts: { title: string; value: "view" | "edit" | "owner" }[] = [
    { title: "Can view", value: "view" },
  ];
  if (selfAccessLevel.value === "owner" || selfAccessLevel.value === "edit") {
    opts.push({ title: "Can edit", value: "edit" });
  }
  if (inviteTarget.value === "users" && selfAccessLevel.value === "owner") {
    opts.push({ title: "Is owner", value: "owner" });
  }
  return opts;
});

const quotaHolder = computed<AccessUser | null>(() => {
  if (quotaHolderId.value == null) return null;
  return (
    users.value.find(
      (u) => u.user_type === "user" && u.id === quotaHolderId.value,
    ) || null
  );
});

const quotaHolderCandidates = computed<AccessUser[]>(() =>
  users.value.filter(
    (u) =>
      u.user_type === "user" &&
      u.access === "owner" &&
      u.id !== quotaHolderId.value,
  ),
);

watch(() => props.modelValue, onDialogToggle);
watch(() => inviteTarget.value, onInviteTargetChange);
watch(() => autocompleteSearch.value, onAutocompleteSearch);

function onDialogToggle(open: boolean) {
    if (!open) return;
    if (!dataLoaded.value && !isLoading.value) {
      loadData();
    }
    // The discovery app runs inside an iframe with scrolling="no" sized to
    // its full content (see hs_discover/templates/hs_discover/search.html),
    // so Vuetify's position:fixed dialog lands at iframe-center — typically
    // far below the parent viewport. Wait for the dialog to mount and the
    // parent's ResizeObserver to grow the iframe (otherwise iframe.offsetHeight
    // is stale), then scroll the parent so iframe-center aligns with the
    // parent's viewport center.
    setTimeout(alignDialogToParentViewport, 80);
  }

function alignDialogToParentViewport() {
    try {
      const parentWin = window.parent;
      if (!parentWin || parentWin === window) return;
      const iframe = parentWin.document.getElementById(
        "discovery-app-frame",
      ) as HTMLIFrameElement | null;
      if (!iframe) return;
      const iframeRect = iframe.getBoundingClientRect();
      // The iframe is sized to body.scrollHeight by the parent's ResizeObserver;
      // use the larger of the two to stay correct if the resize hasn't yet
      // settled when we measure.
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

function onInviteTargetChange() {
    grantTargetId.value = null;
    autocompleteSearch.value = "";
    autocompleteItems.value = [];
    if (
      selectedAccess.value === "owner" &&
      inviteTarget.value === "groups"
    ) {
      selectedAccess.value = "view";
    }
  }

function onAutocompleteSearch(q: string) {
    if (searchDebounce) {
      window.clearTimeout(searchDebounce);
    }
    if (!q || q.length < 2) {
      autocompleteItems.value = [];
      return;
    }
    searchDebounce = window.setTimeout(() => runAutocomplete(q), 300);
  }

async function runAutocomplete(q: string) {
    const token = ++searchToken;
    isSearchingAutocomplete.value = true;
    try {
      const url =
        inviteTarget.value === "users"
          ? `/user-autocomplete/?q=${encodeURIComponent(q)}`
          : `/group-autocomplete/?q=${encodeURIComponent(q)}`;
      const resp = await fetch(url, { credentials: "include" });
      if (!resp.ok) return;
      const data = await resp.json();
      if (token !== searchToken) return;
      // django-autocomplete-light Select2 response: { results: [{id, text}], ... }
      autocompleteItems.value = (data.results || []).map((r: any) => ({
        id: Number(r.id),
        text: r.text,
      }));
    } catch (e) {
      // ignore
    } finally {
      if (token === searchToken) {
        isSearchingAutocomplete.value = false;
      }
    }
  }

async function loadData() {
    isLoading.value = true;
    loadError.value = "";
    try {
      const resp = await fetch(
        `/hsapi/_internal/${props.resourceId}/manage-access-data/`,
        { credentials: "include" },
      );
      if (!resp.ok) {
        loadError.value =
          resp.status === 403
            ? "You don't have permission to manage access for this resource."
            : `Failed to load access data (${resp.status}).`;
        return;
      }
      const data = await resp.json();
      if (data.status !== "success") {
        loadError.value = data.message || "Failed to load access data.";
        return;
      }
      users.value = (data.users_json || []).map((u: AccessUser) => ({
        ...u,
        loading: false,
      }));
      currentUserId.value = data.current_user_id;
      selfAccessLevel.value = data.self_access_level;
      canChangeResourceFlags.value = data.can_change_resource_flags;
      canBePublicDiscoverable.value = data.can_be_public_or_discoverable;
      quotaHolderId.value = data.quota_holder_pk;
      resAccess.value = data.resource_access;
      dataLoaded.value = true;
    } catch (e: any) {
      loadError.value = `Failed to load access data: ${e.message}`;
    } finally {
      isLoading.value = false;
    }
  }

async function postForm(url: string, body: Record<string, string> = {}) {
    const csrfToken = await User.getCSRFToken();
    const formBody = new URLSearchParams(body).toString();
    return fetch(url, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: formBody,
    });
  }

function isRoleDisabled(user: AccessUser, role: "view" | "edit" | "owner"): boolean {
    if (user.access === role) return false; // current — always selectable (no-op)

    if (role === "view") {
      if (user.access === "none") return true;
    } else if (role === "edit") {
      if (selfAccessLevel.value !== "owner" && selfAccessLevel.value !== "edit")
        return true;
    } else if (role === "owner") {
      if (selfAccessLevel.value !== "owner") return true;
    }

    // Last-owner safety
    if (
      user.access === "owner" &&
      hasOnlyOneOwner.value &&
      role !== "owner"
    ) {
      return true;
    }

    // Quota holder cannot lose owner privileges
    if (
      user.user_type === "user" &&
      quotaHolderId.value === user.id &&
      role !== "owner"
    ) {
      return true;
    }

    return false;
  }

function canRemoveRow(user: AccessUser): boolean {
    if (user.access === "owner" && hasOnlyOneOwner.value) return false;
    if (user.user_type === "user" && user.id === quotaHolderId.value)
      return false;
    return (
      selfAccessLevel.value === "owner" || user.id === currentUserId.value
    );
  }

function onChangeAccess(
    user: AccessUser,
    index: number,
    accessToGrant: "view" | "edit" | "owner",
  ) {
    if (user.access === accessToGrant) return;
    if (
      user.user_type === "user" &&
      user.id === currentUserId.value &&
      user.access === "owner"
    ) {
      confirmDemote.value = { open: true, user, index, accessToGrant };
    } else {
      changeAccess(user, index, accessToGrant);
    }
  }

function confirmDemoteAccept() {
    const { user, index, accessToGrant } = confirmDemote.value;
    confirmDemote.value.open = false;
    if (user) changeAccess(user, index, accessToGrant);
  }

async function changeAccess(
    user: AccessUser,
    index: number,
    accessToGrant: "view" | "edit" | "owner",
  ) {
    grantError.value = "";
    user.loading = true;
    users.value.splice(index, 1, user);
    isProcessing.value = true;
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/share-resource-with-${user.user_type}/${accessToGrant}/${user.id}/`,
      );
      const text = await resp.text();
      let payload: any;
      try {
        payload = JSON.parse(text);
      } catch {
        grantError.value = "Unexpected response from server.";
        return;
      }
      if (payload.status === "success") {
        const updated = { ...payload.user, loading: false } as AccessUser;
        users.value.splice(index, 1, updated);
        if (currentUserId.value === updated.id) {
          selfAccessLevel.value = updated.access;
        }
        emit("access-updated");
      } else {
        grantError.value = payload.error_msg || "Failed to change permission.";
        user.loading = false;
        users.value.splice(index, 1, user);
      }
    } catch (e: any) {
      grantError.value = e.message || "Network error.";
      user.loading = false;
      users.value.splice(index, 1, user);
    } finally {
      isProcessing.value = false;
    }
  }

function onRemoveAccess(user: AccessUser, index: number) {
    if (user.id === currentUserId.value) {
      confirmRemoveSelf.value = { open: true, user, index };
    } else {
      removeAccess(user, index);
    }
  }

function confirmRemoveSelfAccept() {
    const { user, index } = confirmRemoveSelf.value;
    confirmRemoveSelf.value.open = false;
    if (user) removeAccess(user, index);
  }

async function removeAccess(user: AccessUser, index: number) {
    grantError.value = "";
    user.loading = true;
    users.value.splice(index, 1, user);
    isProcessing.value = true;
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/unshare-resource-with-${user.user_type}/${user.id}/`,
      );
      const payload = await resp.json();
      if (payload.status === "success") {
        users.value.splice(index, 1);
        if (payload.redirect_to) {
          window.top!.location.href = payload.redirect_to;
        }
        emit("access-updated");
      } else {
        grantError.value = payload.message || "Failed to remove access.";
        user.loading = false;
        users.value.splice(index, 1, user);
      }
    } catch (e: any) {
      grantError.value = e.message || "Network error.";
      user.loading = false;
      users.value.splice(index, 1, user);
    } finally {
      isProcessing.value = false;
    }
  }

async function undoAccess(user: AccessUser, index: number) {
    grantError.value = "";
    user.loading = true;
    users.value.splice(index, 1, user);
    isProcessing.value = true;
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/undo-share-resource-with-${user.user_type}/${user.id}/`,
      );
      const payload = await resp.json();
      if (payload.status === "success") {
        const newPrivilege = payload[`undo_${user.user_type}_privilege`];
        if (newPrivilege === "none") {
          users.value.splice(index, 1);
        } else {
          const updated: AccessUser = {
            ...user,
            access: newPrivilege,
            can_undo: false,
            loading: false,
          };
          users.value.splice(index, 1, updated);
        }
        emit("access-updated");
      } else {
        grantError.value = payload.message || "Undo failed.";
        user.loading = false;
        users.value.splice(index, 1, user);
      }
    } catch (e: any) {
      grantError.value = e.message || "Network error.";
      user.loading = false;
      users.value.splice(index, 1, user);
    } finally {
      isProcessing.value = false;
    }
  }

async function grantAccess() {
    if (!grantTargetId.value) return;
    const targetId = grantTargetId.value.id;
    const isUser = inviteTarget.value === "users";
    const existingIndex = users.value.findIndex(
      (u) => u.id === targetId && u.user_type === (isUser ? "user" : "group"),
    );
    if (
      existingIndex >= 0 &&
      users.value[existingIndex].access === selectedAccess.value
    ) {
      return;
    }

    grantError.value = "";
    isProcessing.value = true;
    if (existingIndex >= 0) {
      const u = users.value[existingIndex];
      u.loading = true;
      users.value.splice(existingIndex, 1, u);
    }

    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/share-resource-with-${
          isUser ? "user" : "group"
        }/${selectedAccess.value}/${targetId}/`,
      );
      const text = await resp.text();
      let payload: any;
      try {
        payload = JSON.parse(text);
      } catch {
        grantError.value = "Failed to change permission.";
        return;
      }
      if (payload.status === "success") {
        const updated = { ...payload.user, loading: false } as AccessUser;
        if (existingIndex >= 0) {
          users.value.splice(existingIndex, 1, updated);
          if (currentUserId.value === updated.id) {
            selfAccessLevel.value = updated.access;
          }
        } else {
          users.value.push(updated);
        }
        grantTargetId.value = null;
        autocompleteSearch.value = "";
        autocompleteItems.value = [];
        emit("access-updated");
      } else {
        grantError.value = payload.error_msg || "Failed to add access.";
        if (existingIndex >= 0) {
          const u = users.value[existingIndex];
          u.loading = false;
          users.value.splice(existingIndex, 1, u);
        }
      }
    } catch (e: any) {
      grantError.value = e.message || "Network error.";
    } finally {
      isProcessing.value = false;
    }
  }

async function onVisibilityChange(value: "public" | "discoverable" | "private") {
    if (value === currentVisibility.value) return;
    const action =
      value === "public"
        ? "make_public"
        : value === "discoverable"
          ? "make_discoverable"
          : "make_private";
    await setResourceAccess(action, value);
  }

async function setResourceAccess(
    action: "make_public" | "make_discoverable" | "make_private",
    value: "public" | "discoverable" | "private",
  ) {
    isProcessingAccess.value = true;
    sharingError.value = "";
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/set-resource-flag/`,
        { flag: action },
      );
      const payload = await resp.json();
      if (payload.status === "success") {
        resAccess.value = {
          ...resAccess.value,
          isPublic: value === "public",
          isDiscoverable: value !== "private",
        };
        emit("access-updated");
      } else {
        sharingError.value = payload.message || "Failed to update sharing.";
      }
    } catch (e: any) {
      sharingError.value = e.message || "Network error.";
    } finally {
      isProcessingAccess.value = false;
    }
  }

async function setShareable(action: "make_shareable" | "make_not_shareable") {
    isProcessingShareable.value = true;
    sharingError.value = "";
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/set-resource-flag/`,
        { flag: action },
      );
      const payload = await resp.json();
      if (payload.status !== "success") {
        sharingError.value = payload.message || "Failed to update.";
        // Roll back the optimistic toggle
        resAccess.value.isShareable = action === "make_not_shareable";
      }
    } catch (e: any) {
      sharingError.value = e.message || "Network error.";
      resAccess.value.isShareable = action === "make_not_shareable";
    } finally {
      isProcessingShareable.value = false;
    }
  }

async function setPrivateLinkSharing(
    action: "enable_private_sharing_link" | "remove_private_sharing_link",
  ) {
    isProcessingPrivateLinkSharing.value = true;
    sharingError.value = "";
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/set-resource-flag/`,
        { flag: action },
      );
      const payload = await resp.json();
      if (payload.status !== "success") {
        sharingError.value = payload.message || "Failed to update.";
        resAccess.value.isPrivateLinkSharing =
          action === "remove_private_sharing_link";
      } else {
        resAccess.value.isPrivateLinkSharing =
          action === "enable_private_sharing_link";
      }
    } catch (e: any) {
      sharingError.value = e.message || "Network error.";
      resAccess.value.isPrivateLinkSharing =
        action === "remove_private_sharing_link";
    } finally {
      isProcessingPrivateLinkSharing.value = false;
    }
  }

async function setQuotaHolder() {
    if (!newQuotaHolderUsername.value) return;
    isChangingQuotaHolder.value = true;
    quotaError.value = "";
    try {
      const resp = await postForm(
        `/hsapi/_internal/${props.resourceId}/change-quota-holder/`,
        { new_holder_username: newQuotaHolderUsername.value },
      );
      const payload = await resp.json();
      if (payload.status === "success") {
        const newHolder = users.value.find(
          (u) =>
            u.user_type === "user" &&
            u.user_name === newQuotaHolderUsername.value,
        );
        if (newHolder) {
          newHolder.can_undo = false;
          quotaHolderId.value = newHolder.id;
        }
        showChangeQuotaHolder.value = false;
        newQuotaHolderUsername.value = null;
        Notifications.toast({
          message: "Quota holder updated.",
          type: "success",
        });
      } else {
        quotaError.value = payload.message || "Failed to update quota holder.";
      }
    } catch (e: any) {
      quotaError.value = e.message || "Network error.";
    } finally {
      isChangingQuotaHolder.value = false;
    }
  }
</script>

<style lang="scss" scoped>
$accent: #4bb5c1;
$border-soft: rgba(0, 0, 0, 0.08);

.manage-access-card {
  border-radius: 12px !important;
  overflow: hidden;
}

.manage-access-card.is-processing {
  pointer-events: none;
}

.dialog-banner {
  height: 6px;
  background: linear-gradient(135deg, #4bb5c1 0%, #2a7c87 100%);
}

.dialog-header {
  display: flex;
  align-items: center;
  padding: 1rem 1.25rem;
  background: #fff;
}

.dialog-title {
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: rgba(0, 0, 0, 0.87);
}

.dialog-body {
  padding: 1.5rem 1.25rem !important;
}

.dialog-actions {
  padding: 0.5rem 1rem;
}

.section-heading {
  color: $accent;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-bottom: 0.4rem;
  margin-bottom: 0.75rem;
  border-bottom: 2px solid #e0e0e0;
}

.field :deep(.v-card) {
  border-color: $border-soft !important;
}

.usage-info {
  padding-left: 1.25rem;
  color: rgba(0, 0, 0, 0.7);

  li {
    margin-bottom: 0.5rem;
  }
}

.access-table {
  background: transparent;
}

.access-table :deep(td) {
  border-bottom: 1px solid $border-soft !important;
  padding-top: 0.65rem !important;
  padding-bottom: 0.65rem !important;
}

.access-table :deep(tr:last-child td) {
  border-bottom: none !important;
}

.access-table tr.is-loading {
  opacity: 0.55;
}

.user-avatar {
  border: 1px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
}

.user-info {
  min-width: 0;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  text-decoration: none;
  line-height: 1.3;

  &:hover {
    color: $accent;
    text-decoration: underline;
  }
}

.user-meta {
  line-height: 1.3;
}

.role-cell {
  width: 140px;
}

.action-cell {
  width: 80px;
}

.role-btn {
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0;

  &.role-owner :deep(.v-btn__content) {
    color: $accent;
  }

  &.role-edit :deep(.v-btn__content) {
    color: rgba(0, 0, 0, 0.75);
  }

  &.role-view :deep(.v-btn__content) {
    color: rgba(0, 0, 0, 0.6);
  }
}

.visibility-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(0, 0, 0, 0.55);
}

.visibility-toggle :deep(.v-btn) {
  text-transform: none;
  letter-spacing: 0;
  font-weight: 500;
}

.visibility-toggle :deep(.v-btn--active) {
  background-color: rgba(75, 181, 193, 0.1);
  color: $accent;
}

.sharing-options {
  border-top: 1px solid $border-soft;
  padding-top: 0.75rem;
}

.sharing-option {
  margin-bottom: 0.75rem;

  &:last-child {
    margin-bottom: 0;
  }
}

.sharing-hint {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.55);
  margin-left: 2rem;
  line-height: 1.4;
}

.confirm-card {
  border-radius: 12px;
}

.pointer-events-none {
  pointer-events: none;
}
</style>
