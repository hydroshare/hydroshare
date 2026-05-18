<template>
  <v-container>
    <v-skeleton-loader
      v-if="isFetchingMetadata"
      type="card"
    ></v-skeleton-loader>

    <template v-if="!isFetchingMetadata && wasLoaded">
      <div id="overview" class="resource-header mb-6">
        <h1 class="text-h5 font-weight-bold mb-3">
          {{ data.name }}
        </h1>

        <div class="d-flex align-center gap-3 mb-1">
          <div class="d-flex align-center" style="gap: 0.4rem">
            <img
              v-if="resourceTypeIcon"
              :src="resourceTypeIcon"
              :alt="resourceTypeLabel"
              :title="resourceTypeLabel"
              class="resource-type-icon flex-shrink-0"
            />

            <v-chip
              v-if="data.creativeWorkStatus"
              size="small"
              :color="getStatusColor(data.creativeWorkStatus.name)"
              :title="data.creativeWorkStatus.description"
              variant="flat"
              label
            >
              {{ data.creativeWorkStatus.name }}
            </v-chip>
          </div>

          <span
            v-if="data.dateModified"
            class="text-body-2 text-medium-emphasis"
          >
            Updated {{ parseDate(data.dateModified) }}
            <span class="font-weight-light"
              >(<timeago :datetime="data.dateModified" />)</span
            >
          </span>

          <span
            v-if="data.viewCount != null"
            class="text-body-2 text-medium-emphasis"
          >
            <v-icon size="14" class="mr-1">mdi-eye-outline</v-icon
            >{{ data.viewCount.toLocaleString() }}
            {{ data.viewCount === 1 ? "view" : "views" }}
          </span>

          <v-spacer></v-spacer>

          <div
            v-if="!isLoadingFiles && !isFetchingMetadata"
            class="d-flex align-center gap-1 flex-shrink-0"
          >
            <v-menu width="500" :close-on-content-click="false">
              <template v-slot:activator="{ props }">
                <v-btn
                  size="small"
                  v-bind="props"
                  prepend-icon="mdi-cog"
                  variant="text"
                  >Settings</v-btn
                >
              </template>
              <v-card>
                <v-card-title
                  class="bg-grey-lighten-3 text-body-1 text-medium-emphasis"
                  >Settings</v-card-title
                >
                <v-divider></v-divider>
                <v-card-text flat>
                  <s3-form
                    :prefix="s3Info.prefix"
                    :bucket="s3Info.bucket"
                    :s3-host="s3Host"
                    :hydroshare-host="hydroshareHost"
                    :accessKey="credentials.accessKey"
                    :secret-key="credentials.secretKey"
                    @apply-changes="onS3FormUpdate"
                    @restore-defaults="onRestoreDefaults"
                  ></s3-form>
                </v-card-text>
              </v-card>
            </v-menu>

            <v-btn
              size="small"
              color="primary"
              prepend-icon="mdi-pen"
              variant="outlined"
              @click="$router.push({ name: 'edit-dataset' })"
              >Edit</v-btn
            >
          </div>
        </div>
      </div>

      <v-divider></v-divider>

      <div class="d-flex gap-4 mt-6">
        <v-container
          class="page-content pa-0"
          :class="{ 'is-sm': $vuetify.display.mdAndDown }"
          fluid
        >
          <v-card id="details" variant="outlined" class="mb-6 details-card">
            <v-card-text class="pa-5">
              <v-row :no-gutters="$vuetify.display.smAndDown">
                <v-col cols="12" sm="6" class="dataset-info">
                  <div v-bind="infoLabelAttr">Authors:</div>

                  <div class="infoValueAttr">
                    <v-menu
                      v-for="(creator, index) of data.creator"
                      offset-y
                      :close-on-content-click="false"
                      class="d-inline"
                      :key="index"
                    >
                      <template v-slot:activator="{ props }">
                        <span
                          class="mr-2 cursor-pointer"
                          v-bind="{ ...props, ...infoValueAttr }"
                        >
                          <div class="d-inline-block">
                            {{ creator.name }}
                            <v-icon small>mdi-menu-down</v-icon>
                          </div>
                        </span>
                      </template>
                      <v-card v-if="creator['type'] == 'Person'" width="auto">
                        <v-card-title class="text-body-1">
                          <v-icon class="mr-2">mdi-account-outline</v-icon>
                          {{ creator.name }}
                        </v-card-title>
                        <v-divider></v-divider>

                        <v-card-text
                          v-if="creator.email || creator.identifier"
                          class="d-flex flex-column gap-1"
                        >
                          <div v-if="creator.email">
                            <div class="d-flex align-center mb-1">
                              <v-icon
                                class="mr-1"
                                small
                                color="secondary"
                                title="Email address"
                                icon="mdi-email-outline"
                              />
                              <div class="d-flex align-center gap-1">
                                <span class="text-medium-emphasis">Email:</span>
                                {{ creator.email }}
                              </div>
                            </div>
                          </div>
                          <div
                            v-if="creator.identifier"
                            class="d-flex align-center"
                          >
                            <i
                              class="fab fa-orcid mr-2 text-secondary text-h6"
                              aria-hidden="true"
                              title="ORCID"
                            ></i>
                            {{ creator.identifier }}
                          </div>

                          <div v-if="creator.affiliation">
                            <div class="d-flex align-center mb-1">
                              <v-icon
                                small
                                color="secondary"
                                class="mr-1"
                                title="Affiliation"
                              >
                                mdi-domain
                              </v-icon>
                              <div class="d-flex align-center gap-1">
                                <span class="text-medium-emphasis"
                                  >Affiliation:</span
                                >
                                <div v-if="creator.affiliation.name">
                                  <span
                                    v-if="creator.affiliation.url"
                                    class="d-inline-flex align-baseline"
                                  >
                                    <a :href="creator.affiliation.url">{{
                                      creator.affiliation.name
                                    }}</a>
                                  </span>
                                  <span v-else>{{
                                    creator.affiliation.name
                                  }}</span>
                                </div>
                              </div>
                            </div>

                            <div v-if="creator.affiliation.address">
                              {{ creator.affiliation.address }}
                            </div>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-menu>
                  </div>

                  <template v-if="owners.length">
                    <div v-bind="infoLabelAttr">Owners:</div>
                    <div class="d-flex flex-wrap align-baseline" style="row-gap: 0.15rem; column-gap: 0.75rem">
                      <v-menu
                        v-for="(owner, ownerIdx) of owners"
                        :key="owner.id || ownerIdx"
                        offset-y
                        :close-on-content-click="false"
                      >
                        <template v-slot:activator="{ props }">
                          <span v-bind="props" class="owner-link">
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
                            <div
                              v-if="ownerOrganizations(owner).length"
                              class="profile-row"
                            >
                              <v-icon size="16" class="profile-row-icon">mdi-domain</v-icon>
                              <div class="d-flex flex-column" style="gap: 0.1rem">
                                <span
                                  v-for="(org, orgIdx) of ownerOrganizations(owner)"
                                  :key="orgIdx"
                                >
                                  {{ org }}
                                </span>
                              </div>
                            </div>
                            <div v-if="ownerLocation(owner)" class="profile-row">
                              <v-icon size="16" class="profile-row-icon">mdi-map-marker-outline</v-icon>
                              {{ ownerLocation(owner) }}
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
                            <v-btn
                              v-if="ownerOrcid(owner)"
                              :href="ownerOrcid(owner)"
                              target="_blank"
                              rel="noopener"
                              variant="text"
                              size="small"
                              class="orcid-btn"
                            >
                              <i class="fab fa-orcid mr-1"></i>
                              ORCID
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
                              <span v-if="owner.viewable_contributions != null && owner.viewable_contributions > 0">
                                Profile · {{ owner.viewable_contributions.toLocaleString() }}
                              </span>
                              <span v-else>Profile</span>
                            </v-btn>
                          </v-card-actions>
                        </v-card>
                      </v-menu>
                    </div>
                  </template>

                  <template v-if="data.provider">
                    <div v-bind="infoLabelAttr">Provider:</div>
                    <div v-bind="infoValueAttr">
                      <span
                        v-if="data.provider.url"
                        class="d-flex align-baseline"
                      >
                        <a :href="data.provider.url">{{
                          data.provider.name
                        }}</a>
                      </span>
                      <template v-else>{{ data.provider.name }}</template>
                    </div>
                  </template>

                  <template v-if="data.publisher">
                    <div v-bind="infoLabelAttr">Publisher:</div>
                    <div v-bind="infoValueAttr">
                      <span
                        v-if="data.publisher.url"
                        class="d-flex align-baseline"
                      >
                        <a :href="data.publisher.url">{{
                          data.publisher.name
                        }}</a>
                      </span>
                      <template v-else>{{ data.publisher.name }}</template>
                    </div>
                  </template>

                  <template v-if="contentSize">
                    <div v-bind="infoLabelAttr">Resource Size:</div>
                    <div v-bind="infoValueAttr">~{{ contentSize }}</div>
                  </template>

                  <template v-if="data.inLanguage">
                    <div v-bind="infoLabelAttr">Language:</div>
                    <div v-bind="infoValueAttr">{{ data.inLanguage }}</div>
                  </template>

                  <template v-if="data.version">
                    <div v-bind="infoLabelAttr">Version:</div>
                    <div v-bind="infoValueAttr">{{ data.version }}</div>
                  </template>
                </v-col>

                <v-col cols="12" sm="6" class="dataset-info">
                  <div v-bind="infoLabelAttr">Created:</div>
                  <div v-bind="infoValueAttr">
                    {{ parseDate(data.dateCreated) }}
                  </div>

                  <template v-if="data.datePublished">
                    <div v-bind="infoLabelAttr">Published:</div>
                    <div v-bind="infoValueAttr">
                      {{ parseDate(data.datePublished) }}
                    </div>
                  </template>

                  <div v-bind="infoLabelAttr">Downloads:</div>
                  <div v-bind="infoValueAttr">
                    {{ data.downloadCount != null ? data.downloadCount.toLocaleString() : "—" }}
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <div v-if="data.description" class="mb-6 field" id="description">
            <div v-bind="headingAttr">Abstract</div>
            <!-- <p class="text-body-1 text-medium-emphasis">{{ data.description }}</p> -->
            <v-banner
              :text="data.description"
              :lines="showDescription ? undefined : 'three'"
              stacked
              class="pa-0 pb-4"
              :border="0"
            >
              <template v-slot:actions>
                <v-btn
                  @click="showDescription = !showDescription"
                  size="x-small"
                  >{{ showDescription ? "Show less" : "Show more" }}</v-btn
                >
              </template>

              <template #text
                ><div class="text-body-1 text-medium-emphasis">
                  {{ data.description }}
                </div></template
              >
            </v-banner>
          </div>

          <div class="mb-6 field" id="content">
            <div v-bind="headingAttr">Content</div>

            <cz-file-explorer
              @showMetadata="onShowMetadata($event)"
              id="fileExplorer"
              class="ma-4"
              v-if="!isLoadingFiles"
              ref="fileExplorer"
              :root-directory="rootDirectory"
              :has-folders="fileExplorerConfig.hasFolders"
              :is-read-only="true"
              :has-file-metadata="() => true"
              :canDownloadItem="() => true"
              @download="
                onFileDownload($event, resourceId, s3Client, s3Info.bucket)
              "
            >
              <template #prepend>
                <span />
              </template>
            </cz-file-explorer>
            <!-- <v-skeleton-loader
            class="mb-12"
            v-else
            type="card"
          ></v-skeleton-loader> -->

            <v-card
              v-if="readmeMd || isLoadingMD"
              id="readme"
              class="readme-container mx-4"
              variant="outlined"
              border="grey thin"
            >
              <v-card-title class="text-overline d-flex gap-2"
                ><div>README</div>
                <div class="text-caption text-medium-emphasis">
                  {{ readMeFileName }}
                </div></v-card-title
              >

              <v-divider></v-divider>
              <v-card-text>
                <div class="text-center py-4" v-if="isLoadingMD">
                  <v-progress-circular
                    indeterminate
                    class="text-center"
                    color="primary"
                  />
                </div>
                <div
                  v-if="!hasTxtReadme"
                  v-html="readmeMd"
                  class="markdown-body px-4"
                ></div>
                <pre v-else class="px-4" style="white-space: pre-wrap">{{
                  readmeMd
                }}</pre>
              </v-card-text>
            </v-card>
          </div>

          <div
            v-if="data.funding && data.funding.length"
            class="mb-6 field"
            id="funding"
          >
            <div v-bind="headingAttr">Funding</div>
            <p class="text-body-2 text-medium-emphasis mb-4">
              This resource was created using funding from the following
              sources:
            </p>
            <v-expansion-panels multiple elevation="1">
              <v-expansion-panel
                v-for="(funding, index) of data.funding"
                :key="index"
                :readonly="!(funding.description || funding.funder)"
              >
                <v-expansion-panel-title class="bg-grey-lighten-5">
                  <div>
                    <div class="text-body-2">{{ funding.name }}</div>

                    <div
                      v-if="funding.identifier"
                      class="text-body-2 font-weight-light"
                    >
                      Award number: {{ funding.identifier }}
                    </div>
                  </div>

                  <template
                    v-slot:actions
                    v-if="!(funding.description || !!funding.funder)"
                    ><span></span
                  ></template>
                </v-expansion-panel-title>
                <v-divider></v-divider>

                <v-expansion-panel-text
                  v-if="funding.description || !!funding.funder"
                >
                  <div
                    class="pt-2 text-body-2 font-weight-light"
                    v-if="funding.description"
                  >
                    {{ funding.description }}
                  </div>
                  <template v-if="!!funding.funder">
                    <div class="d-flex align-center text-body-1 mt-4 mb-2">
                      <v-icon class="mr-2"> mdi-domain </v-icon>
                      <div class="text-body-2 text-medium-emphasis">
                        Funding Organization:
                      </div>
                    </div>
                    <div class="text-body-2">
                      <div>
                        {{ funding.funder.name }}
                      </div>
                      <div>{{ funding.funder.address }}</div>
                      <a :href="funding.funder.url"
                        >{{ funding.funder.url }}
                      </a>
                    </div>
                  </template>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>

          <div
            v-if="
              data.hasPart?.length ||
              data.isPartOf?.length ||
              data.subjectOf?.length
            "
            class="mb-6 field"
            id="related"
          >
            <div v-bind="headingAttr">Related Resources</div>
            <v-card variant="outlined" border="grey thin">
              <v-table>
                <template v-slot:default>
                  <tbody>
                    <tr
                      v-for="(part, index) in data.hasPart"
                      :key="`hp-${index}`"
                    >
                      <td class="">Has part</td>
                      <td>
                        <a :href="part.url">{{ part.url }}</a>
                      </td>
                    </tr>

                    <tr
                      v-for="(part, index) in data.isPartOf"
                      :key="`hp-${index}`"
                    >
                      <td class="">Is part of</td>
                      <td>
                        <a :href="part.url">{{ part.url }}</a>
                      </td>
                    </tr>

                    <tr
                      v-for="(part, index) in data.subjectOf"
                      :key="`hp-${index}`"
                    >
                      <td class="">Subject of</td>
                      <td>
                        <a :href="part.url">{{ part.url }}</a>
                      </td>
                    </tr>
                  </tbody>
                </template>
              </v-table>
            </v-card>
          </div>

          <div
            v-if="hasSpatialFeatures && $vuetify.display.mdAndDown"
            class="mb-6 field text-body-1"
            id="coverage"
          >
            <div v-bind="headingAttr">Spatial Coverage</div>
            <v-row>
              <v-col cols="12" sm="8">
                <v-card variant="outlined" border="grey thin">
                  <cd-spatial-coverage-map :feature="data.spatialCoverage.geo" />
                  <v-divider></v-divider>
                  <v-card-text
                    v-if="data.spatialCoverage.geo['type'] == 'GeoShape'"
                  >
                    <v-row class="align-start">
                      <v-col cols="12" sm="6" class="dataset-info">
                        <div v-bind="infoLabelAttr">North Latitude:</div>
                        <div v-bind="infoValueAttr">
                          {{ boxCoordinates.north }}°
                        </div>

                        <div v-bind="infoLabelAttr">East Longitude:</div>
                        <div v-bind="infoValueAttr">
                          {{ boxCoordinates.east }}°
                        </div>
                      </v-col>
                      <v-col cols="12" sm="6" class="dataset-info">
                        <div v-bind="infoLabelAttr">South Latitude:</div>
                        <div v-bind="infoValueAttr">
                          {{ boxCoordinates.south }}°
                        </div>

                        <div v-bind="infoLabelAttr">West Longitude:</div>
                        <div v-bind="infoValueAttr">
                          {{ boxCoordinates.west }}°
                        </div>
                      </v-col>
                    </v-row>
                  </v-card-text>

                  <v-card-text
                    v-if="data.spatialCoverage.geo['type'] == 'GeoCoordinates'"
                  >
                    <v-row class="align-start">
                      <v-col cols="12" sm="6" class="dataset-info">
                        <div v-bind="infoLabelAttr">Latitude:</div>
                        <div v-bind="infoValueAttr">
                          {{ data.spatialCoverage.geo.latitude }}°
                        </div>
                      </v-col>

                      <v-col cols="12" sm="6" class="dataset-info">
                        <div v-bind="infoLabelAttr">Longitude:</div>
                        <div v-bind="infoValueAttr">
                          {{ data.spatialCoverage.geo.longitude }}°
                        </div>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="4" class="dataset-info one-col">
                <div v-bind="infoLabelAttr">
                  Coordinate System/Geographic Projection:
                </div>
                <div v-bind="infoValueAttr">WGS 84 EPSG:4326</div>

                <div v-bind="infoLabelAttr">Coordinate Units:</div>
                <div v-bind="infoValueAttr">Decimal degrees</div>

                <div v-bind="infoLabelAttr">Place/Area Name:</div>
                <div v-bind="infoValueAttr">
                  {{ data.spatialCoverage.name }}
                </div>
              </v-col>
            </v-row>
          </div>

          <div
            v-if="data.temporalCoverage && $vuetify.display.mdAndDown"
            class="mb-6 field text-body-1"
          >
            <div v-bind="headingAttr">Temporal Coverage</div>

            <v-timeline align-top density="compact" line-color="info">
              <v-timeline-item dot-color="primary">
                <div>
                  <div class="font-weight-normal">
                    <strong>Start Date</strong>
                  </div>
                  <div>{{ parseDate(data.temporalCoverage.startDate) }}</div>
                </div>
              </v-timeline-item>

              <v-timeline-item dot-color="orange">
                <div>
                  <div class="font-weight-normal">
                    <strong>End Date</strong>
                  </div>
                  <div>{{ parseDate(data.temporalCoverage.endDate) }}</div>
                </div>
              </v-timeline-item>
            </v-timeline>
          </div>
        </v-container>

        <div v-if="!$vuetify.display.mdAndDown" class="sidebar break-word">
          <div>
            <v-card v-if="data.keywords?.length" id="subject" variant="flat" class="mb-6">
              <v-card-title class="pa-0 pb-2 text-subtitle-2 font-weight-bold text-uppercase" style="letter-spacing: 0.05em; color: #4BB5C1;">
                Subject Keywords
              </v-card-title>
              <div>
                <v-chip
                  v-for="keyword of data.keywords"
                  :key="keyword"
                  size="small"
                  style="margin: 0.15rem"
                  variant="outlined"
                  class="bg-grey-lighten-5"
                  border="thin"
                >{{ keyword }}</v-chip>
              </div>
            </v-card>

            <v-card v-if="data.license" variant="flat" class="mb-6">
              <v-card-title class="pa-0 pb-2 text-subtitle-2 font-weight-bold text-uppercase" style="letter-spacing: 0.05em; color: #4BB5C1;">
                License
              </v-card-title>
              <div class="text-body-2 text-medium-emphasis">
                <a v-if="data.license.url" :href="data.license.url" target="_blank" rel="noopener">{{ data.license.name }}</a>
                <template v-else>{{ data.license.name }}</template>
              </div>
              <img
                v-if="licenseBadgeUrl"
                :src="licenseBadgeUrl"
                :alt="data.license.name"
                class="cc-badge mt-2"
              />
            </v-card>

            <div v-if="hasSpatialFeatures" class="mb-6">
              <div class="text-subtitle-2 font-weight-bold text-uppercase mb-2" style="letter-spacing: 0.05em; color: #4BB5C1;">
                Spatial Coverage
              </div>
              <v-card variant="outlined" border="grey thin">
                <v-card-text flat class="pa-0">
                  <cd-spatial-coverage-map :feature="data.spatialCoverage.geo" />
                </v-card-text>
                <v-divider></v-divider>
                <v-expansion-panels accordion flat>
                  <v-expansion-panel>
                    <v-expansion-panel-title color="text-overline">
                      Extent
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-card-text v-if="data.spatialCoverage.geo['type'] == 'GeoShape'">
                        <v-row class="align-start">
                          <v-col cols="12" class="dataset-info pa-0">
                            <div v-bind="infoLabelAttr">North Latitude:</div>
                            <div v-bind="infoValueAttr" class="text-right">{{ boxCoordinates.north }}°</div>
                            <div v-bind="infoLabelAttr">East Longitude:</div>
                            <div v-bind="infoValueAttr" class="text-right">{{ boxCoordinates.east }}°</div>
                            <div v-bind="infoLabelAttr">South Latitude:</div>
                            <div v-bind="infoValueAttr" class="text-right">{{ boxCoordinates.south }}°</div>
                            <div v-bind="infoLabelAttr">West Longitude:</div>
                            <div v-bind="infoValueAttr" class="text-right">{{ boxCoordinates.west }}°</div>
                          </v-col>
                        </v-row>
                      </v-card-text>
                      <v-card-text v-if="data.spatialCoverage.geo['type'] == 'GeoCoordinates'">
                        <v-row class="align-start">
                          <v-col cols="12" class="dataset-info">
                            <div v-bind="infoLabelAttr">Latitude:</div>
                            <div v-bind="infoValueAttr">{{ data.spatialCoverage.geo.latitude }}°</div>
                          </v-col>
                          <v-col cols="12" class="dataset-info">
                            <div v-bind="infoLabelAttr">Longitude:</div>
                            <div v-bind="infoValueAttr">{{ data.spatialCoverage.geo.longitude }}°</div>
                          </v-col>
                        </v-row>
                      </v-card-text>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  <v-expansion-panel>
                    <v-expansion-panel-title color="text-overline">
                      Coordinate System
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-card-text class="dataset-info one-col pa-0">
                        <div v-bind="infoLabelAttr">Coordinate System/Geographic Projection:</div>
                        <div v-bind="infoValueAttr">WGS 84 EPSG:4326</div>
                        <div v-bind="infoLabelAttr">Coordinate Units:</div>
                        <div v-bind="infoValueAttr">Decimal degrees</div>
                        <div v-bind="infoLabelAttr">Place/Area Name:</div>
                        <div v-bind="infoValueAttr">{{ data.spatialCoverage.name }}</div>
                      </v-card-text>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card>
            </div>

            <div v-if="data.temporalCoverage" class="mb-6">
              <div class="text-subtitle-2 font-weight-bold text-uppercase mb-2" style="letter-spacing: 0.05em; color: #4BB5C1;">
                Temporal Coverage
              </div>
              <v-card variant="outlined" border="grey thin">
                <v-card-text>
                  <v-timeline align-top density="compact" line-color="info">
                    <v-timeline-item dot-color="primary" icon="mdi-calendar" fill-dot>
                      <div>
                        <strong>Start Date</strong>
                        <div>{{ parseDate(data.temporalCoverage.startDate) }}</div>
                      </div>
                    </v-timeline-item>
                    <v-timeline-item dot-color="orange-darken-2" icon="mdi-calendar" fill-dot>
                      <div>
                        <strong>End Date</strong>
                        <div>{{ parseDate(data.temporalCoverage.endDate) }}</div>
                      </div>
                    </v-timeline-item>
                  </v-timeline>
                </v-card-text>
              </v-card>
            </div>

            <v-card
              v-if="citations.length"
              class="mb-6"
              variant="flat"
              id="citation"
            >
              <v-card-title class="pa-0 pb-2 text-subtitle-2 font-weight-bold text-uppercase" style="letter-spacing: 0.05em; color: #4BB5C1;">
                How to cite
              </v-card-title>
              <v-card-text
                v-for="(citation, index) of citations"
                :key="index"
                class="pa-0 text-body-2 text-medium-emphasis"
              >
                <div class="d-flex align-center justify-space-between gap-1">
                  <div class="citation-text">
                    {{ citation }}
                  </div>

                  <v-tooltip bottom>
                    <template v-slot:activator="{ props }">
                      <v-btn icon v-bind="props" @click="onCopy(citation)" size="small" variant="text">
                        <v-icon> mdi-content-copy </v-icon>
                      </v-btn>
                    </template>
                    <span>Copy</span>
                  </v-tooltip>
                </div>
              </v-card-text>
              <v-card-text
                v-if="!isPublished"
                class="pa-0 pt-2 text-caption text-medium-emphasis font-italic"
              >
                When permanently published, this resource will have a formal Digital
                Object Identifier (DOI) and will be accessible at the following URL:
                <a :href="potentialDoiUrl" target="_blank" rel="noopener">{{ potentialDoiUrl }}</a>.
                When you are ready to permanently publish, click the Publish button at
                the top of the page to request your DOI. Reminder: Once you have published
                your resource, modifications to Title, Authors, or Content files will
                require a new version of the resource.
              </v-card-text>
            </v-card>
          </div>
        </div>
      </div>
    </template>

    <div
      v-if="!wasLoaded && !isFetchingMetadata"
      class="d-flex flex-column align-center"
    >
      <v-empty-state
        icon="mdi-cloud-cancel"
        text="Try adjusting your settings."
        title="We couldn't load this resource."
      ></v-empty-state>
      <v-menu width="500" :close-on-content-click="false">
        <template v-slot:activator="{ props }">
          <v-btn
            size="small"
            v-bind="props"
            color="primary"
            prepend-icon="mdi-cog"
            variant="outlined"
            >Settings</v-btn
          >
        </template>
        <v-card>
          <v-card-title
            class="bg-grey-lighten-3 text-body-1 text-medium-emphasis"
            >Settings</v-card-title
          >
          <v-divider></v-divider>
          <v-card-text flat>
            <s3-form
              :prefix="s3Info.prefix"
              :bucket="s3Info.bucket"
              :s3-host="s3Host"
              :hydroshare-host="hydroshareHost"
              :accessKey="credentials.accessKey"
              :secret-key="credentials.secretKey"
              @apply-changes="onS3FormUpdate"
              @restore-defaults="onRestoreDefaults"
            ></s3-form>
          </v-card-text>
        </v-card>
      </v-menu>
    </div>
  </v-container>
</template>

<script lang="ts">
import "github-markdown-css/github-markdown-light.css";
import { Component, Vue, toNative, Ref } from "vue-facing-decorator";
import {
  CzForm,
  CzFileExplorer,
  Notifications,
} from "@cznethub/cznet-vue-core";
import type { IFolder } from "@cznethub/cznet-vue-core/dist/types";
import { GetObjectCommand, S3Client, _Object } from "@aws-sdk/client-s3";
import { stringify } from "@/utils";
import { fetchResource, onFileDownload } from "./shared";
import S3Form from "./s3-form.vue";
import User from "@/models/user.model";
import { sizeToBytes } from "@/util";
import prettyBytes from "pretty-bytes";
import { useGoTo } from "vuetify";
import { EnumCreativeWorkStatus } from "@/types";
import { contentTypeLabels, contentTypeLogos } from "@/constants";
import markdownit from "markdown-it";
import hljs from "highlight.js"; // https://highlightjs.org

import CdSpatialCoverageMap from "@/components/search-results/cd.spatial-coverage-map.vue";

const md = markdownit({
  linkify: true,
  typographer: true,
  breaks: true,
  html: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) {}
    }

    return ""; // use external default escaping
  },
});

@Component({
  components: { CzForm, CzFileExplorer, S3Form, CdSpatialCoverageMap },
  name: "App",
})
class LandingPage extends Vue {
  resourceId!: string;

  @Ref("form") form!: InstanceType<typeof CzForm>;
  @Ref("fileExplorer") fileExplorer!: InstanceType<typeof CzFileExplorer>;

  protected get isLoggedIn(): boolean {
    return User.$state.isLoggedIn;
  }

  protected get credentials() {
    return User.$state.credentials;
  }

  showDescription = false;
  readmeMd = "";
  readMeFileName = "";
  hasTxtReadme = false;
  isLoadingMD = false;

  schema!: any;
  uischema!: any;
  onFileDownload = onFileDownload;

  data: Record<string, any> = {};
  owners: any[] = [];
  private onParentMessage = (event: MessageEvent) => {
    // atlas.html in the parent posts `{ parentSearch, owners }` after the
    // iframe loads. Owners are injected from the Django view because they
    // aren't part of the S3 dataset_metadata.json payload.
    if (event.origin !== window.location.origin) return;
    const payload = event.data;
    if (payload && Array.isArray(payload.owners)) {
      this.owners = payload.owners;
    }
  };
  stringify = stringify;

  isLoadingFiles: boolean = true;
  currentPath: string = "";
  isFetchingMetadata = true;
  wasLoaded = true;

  s3Client!: S3Client;
  s3Host: string = "http://localhost:9000";
  hydroshareHost: string = "http://localhost:8000";

  s3Info = {
    bucket: "",
    prefix: "",
  };

  config = {
    restrict: true,
    trim: true,
    showUnfocusedDescription: false,
    hideRequiredAsterisk: false,
    collapseNewItems: false,
    breakHorizontal: false,
    initCollapsed: false,
    hideAvatar: false,
    hideArraySummaryValidation: false,
    vuetify: {
      commonAttrs: {
        density: "compact",
        variant: "outlined",
        "persistent-hint": true,
        "hide-details": false,
      },
    },
    isViewMode: true,
    isReadOnly: false,
    isDisabled: false,
  };

  rootDirectory: Partial<IFolder> = {
    name: "root",
    children: [],
  };
  fileExplorerConfig = {
    isReadOnly: true, // Unused for now
    hasFolders: true,
  };

  async startS3Client() {
    const accessKeyId =
      User.$state.credentials.accessKey ||
      import.meta.env.VITE_MINIO_ACCESS_KEY ||
      "";
    const secretAccessKey =
      User.$state.credentials.secretKey ||
      import.meta.env.VITE_MINIO_SECRET_KEY ||
      "";
    this.s3Client = new S3Client({
      region: "us-central-2",
      endpoint: this.s3Host,
      forcePathStyle: true,
      credentials: { accessKeyId, secretAccessKey },
    });
  }
  infoLabelAttr = {
    class: "text-subtitle-2 font-weight-medium",
  };
  selectedMetadata: any = false;
  showMetadata = false;

  infoValueAttr = {
    class: "text-body-2 mb-2 text-medium-emphasis",
  };
  headingAttr = {
    class:
      "section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3",
  };
  scrollOptions = {
    offset: -80,
    easing: "easeInOutCubic",
  };
  goTo = useGoTo();

  onShowMetadata(item: any) {
    this.selectedMetadata = item;
    this.showMetadata = true;
  }

  onCopy(text: string) {
    navigator.clipboard.writeText(text);
    Notifications.toast({ message: "Copied to clipboard", type: "info" });
  }

  async loadReadmeFile() {
    // S3 keys are case-sensitive, so probe the root listing for any
    // file whose name matches readme.md / readme.txt case-insensitively.
    const rootFiles = (this.rootDirectory.children || []).filter(
      (c: any) => !Object.prototype.hasOwnProperty.call(c, "children"),
    );
    const mdFile = rootFiles.find(
      (f: any) => typeof f.name === "string" && f.name.toLowerCase() === "readme.md",
    );
    const txtFile = rootFiles.find(
      (f: any) => typeof f.name === "string" && f.name.toLowerCase() === "readme.txt",
    );
    const target = mdFile || txtFile;
    if (!target) return;
    this.hasTxtReadme = !mdFile;
    this.readMeFileName = target.name;

    const key = `${this.resourceId}/data/contents/${target.name}`;
    let result;
    try {
      result = await this.s3Client.send(
        new GetObjectCommand({ Bucket: this.s3Info.bucket, Key: key }),
      );
    } catch (e) {
      return;
    }

    try {
      this.isLoadingMD = true;
      const rawMd = await result.Body?.transformToString();
      this.readmeMd = this.hasTxtReadme ? rawMd : md.render(rawMd);
    } catch (e) {
      console.log(e);
    } finally {
      this.isLoadingMD = false;
    }

    // Patch the TOC after the readme is successfully loaded. buildToc() in
    // loadResource() replaces User.$state.toc with a fresh array, so this
    // must happen after that runs — i.e., after at least one await above.
    const toc = User.$state.toc;
    if (toc && !toc.some((t) => t.to === "#readme")) {
      const filesIdx = toc.findIndex((t) => t.to === "#fileExplorer");
      const entry = { text: "README", to: "#readme", level: 4 };
      if (filesIdx >= 0) {
        toc.splice(filesIdx + 1, 0, entry);
      } else {
        toc.push(entry);
      }
    }
  }

  get hasSpatialFeatures(): boolean {
    // `spatialCoverage` is schema.org Place; the actual geometry lives on
    // `.geo` and carries the GeoShape / GeoCoordinates type.
    const geoType = this.data.spatialCoverage?.geo?.["type"];
    return geoType === "GeoShape" || geoType === "GeoCoordinates";
  }

  get isPublished(): boolean {
    return this.data?.creativeWorkStatus?.name === "Published";
  }

  get potentialDoiUrl(): string {
    return `https://doi.org/10.4211/hs.${this.resourceId}`;
  }

  get citations(): string[] {
    // hydroshare_schemaorg_adapter sets dataset.citation = [self.citation] —
    // so the live JSON has data.citation as an array of strings. The legacy
    // landing-page template referenced data.document[0].citation, which never
    // exists in this payload.
    const raw = this.data?.citation;
    if (Array.isArray(raw)) return raw.filter((c: any) => typeof c === "string" && c.trim());
    if (typeof raw === "string" && raw.trim()) return [raw];
    return [];
  }

  get licenseBadgeUrl(): string | undefined {
    // The license `name` is the rights statement; map the canonical CC variants
    // to the badge images served by Django from theme/static/img/cc-badges/.
    const statement: string = this.data?.license?.name || "";
    const badges: { [key: string]: string } = {
      "This resource is shared under the Creative Commons Attribution CC BY.": "CC-BY.png",
      "This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.": "CC-BY-SA.png",
      "This resource is shared under the Creative Commons Attribution-NoDerivs CC BY-ND.": "CC-BY-ND.png",
      "This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike CC BY-NC-SA.": "CC-BY-NC-SA.png",
      "This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.": "CC-BY-NC.png",
      "This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs CC BY-NC-ND.": "CC-BY-NC-ND.png",
    };
    const file = badges[statement];
    return file ? `/static/static/img/cc-badges/${file}` : undefined;
  }

  get resourceTypeKey(): string {
    // dataset_metadata.json's additionalType holds the HydroShare resource type
    // (e.g. "CompositeResource"). data["@type"] is the schema.org class ("Dataset").
    return this.data?.additionalType || this.data?.["@type"] || "";
  }

  get resourceTypeLabel(): string {
    const key = this.resourceTypeKey;
    return contentTypeLabels[key] || key;
  }

  get resourceTypeIcon(): string | undefined {
    return contentTypeLogos[this.resourceTypeKey];
  }

  get contentSize() {
    const sumTree = (nodes: any[]): number =>
      nodes.reduce((acc, n) => {
        if (Array.isArray(n?.children)) {
          return acc + sumTree(n.children);
        }
        return acc + (typeof n?.uploadedSize === "number" ? n.uploadedSize : 0);
      }, 0);

    const fromFiles = sumTree(this.rootDirectory.children || []);
    if (fromFiles > 0) return prettyBytes(fromFiles);
  }

  get boxCoordinates() {
    const extents = this.data.spatialCoverage.geo.box
      .trim()
      .split(" ")
      .map((n: string) => +n);
    return {
      north: extents[0],
      east: extents[1],
      south: extents[2],
      west: extents[3],
    };
  }

  async created() {
    // Owners are injected by AtlasLandingView via the parent window
    // (same-origin) — read them synchronously to avoid a race with the
    // iframe-load postMessage. Fall back to the postMessage path if the
    // global isn't there (e.g. component loaded directly outside the iframe).
    try {
      const parentWin = window.parent as any;
      if (parentWin && parentWin !== window && Array.isArray(parentWin.HS_RESOURCE_OWNERS)) {
        this.owners = parentWin.HS_RESOURCE_OWNERS;
      }
    } catch {
      // cross-origin access blocked — postMessage listener will handle it
    }
    window.addEventListener("message", this.onParentMessage);

    if (!this.resourceId && this.$route?.params?.resourceId) {
      this.resourceId = this.$route.params.resourceId as string;
    }

    if (!this.resourceId) {
      this.isFetchingMetadata = false;
      this.wasLoaded = false;
      return;
    }

    if (this.isLoggedIn) {
      console.log("user is already logged in, fetching S3 credentials");
      await User.getOrCreateS3Credentials();
    } else {
      console.log(
        "checking if we just returned from HydroShare login redirect",
      );
      const loggedIn = await User.checkLoginStatus();
      if (loggedIn) {
        await User.getOrCreateS3Credentials();
      }
    }

    if (!this.s3Info.bucket || !this.s3Info.prefix) {
      try {
        const s3info = await User.getResourceS3prefix(this.resourceId);
        if (s3info) {
          this.s3Info = s3info;
          this.s3Info.prefix = `${this.resourceId}/.hsjsonld/`; // TODO: overriding wrong api response value
        }
      } catch (e) {
        this.isLoadingFiles = false;
        this.isFetchingMetadata = false;
      }
    }

    await this.startS3Client();

    /* @ts-ignore */
    this.schema = await import(
      `@/schemas/hydroshare/scientific_dataset_json_schema.json`
    );

    /* @ts-ignore */
    this.uischema = await import(`@/schemas/hydroshare/view-uischema.json`);

    await this.loadResource();
  }

  parseDate(date: string): string {
    const parsed = new Date(Date.parse(date));
    return parsed.toLocaleString("default", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  }

  getStatusColor(status: EnumCreativeWorkStatus) {
    switch (status) {
      case EnumCreativeWorkStatus.Private:
        return "#d9534f";
      case EnumCreativeWorkStatus.Discoverable:
        return "#f0ad4e";
      case EnumCreativeWorkStatus.Public:
        return "#5cb85c";
      case EnumCreativeWorkStatus.Published:
        return "#4BB5C1";
      default:
        return "primary";
    }
  }

  buildToc() {
    const d = this.data;
    const toc: { text: string; to: string; level?: number }[] = [
      { text: "Overview", to: "#overview" },
      { text: "Details", to: "#details" },
    ];

    if (d.description) {
      toc.push({ text: "Abstract", to: "#description" });
    }

    toc.push({ text: "Content", to: "#content" });
    toc.push({ text: "Files", to: "#fileExplorer", level: 4 });

    if (d.funding?.length) {
      toc.push({ text: "Funding", to: "#funding" });
    }

    const hasRelated =
      d.hasPart?.length || d.isPartOf?.length || d.subjectOf?.length;
    if (hasRelated) {
      toc.push({ text: "Related Resources", to: "#related" });
    }

    User.$state.toc = toc;
    User.$state.isTocReady = true;
  }

  beforeUnmount() {
    User.$state.toc = [];
    User.$state.isTocReady = false;
    window.removeEventListener("message", this.onParentMessage);
  }

  ownerLocation(owner: any): string {
    const parts = [owner?.state, owner?.country].filter(Boolean);
    return parts.join(", ");
  }

  ownerOrganizations(owner: any): string[] {
    // HydroShare stores `organization` as a single string with multiple values
    // separated by ";" (see theme/static/js/profile.js splitAndWrapWithClass).
    const raw = owner?.organization;
    if (typeof raw !== "string") return [];
    return raw
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  ownerOrcid(owner: any): string | undefined {
    const ids = owner?.identifiers;
    if (!ids || typeof ids !== "object") return undefined;
    // identifiers is a dict keyed by name; ORCID is usually under "ORCID".
    return ids["ORCID"] || ids["orcid"] || undefined;
  }

  async loadResource() {
    this.isFetchingMetadata = true;
    this.isLoadingFiles = true;
    this.wasLoaded = true;
    User.$state.toc = [];
    User.$state.isTocReady = false;

    const resource = await fetchResource(
      this.resourceId,
      this.s3Client,
      this.s3Info.bucket,
      `${this.s3Info.prefix}dataset_metadata.json`,
    );

    if (resource) {
      this.data = resource.data;
      // Live counters are passed by the Django AtlasLandingView via query params
      // because dataset_metadata.json in S3 is a snapshot and lags the DB counters.
      const liveViewCount = Number(this.$route.query.viewCount);
      if (Number.isFinite(liveViewCount)) {
        this.data.viewCount = liveViewCount;
      }
      const liveDownloadCount = Number(this.$route.query.downloadCount);
      if (Number.isFinite(liveDownloadCount)) {
        this.data.downloadCount = liveDownloadCount;
      }
      // @ts-expect-error The key property is generated when the component is initialized
      this.rootDirectory.children = resource.initialStructure || [];
      this.loadReadmeFile();
      this.buildToc();
    } else {
      this.wasLoaded = false;
    }
    this.isFetchingMetadata = false;
    this.isLoadingFiles = false;
  }

  async onS3FormUpdate(params: any) {
    this.isFetchingMetadata = true;
    this.isLoadingFiles = true;
    this.s3Info.bucket = params.bucket;
    this.s3Info.prefix = params.prefix;
    this.hydroshareHost = params.hydroshareHost;
    this.s3Host = params.s3Host;
    if (params.accessKey || params.secretKey) {
      User.commit((state) => {
        state.credentials = {
          accessKey: params.accessKey || state.credentials.accessKey,
          secretKey: params.secretKey || state.credentials.secretKey,
        };
      });
    }

    await this.startS3Client();
    await this.loadResource();
  }

  async onRestoreDefaults() {
    this.isFetchingMetadata = true;
    this.isLoadingFiles = true;
    this.s3Host = "http://localhost:9000";
    this.hydroshareHost = "http://localhost:8000";

    try {
      User.getResourceS3prefix(this.resourceId).then((s3info) => {
        if (s3info) {
          this.s3Info = s3info;
          this.s3Info.prefix = `${this.resourceId}/.hsjsonld/`; // TODO: overriding wrong api response value
        }
      });
      await this.startS3Client();
      await this.loadResource();
    } catch (e) {
      this.isLoadingFiles = false;
      this.isFetchingMetadata = false;
    }
  }
}
export default toNative(LandingPage);
</script>

<style lang="scss" scoped>
.details-card {
  border-color: rgba(0, 0, 0, 0.08) !important;
}

.resource-type-icon {
  height: 32px;
  width: 32px;
}

.cc-badge {
  height: 32px;
  width: auto;
  display: block;
}

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


.profile-card {
  overflow: hidden;
  border-radius: 12px !important;
}

.profile-banner {
  height: 56px;
  background: linear-gradient(135deg, #4BB5C1 0%, #2a7c87 100%);
}

.profile-header {
  position: relative;
  padding: 0 20px 16px;
  margin-top: -36px;
}

.profile-avatar {
  border: 3px solid #fff;
  background-color: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.profile-identity {
  margin-top: 8px;
}

.profile-name {
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.25;
  color: rgba(0, 0, 0, 0.87);
}

.profile-title {
  font-size: 0.8125rem;
  margin-top: 2px;
}

.profile-meta {
  padding-top: 4px !important;
  font-size: 0.8125rem;
}

.profile-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 3px 0;
  color: rgba(0, 0, 0, 0.7);
}

.profile-row-icon {
  margin-top: 2px;
  color: rgba(0, 0, 0, 0.45);
  flex-shrink: 0;
}

.profile-section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.55);
  margin-bottom: 6px;
}

.profile-actions {
  background-color: #fafafa;
}

.orcid-btn :deep(.v-btn__content) {
  display: inline-flex;
  align-items: center;
}

.orcid-btn .fa-orcid {
  color: #A6CE39;
}

.section-heading {
  color: #4BB5C1;
  letter-spacing: 0.05em;
  padding-bottom: 0.4rem;
  margin-bottom: 0.75rem;
  border-bottom: 2px solid #e0e0e0;
}

.sidebar {
  flex-basis: 22rem;
  flex-shrink: 0;
  min-width: 0;
}

.page-content {
  flex-grow: 1;
  max-width: 100%;
  min-width: 0;

  &.is-sm {
    .dataset-info {
      grid-template-columns: auto;
      gap: 0;
    }
  }
}

:deep(.map-container) {
  height: 15rem;
}

.citation-text {
  min-width: 0;
  word-break: break-word;
}

.dataset-info {
  display: grid;
  grid-template-columns: auto auto;
  gap: 0.1rem 1rem;
  justify-content: start;
  align-items: baseline;
  align-content: baseline;

  &.one-col {
    grid-template-columns: 1fr;
  }
}

:deep(#fileExplorer .v-sheet) {
  background-color: #f6f6f6 !important;
}

.readme-container {
  .v-card-text {
    min-height: 5rem;
    height: 40rem;
    overflow: auto;
    resize: vertical;
  }

  .markdown-body {
    box-sizing: border-box;
    min-width: 200px;
    max-width: 980px;
    padding: 45px;
    font-family: inherit;
  }

  @media (max-width: 767px) {
    .markdown-body {
      padding: 15px;
    }
  }
}
</style>
