<template>
  <v-container>
    <v-skeleton-loader v-if="isFetchingMetadata" type="card" />

    <template v-if="!isFetchingMetadata && wasLoaded">
      <cz-form-composed
        :schema="schema"
        v-model="data"
        v-model:is-valid="isValid"
        v-model:errors="errors"
        :config="config"
      >
        <!-- ===== HEADER: title input + meta + save/cancel actions ===== -->
        <div id="overview" class="resource-header mb-6">
          <div class="d-flex align-start ga-3 mb-3">
            <div class="flex-grow-1">
              <div class="text-overline text-medium-emphasis">
                Resource title<span class="required-mark">{{
                  requiredMark("#/properties/name")
                }}</span>
              </div>
              <cz-field scope="#/properties/name" hide-label />
            </div>

            <!-- Mobile: collapse Cancel + Settings into a 3-dot menu -->
            <v-menu v-if="$vuetify.display.smAndDown">
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
              <v-list density="compact">
                <v-list-item
                  title="Cancel and view"
                  @click="
                    $router.push({ name: 'landing', params: { resourceId } })
                  "
                >
                  <template #prepend>
                    <v-icon size="18">mdi-arrow-left</v-icon>
                  </template>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>

          <!-- Meta + actions row mirrors the landing page header layout.
               creativeWorkStatus and dateModified are hidden as inputs (per
               the old uischema) but still display read-only here for the
               same context the landing page provides. -->
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
                  v-if="data.creativeWorkStatus?.name"
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
                Last modified {{ parseDate(data.dateModified) }}
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
              v-if="!$vuetify.display.smAndDown"
              class="d-flex flex-wrap align-center ga-1 ml-auto"
            >
              <v-btn
                size="small"
                variant="outlined"
                prepend-icon="mdi-arrow-left"
                @click="
                  $router.push({ name: 'landing', params: { resourceId } })
                "
                >Cancel</v-btn
              >
            </div>
          </div>
        </div>

        <v-divider></v-divider>

        <!-- Mobile TOC select. Mirrors landing-page mobile-toc selector;
             scoped CSS in landing-page is reused via the same .mobile-toc
             class so it only renders below 1100px (where the desktop
             <Toc> drawer hides itself). -->
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

        <!-- ===== MAIN GRID: content column + sidebar ===== -->
        <div class="d-flex flex-column flex-lg-row ga-6 mt-6">
          <v-container
            class="page-content pa-0"
            :class="{ 'is-sm': $vuetify.display.mdAndDown }"
            fluid
          >
            <!-- Details card mirrors landing-page exactly. Two equal
                 columns, each a dataset-info grid (label | value). Only
                 Authors + Contributors are editable here — every other
                 field was hidden as an input in the old uischema and
                 surfaces as read-only context. identifier/url were never
                 top-level editable (they only appeared inside array
                 item details), so they're not rendered. -->
            <v-card
              id="details"
              variant="outlined"
              class="mb-6 details-card"
            >
              <v-card-text class="pa-5">
                <v-row :no-gutters="$vuetify.display.smAndDown">
                  <v-col cols="12" sm="6" class="dataset-info">
                    <div v-bind="infoLabelAttr">
                      Authors<span class="required-mark">{{
                        requiredMark("#/properties/creator")
                      }}</span
                      >:
                    </div>
                    <div v-bind="infoValueAttr">
                      <cz-field-modal
                        scope="#/properties/creator"
                        :options="creatorOptions"
                        :label="`Authors${requiredMark('#/properties/creator')}`"
                      >
                        <template
                          #summary="{
                            value,
                            errorsByIndex,
                            hasErrors,
                            openEdit,
                          }"
                        >
                          <div
                            class="modal-summary modal-summary--inline"
                            :class="{ 'has-errors': hasErrors }"
                            @click="openEdit"
                          >
                            <span
                              v-if="!(value && value.length)"
                              class="text-medium-emphasis font-italic"
                              >Click to add authors</span
                            >
                            <span
                              v-else
                              class="d-flex flex-wrap ga-1 align-center"
                            >
                              <v-chip
                                v-for="(person, i) in value"
                                :key="i"
                                size="x-small"
                                variant="outlined"
                                :color="
                                  errorsByIndex[i] ? 'error' : undefined
                                "
                                :title="
                                  errorsByIndex[i]
                                    ? `${errorsByIndex[i].length} issue${errorsByIndex[i].length === 1 ? '' : 's'}`
                                    : ''
                                "
                              >
                                <v-icon
                                  v-if="errorsByIndex[i]"
                                  start
                                  size="12"
                                  color="error"
                                  >mdi-alert-circle</v-icon
                                >
                                {{ person.name || `Author ${i + 1}` }}
                              </v-chip>
                            </span>
                            <v-icon size="small" class="modal-summary__edit"
                              >mdi-pencil</v-icon
                            >
                          </div>
                        </template>
                      </cz-field-modal>
                    </div>

                    <div v-bind="infoLabelAttr">
                      Contributors<span class="required-mark">{{
                        requiredMark("#/properties/contributor")
                      }}</span
                      >:
                    </div>
                    <div v-bind="infoValueAttr">
                      <cz-field-modal
                        scope="#/properties/contributor"
                        :options="contributorOptions"
                        :label="`Contributors${requiredMark(
                          '#/properties/contributor',
                        )}`"
                      >
                        <template
                          #summary="{
                            value,
                            errorsByIndex,
                            hasErrors,
                            openEdit,
                          }"
                        >
                          <div
                            class="modal-summary modal-summary--inline"
                            :class="{ 'has-errors': hasErrors }"
                            @click="openEdit"
                          >
                            <span
                              v-if="!(value && value.length)"
                              class="text-medium-emphasis font-italic"
                              >Click to add contributors</span
                            >
                            <span
                              v-else
                              class="d-flex flex-wrap ga-1 align-center"
                            >
                              <v-chip
                                v-for="(person, i) in value"
                                :key="i"
                                size="x-small"
                                variant="outlined"
                                :color="
                                  errorsByIndex[i] ? 'error' : undefined
                                "
                              >
                                <v-icon
                                  v-if="errorsByIndex[i]"
                                  start
                                  size="12"
                                  color="error"
                                  >mdi-alert-circle</v-icon
                                >
                                {{ person.name || `Contributor ${i + 1}` }}
                              </v-chip>
                            </span>
                            <v-icon size="small" class="modal-summary__edit"
                              >mdi-pencil</v-icon
                            >
                          </div>
                        </template>
                      </cz-field-modal>
                    </div>

                    <template v-if="data.provider">
                      <div v-bind="infoLabelAttr">Provider:</div>
                      <div v-bind="infoValueAttr">
                        <a
                          v-if="data.provider.url"
                          :href="data.provider.url"
                          >{{ data.provider.name }}</a
                        >
                        <template v-else>{{ data.provider.name }}</template>
                      </div>
                    </template>

                    <template v-if="data.publisher">
                      <div v-bind="infoLabelAttr">Publisher:</div>
                      <div v-bind="infoValueAttr">
                        <a
                          v-if="data.publisher.url"
                          :href="data.publisher.url"
                          >{{ data.publisher.name }}</a
                        >
                        <template v-else>{{ data.publisher.name }}</template>
                      </div>
                    </template>

                    <template v-if="resourceTypeLabel">
                      <div v-bind="infoLabelAttr">Resource Type:</div>
                      <div v-bind="infoValueAttr">{{ resourceTypeLabel }}</div>
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
                    <template v-if="data.dateCreated">
                      <div v-bind="infoLabelAttr">Created:</div>
                      <div v-bind="infoValueAttr">
                        {{ parseDate(data.dateCreated) }}
                      </div>
                    </template>

                    <template v-if="data.datePublished">
                      <div v-bind="infoLabelAttr">Published:</div>
                      <div v-bind="infoValueAttr">
                        {{ parseDate(data.datePublished) }}
                      </div>
                    </template>

                    <div v-bind="infoLabelAttr">Downloads:</div>
                    <div v-bind="infoValueAttr">
                      {{
                        data.downloadCount != null
                          ? data.downloadCount.toLocaleString()
                          : "—"
                      }}
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Abstract -->
            <div class="mb-6 field" id="description">
              <div
                class="section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3"
              >
                Abstract<span class="required-mark">{{
                  requiredMark("#/properties/description")
                }}</span>
              </div>
              <cz-field
                scope="#/properties/description"
                :options="descriptionOptions"
                hide-label
              />
            </div>

            <!-- Content (file explorer with Uppy) keeps its existing wiring -->
            <div class="mb-6 field" id="content">
              <div
                class="section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3"
              >
                Content
              </div>
              <div
                v-if="!isLoadingFiles"
                id="fileExplorer"
                class="my-4"
              >
                <cz-file-explorer
                  ref="fileExplorer"
                  @update:valid-items="toUpload = $event"
                  :root-directory="rootDirectory"
                  :has-folders="fileExplorerConfig.hasFolders"
                  :is-read-only="false"
                  :has-file-metadata="() => false"
                  :folder-name-regex="folderNameRegex"
                  :canDownloadItem="() => true"
                  :upload="uploadFiles"
                  :delete-file-or-folder="deleteFileOrFolder"
                  :rename-file-or-folder="renameFileOrFolder"
                  @download="
                    onFileDownload(
                      $event,
                      resourceId,
                      s3Client,
                      s3Info.bucket
                    )
                  "
                >
                  <template #prepend>
                    <span />
                  </template>
                  <template #drop-area>
                    <HsUppy
                      ref="hsUppyRef"
                      :s3Info="s3Info"
                      :s3Host="s3Host"
                      :fileExplorer="fileExplorer"
                      :upload-prefix="`${resourceId}/data/contents/`"
                      @file-uploaded="onUppyFileUploaded"
                    />
                  </template>
                </cz-file-explorer>
              </div>
              <v-skeleton-loader
                v-else
                class="mb-12"
                type="card"
              ></v-skeleton-loader>

              <!-- Editable README; see cd.readme-editor.vue. -->
              <cd-readme-editor
                v-if="!isLoadingFiles"
                id="readme"
                class="mt-4"
                :resource-id="resourceId"
                :s3-client="s3Client"
                :bucket="s3Info.bucket"
                :file-name="readmeFileName"
                @change="onReadmeChange"
              />
            </div>

            <!-- Funding -->
            <div class="mb-6 field" id="funding">
              <div
                class="section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3"
              >
                Funding<span class="required-mark">{{
                  requiredMark("#/properties/funding")
                }}</span>
              </div>
              <cz-field-modal
                scope="#/properties/funding"
                :options="fundingOptions"
                :label="`Funding${requiredMark('#/properties/funding')}`"
              >
                <template
                  #summary="{ value, errorsByIndex, hasErrors, openEdit }"
                >
                  <div
                    class="modal-summary"
                    :class="{ 'has-errors': hasErrors }"
                    @click="openEdit"
                  >
                    <div
                      v-if="!(value && value.length)"
                      class="text-body-2 text-medium-emphasis font-italic"
                    >
                      Click to add funding sources
                    </div>
                    <ul v-else class="funding-list">
                      <li
                        v-for="(f, i) in value"
                        :key="i"
                        :class="{ 'has-errors': errorsByIndex[i] }"
                      >
                        <v-icon
                          v-if="errorsByIndex[i]"
                          size="14"
                          color="error"
                          class="mr-1"
                          >mdi-alert-circle</v-icon
                        >
                        <strong>{{ f.name || `Funding ${i + 1}` }}</strong>
                        <span
                          v-if="f.identifier"
                          class="text-caption text-medium-emphasis ml-2"
                          >Award {{ f.identifier }}</span
                        >
                      </li>
                    </ul>
                    <v-icon size="small" class="modal-summary__edit"
                      >mdi-pencil</v-icon
                    >
                  </div>
                </template>
              </cz-field-modal>
            </div>

            <!-- Related Resources. hasPart/isPartOf were hidden in the old
                 uischema; only subjectOf + relation are editable inputs.
                 hasPart/isPartOf still render as read-only links so the
                 user can see them (matching landing page). -->
            <div class="mb-6 field" id="related">
              <div
                class="section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3"
              >
                Related Resources<span class="required-mark">{{
                  requiredMark("#/properties/relation") ||
                  requiredMark("#/properties/subjectOf")
                }}</span>
              </div>

              <template
                v-if="data.hasPart?.length || data.isPartOf?.length"
              >
                <v-card variant="outlined" border="grey thin" class="mb-4">
                  <v-table density="compact">
                    <tbody>
                      <tr
                        v-for="(part, index) in data.hasPart"
                        :key="`hp-${index}`"
                      >
                        <td class="relation-label">Has part</td>
                        <td class="relation-url">
                          <a :href="part.url">{{ part.url }}</a>
                        </td>
                      </tr>
                      <tr
                        v-for="(part, index) in data.isPartOf"
                        :key="`ipo-${index}`"
                      >
                        <td class="relation-label">Is part of</td>
                        <td class="relation-url">
                          <a :href="part.url">{{ part.url }}</a>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </template>

              <cz-field
                scope="#/properties/subjectOf"
                :options="subjectOfOptions"
                label="Subject of"
              />
              <cz-field
                scope="#/properties/relation"
                :options="relationOptions"
                label="Relations"
              />
            </div>

            <!-- Additional metadata (not on landing page, but useful here) -->
            <div class="mb-6 field" id="additional">
              <div
                class="section-heading text-subtitle-1 font-weight-bold text-uppercase mb-3"
              >
                Additional metadata<span class="required-mark">{{
                  requiredMark("#/properties/additionalProperty")
                }}</span>
              </div>
              <cz-field-modal
                scope="#/properties/additionalProperty"
                :options="additionalPropertyOptions"
                :label="`Additional metadata${requiredMark(
                  '#/properties/additionalProperty',
                )}`"
              >
                <template
                  #summary="{ value, errorsByIndex, hasErrors, openEdit }"
                >
                  <div
                    class="modal-summary"
                    :class="{ 'has-errors': hasErrors }"
                    @click="openEdit"
                  >
                    <div
                      v-if="!(value && value.length)"
                      class="text-body-2 text-medium-emphasis font-italic"
                    >
                      Click to add metadata entries
                    </div>
                    <ul v-else class="additional-list">
                      <li
                        v-for="(p, i) in value"
                        :key="i"
                        :class="{ 'has-errors': errorsByIndex[i] }"
                      >
                        <v-icon
                          v-if="errorsByIndex[i]"
                          size="14"
                          color="error"
                          class="mr-1"
                          >mdi-alert-circle</v-icon
                        >
                        <strong>{{ p.name || `Entry ${i + 1}` }}</strong>
                        <span
                          v-if="p.value"
                          class="text-caption text-medium-emphasis ml-2"
                          >{{ p.value }}</span
                        >
                      </li>
                    </ul>
                    <v-icon size="small" class="modal-summary__edit"
                      >mdi-pencil</v-icon
                    >
                  </div>
                </template>
              </cz-field-modal>
            </div>
          </v-container>

          <!-- Sidebar mirrors landing page sidebar positions -->
          <div class="sidebar break-word">
            <div>
              <v-card variant="flat" class="mb-6">
                <v-card-title
                  class="pa-0 pb-2 text-subtitle-2 font-weight-bold text-uppercase"
                  style="letter-spacing: 0.05em; color: #546e7a;"
                >
                  Subject Keywords<span class="required-mark">{{
                    requiredMark("#/properties/keywords")
                  }}</span>
                </v-card-title>
                <cz-field scope="#/properties/keywords" hide-label />
              </v-card>

              <v-card variant="flat" class="mb-6">
                <v-card-title
                  class="pa-0 pb-2 text-subtitle-2 font-weight-bold text-uppercase"
                  style="letter-spacing: 0.05em; color: #546e7a;"
                >
                  License<span class="required-mark">{{
                    requiredMark("#/properties/license")
                  }}</span>
                </v-card-title>
                <cz-field
                  scope="#/properties/license"
                  :options="licenseOptions"
                  hide-label
                />
              </v-card>

              <div class="mb-6">
                <div
                  class="text-subtitle-2 font-weight-bold text-uppercase mb-2"
                  style="letter-spacing: 0.05em; color: #546e7a;"
                >
                  Spatial Coverage<span class="required-mark">{{
                    requiredMark("#/properties/spatialCoverage")
                  }}</span>
                </div>
                <cz-field-modal
                  scope="#/properties/spatialCoverage"
                  :options="spatialCoverageOptions"
                  :label="`Spatial Coverage${requiredMark(
                    '#/properties/spatialCoverage',
                  )}`"
                >
                  <template
                    #summary="{ value, hasErrors, openEdit }"
                  >
                    <v-card
                      variant="outlined"
                      border="grey thin"
                      class="modal-summary modal-summary--card"
                      :class="{ 'has-errors': hasErrors }"
                      @click="openEdit"
                    >
                      <div
                        v-if="hasErrors"
                        class="pa-2 bg-red-lighten-5 text-body-2 d-flex align-center"
                      >
                        <v-icon
                          color="error"
                          size="small"
                          class="mr-2"
                          >mdi-alert-circle</v-icon
                        >
                        Coverage has validation issues — click to fix
                      </div>
                      <cd-spatial-coverage-map
                        v-if="value?.geo"
                        :feature="value.geo"
                      />
                      <v-card-text
                        v-else
                        class="text-body-2 text-medium-emphasis font-italic"
                      >
                        Click to set spatial coverage
                      </v-card-text>
                      <v-divider v-if="value?.name"></v-divider>
                      <v-card-text
                        v-if="value?.name"
                        class="text-body-2 py-2"
                      >
                        {{ value.name }}
                      </v-card-text>
                    </v-card>
                  </template>
                </cz-field-modal>
              </div>

              <div class="mb-6">
                <div
                  class="text-subtitle-2 font-weight-bold text-uppercase mb-2"
                  style="letter-spacing: 0.05em; color: #546e7a;"
                >
                  Temporal Coverage<span class="required-mark">{{
                    requiredMark("#/properties/temporalCoverage")
                  }}</span>
                </div>
                <cz-field
                  scope="#/properties/temporalCoverage"
                  :options="temporalCoverageOptions"
                  hide-label
                />
              </div>

              <!-- Citation was hidden as an input in the old uischema —
                   it's auto-generated. Display as read-only text. -->
              <div v-if="citations.length" id="citation" class="mb-6">
                <div
                  class="text-subtitle-2 font-weight-bold text-uppercase mb-2"
                  style="letter-spacing: 0.05em; color: #546e7a;"
                >
                  How to cite
                </div>
                <div
                  v-for="(citation, index) of citations"
                  :key="index"
                  class="text-body-2 text-medium-emphasis"
                  style="word-break: break-word;"
                >
                  {{ citation }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== SAVE / CANCEL bar at bottom (always visible) ===== -->
        <v-divider class="my-6"></v-divider>
        <div class="d-flex flex-wrap align-center ga-2">
          <v-btn
            v-if="!$vuetify.display.smAndDown"
            variant="text"
            prepend-icon="mdi-arrow-left"
            @click="
              $router.push({ name: 'landing', params: { resourceId } })
            "
          >
            Cancel
          </v-btn>

          <v-spacer></v-spacer>

          <v-menu
            :disabled="!errors.length"
            open-on-hover
            bottom
            left
            offset-y
            transition="fade"
          >
            <template #activator="{ props }">
              <div v-bind="props" class="d-flex">
                <v-badge
                  :model-value="!isValid"
                  bordered
                  color="error"
                  icon="mdi-exclamation-thick"
                  overlap
                >
                  <v-btn
                    color="primary"
                    variant="elevated"
                    prepend-icon="mdi-content-save"
                    @click="submit"
                    :disabled="!isValid || isSubmitting"
                  >
                    {{ isSubmitting ? "Saving Changes..." : "Save Changes" }}
                  </v-btn>
                </v-badge>
              </div>
            </template>

            <v-card>
              <v-card-text>
                <ul class="text-subtitle-1 ml-4">
                  <li v-for="(error, index) of errors" :key="index">
                    <b>{{ error.title }}</b> {{ error.message }}.
                  </li>
                </ul>
              </v-card-text>
            </v-card>
          </v-menu>
        </div>
      </cz-form-composed>
    </template>

    <v-empty-state
      v-if="!wasLoaded && !isFetchingMetadata"
      icon="mdi-cloud-cancel"
      text="Try adjusting your settings."
      title="We couldn't load this resource."
    ></v-empty-state>
  </v-container>
</template>

<script lang="ts">
import { Component, Vue, toNative, Ref } from "vue-facing-decorator";
import {
  CzFormComposed,
  CzField,
  CzFieldModal,
  CzFileExplorer,
  Notifications,
} from "@cznethub/cznet-vue-core";
import type { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";
import {
  S3Client,
  PutObjectCommand,
  DeleteObjectsCommand,
  ListObjectsV2Command,
  HeadObjectCommand,
  DeleteObjectCommand,
  CopyObjectCommand,
} from "@aws-sdk/client-s3";
import { fetchResource, onFileDownload, readRootFolder } from "./shared";
import { createCookieS3Client } from "./cookie-s3-client";
import HsUppy from "./hs-uppy.vue";
import CdSpatialCoverageMap from "@/components/search-results/cd.spatial-coverage-map.vue";
import CdReadmeEditor from "./cd.readme-editor.vue";
import User from "@/models/user.model";
import { contentTypeLabels, contentTypeLogos, S3_PROXY_URL } from "@/constants";
import prettyBytes from "pretty-bytes";

interface FormError {
  title: string;
  message: string;
}

@Component({
  components: {
    CzFormComposed,
    CzField,
    CzFieldModal,
    CzFileExplorer,
    HsUppy,
    CdSpatialCoverageMap,
    CdReadmeEditor,
  },
  name: "App",
})
class App extends Vue {
  resourceId!: string;

  @Ref("fileExplorer") fileExplorer!: InstanceType<typeof CzFileExplorer>;
  @Ref("hsUppyRef") hsUppyRef!: InstanceType<typeof HsUppy>;

  protected get isLoggedIn(): boolean {
    return User.$state.isLoggedIn;
  }

  schema!: any;
  onFileDownload = onFileDownload;

  isValid: boolean = false;
  errors: FormError[] = [];
  data: Record<string, any> = {};

  // Root README name (readme.md/readme.txt, original casing) or null; passed
  // to cd.readme-editor.vue.
  readmeFileName: string | null = null;

  parseDate(value: string | null | undefined): string {
    if (!value) return "";
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString();
  }

  // Returns true when the given top-level scope is listed in the schema's
  // `required` array — used by the template to programmatically append a
  // required-asterisk to section titles instead of hardcoding it. We pass
  // hide-label down to <cz-field>, so the underlying input no longer shows
  // its own `*`; this method lets the consumer surface the asterisk on the
  // template's external title.
  isRequired(scope: string): boolean {
    const required: string[] = this.schema?.required ?? [];
    const m = scope.match(/^#\/properties\/([^/]+)$/);
    if (!m) return false;
    return required.includes(m[1]);
  }

  // Convenience for templates: returns " *" when the scope is required,
  // empty string otherwise. Lets section headings be written as
  // `Abstract{{ requiredMark('#/properties/description') }}`.
  requiredMark(scope: string): string {
    return this.isRequired(scope) ? " *" : "";
  }

  // Same class strings landing-page.vue uses for Details rows so the edit
  // page picks up the identical typography + alignment.
  readonly infoLabelAttr = {
    class:
      "text-caption text-uppercase text-medium-emphasis font-weight-medium dataset-info__label",
  };
  readonly infoValueAttr = {
    class: "text-body-2 dataset-info__value",
  };

  // -----------------------------------------------------------------
  // Per-scope uischema options carried over from the original
  // edit-uischema.json. cz-field forwards each `options` object straight
  // through to the synthetic uischema element it constructs, so directives
  // like `multi: true` (textarea), `detail` (array-item layouts),
  // `showSortButtons`, `collapsed`, `elementLabelProp`, and embedded
  // `MapLayout` blocks render the same as the uischema-driven path.
  // -----------------------------------------------------------------

  readonly descriptionOptions = { multi: true, trim: true };

  readonly spatialCoverageOptions = {
    detail: {
      type: "Object",
      elements: [
        { type: "Control", scope: "#/properties/name" },
        {
          type: "Control",
          scope: "#/properties/geo",
          options: {
            detail: {
              type: "VerticalLayout",
              elements: [
                { type: "Control", scope: "#/properties/@type" },
                {
                  type: "MapLayout",
                  options: {
                    map: {
                      type: "point",
                      north: "latitude",
                      east: "longitude",
                    },
                  },
                  elements: [
                    {
                      type: "HorizontalLayout",
                      elements: [
                        {
                          type: "Control",
                          scope: "#/properties/latitude",
                        },
                        {
                          type: "Control",
                          scope: "#/properties/longitude",
                        },
                      ],
                    },
                  ],
                },
                {
                  type: "Control",
                  scope: "#/properties/box",
                  options: {
                    description:
                      "Bounding box: north east south west (space separated decimal degrees)",
                  },
                },
              ],
            },
          },
        },
      ],
    },
  };

  readonly temporalCoverageOptions = {
    detail: {
      type: "Object",
      elements: [
        {
          type: "HorizontalLayout",
          elements: [
            { type: "Control", scope: "#/properties/startDate" },
            { type: "Control", scope: "#/properties/endDate" },
          ],
        },
      ],
    },
  };

  private readonly personDetailLayout = {
    type: "VerticalLayout",
    elements: [
      { type: "Control", scope: "#/properties/@type" },
      {
        type: "HorizontalLayout",
        elements: [
          { type: "Control", scope: "#/properties/name" },
          { type: "Control", scope: "#/properties/email" },
        ],
      },
      { type: "Control", scope: "#/properties/identifier" },
      {
        type: "HorizontalLayout",
        elements: [
          { type: "Control", scope: "#/properties/url" },
          { type: "Control", scope: "#/properties/address" },
        ],
      },
      {
        type: "Control",
        scope: "#/properties/affiliation",
        options: {
          detail: {
            type: "Object",
            elements: [
              { type: "Control", scope: "#/properties/name" },
              {
                type: "HorizontalLayout",
                elements: [
                  { type: "Control", scope: "#/properties/url" },
                  { type: "Control", scope: "#/properties/address" },
                ],
              },
            ],
          },
        },
      },
    ],
  };

  get creatorOptions() {
    return {
      elementLabelProp: ["name"],
      showSortButtons: true,
      detail: this.personDetailLayout,
    };
  }

  get contributorOptions() {
    return {
      elementLabelProp: ["name"],
      showSortButtons: true,
      collapsed: true,
      detail: this.personDetailLayout,
    };
  }

  readonly fundingOptions = {
    elementLabelProp: ["name"],
    showSortButtons: true,
    detail: {
      type: "VerticalLayout",
      elements: [
        {
          type: "HorizontalLayout",
          elements: [
            { type: "Control", scope: "#/properties/name" },
            {
              type: "Control",
              scope: "#/properties/identifier",
              options: { label: "Award number" },
            },
          ],
        },
        {
          type: "Control",
          scope: "#/properties/description",
          options: { multi: true },
        },
        {
          type: "Control",
          scope: "#/properties/funder",
          options: {
            detail: {
              type: "Object",
              elements: [
                { type: "Control", scope: "#/properties/name" },
                {
                  type: "HorizontalLayout",
                  elements: [
                    { type: "Control", scope: "#/properties/url" },
                    { type: "Control", scope: "#/properties/address" },
                  ],
                },
              ],
            },
          },
        },
      ],
    },
  };

  private readonly nameUrlDescriptionLayout = {
    type: "VerticalLayout",
    elements: [
      {
        type: "HorizontalLayout",
        elements: [
          { type: "Control", scope: "#/properties/name" },
          { type: "Control", scope: "#/properties/url" },
        ],
      },
      {
        type: "Control",
        scope: "#/properties/description",
        options: { multi: true },
      },
    ],
  };

  get relationOptions() {
    return {
      showSortButtons: true,
      collapsed: true,
      elementLabelProp: ["name"],
      detail: this.nameUrlDescriptionLayout,
    };
  }

  get subjectOfOptions() {
    return {
      elementLabelProp: ["name"],
      showSortButtons: true,
      collapsed: true,
      detail: this.nameUrlDescriptionLayout,
    };
  }

  readonly additionalPropertyOptions = {
    showSortButtons: true,
    collapsed: true,
    elementLabelProp: ["name"],
    detail: {
      type: "VerticalLayout",
      elements: [
        {
          type: "HorizontalLayout",
          elements: [
            { type: "Control", scope: "#/properties/name" },
            { type: "Control", scope: "#/properties/propertyID" },
          ],
        },
        { type: "Control", scope: "#/properties/value" },
        {
          type: "Control",
          scope: "#/properties/description",
          options: { multi: true },
        },
        {
          type: "HorizontalLayout",
          elements: [
            { type: "Control", scope: "#/properties/unitCode" },
            { type: "Control", scope: "#/properties/measurementTechnique" },
          ],
        },
        {
          type: "HorizontalLayout",
          elements: [
            { type: "Control", scope: "#/properties/minValue" },
            { type: "Control", scope: "#/properties/maxValue" },
          ],
        },
      ],
    },
  };

  readonly licenseOptions = {
    detail: {
      type: "VerticalLayout",
      elements: [
        { type: "Control", scope: "#/properties/name" },
        { type: "Control", scope: "#/properties/url" },
        {
          type: "Control",
          scope: "#/properties/description",
          options: { multi: true },
        },
      ],
    },
  };

  // Same resource-type-icon mapping the landing page uses, so the visual
  // marker next to the status chip is consistent across both pages.
  get resourceTypeKey(): string {
    return this.data?.additionalType || this.data?.["@type"] || "";
  }

  get resourceTypeLabel(): string {
    const key = this.resourceTypeKey;
    return contentTypeLabels[key] || key;
  }

  get resourceTypeIcon(): string | undefined {
    return contentTypeLogos[this.resourceTypeKey];
  }

  // Total uploaded bytes across the resource's file tree. Same algorithm
  // as landing-page so the "Resource size" cell shows the same number.
  get contentSize(): string | undefined {
    const sumTree = (nodes: any[]): number =>
      nodes.reduce((acc, n) => {
        if (Array.isArray(n?.children)) return acc + sumTree(n.children);
        return acc + (typeof n?.uploadedSize === "number" ? n.uploadedSize : 0);
      }, 0);
    const fromFiles = sumTree(this.rootDirectory.children || []);
    return fromFiles > 0 ? prettyBytes(fromFiles) : undefined;
  }

  // Match landing-page.vue's chip colors so the read-only status chip in
  // the edit header looks identical to its landing-page counterpart.
  getStatusColor(name: string): string {
    switch ((name || "").toLowerCase()) {
      case "draft":
        return "#f0ad4e";
      case "public":
        return "#5cb85c";
      case "published":
        return "#4BB5C1";
      default:
        return "primary";
    }
  }

  // Mirror of landing-page.vue's tocItems / scrollToSection / buildToc.
  // The desktop TOC drawer (rendered via the `toc` named route view) and
  // the inline mobile <v-select> both read from User.$state.toc, so
  // building the same list shape lights up both at once.
  get tocItems() {
    return User.$state.toc;
  }

  get citations(): string[] {
    return this.data?.document?.[0]?.citation ?? [];
  }

  scrollToSection(hash: string | null) {
    if (!hash) return;
    const el = document.querySelector(hash) as HTMLElement | null;
    if (!el) return;

    // Iframe-aware scroll: the host page sets scrolling="no" and auto-sizes
    // the iframe to content, so window.scrollTo here is a no-op. Walk over
    // to the same-origin parent and scroll there instead.
    if (window.parent && window.parent !== window) {
      const frame = window.frameElement as HTMLIFrameElement | null;
      if (frame) {
        try {
          const parentWin = window.parent as Window;
          const iframeTop =
            frame.getBoundingClientRect().top +
            (parentWin.scrollY || parentWin.pageYOffset || 0);
          const elTop = el.getBoundingClientRect().top;
          parentWin.scrollTo({
            top: iframeTop + elTop - 16,
            behavior: "smooth",
          });
          return;
        } catch {
          // Cross-origin — fall through to in-iframe scroll.
        }
      }
    }

    const top = el.getBoundingClientRect().top + window.scrollY - 16;
    window.scrollTo({ top, behavior: "smooth" });
  }

  buildToc() {
    const d = this.data;
    const toc: { text: string; to: string; level?: number }[] = [
      { text: "Overview", to: "#overview" },
      { text: "Details", to: "#details" },
    ];

    if (d?.description !== undefined) {
      toc.push({ text: "Abstract", to: "#description" });
    }

    toc.push({ text: "Content", to: "#content" });
    toc.push({ text: "Files", to: "#fileExplorer", level: 4 });
    toc.push({ text: "Funding", to: "#funding" });

    const hasRelated =
      d?.hasPart?.length ||
      d?.isPartOf?.length ||
      d?.subjectOf?.length ||
      d?.relation?.length;
    if (hasRelated) {
      toc.push({ text: "Related Resources", to: "#related" });
    }

    toc.push({ text: "Additional metadata", to: "#additional" });

    User.$state.toc = toc;
    User.$state.isTocReady = true;
  }

  beforeUnmount() {
    // Clean up the global TOC state so the next route doesn't inherit our
    // section list. Mirrors landing-page.vue's beforeUnmount.
    User.$state.toc = [];
    User.$state.isTocReady = false;
  }

  isLoadingFiles: boolean = true;
  isSubmitting: boolean = false;
  currentPath: string = "";
  folderNameRegex = /^[-()\w\s]*$/;
  isFetchingMetadata = true;
  wasLoaded = true;

  s3Client!: S3Client;
  s3Host: string = S3_PROXY_URL;
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
    isViewMode: false,
    isReadOnly: false,
    isDisabled: false,
  };

  toUpload: any[] = [];
  rootDirectory: Partial<IFolder> = {
    name: "root",
    children: [],
  };
  fileExplorerConfig = {
    isReadOnly: true, // Unused for now
    hasFolders: true,
  };

  startS3Client() {
    this.s3Client = createCookieS3Client(this.s3Host);
  }

  async created() {
    if (!this.resourceId && this.$route?.params?.resourceId) {
      this.resourceId = this.$route.params.resourceId as string;
    }

    if (!this.isLoggedIn) {
      // Refresh login state (e.g. just returned from a HydroShare login
      // redirect). S3 access now rides on the session cookies themselves,
      // so there are no credentials to mint.
      await User.checkLoginStatus();
    }

    if (!this.s3Info.bucket || !this.s3Info.prefix) {
      try {
        const s3info = await User.getResourceS3prefix(this.resourceId);
        if (s3info) {
          this.s3Info = s3info;
          // The edit page works on .hsmetadata/user_metadata.json — the
          // user-editable metadata file. The s3 auth service only authorizes
          // writes under data/contents/ and .hsmetadata/; the landing page's
          // .hsjsonld/dataset_metadata.json is system-generated (hs_extract
          // merges user_metadata.json back into it on save).
          this.s3Info.prefix = `${this.resourceId}/.hsmetadata/`;
        }
      } catch {
        this.isLoadingFiles = false;
        this.isFetchingMetadata = false;
      }
    }

    this.startS3Client();

    // Load the edit schema. Fields marked `readOnly: true` render disabled;
    // the layout itself is composed directly in the template (no uischema).
    /* @ts-ignore */
    this.schema = await import(
      `@/schemas/hydroshare/resource_edit_schema.json`
    );

    this.loadResource();
  }

  async loadResource() {
    this.isFetchingMetadata = true;
    this.isLoadingFiles = true;
    this.wasLoaded = true;

    const resource = await fetchResource(
      this.resourceId,
      this.s3Client,
      this.s3Info.bucket,
      `${this.s3Info.prefix}user_metadata.json`,
    );

    if (resource) {
      this.data = this.normalizeFormData(resource.data);
      // @ts-expect-error The key property is generated when the component is initialized
      this.rootDirectory.children = resource.initialStructure;
      this.buildToc();
      this.detectReadme();
    } else {
      this.wasLoaded = false;
    }
    this.isFetchingMetadata = false;
    this.isLoadingFiles = false;
  }

  // Set readmeFileName (case-insensitive readme.md/readme.txt) and sync the TOC
  // entry. Re-run whenever the file tree changes so the editor stays current.
  detectReadme() {
    const rootFiles = (this.rootDirectory.children || []).filter(
      (c: any) => !Object.prototype.hasOwnProperty.call(c, "children"),
    );
    const mdFile = rootFiles.find(
      (f: any) =>
        typeof f.name === "string" && f.name.toLowerCase() === "readme.md",
    );
    const txtFile = rootFiles.find(
      (f: any) =>
        typeof f.name === "string" && f.name.toLowerCase() === "readme.txt",
    );
    const target: any = mdFile || txtFile;
    this.readmeFileName = target ? target.name : null;
    if (target) {
      this.addReadmeToc();
    } else {
      this.removeReadmeToc();
    }
  }

  // Add the "README" TOC entry under "Files". Idempotent.
  private addReadmeToc() {
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

  // Remove the "README" TOC entry. Idempotent.
  private removeReadmeToc() {
    const toc = User.$state.toc;
    if (!toc) return;
    const idx = toc.findIndex((t) => t.to === "#readme");
    if (idx >= 0) {
      toc.splice(idx, 1);
    }
  }

  // On an editor write, keep the file tree and TOC in sync without a reload.
  onReadmeChange(payload: {
    action: "created" | "saved" | "converted";
    name: string;
    previousName?: string;
    size: number;
  }) {
    const root = this.rootDirectory as any;
    const children: any[] = Array.isArray(root?.children) ? root.children : [];
    this.readmeFileName = payload.name;

    if (payload.action === "created") {
      if (!children.some((c) => c.name === payload.name)) {
        children.push({
          name: payload.name,
          isUploaded: true,
          file: null,
          uploadedSize: payload.size,
          contentKey: `${this.resourceId}/data/contents/${payload.name}`,
        });
      }
      this.addReadmeToc();
    } else if (payload.action === "converted") {
      const node = children.find((c) => c.name === payload.previousName);
      if (node) {
        node.name = payload.name;
        node.uploadedSize = payload.size;
        node.contentKey = `${this.resourceId}/data/contents/${payload.name}`;
      }
    } else {
      const node = children.find((c) => c.name === payload.name);
      if (node) {
        node.uploadedSize = payload.size;
      }
    }
  }

  /**
   * HsUppy emits this once per successfully uploaded file. We own the
   * file-explorer ref directly (vs. HsUppy, which only sees it as a prop and
   * can't react to its delayed binding) so we shape the item the same way
   * readRootFolder does and push it into the right folder. Idempotent — skips
   * if the name already exists in the target folder.
   */
  onUppyFileUploaded(file: any) {
    if (!this.fileExplorer || !file) return;
    const root = this.rootDirectory as any;
    if (!root || !Array.isArray(root.children)) return;

    const folderPath: string | null =
      file?.meta?.existing_path_in_resource || null;
    const targetFolder = this.findExplorerFolder(root, folderPath) || root;

    if (targetFolder.children.some((c: any) => c.name === file.name)) return;
    targetFolder.children.push({
      name: file.name,
      isUploaded: true,
      file: null,
      uploadedSize: file.size,
      contentKey: file?.meta?.dynamic_key,
    });
  }

  private findExplorerFolder(root: any, path: string | null): any | null {
    if (!path) return root;
    const parts = path.split("/").filter(Boolean);
    let current = root;
    for (const segment of parts) {
      const next = (current.children || []).find(
        (c: any) =>
          c &&
          c.name === segment &&
          Object.prototype.hasOwnProperty.call(c, "children"),
      );
      if (!next) return null;
      current = next;
    }
    return current;
  }

  // cz-form's array control calls .map() on the bound value, so any array
  // field the UI schema renders must exist as an array in the data — the
  // schema's `default: []` only seeds AJV validation, not the v-model.
  private normalizeFormData(data: Record<string, any>): Record<string, any> {
    const arrayFields = [
      "keywords",
      "creator",
      "contributor",
      "funding",
      "relation",
      "subjectOf",
      "additionalProperty",
      "citation",
      "identifier",
    ];
    const objectFields = ["spatialCoverage", "temporalCoverage"];
    const normalized = { ...data };
    for (const field of arrayFields) {
      if (!Array.isArray(normalized[field])) {
        normalized[field] = [];
      }
    }
    for (const field of objectFields) {
      if (normalized[field] == null || typeof normalized[field] !== "object") {
        normalized[field] = {};
      }
    }
    // license is now an object schema; coerce legacy URL-string licenses
    // into the {@type, url} shape so the form renders without breaking.
    if (typeof normalized.license === "string") {
      normalized.license = {
        "@type": "CreativeWork",
        url: normalized.license,
      };
    } else if (normalized.license == null) {
      normalized.license = {};
    }
    return normalized;
  }

  async submit() {
    try {
      const key = `${this.s3Info.prefix}user_metadata.json`;
      const content = JSON.stringify(this.data, null, 2);
      const command = new PutObjectCommand({
        Bucket: this.s3Info.bucket,
        Key: key,
        Body: content,
        ContentType: "application/json",
      });
      this.isSubmitting = true;
      await this.s3Client.send(command);

      Notifications.toast({
        title: "Success",
        message: "Metadata uploaded to S3 successfully!",
        type: "success",
      });

      // @ts-ignore
      this.$router.push({
        name: "landing",
        params: { resourceId: this.resourceId },
      });
    } catch (error: any) {
      console.error("Error uploading to S3:", error);
      Notifications.toast({
        title: "Error",
        message: `Failed to upload metadata to S3. Details: ${error.message}`,
        type: "error",
      });
    } finally {
      this.isSubmitting = false;
    }
  }

  async uploadFiles(files: IFile[]): Promise<boolean[]> {
    if (files.length) {
      // Annotate file paths before uploading
      files.forEach((f) => {
        f.isDisabled = true;
        f.path = this.fileExplorer.getPathString(f);
      });
      return this._uploadFiles(files);
    }
    return [];
  }

  private async _uploadFiles(
    itemsToUpload: (IFile | IFolder)[],
  ): Promise<boolean[]> {
    itemsToUpload.forEach((i) => (i.isDisabled = true));
    const filesToUpload = itemsToUpload.filter((i) =>
      Object.prototype.hasOwnProperty.call(i, "file"),
    ) as IFile[];
    const foldersToUpload = itemsToUpload.filter((i) =>
      Object.prototype.hasOwnProperty.call(i, "children"),
    ) as IFolder[];

    // const basePrefix = `${this.resourceId}/data/contents/${this.currentPath}`;

    // compute folder paths
    let folderPaths = foldersToUpload
      .map((f) => f.path)
      .filter((f) => !!f) as string[];

    // unique + sort deeper first
    folderPaths = [...new Set(folderPaths)].sort(
      (a, b) => b.split("/").length - a.split("/").length,
    );

    const that = this;
    let responses: boolean[] = [];
    itemsToUpload.forEach((i) => (i.isDisabled = false));

    if (folderPaths.length) {
      responses = await _createFoldersByDepth(folderPaths, 1);
    } else {
      responses = await _uploadFiles();
    }

    async function _createFoldersByDepth(
      paths: string[],
      depth: number,
    ): Promise<boolean[]> {
      const depthPaths = paths.filter((p) => p.split("/").length === depth);

      const folderCreatePromises = depthPaths.map((path: string) => {
        const rootPrefix = `${that.resourceId}/data/contents/`;
        const folderKey = `${rootPrefix}${path}/`; // Ensure trailing slash for folder marker

        return that.s3Client.send(
          new PutObjectCommand({
            Bucket: that.s3Info.bucket,
            Key: folderKey,
            Body: "",
            ContentType: "application/x-directory",
          }),
        );
      });

      await Promise.allSettled(folderCreatePromises);
      const remaining = paths.filter((p) => p.split("/").length > depth);

      return remaining.length
        ? _createFoldersByDepth(remaining, depth + 1)
        : _uploadFiles();
    }

    async function _uploadFiles(): Promise<boolean[]> {
      const fileUploadPromises = filesToUpload.map(async (file: IFile) => {
        const path = that.fileExplorer.getPathString(file);
        try {
          if (!that.hsUppyRef) {
            throw new Error("HsUppy component not available");
          }

          const uppy = that.hsUppyRef.getUppyInstance();
          if (!uppy) {
            throw new Error("Uppy instance not available");
          }
          uppy.getPlugin("Dashboard")?.openModal();
          const fileId = uppy.addFile({
            name: file.name,
            type: file.file?.type || "application/octet-stream",
            data: file.file,
            meta: {
              bucket_name: that.s3Info.bucket,
              dynamic_key: `${that.s3Info.prefix}${path}`,
            },
          });

          if (!fileId) {
            throw new Error("Failed to add file to Uppy");
          }

          // Since Uppy has autoProceed: true, it will start uploading automatically
          // Wait for the upload to complete for this specific file
          return new Promise<boolean>((resolve) => {
            const successHandler = (successFileId: string, _response: any) => {
              if (successFileId === fileId) {
                uppy.off("upload-success", successHandler);
                uppy.off("upload-error", errorHandler);
                resolve(true);
              }
            };

            const errorHandler = (errorFileId: string, error: any) => {
              if (errorFileId === fileId) {
                uppy.off("upload-success", successHandler);
                uppy.off("upload-error", errorHandler);
                console.error("Upload error for file:", file.name, error);
                resolve(false);
              }
            };

            uppy.on("upload-success", successHandler);
            uppy.on("upload-error", errorHandler);

            // Add timeout as fallback
            setTimeout(() => {
              uppy.off("upload-success", successHandler);
              uppy.off("upload-error", errorHandler);
              console.warn("Upload timeout for file:", file.name);
              resolve(false);
            }, 300000); // 5 minute timeout
          });
        } catch (_e) {
          console.error("Error in file upload:", _e);
          return false;
        }
      });

      const results = await Promise.allSettled(fileUploadPromises);

      filesToUpload.forEach((f, index) => {
        if (results[index].status === "fulfilled" && results[index].value) {
          f.isUploaded = true;
        }
      });

      if (results.some((r) => r.status === "rejected")) {
        Notifications.toast({
          message: "Some of your files failed to upload",
          type: "error",
        });
      }

      return results.map((r) => (r.status === "fulfilled" ? r.value : false));
    }

    return responses;
  }

  async deleteFileOrFolder(item: IFile | IFolder): Promise<boolean> {
    let path = this.fileExplorer.getPathString(item);
    const isFolder = Object.prototype.hasOwnProperty.call(item, "children");
    if (isFolder && !path.endsWith("/")) {
      path += "/";
    }
    const basePrefix = `${this.resourceId}/data/contents/`;
    try {
      if (isFolder) {
        let continuationToken: string | undefined;
        const objectsToDelete: { Key: string }[] = [];

        do {
          const listCommand = new ListObjectsV2Command({
            Bucket: this.s3Info.bucket,
            Prefix: `${basePrefix}${path}`,
            ContinuationToken: continuationToken,
          });
          const listResponse = await this.s3Client.send(listCommand);

          if (listResponse.Contents) {
            listResponse.Contents.forEach((obj) => {
              if (obj.Key) {
                objectsToDelete.push({ Key: obj.Key });
                console.log(`Added to delete: ${obj.Key}`);
              }
            });
          }

          continuationToken = listResponse.NextContinuationToken;
        } while (continuationToken);

        // Add the folder marker key if not already included
        const folderMarkerKey = `${basePrefix}${path}`;
        if (!objectsToDelete.some((obj) => obj.Key === folderMarkerKey)) {
          objectsToDelete.push({ Key: folderMarkerKey });
          console.log(`Added top-level folder marker: ${folderMarkerKey}`);
        }

        const batchSize = 1000;
        if (objectsToDelete.length === 0) {
          console.log(`No objects found to delete for folder: ${path}`);
        } else {
          for (let i = 0; i < objectsToDelete.length; i += batchSize) {
            const batch = objectsToDelete.slice(i, i + batchSize);
            await this.s3Client.send(
              new DeleteObjectsCommand({
                Bucket: this.s3Info.bucket,
                Delete: { Objects: batch },
              }),
            );
            console.log(
              `Deleted batch of ${batch.length} objects:`,
              batch.map((obj) => obj.Key),
            );
          }
        }

        // Verify deletion
        const verifyCommand = new ListObjectsV2Command({
          Bucket: this.s3Info.bucket,
          Prefix: `${basePrefix}${path}`,
        });
        const verifyResponse = await this.s3Client.send(verifyCommand);
        if (verifyResponse.Contents && verifyResponse.Contents.length > 0) {
          console.warn(
            `Objects still exist after deletion for ${path}:`,
            verifyResponse.Contents.map((obj) => obj.Key),
          );
        } else {
          console.log(`Verified: No objects remain under ${path}`);
        }

        // Check parent listing for CommonPrefixes
        const listParentCommand = new ListObjectsV2Command({
          Bucket: this.s3Info.bucket,
          Prefix: `${this.resourceId}/data/contents/`,
          Delimiter: "/",
        });
        const parentResponse = await this.s3Client.send(listParentCommand);
        if (
          parentResponse.CommonPrefixes &&
          parentResponse.CommonPrefixes.some(
            (p) => p.Prefix === `${basePrefix}${path}`,
          )
        ) {
          console.warn(
            `Folder ${path} still appears in CommonPrefixes after deletion`,
          );
        } else {
          console.log(`Verified: ${path} no longer in CommonPrefixes`);
        }
      } else {
        await this.s3Client.send(
          new DeleteObjectsCommand({
            Bucket: this.s3Info.bucket,
            Delete: { Objects: [{ Key: `${basePrefix}${path}` }] },
          }),
        );
        console.log(`Deleted file: ${basePrefix}${path}`);
      }

      // Deleting the README clears the editor + TOC.
      if (!isFolder && path === this.readmeFileName) {
        this.readmeFileName = null;
        this.removeReadmeToc();
      }

      Notifications.toast({
        title: "Success",
        message: `${isFolder ? "Folder" : "File"} deleted successfully!`,
        type: "success",
      });
      return true;
    } catch (error: any) {
      console.error(`Error deleting ${isFolder ? "folder" : "file"}:`, error);
      Notifications.toast({
        title: "Error",
        message: `Failed to delete ${isFolder ? "folder" : "file"}: ${error.message}`,
        type: "error",
      });
      return false;
    }
  }

  async renameFileOrFolder(
    item: IFile | IFolder,
    newNameOrPath: string,
  ): Promise<void> {
    const isFolder = Object.prototype.hasOwnProperty.call(item, "children");

    // s3Info.prefix is set to `<id>/.hsjsonld/` for metadata fetching — the
    // file tree lives under `<id>/data/contents/`. Use the contents path
    // explicitly so copy/head/list/delete operations target the actual
    // objects (matches what deleteFileOrFolder already does).
    const basePrefix = `${this.resourceId}/data/contents/`;

    // --- in-scope utils ---
    const normalizeRel = (p: string) => {
      let s = (p || "").trim();
      s = s
        .replace(/^\/+/, "")
        .replace(/\/{2,}/g, "/")
        .replace(/^\.\/+/, "")
        .replace(/\/+$/g, "");
      const parts: string[] = [];
      s.split("/").forEach((seg) => {
        if (!seg || seg === ".") return;
        if (seg === "..") parts.pop();
        else parts.push(seg);
      });
      return parts.join("/");
    };
    const asFolder = (p: string) => (p.endsWith("/") ? p : p + "/");
    const splitParentBase = (rel: string, folder: boolean) => {
      const clean = normalizeRel(folder ? rel.replace(/\/+$/, "") : rel);
      const parts = clean.split("/").filter(Boolean);
      const base = parts.pop() || "";
      const parent = parts.join("/");
      return { parent, base };
    };
    const sameRel = (a: string, b: string) =>
      normalizeRel(a.replace(/\/+$/, "")) ===
      normalizeRel(b.replace(/\/+$/, ""));
    const encodeCopySourceKey = (key: string) =>
      encodeURIComponent(key).replace(/%2F/g, "/");

    // --- resolve old/new relative paths ---
    let oldRel = this.fileExplorer.getPathString(item);
    if (isFolder && !oldRel.endsWith("/")) oldRel += "/";
    const { parent: oldParent, base: oldBase } = splitParentBase(
      oldRel,
      isFolder,
    );

    const raw = (newNameOrPath || "").trim();
    const isRootExplicit = raw === "/" || raw === "";
    const hasSlash = raw.includes("/");

    let newRel: string;

    if (isRootExplicit) {
      // explicit move to root
      newRel = isFolder ? asFolder(oldBase) : oldBase;
    } else if (!hasSlash) {
      // **Key change**:
      // If no slash AND same basename AND item has a parent -> interpret as MOVE TO ROOT
      if (oldParent && raw === oldBase) {
        newRel = isFolder ? asFolder(oldBase) : oldBase; // move to root, keep name
      } else {
        // true rename: keep same parent
        newRel = oldParent ? `${oldParent}/${raw}` : raw;
        if (isFolder) newRel = asFolder(newRel);
      }
    } else {
      // path includes "/": could be "drop ON folder" or full path
      let candidate = normalizeRel(raw);
      // If it ends with "/" or a folder marker exists, move INTO it and keep basename
      let treatAsFolder = raw.endsWith("/");
      if (!treatAsFolder) {
        try {
          await this.s3Client.send(
            new HeadObjectCommand({
              Bucket: this.s3Info.bucket,
              Key: `${basePrefix}${asFolder(candidate)}`,
            }),
          );
          treatAsFolder = true;
        } catch {
          /* not a marker */
        }
      }
      newRel = treatAsFolder
        ? isFolder
          ? asFolder(`${candidate}/${oldBase}`)
          : `${candidate}/${oldBase}`
        : isFolder
          ? asFolder(candidate)
          : candidate;
    }

    const oldKey = `${basePrefix}${oldRel}`;
    const newKey = `${basePrefix}${newRel}`;

    // self / no-op guard
    if (sameRel(oldRel, newRel)) {
      Notifications.toast({
        title: "No change",
        message: "Item is already there.",
        type: "info",
      });
      return;
    }

    // --- do the move/rename safely ---
    try {
      // ensure destination parent for files
      if (!isFolder) {
        const { parent: destParent } = splitParentBase(newRel, false);
        if (destParent) {
          const destFolderKey = `${basePrefix}${asFolder(destParent)}`;
          try {
            await this.s3Client.send(
              new HeadObjectCommand({
                Bucket: this.s3Info.bucket,
                Key: destFolderKey,
              }),
            );
          } catch (err: any) {
            if (
              err?.name === "NotFound" ||
              err?.$metadata?.httpStatusCode === 404
            ) {
              await this.s3Client.send(
                new PutObjectCommand({
                  Bucket: this.s3Info.bucket,
                  Key: destFolderKey,
                  Body: "",
                  ContentType: "application/x-directory",
                }),
              );
            } else {
              throw err;
            }
          }
        }
      }

      // copy (skip copy-to-self; encode CopySource)
      if (isFolder) {
        let token: string | undefined;
        const jobs: Promise<any>[] = [];
        do {
          const list = await this.s3Client.send(
            new ListObjectsV2Command({
              Bucket: this.s3Info.bucket,
              Prefix: oldKey,
              ContinuationToken: token,
            }),
          );
          (list.Contents || []).forEach((obj) => {
            if (!obj.Key) return;
            const rel = obj.Key.replace(oldKey, "");
            const dest = `${newKey}${rel}`;
            if (dest === obj.Key) return; // prevent illegal self-copy
            jobs.push(
              this.s3Client.send(
                new CopyObjectCommand({
                  Bucket: this.s3Info.bucket,
                  CopySource: `${this.s3Info.bucket}/${encodeCopySourceKey(obj.Key)}`,
                  Key: dest,
                }),
              ),
            );
          });
          token = list.NextContinuationToken;
        } while (token);
        await Promise.allSettled(jobs);
      } else {
        if (oldKey !== newKey) {
          await this.s3Client.send(
            new CopyObjectCommand({
              Bucket: this.s3Info.bucket,
              CopySource: `${this.s3Info.bucket}/${encodeCopySourceKey(oldKey)}`,
              Key: newKey,
            }),
          );
        }
      }

      // verify destination
      if (isFolder) {
        const verify = await this.s3Client.send(
          new ListObjectsV2Command({
            Bucket: this.s3Info.bucket,
            Prefix: newKey,
            MaxKeys: 1,
          }),
        );
        if (!verify.Contents || verify.Contents.length === 0)
          throw new Error(`Verification failed: nothing at ${newKey}`);
      } else {
        await this.s3Client.send(
          new HeadObjectCommand({ Bucket: this.s3Info.bucket, Key: newKey }),
        );
      }

      // delete originals (and clean ancestor markers)
      const cleanupEmptyAncestors = async (startParentRel: string) => {
        let cur = startParentRel;
        while (cur) {
          const markerKey = `${basePrefix}${asFolder(cur)}`;
          const probe = await this.s3Client.send(
            new ListObjectsV2Command({
              Bucket: this.s3Info.bucket,
              Prefix: markerKey,
              MaxKeys: 2,
            }),
          );
          const hasNonMarker = !!(
            probe.Contents &&
            probe.Contents.some((o) => o.Key && o.Key !== markerKey)
          );
          if (!hasNonMarker) {
            try {
              await this.s3Client.send(
                new DeleteObjectCommand({
                  Bucket: this.s3Info.bucket,
                  Key: markerKey,
                }),
              );
            } catch {}
            cur = cur.split("/").slice(0, -1).join("/");
          } else break;
        }
      };

      if (isFolder) {
        let token: string | undefined;
        do {
          const list = await this.s3Client.send(
            new ListObjectsV2Command({
              Bucket: this.s3Info.bucket,
              Prefix: oldKey,
              ContinuationToken: token,
            }),
          );
          const objs = (list.Contents || [])
            .map((o) => ({ Key: o.Key! }))
            .filter((o) => !o.Key!.startsWith(newKey));
          if (objs.length) {
            await this.s3Client.send(
              new DeleteObjectsCommand({
                Bucket: this.s3Info.bucket,
                Delete: { Objects: objs },
              }),
            );
          }
          token = list.NextContinuationToken;
        } while (token);
        try {
          await this.s3Client.send(
            new DeleteObjectCommand({
              Bucket: this.s3Info.bucket,
              Key: oldKey,
            }),
          );
        } catch {}
        if (oldParent) await cleanupEmptyAncestors(oldParent);
      } else {
        await this.s3Client.send(
          new DeleteObjectsCommand({
            Bucket: this.s3Info.bucket,
            Delete: { Objects: [{ Key: oldKey }] },
          }),
        );
        if (oldParent) await cleanupEmptyAncestors(oldParent);
      }

      // refresh
      const root = `${this.resourceId}/data/contents/`;
      // @ts-expect-error The key property is generated when the component is initialized
      this.rootDirectory.children = await readRootFolder(
        root,
        this.s3Client,
        this.s3Info.bucket,
      );

      // Reflect a README rename in the editor.
      this.detectReadme();

      Notifications.toast({
        title: "Success",
        message: `${hasSlash || isRootExplicit ? "Moved" : "Renamed"} ${isFolder ? "folder" : "file"} successfully!`,
        type: "success",
      });
    } catch (error: any) {
      console.error("Rename/move failed:", error);
      Notifications.toast({
        title: "Error",
        message: `Failed to ${hasSlash || isRootExplicit ? "move" : "rename"} ${isFolder ? "folder" : "file"}: ${error?.message || error}`,
        type: "error",
      });
    }
  }
}
export default toNative(App);
</script>

<style lang="scss" scoped>
// Mirror the landing page section styling so the edit view reads as the
// same page with in-place inputs swapped for the read-only text.
.section-heading {
  color: #4bb5c1;
  letter-spacing: 0.05em;
  padding-bottom: 0.4rem;
  margin-bottom: 0.75rem;
  border-bottom: 2px solid #e0e0e0;
}

.details-card {
  border-color: rgba(0, 0, 0, 0.08) !important;
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

.page-content {
  flex-grow: 1;
  max-width: 100%;
  min-width: 0;
}

// Match landing-page's dataset-info grid for Details rows: two columns
// per v-col (label | value) with the same gaps and alignment so the edit
// page renders the same way the landing page does for every row that's
// read-only, and the editable rows (Authors, Contributors) fit cleanly
// in the value cell via the modal-summary--inline variant below.
.dataset-info {
  display: grid;
  grid-template-columns: max-content 1fr;
  column-gap: 1.5rem;
  row-gap: 0.5rem;
  justify-content: start;
  align-items: baseline;
  align-content: baseline;
}

.dataset-info__label {
  letter-spacing: 0.05em;
  line-height: 1.4;
}

.dataset-info__value {
  line-height: 1.4;
}

// Inline variant of the modal-summary used inside the dataset-info grid:
// no border/padding so it sits flush with the surrounding read-only text,
// edit affordance still appears on hover.
.modal-summary--inline {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0;
  border: none;

  &:hover {
    background-color: transparent;
    border-color: transparent;
  }

  &.has-errors {
    background-color: transparent;
    border: none;
  }

  .modal-summary__edit {
    position: static;
    margin-left: 0.25rem;
  }
}

// Same icon size landing-page uses next to its status chip.
.resource-type-icon {
  height: 32px;
  width: 32px;
}

// Required-asterisk on programmatic section titles. Matches Vuetify's
// in-input asterisk styling so the visual cue reads the same whether
// the asterisk sits on a floating label or on a consumer-rendered title.
.required-mark {
  color: rgb(var(--v-theme-error));
  margin-left: 0.125rem;
}

// Modal-summary chrome: complex fields (authors, contributors, spatial,
// funding, additional metadata) render a landing-page-style read-only
// preview that the user clicks to open the full editor in a v-dialog.
// Hover/keyboard affordance lives here so it's consistent across all
// summaries, and a red left rule plus the inline alert icons surface
// validation errors without requiring the user to open the modal.
.modal-summary {
  position: relative;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 0.5rem 2rem 0.5rem 0.625rem;
  cursor: pointer;
  transition:
    background-color 0.12s ease,
    border-color 0.12s ease;

  &:hover {
    background-color: rgba(0, 0, 0, 0.03);
    border-color: rgba(0, 0, 0, 0.12);
  }

  &.has-errors {
    border-color: rgb(var(--v-theme-error));
    background-color: rgba(244, 67, 54, 0.04);
  }

  // The pencil icon hints "click to edit". Sits at the top-right of the
  // summary box; only visible on hover/focus to keep the chip list quiet.
  &__edit {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    opacity: 0;
    transition: opacity 0.12s ease;
    color: rgba(0, 0, 0, 0.4);
  }

  &:hover &__edit,
  &:focus-within &__edit {
    opacity: 1;
  }
}

// Variant: when the summary IS the card (e.g. spatial coverage's map
// preview), we don't want the wrapper padding to push the map away from
// the card edge.
.modal-summary--card {
  padding: 0;

  &.has-errors {
    // The internal alert banner already provides the error coloring; tone
    // down the outer border so it doesn't double up.
    background-color: transparent;
  }
}

.funding-list,
.additional-list {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    padding: 0.25rem 0;
    font-size: 0.875rem;

    &.has-errors {
      color: rgb(var(--v-theme-error));
    }
  }
}

// Mobile TOC select — copies landing-page's behavior of only rendering
// below 1100px, exactly the cutoff at which the desktop <Toc> drawer
// hides itself via toc.vue's own media query.
.mobile-toc {
  background: rgb(var(--v-theme-surface));

  @media (min-width: 1100px) {
    display: none !important;
  }
}

// Related Resources table — mirror landing-page's wrap-long-URLs behavior
// so the read-only rows in the edit page look identical.
.v-table {
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
</style>
