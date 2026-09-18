<template>
  <v-container>
    <v-skeleton-loader
      v-if="isFetchingMetadata"
      type="card"
    ></v-skeleton-loader>

    <template v-if="!isFetchingMetadata && wasLoaded">
      <!-- Legacy landing-page warnings/notifications. Each Django session-driven
           value (just_created / just_copied) plus resource-state checks
           (missing metadata, replaced/version-of, review/published) gets its
           own dismissable alert above the title. -->
      <div v-if="showNewVersionAlert" class="mb-4">
        <v-alert
          type="success"
          variant="tonal"
          closable
          @click:close="dismissedAlerts.newVersion = true"
        >
          <strong>Congratulations!</strong>
          Your new version has been created. A link to the older version has
          been added below the resource title. To modify this new version or
          change the sharing status, click the Edit button. Note that this new
          version is created as a private resource by default — if you want it
          to be discoverable, you need to make it public, discoverable, or
          published.
        </v-alert>
      </div>

      <div v-if="showCopyAlert" class="mb-4">
        <v-alert
          type="success"
          variant="tonal"
          closable
          @click:close="dismissedAlerts.copy = true"
        >
          <strong>Congratulations!</strong>
          Your new copy of the resource has been created. A <em>Derived From</em>
          source metadata element has been added to this resource in the
          Related Resources section below that links to the original resource.
          Please respect the terms of the license of the original resource and
          recognize the original authors as appropriate. Note that this copy is
          created as a private resource by default.
        </v-alert>
      </div>

      <div v-if="showMissingMetadataAlert" class="mb-4">
        <v-alert
          :type="alerts.justCreated ? 'success' : 'warning'"
          variant="tonal"
          closable
          @click:close="dismissedAlerts.missing = true"
        >
          <div v-if="alerts.justCreated">
            This is the landing page for the {{ alerts.displayName || "resource" }}
            you just created. Add files in the content area below and enter
            metadata where needed.
          </div>
          <div v-if="alerts.missingMetadata && alerts.missingMetadata.length" class="mt-2">
            We recommend following these minimum metadata requirements before
            making your {{ alerts.displayName || "resource" }} public or
            discoverable:
            <ul class="ml-4 mt-1">
              <li v-for="el in alerts.missingMetadata" :key="el">{{ el }}</li>
              <li v-if="alerts.isUntitled">Title: needs to be changed</li>
              <li v-for="el in alerts.recommendedMissing || []" :key="`r-${el}`">
                {{ el }}
              </li>
            </ul>
          </div>
          <div v-if="alerts.hasRequiredContentFiles === false" class="mt-2">
            You must
            <template v-if="alerts.missingMetadata && alerts.missingMetadata.length">
              also
            </template>
            add content files to your {{ alerts.displayName || "resource" }}
            before it can be published, public, or discoverable.
          </div>
        </v-alert>
      </div>

      <div v-if="showReplacedByAlert" class="mb-4">
        <v-alert
          type="info"
          variant="tonal"
          closable
          @click:close="dismissedAlerts.replacedBy = true"
        >
          A newer version of this resource
          <a :href="alerts.isReplacedBy || undefined" target="_blank" rel="noopener">
            is available
          </a>
          that replaces this version.
        </v-alert>
      </div>

      <div v-if="showVersionOfAlert" class="mb-4">
        <v-alert
          type="info"
          variant="tonal"
          closable
          @click:close="dismissedAlerts.versionOf = true"
        >
          An older version of this resource
          <a :href="alerts.isVersionOf || undefined" target="_blank" rel="noopener">
            is available
          </a>.
        </v-alert>
      </div>

      <div id="overview" class="resource-header mb-6">
        <div class="d-flex align-start ga-3 mb-2">
          <h1 class="text-h5 font-weight-bold flex-grow-1 ma-0">
            {{ data.name }}
          </h1>

          <!-- Mobile: 3-dot menu sits flush-right next to the title. -->
          <v-menu
            v-if="$vuetify.display.smAndDown && !isLoadingFiles && !isFetchingMetadata"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-dots-vertical"
                size="small"
                variant="text"
                aria-label="More actions"
                class="flex-shrink-0"
              />
            </template>
            <v-list density="compact" class="title-actions-menu" min-width="180">
              <v-list-item
                title="Edit"
                @click="$router.push({ name: 'edit-dataset' })"
              >
                <template #prepend>
                  <v-icon size="18">mdi-pen</v-icon>
                </template>
              </v-list-item>
              <v-list-item
                v-if="isLoggedIn"
                title="Manage access"
                @click="showManageAccess = true"
              >
                <template #prepend>
                  <v-icon size="18">mdi-account-multiple</v-icon>
                </template>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>

        <!-- Meta info + (desktop) action buttons on the same row. The action
             group is pushed to the right via ml-auto and hidden on mobile,
             where the same actions live in the 3-dot menu next to the title. -->
        <div class="d-flex flex-wrap align-center ga-3">
          <div class="d-flex flex-wrap align-center gc-4 gr-1">
            <div class="d-flex align-center ga-2">
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
          </div>

          <div
            v-if="
              !isLoadingFiles &&
              !isFetchingMetadata &&
              !$vuetify.display.smAndDown
            "
            class="d-flex flex-wrap align-center ga-1 ml-auto"
          >
            <v-btn
              v-if="isLoggedIn"
              size="small"
              prepend-icon="mdi-account-multiple"
              variant="outlined"
              @click="showManageAccess = true"
              >Manage access</v-btn
            >

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

      <cd-manage-access
        v-if="resourceId"
        v-model="showManageAccess"
        :resource-id="resourceId"
      />

      <v-divider></v-divider>

      <v-select
        v-if="tocItems.length"
        class="mobile-toc mt-4"
        :items="tocItems"
        item-title="text"
        item-value="to"
        density="compact"
        variant="outlined"
        hide-details
        prepend-inner-icon="mdi-format-list-bulleted"
        label="Jump to section"
        :model-value="null"
        @update:model-value="scrollToSection"
      >
        <template #item="{ props, item }">
          <v-list-item
            v-bind="props"
            :class="{
              'ps-8': item.raw.level && item.raw.level >= 4,
            }"
          />
        </template>
      </v-select>

      <div class="d-flex flex-column flex-lg-row ga-6 mt-6">
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

                  <div v-bind="infoValueAttr">
                    <cd-author-profile
                      v-for="(creator, index) of data.creator"
                      :key="index"
                      :creator="creator"
                      :profile-link="creatorProfileLink(creator)"
                      :identifiers="creatorIdentifiers(creator)"
                    />
                  </div>

                  <template v-if="owners.length">
                    <div v-bind="infoLabelAttr">Owners:</div>
                    <div
                      class="d-flex flex-wrap align-baseline"
                      style="row-gap: 0.15rem; column-gap: 0.75rem"
                    >
                      <cd-owner-profile
                        v-for="(owner, ownerIdx) of owners"
                        :key="owner.id || ownerIdx"
                        :owner="owner"
                      />
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
              :ref="setDescriptionBannerRef"
            >
              <template v-slot:actions>
                <v-btn
                  v-if="isDescriptionClamped || showDescription"
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

            <!-- CzFileExplorer renders a fragment root, so id/class passed
                 directly to it are dropped by Vue. Wrap so #fileExplorer
                 exists for the TOC anchor and the :deep selectors. -->
            <div
              v-if="!isLoadingFiles"
              id="fileExplorer"
              class="my-4"
            >
              <cz-file-explorer
                @showMetadata="onShowMetadata($event)"
                ref="fileExplorer"
                :root-directory="rootDirectory"
                :has-folders="fileExplorerConfig.hasFolders"
                :is-read-only="true"
                :has-file-metadata="() => true"
                :canDownloadItem="(item: IFile | IFolder) => !isFolder(item)"
                :load-file-preview="(item) => loadFilePreview(item)"
                :download-zipped="(item: IFile | IFolder) => onZippedDownload(item, resourceId)"
                :download-archive="() => onDownloadBag(resourceId, bagUrl)"
                @download="
                  onFileDownload($event, resourceId, s3Client, s3Info.bucket)
                "
                downloadArchiveHelpText="Download all content as Zipped BagIt Archive"
              >
                <template #prepend>
                  <span />
                </template>
              </cz-file-explorer>
            </div>
            <!-- <v-skeleton-loader
            class="mb-12"
            v-else
            type="card"
          ></v-skeleton-loader> -->

            <v-card
              v-if="readmeMd || isLoadingMD"
              id="readme"
              class="readme-container"
              variant="outlined"
              border="grey thin"
            >
              <v-card-title class="text-overline d-flex ga-2"
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
                  class="markdown-body"
                ></div>
                <pre v-else style="white-space: pre-wrap">{{
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
            v-if="hasRelatedResources"
            class="mb-6 field"
            id="related"
          >
          <div v-bind="headingAttr">Related Resources</div>
            <v-card variant="outlined" border="grey thin">
              <v-table class="related-resources-table">
                <template v-slot:default>
                  <tbody>
                    <tr
                      v-for="(part, index) in data.hasPart?.filter(p => p.url)"
                      :key="`hp-${index}`"
                    >
                      <td class="relation-label">Has part</td>
                      <td class="relation-url">
                        <a :href="part.url">{{ part.url }}</a>
                      </td>
                    </tr>

                    <tr
                      v-for="(part, index) in data.isPartOf?.filter(p => p.url)"
                      :key="`ipo-${index}`"
                    >
                      <td class="relation-label">Is part of</td>
                      <td class="relation-url">
                        <a :href="part.url">{{ part.url }}</a>
                      </td>
                    </tr>

                    <tr
                      v-for="(part, index) in data.subjectOf?.filter(p => p.url)"
                      :key="`so-${index}`"
                    >
                      <td class="relation-label">Subject of</td>
                      <td class="relation-url">
                        <a :href="part.url">{{ part.url }}</a>
                      </td>
                    </tr>
                  </tbody>
                </template>
              </v-table>
            </v-card>
          </div>

        </v-container>

        <div class="sidebar break-word">
          <div>
            <v-card v-if="data.keywords?.length" id="subject" variant="flat" class="mb-6">
              <v-card-title class="sidebar-heading pa-0">
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
              <v-card-title class="sidebar-heading pa-0">
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
              <div class="sidebar-heading">
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
                      <v-card-text v-if="spatialGeoType == 'GeoShape'">
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
                      <v-card-text v-if="spatialGeoType == 'GeoCoordinates'">
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
              <div class="sidebar-heading">
                Temporal Coverage
              </div>
              <v-card variant="outlined" border="grey thin">
                <v-card-text>
                  <v-timeline align-top density="compact" line-color="info">
                    <!-- Per the schema, startDate is required and endDate is
                         optional (open-ended periods). Render each item
                         conditionally so an ongoing period doesn't show a
                         dangling End Date row. -->
                    <v-timeline-item
                      v-if="data.temporalCoverage.startDate"
                      dot-color="primary"
                      icon="mdi-calendar"
                      fill-dot
                    >
                      <div>
                        <strong>Start Date</strong>
                        <div>{{ parseDate(data.temporalCoverage.startDate) }}</div>
                      </div>
                    </v-timeline-item>
                    <v-timeline-item
                      v-if="data.temporalCoverage.endDate"
                      dot-color="orange-darken-2"
                      icon="mdi-calendar"
                      fill-dot
                    >
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
              <v-card-title class="sidebar-heading pa-0">
                How to cite
              </v-card-title>
              <v-card-text
                v-for="(citation, index) of citations"
                :key="index"
                class="pa-0 text-body-2 text-medium-emphasis"
              >
                <div class="d-flex align-center justify-space-between ga-3">
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
        text="Sign in or check that the resource exists and you have access to it."
        title="We couldn't load this resource."
      ></v-empty-state>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import "github-markdown-css/github-markdown-light.css";
import {
  CzFileExplorer,
  Notifications,
} from "@cznethub/cznet-vue-core";
import type { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";
import { GetObjectCommand, S3Client, _Object } from "@aws-sdk/client-s3";
import {
  fetchResource,
  getStatusColor,
  onDownloadBag,
  onFileDownload,
  onZippedDownload,
  parseDate,
} from "./shared";
import { isFolder } from "./zip-download";
import { loadReadme } from "./readme-s3";
import { createCookieS3Client } from "./cookie-s3-client";
import User from "@/models/user.model";
import prettyBytes from "pretty-bytes";
import { useRoute } from "vue-router";
import { contentTypeLabels, contentTypeLogos, S3_PROXY_URL } from "@/constants";
import { renderMarkdown } from "./markdown";

import CdSpatialCoverageMap from "@/components/search-results/cd.spatial-coverage-map.vue";
import CdAuthorProfile from "./cd.author-profile.vue";
import CdOwnerProfile from "./cd.owner-profile.vue";
import CdManageAccess from "./cd.manage-access.vue";

const route = useRoute();

const resourceId = ref<string>("");

const isLoggedIn = computed<boolean>(() => User.$state.isLoggedIn);

const showDescription = ref(false);
const isDescriptionClamped = ref(false);
const showManageAccess = ref(false);
const readmeMd = ref("");
const readMeFileName = ref("");
const hasTxtReadme = ref(false);
const isLoadingMD = ref(false);

/**
 * Fetches a Blob for cz-file-explorer's preview dialog. The dialog passes
 * the explorer-annotated `item` (with `path` already set by `onPreview` →
 * `getPathString`).
 */
async function loadFilePreview(item: any): Promise<Blob> {
  const key = `${resourceId.value}/data/contents/${item.path || item.name}`;
  const result = await s3Client.value.send(
    new GetObjectCommand({ Bucket: s3Info.value.bucket, Key: key }),
  );
  const bytes = await result.Body?.transformToByteArray();
  if (!bytes) throw new Error("Empty response from S3");
  return new Blob([bytes], {
    type: result.ContentType || "application/octet-stream",
  });
}

const data = ref<Record<string, any>>({});
const owners = ref<any[]>([]);
const creatorProfiles = ref<Array<{
  name: string;
  hs_user_id?: number | null;
  is_active_user?: boolean;
  relative_uri?: string | null;
  identifiers?: Record<string, string> | null;
}>>([]);
const alerts = ref<{
  justCreated?: boolean;
  justCopied?: boolean;
  missingMetadata?: string[];
  recommendedMissing?: string[];
  hasRequiredContentFiles?: boolean;
  isUntitled?: boolean;
  isReplacedBy?: string | null;
  isVersionOf?: string | null;
  reviewPending?: boolean;
  isPublished?: boolean;
  displayName?: string;
}>({});
const bagUrl = ref<string>("");
const dismissedAlerts = ref<Record<string, boolean>>({});
const onParentMessage = (event: MessageEvent) => {
  // search.html in the parent posts `{ parentSearch, owners }` after the
  // iframe loads. Owners are injected from the Django view because they
  // aren't part of the S3 dataset_metadata.json payload.
  if (event.origin !== window.location.origin) return;
  const payload = event.data;
  if (payload && Array.isArray(payload.owners)) {
    owners.value = payload.owners;
  }
};

const isLoadingFiles = ref(true);
const isFetchingMetadata = ref(true);
const wasLoaded = ref(true);

const s3Client = shallowRef<S3Client>(undefined as unknown as S3Client);
const s3Host = S3_PROXY_URL;

const s3Info = ref({
  bucket: "",
  prefix: "",
});

const rootDirectory = ref<Partial<IFolder>>({
  name: "root",
  children: [],
});
const fileExplorerConfig = {
  isReadOnly: true, // Unused for now
  hasFolders: true,
};

function startS3Client() {
  s3Client.value = createCookieS3Client(s3Host);
}
// Labels read as supporting context (small, uppercase, muted) so values
// — the actual data — stand out as the primary content.
const infoLabelAttr = {
  class:
    "text-caption text-uppercase text-medium-emphasis font-weight-medium dataset-info__label",
};
const selectedMetadata = ref<any>(false);
const showMetadata = ref(false);

// mb-2 used to live here; it doubled-up with the grid's row-gap and made
// spacing between rows inconsistent (text rows had a margin but card-based
// rows like author profiles did not). The grid handles spacing now.
const infoValueAttr = {
  class: "text-body-2 dataset-info__value",
};
const headingAttr = {
  class:
    "section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3",
};

function onShowMetadata(item: any) {
  selectedMetadata.value = item;
  showMetadata.value = true;
}

function onCopy(text: string) {
  navigator.clipboard.writeText(text);
  Notifications.toast({ message: "Copied to clipboard", type: "info" });
}

const tocItems = computed(() => User.$state.toc);

function scrollToSection(hash: string | null) {
  if (!hash) return;
  const el = document.querySelector(hash) as HTMLElement | null;
  if (!el) return;

  // Mirror toc.vue: the iframe has scrolling="no" and is auto-sized to
  // content, so window.scrollTo inside the iframe is a no-op. Reach across
  // to the same-origin parent and scroll there.
  if (window.parent && window.parent !== window) {
    const frame = window.frameElement as HTMLIFrameElement | null;
    if (frame) {
      try {
        const parentWin = window.parent as Window;
        const iframeTop =
          frame.getBoundingClientRect().top +
          (parentWin.scrollY || parentWin.pageYOffset || 0);
        const elTop = el.getBoundingClientRect().top;
        parentWin.scrollTo({ top: iframeTop + elTop - 16, behavior: "smooth" });
        return;
      } catch {
        // Cross-origin — fall through to in-iframe scroll.
      }
    }
  }

  const top = el.getBoundingClientRect().top + window.scrollY - 16;
  window.scrollTo({ top, behavior: "smooth" });
}

function setDescriptionBannerRef(el: any) {
  // Mirrors cd.search-results' setBannerRef: only show the "Show more"
  // button when the three-line clamp actually truncates the text.
  if (!el || showDescription.value) return;
  nextTick(() => {
    const bannerEl = el.$el || el;
    const textEl = bannerEl.querySelector?.(".v-banner-text");
    if (textEl) {
      isDescriptionClamped.value = textEl.scrollHeight > textEl.clientHeight;
    }
  });
}

async function loadReadmeFile() {
  // S3 keys are case-sensitive, so probe the root listing for any
  // file whose name matches readme.md / readme.txt case-insensitively.
  const rootFiles = (rootDirectory.value.children || []).filter(
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
  hasTxtReadme.value = !mdFile;
  readMeFileName.value = target.name;

  // Cache-busting read (see loadReadme) so edits show without a cache clear.
  let rawMd: string;
  try {
    isLoadingMD.value = true;
    rawMd = await loadReadme(s3Info.value.bucket, resourceId.value, target.name);
  } catch (e) {
    // Failed to load — skip rendering and the TOC entry.
    isLoadingMD.value = false;
    return;
  }

  try {
    readmeMd.value = hasTxtReadme.value ? rawMd : renderMarkdown(rawMd);
  } catch (e) {
    console.log(e);
  } finally {
    isLoadingMD.value = false;
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

const showNewVersionAlert = computed<boolean>(() =>
  Boolean(
    !dismissedAlerts.value.newVersion &&
      alerts.value.justCreated &&
      alerts.value.isVersionOf,
  ),
);

const showCopyAlert = computed<boolean>(() =>
  Boolean(
    !dismissedAlerts.value.copy &&
      alerts.value.justCreated &&
      alerts.value.justCopied,
  ),
);

const showMissingMetadataAlert = computed<boolean>(() => {
  if (dismissedAlerts.value.missing) return false;
  const hasMissing = (alerts.value.missingMetadata || []).length > 0;
  const noFiles = alerts.value.hasRequiredContentFiles === false;
  return Boolean(hasMissing || alerts.value.isUntitled || noFiles);
});

const showReplacedByAlert = computed<boolean>(() =>
  Boolean(!dismissedAlerts.value.replacedBy && alerts.value.isReplacedBy),
);

const showVersionOfAlert = computed<boolean>(() =>
  // Only show the "older version exists" pointer when we're NOT also showing
  // the just-created-new-version banner (which already explains the
  // relationship and would otherwise duplicate the message).
  Boolean(
    !dismissedAlerts.value.versionOf &&
      alerts.value.isVersionOf &&
      !alerts.value.justCreated,
  ),
);

const hasRelatedResources = computed<boolean>(() => {
  const d = data.value;
  return (
    d.hasPart?.some((p: any) => p.url) ||
    d.isPartOf?.some((p: any) => p.url) ||
    d.subjectOf?.some((p: any) => p.url)
  );
});

// Prefer @type; fall back to legacy `type` for not-yet-migrated data.
const spatialGeoType = computed<string | undefined>(() => {
  const geo = data.value.spatialCoverage?.geo;
  return geo?.["@type"] ?? geo?.["type"];
});

const hasSpatialFeatures = computed<boolean>(
  () =>
    // `spatialCoverage` is schema.org Place; the actual geometry lives on
    // `.geo` and carries the GeoShape / GeoCoordinates type.
    spatialGeoType.value === "GeoShape" ||
    spatialGeoType.value === "GeoCoordinates",
);

const isPublished = computed<boolean>(
  () => data.value?.creativeWorkStatus?.name === "Published",
);

const potentialDoiUrl = computed<string>(
  () => `https://doi.org/10.4211/hs.${resourceId.value}`,
);

const citations = computed<string[]>(() => {
  // hydroshare_schemaorg_adapter sets dataset.citation = [self.citation] —
  // so the live JSON has data.citation as an array of strings. The legacy
  // landing-page template referenced data.document[0].citation, which never
  // exists in this payload.
  const raw = data.value?.citation;
  if (Array.isArray(raw)) return raw.filter((c: any) => typeof c === "string" && c.trim());
  if (typeof raw === "string" && raw.trim()) return [raw];
  return [];
});

const licenseBadgeUrl = computed<string | undefined>(() => {
  // The license `name` is the rights statement; map the canonical CC variants
  // to the badge images served by Django from theme/static/img/cc-badges/.
  const statement: string = data.value?.license?.name || "";
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
});

const resourceTypeKey = computed<string>(
  () =>
    // dataset_metadata.json's additionalType holds the HydroShare resource type
    // (e.g. "CompositeResource"). data["@type"] is the schema.org class ("Dataset").
    data.value?.additionalType || data.value?.["@type"] || "",
);

const resourceTypeLabel = computed<string>(() => {
  const key = resourceTypeKey.value;
  return contentTypeLabels[key] || key;
});

const resourceTypeIcon = computed<string | undefined>(
  () => contentTypeLogos[resourceTypeKey.value],
);

const contentSize = computed(() => {
  const sumTree = (nodes: any[]): number =>
    nodes.reduce((acc, n) => {
      if (Array.isArray(n?.children)) {
        return acc + sumTree(n.children);
      }
      return acc + (typeof n?.uploadedSize === "number" ? n.uploadedSize : 0);
    }, 0);

  const fromFiles = sumTree(rootDirectory.value.children || []);
  if (fromFiles > 0) return prettyBytes(fromFiles);
});

const boxCoordinates = computed(() => {
  const extents = data.value.spatialCoverage.geo.box
    .trim()
    .split(" ")
    .map((n: string) => +n);
  return {
    north: extents[0],
    east: extents[1],
    south: extents[2],
    west: extents[3],
  };
});

// created()
async function init() {
  // Owners are injected by AtlasLandingView via the parent window
  // (same-origin) — read them synchronously to avoid a race with the
  // iframe-load postMessage. Fall back to the postMessage path if the
  // global isn't there (e.g. component loaded directly outside the iframe).
  try {
    const parentWin = window.parent as any;
    if (parentWin && parentWin !== window) {
      if (Array.isArray(parentWin.HS_RESOURCE_OWNERS)) {
        owners.value = parentWin.HS_RESOURCE_OWNERS;
      }
      if (Array.isArray(parentWin.HS_RESOURCE_CREATOR_PROFILES)) {
        creatorProfiles.value = parentWin.HS_RESOURCE_CREATOR_PROFILES;
      }
      if (parentWin.HS_RESOURCE_ALERTS && typeof parentWin.HS_RESOURCE_ALERTS === "object") {
        alerts.value = parentWin.HS_RESOURCE_ALERTS;
      }
      if (parentWin.HS_BAG_URL && typeof parentWin.HS_BAG_URL === "string") {
        bagUrl.value = parentWin.HS_BAG_URL;
      }
    }
  } catch {
    // cross-origin access blocked — postMessage listener will handle it
  }
  window.addEventListener("message", onParentMessage);

  if (!resourceId.value && route?.params?.resourceId) {
    resourceId.value = route.params.resourceId as string;
  }

  if (!resourceId.value) {
    isFetchingMetadata.value = false;
    wasLoaded.value = false;
    return;
  }

  if (!isLoggedIn.value) {
    // Refresh login state (e.g. just returned from a HydroShare login
    // redirect). S3 access now rides on the session cookies themselves,
    // so there are no credentials to mint.
    await User.checkLoginStatus();
  }

  if (!s3Info.value.bucket) {
    try {
      const bucket = await User.getResourceBucket(resourceId.value);
      if (bucket) {
        // This page reads system-generated metadata from `.hsjsonld/`, not the
        // endpoint's `data/contents/` root.
        s3Info.value = { bucket, prefix: `${resourceId.value}/.hsjsonld/` };
      }
    } catch (e) {
      isLoadingFiles.value = false;
      isFetchingMetadata.value = false;
    }
  }

  startS3Client();

  await loadResource();
}


function buildToc() {
  const d = data.value;
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

  if (hasRelatedResources.value) {
    toc.push({ text: "Related Resources", to: "#related" });
  }

  User.$state.toc = toc;
  User.$state.isTocReady = true;
}

onBeforeUnmount(() => {
  User.$state.toc = [];
  User.$state.isTocReady = false;
  window.removeEventListener("message", onParentMessage);
});

function findCreatorProfile(creator: any) {
  if (!creator?.name) return undefined;
  return creatorProfiles.value.find(
    (p) => p && p.name && p.name === creator.name,
  );
}

function creatorProfileLink(creator: any): string | null {
  // The schema.org dataset_metadata.json carries no HydroShare-user linkage,
  // so we match by name against the side-channel `creatorProfiles` payload
  // (populated by AtlasLandingView from resource.cached_metadata.creators).
  const profile = findCreatorProfile(creator);
  if (!profile || !profile.is_active_user || !profile.relative_uri) return null;
  return profile.relative_uri;
}

function creatorIdentifiers(creator: any): Record<string, string> {
  // Same side-channel rationale as creatorProfileLink — the schema.org
  // adapter only emits ORCID, so we sourcemap the full dict from
  // cached_metadata.creators.
  const profile = findCreatorProfile(creator);
  return profile?.identifiers || {};
}

async function loadResource() {
  isFetchingMetadata.value = true;
  isLoadingFiles.value = true;
  wasLoaded.value = true;
  User.$state.toc = [];
  User.$state.isTocReady = false;

  const resource = await fetchResource(
    resourceId.value,
    s3Client.value,
    s3Info.value.bucket,
    `${s3Info.value.prefix}dataset_metadata.json`,
  );

  if (resource) {
    data.value = resource.data;
    // Live counters are passed by the Django AtlasLandingView via query params
    // because dataset_metadata.json in S3 is a snapshot and lags the DB counters.
    const liveViewCount = Number(route.query.viewCount);
    if (Number.isFinite(liveViewCount)) {
      data.value.viewCount = liveViewCount;
    }
    const liveDownloadCount = Number(route.query.downloadCount);
    if (Number.isFinite(liveDownloadCount)) {
      data.value.downloadCount = liveDownloadCount;
    }
    // @ts-expect-error The key property is generated when the component is initialized
    rootDirectory.value.children = resource.initialStructure || [];
    loadReadmeFile();
    buildToc();
  } else {
    wasLoaded.value = false;
  }
  isFetchingMetadata.value = false;
  isLoadingFiles.value = false;
}

init();
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

.section-heading {
  color: rgb(var(--v-theme-accent));
  letter-spacing: 0.05em;
  padding-bottom: 0.4rem;
  margin-bottom: 0.75rem;
  border-bottom: 2px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

// Sidebar section titles — identical treatment to the edit page's, so the
// two views read as modes of each other rather than separate designs.
.sidebar-heading {
  color: rgb(var(--v-theme-accent));
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.375rem;
  text-transform: uppercase;
}

.sidebar {
  flex-basis: 22rem;
  flex-shrink: 0;
  min-width: 0;

  @media (max-width: 1279px) {
    flex-basis: auto;
    width: 100%;
  }
}

// Mobile title 3-dot menu: tighten the gap between each item's prepend icon
// and its title. Vuetify renders a separate `.v-list-item__spacer` div after
// the icon whose width is driven by `--v-list-prepend-gap` (default 32px,
// which feels airy for a compact dropdown). Override the variable here
// instead of fighting `padding`/`margin` on the prepend wrapper — that
// padding doesn't control the icon→title gap.
.title-actions-menu {
  --v-list-prepend-gap: 10px;

  :deep(.v-list-item__prepend) {
    width: auto;
    min-width: 0;
  }

  :deep(.v-list-item__prepend > .v-icon) {
    opacity: 0.7;
  }

  :deep(.v-list-item-title) {
    font-size: 0.875rem;
    line-height: 1.25;
  }

  :deep(.v-list-item) {
    min-height: 36px;
    padding-inline: 0.875rem;
  }
}

.mobile-toc {
  background: rgb(var(--v-theme-surface));

  // The desktop TOC (toc.vue) hides itself below 1100px via its own media
  // query. Show this mobile select only in that same range so the two never
  // overlap.
  @media (min-width: 1100px) {
    display: none !important;
  }
}

.page-content {
  flex-grow: 1;
  max-width: 100%;
  min-width: 0;

  // Below the desktop column threshold the details grid collapses to a
  // single column. Keep a small row-gap so stacked label/value pairs don't
  // run together, but leave column-gap at 0 since there's only one column.
  &.is-sm {
    .dataset-info {
      grid-template-columns: 1fr;
      column-gap: 0;
      row-gap: 0.25rem;
    }

    .dataset-info__label {
      // Tighten the gap between a label and its value when stacked, while
      // still giving room above to separate from the previous pair.
      margin-top: 0.5rem;
    }

    .dataset-info__label:first-child {
      margin-top: 0;
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
  grid-template-columns: max-content 1fr;
  column-gap: 1.5rem;
  row-gap: 0.5rem;
  justify-content: start;
  align-items: baseline;
  align-content: baseline;

  &.one-col {
    grid-template-columns: 1fr;
    row-gap: 0.25rem;
  }
}

// Visual separator under each label so the eye can pick out the "this is a
// field name" rows from the values without relying on color alone.
.dataset-info__label {
  letter-spacing: 0.05em;
  line-height: 1.4;
}

.dataset-info__value {
  line-height: 1.4;
}

:deep(#fileExplorer .v-sheet) {
  background-color: #f6f6f6 !important;
}

// Related Resources table: long URLs were overflowing and forcing a
// horizontal scrollbar on the table. Wrap long URLs at any character so the
// URL column fits; keep the relation label ("Has part", "Is part of",
// "Subject of") on one line so it stays readable.
.related-resources-table {
  :deep(.relation-label) {
    white-space: nowrap;
    padding-right: 1.5rem !important;
  }

  :deep(.relation-url),
  :deep(.relation-url a) {
    overflow-wrap: anywhere;
    word-break: break-word;
  }
}

.readme-container {
  .v-card-text {
    min-height: 5rem;
    height: 40rem;
    overflow: auto;
    resize: vertical;
    padding: 1rem;
  }

  // github-markdown-css ships with `padding: 45px` and `max-width: 980px` on
  // .markdown-body — both are meant for full-page documents and look way too
  // padded when the README is embedded in a card. Override to use only the
  // surrounding v-card-text padding.
  .markdown-body {
    box-sizing: border-box;
    min-width: 200px;
    max-width: 100%;
    padding: 0;
    font-family: inherit;
  }
}
</style>
