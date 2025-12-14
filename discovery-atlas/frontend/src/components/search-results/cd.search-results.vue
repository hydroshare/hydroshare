<template>
  <v-container
    class="cd-search-results text-body-1"
    :class="{ 'is-small': $vuetify.display.smAndDown }"
  >
    <div class="d-flex align-baseline">
      <div class="text-h5 font-weight-bold mr-2">Discover</div>
      <div class="text-medium-emphasis text-body-1 font-italic">
        Public resources shared with the community
      </div>
    </div>
    <v-divider class="mt-2 mb-6"></v-divider>
    <div class="d-sm-block d-md-flex">
      <v-container class="sidebar flex-shrink-0">
        <div class="sidebar--content">
          <div class="text-h6 mb-6">Filters</div>

          <!-- SUBJECT/KEYWORDS -->
          <cd-search
            v-model="filter.subject.value"
            :target-field="EnumHistoryTypes.SUBJECT"
            :append-search-button="false"
            :is-eager="true"
            @blur="pushSearchRoute"
            @keyup.enter="pushSearchRoute"
            @hint-selected="pushSearchRoute()"
            @clear="
              filter.subject.value = '';
              pushSearchRoute();
            "
            :inputAttrs="{
              variant: 'outlined',
              prependInnerIcon: filter.subject.icon,
              label: filter.subject.title,
            }"
            class="mt-6"
          >
          </cd-search>

          <!-- CREATOR/CONTRIBUTOR NAME -->
          <cd-search
            v-model="filter.creatorName.value"
            :target-field="EnumHistoryTypes.CREATOR"
            :append-search-button="false"
            :is-eager="true"
            @blur="pushSearchRoute"
            @keyup.enter="pushSearchRoute"
            @hint-selected="pushSearchRoute()"
            @clear="
              filter.creatorName.value = '';
              pushSearchRoute();
            "
            :inputAttrs="{
              variant: 'outlined',
              prependInnerIcon: 'mdi-account-edit',
              label: filter.creatorName.title,
            }"
            class="mt-6"
          >
          </cd-search>

          <!-- FUNDER -->
          <cd-search
            v-model="filter.fundingFunderName.value"
            :target-field="EnumHistoryTypes.FUNDER"
            :append-search-button="false"
            :is-eager="true"
            @blur="pushSearchRoute"
            @keyup.enter="pushSearchRoute"
            @hint-selected="pushSearchRoute()"
            @clear="
              filter.fundingFunderName.value = '';
              pushSearchRoute();
            "
            :inputAttrs="{
              variant: 'outlined',
              prependInnerIcon: filter.fundingFunderName.icon,
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
                  v-model="filter.dataCoverage.isEnabled"
                  @update:model-value="pushSearchRoute()"
                  density="compact"
                  hide-details
                  color="primary"
                ></v-switch>
                <div class="ml-4 text-body-1 cursor-pointer">
                  Temporal coverage
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <cd-range-input
                  v-model="filter.dataCoverage.value"
                  v-model:isActive="filter.dataCoverage.isEnabled"
                  @update:is-active="pushSearchRoute"
                  @end="onFilterControlChange(filter.dataCoverage)"
                  :min="filter.dataCoverage.min"
                  :max="filter.dataCoverage.max"
                  label="Temporal coverage"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- CONTENT TYPE -->
            <v-expansion-panel tile key="1">
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-3">
                <v-switch
                  @click.stop=""
                  v-model="filter.contentType.isEnabled"
                  @update:model-value="pushSearchRoute()"
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
                  v-for="(option, index) of filter.contentType.options"
                  class="d-flex justify-space-between align-center"
                >
                  <v-checkbox
                    v-model="filter.contentType.value"
                    @update:model-value="
                      onFilterControlChange(filter.contentType)
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
                  v-model="filter.availability.isEnabled"
                  @update:model-value="pushSearchRoute()"
                  density="compact"
                  hide-details
                  color="primary"
                ></v-switch>
                <div class="ml-4 text-body-1 cursor-pointer">Availiability</div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <div
                  v-for="(option, index) of filter.availability.options"
                  class="d-flex justify-space-between align-center"
                >
                  <v-checkbox
                    v-model="filter.availability.value"
                    @update:model-value="
                      onFilterControlChange(filter.availability)
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
                  v-model="filter.creationDate.isEnabled"
                  @update:model-value="pushSearchRoute()"
                  density="compact"
                  hide-details
                  color="primary"
                ></v-switch>

                <div class="ml-4 text-body-1 cursor-pointer">Date created</div>
              </v-expansion-panel-title>

              <v-expansion-panel-text key="4">
                <cd-range-input
                  v-model="filter.creationDate.value"
                  v-model:isActive="filter.creationDate.isEnabled"
                  @update:is-active="pushSearchRoute"
                  @end="onFilterControlChange(filter.creationDate)"
                  :min="filter.creationDate.min"
                  :max="filter.creationDate.max"
                  label="Date created"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- PUBLICATION YEAR -->
            <v-expansion-panel tile>
              <v-expansion-panel-title class="py-0 px-4" color="grey-lighten-4">
                <v-switch
                  @click.stop=""
                  v-model="filter.publicationYear.isEnabled"
                  @update:model-value="pushSearchRoute()"
                  density="compact"
                  hide-details
                  color="primary"
                ></v-switch>

                <div class="ml-4 text-body-1 cursor-pointer">
                  Publication year
                </div>
              </v-expansion-panel-title>

              <v-expansion-panel-text>
                <cd-range-input
                  v-model="filter.publicationYear.value"
                  v-model:isActive="filter.publicationYear.isEnabled"
                  @update:is-active="pushSearchRoute"
                  @end="onFilterControlChange(filter.publicationYear)"
                  :min="filter.publicationYear.min"
                  :max="filter.publicationYear.max"
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

      <div class="results-content-wrapper">
        <v-container class="results-content">
          <div class="d-flex align-center gap-1 mb-6">
            <cd-search
              v-model="searchQuery"
              :target-field="EnumHistoryTypes.TERM"
              :auto-focus="true"
              @update:model-value="pushSearchRoute"
              @clear="
                searchQuery = '';
                pushSearchRoute();
              "
              :inputAttrs="{
                variant: 'outlined',
                prependInnerIcon: 'mdi-magnify',
                placeholder: $t(`home.search.inputPlaceholder`),
              }"
            />
          </div>

          <div v-if="isSomeFilterActive" class="d-flex gap-1 mb-4 flex-wrap">
            <v-chip
              v-for="f of activeFilters"
              color="primary"
              closable
              label
              @click:close="
                f.clear();
                pushSearchRoute();
              "
            >
              <v-icon v-if="f.icon" class="mr-2" :icon="f.icon"></v-icon>
              <p>
                <span>{{ f.title }}: </span>
                <b v-if="f.type === enumFilterTypes.RANGE">{{
                  `${f.value[0]} to ${f.value[1]}`
                }}</b>
                <b
                  v-else-if="
                    f.type === enumFilterTypes.SELECT_MULTIPLE &&
                    Array.isArray(f.value)
                  "
                  >{{
                    f.value
                      .map(
                        (opt: string) =>
                          f.options?.find((fi) => fi.value === opt)?.label,
                      )
                      .join(", ")
                  }}</b
                >
                <b v-else-if="Array.isArray(f.value)">{{
                  f.value.join(", ")
                }}</b>
                <b v-else>{{ f.value }}</b>
              </p>
            </v-chip>
          </div>

          <div class="results-container mb-12">
            <v-data-table-virtual
              :headers="headers.filter((header) => header.visible)"
              :items="results"
              class="elevation-2 text-body-1"
              hover
              show-expand
              density="compact"
              :loading="isSearching"
              v-model:sort-by="sortBy"
              @update:sort-by="onSortChange()"
              :cell-props="
                (item) => ({
                  class: { isSorted: item.column.key === sortBy[0]?.key },
                })
              "
            >
              <template #no-data>
                <div class="text-body-2 text-center py-4">
                  <v-empty-state
                    text="No results found."
                    icon="mdi-text-box-remove"
                  />
                </div>
              </template>
              <template #loading>
                <div class="text-subtitle-2 text-center">
                  Loading results...
                </div>
              </template>
              <template #item.icons="{ item }">
                <div class="d-flex align-center justify-start">
                  <v-img
                    class="mr-2"
                    v-if="contentTypeLogos[item.contentType]"
                    :src="contentTypeLogos[item.contentType]"
                    v-tooltip="contentTypeLabels[item.contentType]"
                    width="30"
                    max-width="30"
                  />
                  <v-img
                    v-if="item.sharingStatus === 'Public'"
                    class="img-access-icon flex-grow-0"
                    width="25"
                    :src="sharingStatusIcons.PUBLIC"
                    v-tooltip="'Public'"
                    alt="Public"
                  />
                  <v-img
                    v-else-if="item.sharingStatus === 'Private'"
                    class="img-access-icon flex-grow-0"
                    width="25"
                    :src="sharingStatusIcons.PRIVATE"
                    v-tooltip="'Private'"
                    alt="Private"
                  />
                  <v-img
                    v-else-if="item.sharingStatus === 'Discoverable'"
                    class="img-access-icon flex-grow-0"
                    width="25"
                    :src="sharingStatusIcons.DISCOVERABLE"
                    v-tooltip="'Discoverable'"
                    alt="Discoverable"
                  />
                  <v-img
                    v-else-if="item.sharingStatus === 'Published'"
                    class="img-access-icon flex-grow-0"
                    width="25"
                    :src="sharingStatusIcons.PUBLISHED"
                    v-tooltip="'Published'"
                    alt="Published"
                  />
                  <v-img
                    v-if="hasSpatialFeatures(item)"
                    class="img-access-icon flex-grow-0"
                    width="25"
                    :src="sharingStatusIcons.SPATIAL"
                    v-tooltip="'Contains Spatial Coverage'"
                    alt="Contains Spatial Coverage"
                  />
                </div>
              </template>
              <template #item.name="{ item }">
                <a
                  v-if="item.identifier"
                  class="text-decoration-none text-body-1"
                  :href="item.identifier"
                  target="_blank"
                  v-html="highlight(item, 'name')"
                ></a>
                <p v-else v-html="highlight(item, 'name')"></p>
              </template>
              <template #item.creatorName="{ item }">
                <div v-html="highlightCreators(item)"></div>
              </template>
              <template #item.dateCreated="{ item }">
                <span v-if="item.dateCreated">{{
                  formatDate(item.dateCreated)
                }}</span>
              </template>
              <template #item.lastModified="{ item }">
                <span v-if="item.lastModified">{{
                  formatDate(item.lastModified)
                }}</span>
              </template>
              <template #expanded-row="{ item }">
                <div class="d-table-row">
                  <td class="d-table-cell" colspan="6">
                    <v-card class="mx-4" flat>
                      <v-card-text>
                        <div class="d-flex gap-2">
                          <div class="flex-grow-1">
                            <p
                              class="mb-2"
                              v-html="
                                highlight(
                                  item,
                                  'creator',
                                  ' | ',
                                  'creator.name',
                                )
                              "
                            ></p>
                            <div class="mb-2">
                              <v-chip
                                v-for="keyword of item.keywords"
                                size="small"
                                style="margin: 0.25rem"
                                variant="outlined"
                                class="bg-grey-lighten-5"
                                border="thin"
                                >{{ keyword }}</v-chip
                              >
                            </div>
                            <p
                              :class="{ 'snip-3': !item._showMore }"
                              v-html="highlight(item, 'description')"
                            ></p>
                            <v-btn
                              size="x-small"
                              variant="text"
                              color="primary"
                              class="mb-2"
                              @click="item._showMore = !item._showMore"
                              >Show
                              {{ item._showMore ? "less" : "more" }}...</v-btn
                            >
                            <p class="mb-2" v-if="item.datePublished">
                              <b>Date published</b>: {{ item.datePublished }}
                            </p>
                            <p v-if="item.funding.length" class="mb-2">
                              <b>Funded by</b>: {{ item.funding.join(" | ") }}
                            </p>
                            <p class="mb-2">
                              <b>License</b>: {{ item.license }}
                            </p>
                          </div>

                          <div v-if="hasSpatialFeatures(item)">
                            <div class="mb-4">
                              <cd-spatial-coverage-map
                                :feature="item.spatialCoverage"
                              />
                            </div>
                          </div>
                        </div>
                      </v-card-text>
                    </v-card>
                    <v-divider></v-divider>
                  </td>
                </div>
              </template>
              <template
                #item.data-table-expand="{
                  internalItem,
                  isExpanded,
                  toggleExpand,
                }"
              >
                <v-btn
                  :append-icon="
                    isExpanded(internalItem)
                      ? 'mdi-chevron-up'
                      : 'mdi-chevron-down'
                  "
                  :text="isExpanded(internalItem) ? 'Collapse' : 'Show more'"
                  class="text-none"
                  color="medium-emphasis"
                  size="small"
                  variant="text"
                  border
                  slim
                  @click="toggleExpand(internalItem)"
                ></v-btn>
              </template>

              <!-- <div class="my-1" v-if="result.datePublished">
                  Publication Date: {{ formatDate(result.datePublished) }}
                </div> -->
            </v-data-table-virtual>
            <v-progress-linear
              v-if="isFetchingMore"
              color="primary"
              indeterminate
            ></v-progress-linear>
          </div>

          <div
            v-if="results.length"
            v-intersect="{
              handler: onIntersect,
              options: { threshold: [0, 0.5, 1.0] },
            }"
          ></div>
          <div v-if="isFetchingMore" class="text-subtitle-2 text-center">
            <p>Loading more results...</p>
          </div>
          <div
            v-if="results.length && !hasMore"
            class="text-subtitle-2 text-center"
          >
            End of results.
          </div>
        </v-container>
      </div>
    </div>
  </v-container>
</template>

<script lang="ts">
import { Component, Vue, Watch, toNative } from "vue-facing-decorator";
import {
  MIN_YEAR,
  MAX_YEAR,
  contentTypeLogos,
  sharingStatusIcons,
  contentTypeLabels,
  INITIAL_RANGE,
} from "@/constants";
import { sameRouteNavigationErrorHandler } from "@/constants";
import { formatDate } from "@/util";
import CdSpatialCoverageMap from "@/components/search-results/cd.spatial-coverage-map.vue";
import CdSearch from "@/components/search/cd.search.vue";
import SearchResults from "@/models/search-results.model";
import SearchHistory from "@/models/search-history.model";
import Search from "@/models/search.model";
import { Notifications } from "@cznethub/cznet-vue-core";
import {
  ISearchParams,
  IResult,
  EnumShortParams,
  EnumDictionary,
  EnumHistoryTypes,
} from "@/types";
import CdRangeInput from "./cd.range-input.vue";
import { useRoute, useRouter } from "vue-router";
import { EnumFilterTypes, Filter } from "./filter";

@Component({
  name: "cd-search-results",
  components: { CdSearch, CdSpatialCoverageMap, CdRangeInput },
})
class CdSearchResults extends Vue {
  isIntersecting = false;
  searchQuery = "";
  pageNumber = 1;
  pageSize = 20;
  hasMore = true;
  isSearching = false;
  isFetchingMore = false;
  sortBy: { key: string; order?: boolean | "asc" | "desc" }[] = [];
  // public view: 'list' | 'map' = 'list'
  filter: { [key: string]: Filter } = {
    availability: new Filter({
      name: "creativeWorkStatus",
      title: "Availability",
      icon: "mdi-lock-outline",
      urlLabel: EnumShortParams.AVAILABILITY,
      type: EnumFilterTypes.SELECT_MULTIPLE,
      options: [
        {
          value: "Discoverable",
          label: "Discoverable",
          icon: sharingStatusIcons.DISCOVERABLE,
        },
        {
          value: "Public",
          label: "Public",
          icon: sharingStatusIcons.PUBLIC,
        },
        {
          value: "Published",
          label: "Published",
          icon: sharingStatusIcons.PUBLISHED,
        },
      ],
    }),
    contentType: new Filter({
      name: "contentType",
      title: "Content type",
      icon: "mdi-card-multiple-outline",
      urlLabel: EnumShortParams.CONTENT_TYPE,
      type: EnumFilterTypes.SELECT_MULTIPLE,
      options: this._contentTypes.map((contentType: string) => {
        return {
          value: contentType,
          label: contentTypeLabels[contentType],
          logo: contentTypeLogos[contentType],
        };
      }),
    }),
    dataCoverage: new Filter({
      name: "dataCoverage",
      title: "Temporal coverage",
      icon: "mdi-calendar-range",
      urlLabel: EnumShortParams.DATA_COVERAGE,
      type: EnumFilterTypes.RANGE,
      min: MIN_YEAR,
      max: MAX_YEAR,
      getter: () => {
        return SearchResults.$state.dataCoverage;
      },
      setter: (range: [number, number]) => {
        SearchResults.commit((state) => {
          state.dataCoverage = range;
        });
      },
      clear: () => {
        SearchResults.commit((state) => {
          state.dataCoverage = INITIAL_RANGE;
        });
      },
    }),
    creationDate: new Filter({
      name: "dateCreated",
      title: "Date created",
      icon: "mdi-calendar-plus",
      urlLabel: EnumShortParams.CREATION_DATE,
      type: EnumFilterTypes.RANGE,
      min: MIN_YEAR,
      max: MAX_YEAR,
      getter: () => {
        return SearchResults.$state.creationDate;
      },
      setter: (range: [number, number]) => {
        SearchResults.commit((state) => {
          state.creationDate = range;
        });
      },
      clear: () => {
        SearchResults.commit((state) => {
          state.creationDate = INITIAL_RANGE;
        });
      },
    }),
    publicationYear: new Filter({
      name: "published",
      title: "Publication year",
      icon: "mdi-calendar-star-four-points",
      urlLabel: EnumShortParams.PUBLICATION_YEAR,
      type: EnumFilterTypes.RANGE,
      min: MIN_YEAR,
      max: MAX_YEAR,
      getter: () => {
        return SearchResults.$state.publicationYear;
      },
      setter: (range: [number, number]) => {
        SearchResults.commit((state) => {
          state.publicationYear = range;
        });
      },
      clear: () => {
        SearchResults.commit((state) => {
          state.publicationYear = INITIAL_RANGE;
        });
      },
    }),
    subject: new Filter({
      title: "Subject keywords",
      name: "keyword",
      historyType: EnumHistoryTypes.SUBJECT,
      urlLabel: EnumShortParams.SUBJECT,
      type: EnumFilterTypes.STRING,
      icon: "mdi-pen",
    }),
    creatorName: new Filter({
      name: "creatorName",
      title: "Author/contributor's name",
      historyType: EnumHistoryTypes.CREATOR,
      urlLabel: EnumShortParams.AUTHOR_NAME,
      type: EnumFilterTypes.STRING,
      icon: "mdi-account-outline",
    }),
    fundingFunderName: new Filter({
      name: "fundingFunderName",
      title: "Funder",
      historyType: EnumHistoryTypes.FUNDER,
      urlLabel: EnumShortParams.FUNDER,
      type: EnumFilterTypes.STRING,
      icon: "mdi-domain",
    }),
  };
  contentTypeLogos = contentTypeLogos;
  sharingStatusIcons = sharingStatusIcons;
  contentTypeLabels = contentTypeLabels;
  enumFilterTypes = EnumFilterTypes;

  headers = reactive([
    {
      title: "",
      key: "icons",
      visible: true,
      width: 60,
      minWidth: 60,
      sortable: false,
    },
    {
      title: "Title",
      key: "name",
      visible: true,
      minWidth: 200,
      sortRaw: () => 1,
    },
    {
      title: "First Author",
      key: "creatorName",
      visible: true,
      minWidth: 200,
      sortRaw: () => 1,
    },
    {
      title: "Date Created",
      key: "dateCreated",
      visible: true,
      minWidth: 200,
      sortRaw: () => 1,
    },
    {
      title: "Last Modified",
      key: "lastModified",
      visible: true,
      minWidth: 200,
      sortRaw: () => 1,
    },
  ]);

  formatDate = formatDate;
  route = useRoute();
  router = useRouter();
  EnumHistoryTypes = EnumHistoryTypes;

  public get registeredFilters() {
    return Object.values(this.filter);
  }

  public get activeFilters() {
    return this.registeredFilters.filter((f) => f.isActive());
  }

  public get panels() {
    return SearchResults.$state.panels;
  }

  public set panels(range: number[]) {
    SearchResults.commit((state) => {
      state.panels = range;
    });
  }

  public get results(): IResult[] {
    return Search.$state.results;
  }

  public get isSomeFilterActive() {
    return this.registeredFilters.some((f) => f.isActive());
  }

  @Watch("_contentTypes")
  onContentTypesChanged() {
    this.filter.contentType.options = this._contentTypes.map(
      (contentType: string) => {
        return {
          value: contentType,
          label: contentTypeLabels[contentType],
          logo: contentTypeLogos[contentType],
        };
      },
    );
  }

  private get _contentTypes() {
    return Search.$state.contentTypes;
  }

  public get isFetchingContentTypes() {
    return Search.$state.isFetchingContentTypes;
  }

  /** Search query parameters */
  get queryParams(): ISearchParams {
    let params: ISearchParams = {
      term: this.searchQuery,
      pageSize: this.pageSize,
      pageNumber: this.pageNumber,
    };

    if (this.sortBy[0]) {
      params.sortBy = this.sortBy[0].key;
      params.order = this.sortBy[0].order as "asc" | "desc";
    }

    this.registeredFilters.forEach((f) => {
      params = { ...params, ...f.getQueryParams() };
    });

    return params;
  }

  /** Route query parameters with short keys. These are parameters needed to replicate a search. */
  public get routeParams(): EnumDictionary<EnumShortParams, any> {
    let params: { [key: string]: string } = {
      [EnumShortParams.QUERY]: this.searchQuery,
    };

    if (this.sortBy[0]) {
      params.sortBy = this.sortBy[0].key;
      params.order = this.sortBy[0].order as string;
    }

    this.registeredFilters.forEach((f) => {
      params = { ...params, ...f.getRouteParams() };
    });
    return params as EnumDictionary<EnumShortParams, any>;
  }

  created() {
    this._loadRouteParams();
    this._onSearch();
  }

  public onIntersect(_isIntersecting: boolean, entries: any[], _observer: any) {
    this.isIntersecting = entries[0]?.intersectionRatio >= 0.5;
    if (
      this.isIntersecting &&
      this.results.length &&
      this.hasMore &&
      !this.isSearching &&
      !this.isFetchingMore
    ) {
      this.fetchMore();
    }
  }

  logHistory() {
    if (this.queryParams.term) {
      SearchHistory.log(this.queryParams.term, EnumHistoryTypes.TERM);
    }

    this.registeredFilters.forEach((f) => {
      if (f.historyType && f.value?.trim()) {
        SearchHistory.log(f.value?.trim(), f.historyType);
      }
    });
  }

  /** Pushes the desired search to the router, which will reload the route with the new query parameters */
  pushSearchRoute(value?: string) {
    if (value && this.route.name !== "search") {
      this.router
        .push({ name: "search", query: { q: value } })
        .catch(sameRouteNavigationErrorHandler);
    }

    try {
      this.logHistory();

      // This will reload the component because the router-view in the App component has `:key="route.fullPath"`
      this.router
        .push({
          name: "search",
          query: this.routeParams,
        })
        .catch(sameRouteNavigationErrorHandler);
    } catch (e) {
      console.log(e);
      Search.commit((state) => {
        state.results = [];
      });
      Notifications.toast({
        message: `Failed to perform search`,
        type: "error",
      });
    }
  }

  async _onSearch() {
    this.hasMore = true;
    this.isSearching = true;
    this.pageNumber = 1;

    this.hasMore = !!(await Search.search(this.queryParams));
    this.isSearching = false;
  }

  /** Get the next page of results. */
  public async fetchMore() {
    this.pageNumber++;
    this.isFetchingMore = true;
    try {
      this.hasMore = await Search.fetchMore(this.queryParams);
    } catch (e) {
      console.log(e);
    }
    this.isFetchingMore = false;
  }

  public onFilterControlChange(filter: Filter) {
    filter.isEnabled = true;

    this.pushSearchRoute();
  }

  public highlightCreators(result: IResult) {
    if (!result.creator) {
      return "";
    }
    const div = document.createElement("DIV");
    // div.innerHTML = result.creator.join(", ");
    div.innerHTML = result.creator[0] || "";

    let content = div.textContent || div.innerText || "";

    if (result.highlights) {
      let hits = result.highlights
        .filter((highlight) => highlight.path === "creator.name")
        .map((hit) =>
          hit.texts.filter((t) => t.type === "hit").map((t) => t.value),
        )
        .flat();

      hits = [...new Set(hits)];
      hits.map((hit) => {
        content = content.replaceAll(hit, `<mark>${hit}</mark>`);
      });
    }
    return content;
  }

  /** Applies highlights to a string or string[] field and returns the new content as HTML */
  public highlight(
    result: IResult,
    path: keyof IResult,
    separator?: string,
    arrayItemPath?: string,
  ) {
    const div = document.createElement("DIV");
    const field = result[path];

    div.innerHTML = Array.isArray(field)
      ? field.join(separator || ", ")
      : field;
    let content = div.textContent || div.innerText || "";

    if (result.highlights) {
      let hits = result.highlights
        .filter(
          (highlight) =>
            highlight.path === path || highlight.path === arrayItemPath,
        )
        .map((hit) =>
          hit.texts.filter((t) => t.type === "hit").map((t) => t.value),
        )
        .flat();

      hits = [...new Set(hits)];
      hits.map((hit) => {
        content = content.replaceAll(hit, `<mark>${hit}</mark>`);
      });
    }

    return content;
  }

  public clearFilters() {
    const wasSomeActive = this.isSomeFilterActive;
    this.registeredFilters.forEach((f) => f.clear());

    if (wasSomeActive) {
      this.pushSearchRoute();
    }
  }

  public onSortChange() {
    this.pushSearchRoute();
  }

  /** Load route query parameters into component values. */
  private _loadRouteParams() {
    this.searchQuery = this.$route.query[EnumShortParams.QUERY] as string;
    if (this.$route.query.sortBy) {
      this.sortBy = [
        {
          key: this.$route.query.sortBy as string,
          order: this.$route.query.order === "desc" ? "desc" : "asc",
        },
      ];
    }
    this.registeredFilters.forEach((f) => f.loadFromRoute(this.$route.query));
  }

  public hasSpatialFeatures(result: IResult): boolean {
    return !!result.spatialCoverage;
  }
}
export default toNative(CdSearchResults);
</script>

<style lang="scss" scoped>
.v-expansion-panel--active,
.v-expansion-panel--active:not(:first-child),
.v-expansion-panel--active + .v-expansion-panel {
  margin-top: 1px;
}

:deep(.v-table .v-data-table__tr:nth-child(even) td) {
  background: #f7f7f7;
  &.isSorted {
    background: #eee !important;
  }
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

.cd-search-results.is-small {
  .sidebar {
    width: 100%;
  }
}

.results-content-wrapper {
  flex: 1 1 auto;
}

// .results-content {
//   min-width: 0; // https://stackoverflow.com/a/66689926/3288102
//   max-width: 70rem;
//   margin: unset;
// }

.results-container {
  * {
    word-break: break-word;
  }

  a {
    text-decoration: none;
    &:hover {
      text-decoration: underline !important;
    }
  }
}

.grayed-out {
  opacity: 0.55;
}

:deep(.v-select--chips .v-select__selections .v-chip--select:first-child) {
  margin-top: 1rem;
}
</style>
