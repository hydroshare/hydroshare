<template>
  <v-container class="sidebar flex-shrink-0">
    <div class="sidebar--content">
      <div class="text-h6 mb-6">Filters</div>

      <!-- SUBJECT/KEYWORDS -->
      <cd-search
        v-model="modelValue.subject.value"
        :target-field="EnumHistoryTypes.SUBJECT"
        :append-search-button="false"
        :is-eager="true"
        @blur="$emit('update:model-value', modelValue)"
        @keyup.enter="$emit('update:model-value', modelValue)"
        @hint-selected="$emit('update:model-value', modelValue)"
        @clear="
          modelValue.subject.value = '';
          $emit('update:model-value', modelValue);
        "
        :inputAttrs="{
          variant: 'outlined',
          prependInnerIcon: modelValue.subject.icon,
          label: modelValue.subject.title,
        }"
        class="mt-6"
      >
      </cd-search>

      <!-- CREATOR/CONTRIBUTOR NAME -->
      <cd-search
        v-model="modelValue.creatorName.value"
        :target-field="EnumHistoryTypes.CREATOR"
        :append-search-button="false"
        :is-eager="true"
        @blur="$emit('update:model-value', modelValue)"
        @keyup.enter="$emit('update:model-value', modelValue)"
        @hint-selected="$emit('update:model-value', modelValue)"
        @clear="
          modelValue.creatorName.value = '';
          $emit('update:model-value', modelValue);
        "
        :inputAttrs="{
          variant: 'outlined',
          prependInnerIcon: 'mdi-account-edit',
          label: modelValue.creatorName.title,
        }"
        class="mt-6"
      >
      </cd-search>

      <!-- FUNDER -->
      <cd-search
        v-model="modelValue.fundingFunderName.value"
        :target-field="EnumHistoryTypes.FUNDER"
        :append-search-button="false"
        :is-eager="true"
        @blur="$emit('update:model-value', modelValue)"
        @keyup.enter="$emit('update:model-value', modelValue)"
        @hint-selected="$emit('update:model-value', modelValue)"
        @clear="
          modelValue;
          modelValue.fundingFunderName.value = '';
          $emit('update:model-value', modelValue);
        "
        :inputAttrs="{
          variant: 'outlined',
          prependInnerIcon: modelValue.fundingFunderName.icon,
          label: 'Funder',
        }"
        class="my-6"
      >
      </cd-search>

      <v-expansion-panels multiple v-model="panels">
        <!-- TEMPORAL COVERAGE -->
        <v-expansion-panel tile key="2">
          <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
            <v-switch
              @click.stop=""
              v-model="modelValue.dataCoverage.isEnabled"
              @update:model-value="$emit('update:model-value', modelValue)"
              density="compact"
              hide-details
              color="primary"
            ></v-switch>
            <div class="ml-4 text-body-1 cursor-pointer">Temporal coverage</div>
          </v-expansion-panel-title>

          <v-expansion-panel-text>
            <cd-range-input
              v-model="modelValue.dataCoverage.value"
              v-model:isActive="modelValue.dataCoverage.isEnabled"
              @update:is-active="$emit('update:model-value', modelValue)"
              @end="onFilterControlChange(modelValue.dataCoverage)"
              :min="modelValue.dataCoverage.min"
              :max="modelValue.dataCoverage.max"
              label="Temporal coverage"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- CONTENT TYPE -->
        <v-expansion-panel tile key="1">
          <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-3">
            <v-switch
              @click.stop=""
              v-model="modelValue.contentType.isEnabled"
              @update:model-value="$emit('update:model-value', modelValue)"
              density="compact"
              hide-details
              color="primary"
            ></v-switch>
            <div class="ml-4 text-body-1 cursor-pointer">Content type</div>
          </v-expansion-panel-title>

          <v-progress-linear
            v-if="isFetchingContentTypes"
            color="primary"
            indeterminate
          ></v-progress-linear>

          <v-expansion-panel-text>
            <div
              v-for="(option, index) of modelValue.contentType.options"
              class="d-flex justify-space-between align-center"
            >
              <v-checkbox
                v-model="modelValue.contentType.value"
                @update:model-value="
                  onFilterControlChange(modelValue.contentType)
                "
                :label="option.label"
                :key="index"
                :value="option.value"
                hide-details
                density="compact"
                color="primary"
              ></v-checkbox>

              <v-img
                v-if="option.logo"
                :src="option.logo"
                v-tooltip="option.label"
                :alt="option.label"
                width="30"
                max-width="30"
              />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- AVAILABILITY -->
        <v-expansion-panel tile key="0">
          <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-3">
            <v-switch
              @click.stop=""
              v-model="modelValue.availability.isEnabled"
              @update:model-value="$emit('update:model-value', modelValue)"
              density="compact"
              hide-details
              color="primary"
            ></v-switch>
            <div class="ml-4 text-body-1 cursor-pointer">Availiability</div>
          </v-expansion-panel-title>

          <v-expansion-panel-text>
            <div
              v-for="(option, index) of modelValue.availability.options"
              class="d-flex justify-space-between align-center"
            >
              <v-checkbox
                v-model="modelValue.availability.value"
                @update:model-value="
                  onFilterControlChange(modelValue.availability)
                "
                color="primary"
                :label="option.label"
                :key="index"
                :value="option.value"
                hide-details
                density="compact"
              ></v-checkbox>
              <v-img
                :src="option.icon"
                class="img-access-icon flex-grow-0"
                width="25"
                v-tooltip="option.label"
                :alt="option.label"
              />
            </div>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- DATE CREATED -->
        <v-expansion-panel tile key="3">
          <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
            <v-switch
              @click.stop=""
              v-model="modelValue.creationDate.isEnabled"
              @update:model-value="$emit('update:model-value', modelValue)"
              density="compact"
              hide-details
              color="primary"
            ></v-switch>

            <div class="ml-4 text-body-1 cursor-pointer">Date created</div>
          </v-expansion-panel-title>

          <v-expansion-panel-text key="4">
            <cd-range-input
              v-model="modelValue.creationDate.value"
              v-model:isActive="modelValue.creationDate.isEnabled"
              @update:is-active="$emit('update:model-value', modelValue)"
              @end="onFilterControlChange(modelValue.creationDate)"
              :min="modelValue.creationDate.min"
              :max="modelValue.creationDate.max"
              label="Date created"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- PUBLICATION YEAR -->
        <v-expansion-panel tile>
          <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
            <v-switch
              @click.stop=""
              v-model="modelValue.publicationYear.isEnabled"
              @update:model-value="$emit('update:model-value', modelValue)"
              density="compact"
              hide-details
              color="primary"
            ></v-switch>

            <div class="ml-4 text-body-1 cursor-pointer">Publication year</div>
          </v-expansion-panel-title>

          <v-expansion-panel-text>
            <cd-range-input
              v-model="modelValue.publicationYear.value"
              v-model:isActive="modelValue.publicationYear.isEnabled"
              @update:is-active="$emit('update:model-value', modelValue)"
              @end="onFilterControlChange(modelValue.publicationYear)"
              :min="modelValue.publicationYear.min"
              :max="modelValue.publicationYear.max"
              label="Publication year"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <v-btn
        :disabled="!isSomeFilterActive"
        @click="clearFilters"
        class="mt-8"
        variant="outlined"
        block
        >Clear Filters</v-btn
      >
    </div>
  </v-container>
</template>

<script lang="ts">
import { Component, Prop, Vue, toNative } from "vue-facing-decorator";
import {
  contentTypeLogos,
  sharingStatusIcons,
  contentTypeLabels,
} from "@/constants";
import { formatDate } from "@/util";
import CdSpatialCoverageMap from "@/components/search-results/cd.spatial-coverage-map.vue";
import CdSearch from "@/components/search/cd.search.vue";
import SearchResults from "@/models/search-results.model";
import Search from "@/models/search.model";
import { EnumHistoryTypes } from "@/types";
import CdRangeInput from "./cd.range-input.vue";
import { useRoute, useRouter } from "vue-router";
import { EnumFilterTypes, Filter } from "./filter";

@Component({
  name: "cd-search-results",
  components: { CdSearch, CdSpatialCoverageMap, CdRangeInput },
  emits: ["update:model-value"],
})
class CdSearchSidebar extends Vue {
  isIntersecting = false;
  searchQuery = "";
  pageNumber = 1;
  pageSize = 20;
  hasMore = true;
  isSearching = false;
  isFetchingMore = false;

  @Prop() modelValue!: { [key: string]: Filter };
  contentTypeLogos = contentTypeLogos;
  sharingStatusIcons = sharingStatusIcons;
  contentTypeLabels = contentTypeLabels;
  enumFilterTypes = EnumFilterTypes;

  formatDate = formatDate;
  route = useRoute();
  router = useRouter();
  EnumHistoryTypes = EnumHistoryTypes;

  public get registeredFilters() {
    return Object.values(this.modelValue);
  }

  public get panels() {
    return SearchResults.$state.panels;
  }

  public set panels(range: number[]) {
    SearchResults.commit((state) => {
      state.panels = range;
    });
  }

  public get isSomeFilterActive() {
    return this.registeredFilters.some((f) => f.isActive());
  }

  public get isFetchingContentTypes() {
    return Search.$state.isFetchingContentTypes;
  }

  public onFilterControlChange(filter: Filter) {
    filter.isEnabled = true;

    this.$emit("update:model-value", this.modelValue);
  }

  public clearFilters() {
    const wasSomeActive = this.isSomeFilterActive;
    this.registeredFilters.forEach((f) => f.clear());

    if (wasSomeActive) {
      this.$emit("update:model-value", this.modelValue);
    }
  }
}
export default toNative(CdSearchSidebar);
</script>

<style lang="scss" scoped>
.v-expansion-panel--active,
.v-expansion-panel--active:not(:first-child),
.v-expansion-panel--active + .v-expansion-panel {
  margin-top: 1px;
}

:deep(.v-table) {
  .v-data-table__th--sorted,
  .v-data-table__td.isSorted {
    background: #f7f7f7 !important;
  }
}

:deep(.v-table tr.v-data-table__tr td) {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.sidebar {
  width: 20rem;
}

:deep(.v-select--chips .v-select__selections .v-chip--select:first-child) {
  margin-top: 1rem;
}
</style>
