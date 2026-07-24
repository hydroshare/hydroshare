<template>
  <v-menu offset-y :close-on-content-click="false" class="d-inline">
    <template v-slot:activator="{ props: activatorProps }">
      <span
        class="mr-2 cursor-pointer"
        v-bind="activatorProps"
      >
        <span class="d-inline-block">
          {{ creator.name }}
          <v-icon small>mdi-menu-down</v-icon>
        </span>
      </span>
    </template>

    <v-card class="profile-card" min-width="300" max-width="360">
      <div class="profile-banner"></div>
      <div class="profile-header">
        <v-avatar size="72" color="grey-lighten-3" class="profile-avatar">
          <v-icon size="48" color="grey-darken-1">
            {{ isOrganization ? "mdi-domain" : "mdi-account" }}
          </v-icon>
        </v-avatar>
        <div class="profile-identity">
          <div class="profile-name">{{ creator.name }}</div>
          <div class="profile-title text-medium-emphasis">
            {{ isOrganization ? "Organization" : "Author" }}
          </div>
        </div>
      </div>

      <v-card-text
        v-if="creator.affiliation?.name || creator.address"
        class="profile-meta pt-0 pb-3"
      >
        <div v-if="creator.affiliation?.name" class="profile-row">
          <v-icon size="16" class="profile-row-icon">mdi-domain</v-icon>
          <span v-if="creator.affiliation.url">
            <a :href="creator.affiliation.url" target="_blank" rel="noopener">
              {{ creator.affiliation.name }}
            </a>
          </span>
          <span v-else>{{ creator.affiliation.name }}</span>
        </div>
        <div v-if="creator.address" class="profile-row">
          <v-icon size="16" class="profile-row-icon">mdi-map-marker-outline</v-icon>
          {{ creator.address }}
        </div>
      </v-card-text>

      <v-divider v-if="identifierList.length" />

      <v-card-text v-if="identifierList.length" class="py-3">
        <div class="profile-section-label">External Profiles</div>
        <div class="d-flex flex-wrap align-center" style="gap: 0.5rem">
          <a
            v-for="ident of identifierList"
            :key="ident.key"
            :href="ident.url"
            target="_blank"
            rel="noopener"
            class="identifier-link"
            :title="ident.attrs ? ident.attrs.title : ident.key"
          >
            <img
              v-if="ident.attrs"
              :src="ident.attrs.src"
              :alt="ident.attrs.title"
              class="identifier-icon"
            />
            <span v-else class="identifier-fallback">
              <v-icon size="18">mdi-link-variant</v-icon>
              {{ ident.key }}
            </span>
          </a>
        </div>
      </v-card-text>

      <v-divider v-if="hasActions" />

      <v-card-actions v-if="hasActions" class="profile-actions px-4 py-3">
        <v-btn
          v-if="creator.email"
          :href="`mailto:${creator.email}`"
          variant="text"
          size="small"
          prepend-icon="mdi-email-outline"
        >
          Email
        </v-btn>
        <v-spacer />
        <v-btn
          v-if="profileLink"
          :href="profileLink"
          target="_blank"
          rel="noopener"
          size="small"
          variant="flat"
          color="primary"
        >
          Profile
        </v-btn>
        <v-btn
          v-else-if="creator.url"
          :href="creator.url"
          target="_blank"
          rel="noopener"
          size="small"
          variant="flat"
          color="primary"
        >
          Website
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-menu>
</template>

<script lang="ts">
import { Component, Vue, toNative, Prop } from "vue-facing-decorator";
import { listIdentifiers, IdentifierItem } from "./identifier-attrs";

@Component({
  name: "cd-author-profile",
  components: {},
})
class CdAuthorProfile extends Vue {
  @Prop({ type: Object, required: true }) creator!: any;
  @Prop({ type: String, default: null }) profileLink!: string | null;
  @Prop({ type: Object, default: () => ({}) }) identifiers!: Record<string, string>;

  get isOrganization(): boolean {
    return this.creator?.type === "Organization";
  }

  get identifierList(): IdentifierItem[] {
    // Side-channel identifiers (from cached_metadata.creators) are the primary
    // source; fall back to the schema.org `identifier` field (ORCID URL only)
    // when name-matching missed in the parent.
    const list = listIdentifiers(this.identifiers);
    if (list.length === 0 && typeof this.creator?.identifier === "string") {
      return listIdentifiers({ ORCID: this.creator.identifier });
    }
    return list;
  }

  get hasActions(): boolean {
    return Boolean(
      this.creator?.email || this.creator?.url || this.profileLink,
    );
  }
}

export default toNative(CdAuthorProfile);
</script>

<style lang="scss" scoped>
@import "./profile-card.scss";

.identifier-link {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  transition: transform 0.12s ease, filter 0.12s ease;
}

.identifier-link:hover {
  transform: translateY(-1px);
  filter: brightness(0.9);
}

.identifier-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.identifier-fallback {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.7);
}
</style>
