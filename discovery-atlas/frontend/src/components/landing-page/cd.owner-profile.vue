<template>
  <v-menu offset-y :close-on-content-click="false">
    <template v-slot:activator="{ props: activatorProps }">
      <span v-bind="activatorProps" class="owner-link">
        {{ owner.best_name }}
        <v-icon small>mdi-menu-down</v-icon>
      </span>
    </template>

    <v-card class="profile-card" min-width="300" max-width="360">
      <div class="profile-banner"></div>
      <div class="profile-header">
        <v-avatar
          v-if="owner.pictureUrl"
          size="72"
          class="profile-avatar"
        >
          <img :src="owner.pictureUrl" :alt="owner.best_name" />
        </v-avatar>
        <v-avatar
          v-else
          size="72"
          color="grey-lighten-3"
          class="profile-avatar"
        >
          <v-icon size="48" color="grey-darken-1">mdi-account</v-icon>
        </v-avatar>
        <div class="profile-identity">
          <div class="profile-name">{{ owner.best_name }}</div>
          <div v-if="owner.title" class="profile-title text-medium-emphasis">
            {{ owner.title }}
          </div>
        </div>
      </div>

      <v-card-text class="profile-meta pt-0 pb-3">
        <div v-if="organizations.length" class="profile-row">
          <v-icon size="16" class="profile-row-icon">mdi-domain</v-icon>
          <div class="d-flex flex-column" style="gap: 0.1rem">
            <span v-for="(org, orgIdx) of organizations" :key="orgIdx">
              {{ org }}
            </span>
          </div>
        </div>
        <div v-if="location" class="profile-row">
          <v-icon size="16" class="profile-row-icon">mdi-map-marker-outline</v-icon>
          {{ location }}
        </div>
        <div v-if="owner.joined" class="profile-row">
          <v-icon size="16" class="profile-row-icon">mdi-calendar-outline</v-icon>
          Joined {{ owner.joined }}
        </div>
      </v-card-text>

      <v-divider v-if="owner.subject_areas && owner.subject_areas.length" />

      <v-card-text
        v-if="owner.subject_areas && owner.subject_areas.length"
        class="py-3"
      >
        <div class="profile-section-label">Subject Areas</div>
        <div class="d-flex flex-wrap" style="gap: 0.25rem">
          <v-chip
            v-for="(area, areaIdx) of owner.subject_areas"
            :key="areaIdx"
            size="x-small"
            variant="tonal"
            color="primary"
            label
          >
            {{ area }}
          </v-chip>
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

      <v-divider />

      <v-card-actions class="profile-actions px-4 py-3">
        <v-btn
          v-if="owner.email"
          :href="`mailto:${owner.email}`"
          variant="text"
          size="small"
          prepend-icon="mdi-email-outline"
          class="text-lowercase"
        >
          Email
        </v-btn>
        <v-spacer />
        <v-btn
          v-if="owner.user_name"
          :href="`/user/${owner.id}/`"
          target="_blank"
          rel="noopener"
          size="small"
          variant="flat"
          color="primary"
        >
          <span
            v-if="
              owner.viewable_contributions != null &&
              owner.viewable_contributions > 0
            "
          >
            Profile · {{ owner.viewable_contributions.toLocaleString() }}
          </span>
          <span v-else>Profile</span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-menu>
</template>

<script lang="ts">
import { Component, Vue, toNative, Prop } from "vue-facing-decorator";
import { listIdentifiers, IdentifierItem } from "./identifier-attrs";

@Component({
  name: "cd-owner-profile",
  components: {},
})
class CdOwnerProfile extends Vue {
  @Prop({ type: Object, required: true }) owner!: any;

  get organizations(): string[] {
    // HydroShare stores `organization` as a single string with multiple values
    // separated by ";" (see theme/static/js/profile.js splitAndWrapWithClass).
    const raw = this.owner?.organization;
    if (typeof raw !== "string") return [];
    return raw
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  get location(): string {
    const parts = [this.owner?.state, this.owner?.country].filter(Boolean);
    return parts.join(", ");
  }

  get identifierList(): IdentifierItem[] {
    return listIdentifiers(this.owner?.identifiers);
  }
}

export default toNative(CdOwnerProfile);
</script>

<style lang="scss" scoped>
@import "./profile-card.scss";

.owner-link {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.7);
  line-height: 1.4;
  transition: color 0.12s ease;
}

.owner-link:hover {
  color: rgb(var(--v-theme-primary));
}

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
