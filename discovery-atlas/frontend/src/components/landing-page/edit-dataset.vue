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
        <!-- ===== ALERTS (same source as the landing page) ===== -->
        <div v-if="showMissingMetadataAlert" class="mb-4">
          <v-alert
            type="warning"
            variant="tonal"
            density="comfortable"
            closable
            @click:close="dismissedAlerts.missing = true"
          >
            <div v-if="alerts.missingMetadata && alerts.missingMetadata.length">
              We recommend completing these before making your
              {{ alerts.displayName || "resource" }} public or discoverable:
              <ul class="ml-4 mt-1">
                <li v-for="el in alerts.missingMetadata" :key="el">{{ el }}</li>
                <li v-if="alerts.isUntitled">Title: needs to be changed</li>
                <li
                  v-for="el in alerts.recommendedMissing || []"
                  :key="`r-${el}`"
                >
                  {{ el }}
                </li>
              </ul>
            </div>
            <div v-if="alerts.hasRequiredContentFiles === false" class="mt-2">
              You must
              <template
                v-if="alerts.missingMetadata && alerts.missingMetadata.length"
                >also</template
              >
              add content files to your
              {{ alerts.displayName || "resource" }} before it can be
              published, public, or discoverable.
            </div>
          </v-alert>
        </div>

        <div v-if="showReplacedByAlert" class="mb-4">
          <v-alert
            type="info"
            variant="tonal"
            density="comfortable"
            closable
            @click:close="dismissedAlerts.replacedBy = true"
          >
            A newer version of this resource
            <a
              :href="alerts.isReplacedBy || undefined"
              target="_blank"
              rel="noopener"
              >is available</a
            >
            that replaces this version.
          </v-alert>
        </div>

        <div v-if="showVersionOfAlert" class="mb-4">
          <v-alert
            type="info"
            variant="tonal"
            density="comfortable"
            closable
            @click:close="dismissedAlerts.versionOf = true"
          >
            An older version of this resource
            <a
              :href="alerts.isVersionOf || undefined"
              target="_blank"
              rel="noopener"
              >is available</a
            >.
          </v-alert>
        </div>

        <div v-if="showPublishedAlert" class="mb-4">
          <v-alert type="info" variant="tonal" density="comfortable">
            This resource is published. Metadata changes to a published
            resource may require review.
          </v-alert>
        </div>

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

            <!-- Save is mirrored here as well as at the foot of the form:
                 the page can run to several thousand px inside an iframe the
                 host sets to scrolling="no", so reaching the bottom bar means
                 scrolling the PARENT window all the way down. On narrow
                 screens the wrap drops this pair onto its own line. -->
            <div class="d-flex flex-wrap align-center ga-2 ml-auto">
              <v-btn
                size="small"
                variant="outlined"
                prepend-icon="mdi-arrow-left"
                @click="leaveToLanding"
                >Back</v-btn
              >
              <cd-save-button
                :errors="errors"
                :is-valid="isValid"
                :is-submitting="isSubmitting"
                label="Save"
                busy-label="Saving..."
                size="small"
                variant="flat"
                @click="submit"
              />
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
        <div class="d-flex flex-column flex-lg-row mt-6 single-col-layout">
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
                            role="button"
                            tabindex="0"
                            aria-label="Edit authors"
                            @click="openEdit"
                            @keydown.enter.prevent="openEdit"
                            @keydown.space.prevent="openEdit"
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
                                {{ person?.name || `Author ${Number(i) + 1}` }}
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
                            role="button"
                            tabindex="0"
                            aria-label="Edit contributors"
                            @click="openEdit"
                            @keydown.enter.prevent="openEdit"
                            @keydown.space.prevent="openEdit"
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
                                {{ person?.name || `Contributor ${Number(i) + 1}` }}
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

              <!-- Legacy: baseresource.html shows this in edit mode when the
                   resource accepts uploads and is neither published nor
                   pending review (superusers excepted). -->
              <v-alert
                v-if="!(alerts.isPublished || alerts.reviewPending)"
                type="info"
                variant="tonal"
                density="compact"
                closable
                class="mb-4 text-body-2"
              >
                Upload a <code>readme.md</code> or <code>readme.txt</code> at
                the root of your resource and it will be rendered on the page
                automatically. Markdown is supported in <code>readme.md</code>.
                <a
                  href="https://daringfireball.net/projects/markdown/basics"
                  target="_blank"
                  rel="noopener"
                  >Learn more about Markdown</a
                >.
              </v-alert>

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
                  :canDownloadItem="(item: IFile | IFolder) => !isFolder(item)"
                  :download-zipped="(item: IFile | IFolder) => onZippedDownload(item, resourceId)"
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
                @update:dirty="readmeDirty = $event"
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
              <!-- Edited in place: this column is ~650px, which comfortably
                   fits the grant form, and Related Resources directly below
                   is already inline. A modal here was chrome for its own
                   sake. Modals are reserved for the cramped contexts — the
                   Details card cells and the 22rem sidebar. -->
              <cz-field
                scope="#/properties/funding"
                :options="fundingOptions"
                hide-label
              />
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
              <!-- Inline, same reasoning as Funding above. -->
              <cz-field
                scope="#/properties/additionalProperty"
                :options="additionalPropertyOptions"
                hide-label
              />
            </div>
          </v-container>

          <!-- Sidebar mirrors landing page sidebar positions -->
          <div class="sidebar break-word">
            <div>
              <!-- Plain divs, not v-card: the cards were purely decorative
                   (copied from the read-only landing page) but the library
                   collapses control margins differently inside a .v-card, so
                   these two sections silently lost the spacing the others
                   had. -->
              <div id="subject" class="mb-6">
                <div class="sidebar-heading">
                  Subject Keywords<span class="required-mark">{{
                    requiredMark("#/properties/keywords")
                  }}</span>
                </div>
                <cz-field scope="#/properties/keywords" hide-label />

                <!-- Legacy: subject.html gates this on `not cm.raccess.published`
                     and edit mode. A published resource can't be made private,
                     so the warning doesn't apply there. -->
                <v-alert
                  v-if="!alerts.isPublished"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mt-2 text-body-2"
                >
                  Deleting all keywords will set the resource sharing status to
                  <strong>private</strong>.
                </v-alert>
              </div>

              <div id="spatial" class="mb-6">
                <div class="sidebar-heading">
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
                    <!-- The click target is deliberately NOT the whole card:
                         Leaflet doesn't stop click propagation, so panning
                         the preview map ended every drag by opening the
                         modal. Editing is an explicit button instead. -->
                    <v-card
                      variant="outlined"
                      border="grey thin"
                      class="modal-summary modal-summary--card"
                      :class="{ 'has-errors': hasErrors }"
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
                        Coverage has validation issues
                      </div>
                      <cd-spatial-coverage-map
                        v-if="value?.geo"
                        :feature="value.geo"
                      />
                      <v-card-text
                        v-else
                        class="text-body-2 text-medium-emphasis font-italic pb-0"
                      >
                        No spatial coverage set
                      </v-card-text>
                      <v-divider></v-divider>
                      <div class="d-flex align-center ga-2 px-3 py-2">
                        <span
                          v-if="value?.name"
                          class="text-body-2 text-truncate flex-grow-1"
                          >{{ value.name }}</span
                        >
                        <v-spacer v-else />
                        <v-btn
                          v-if="hasSpatialCoverage"
                          size="small"
                          variant="text"
                          color="error"
                          prepend-icon="mdi-close"
                          @click="clearSpatialCoverage"
                          >Clear</v-btn
                        >
                        <v-btn
                          size="small"
                          variant="text"
                          prepend-icon="mdi-pencil"
                          @click="openEdit"
                          >Edit</v-btn
                        >
                      </div>
                    </v-card>
                  </template>
                </cz-field-modal>
              </div>

              <div id="temporal" class="mb-6 temporal-coverage">
                <div class="sidebar-heading">
                  Temporal Coverage<span class="required-mark">{{
                    requiredMark("#/properties/temporalCoverage")
                  }}</span>
                </div>
                <!-- The landing page uses a v-timeline here, but it reads as
                     a motif around two lines of static text. Wrapping *inputs*
                     in it spent ~62px of a 352px sidebar on the dot rail and
                     truncated the date fields, so edit mode uses plain
                     labelled fields with the same calendar cue. -->
                <v-card variant="outlined" border="grey thin">
                  <v-card-text class="py-3">
                    <div class="d-flex align-center ga-2 mb-1">
                      <v-icon size="16" color="primary">mdi-calendar</v-icon>
                      <span class="text-body-2 font-weight-bold"
                        >Start date<span class="required-mark">*</span></span
                      >
                    </div>
                    <cz-field
                      scope="#/properties/temporalCoverage/properties/startDate"
                      hide-label
                    />

                    <div class="d-flex align-center ga-2 mb-1 mt-3">
                      <v-icon size="16" color="orange-darken-2"
                        >mdi-calendar</v-icon
                      >
                      <span class="text-body-2 font-weight-bold">End date</span>
                    </div>
                    <cz-field
                      scope="#/properties/temporalCoverage/properties/endDate"
                      hide-label
                    />

                    <div v-if="hasTemporalCoverage" class="d-flex mt-2">
                      <v-spacer />
                      <v-btn
                        size="small"
                        variant="text"
                        color="error"
                        prepend-icon="mdi-close"
                        @click="clearTemporalCoverage"
                        >Clear</v-btn
                      >
                    </div>
                  </v-card-text>
                </v-card>
              </div>

              <!-- Citation was hidden as an input in the old uischema —
                   it's auto-generated. Display as read-only text. -->
              <div v-if="citations.length" id="citation" class="mb-6">
                <div class="sidebar-heading">
                  How to cite
                </div>
                <div
                  v-for="(citation, index) of citations"
                  :key="index"
                  class="citation-card"
                >
                  <div class="citation-text">{{ citation }}</div>
                  <div class="citation-actions">
                    <v-btn
                      class="citation-copy"
                      size="small"
                      variant="tonal"
                      color="accent"
                      :prepend-icon="copiedCitation === index ? 'mdi-check' : 'mdi-content-copy'"
                      @click="onCopyCitation(citation, index)"
                    >{{ copiedCitation === index ? "Copied" : "Copy citation" }}</v-btn>
                  </div>
                </div>

                <div v-if="!isPublished" class="citation-note">
                  <v-icon class="citation-note__icon" size="16">mdi-information-outline</v-icon>
                  <div>
                    When permanently published, this resource will have a formal Digital
                    Object Identifier (DOI) and will be accessible at the following URL:
                    <a :href="potentialDoiUrl" target="_blank" rel="noopener">{{ potentialDoiUrl }}</a>.
                    When you are ready to permanently publish, click the Publish button at
                    the top of the page to request your DOI. Reminder: Once you have published
                    your resource, modifications to Title, Authors, or Content files will
                    require a new version of the resource.
                  </div>
                </div>
              </div>

              <div id="license" class="mb-6">
                <div class="sidebar-heading">
                  License<span class="required-mark">{{
                    requiredMark("#/properties/license")
                  }}</span>
                </div>
                <cz-field
                  scope="#/properties/license"
                  :options="licenseOptions"
                  hide-label
                />
              </div>
            </div>
          </div>
        </div>

        <!-- ===== SAVE / CANCEL bar at bottom (always visible) ===== -->
        <v-divider class="my-6"></v-divider>
        <!-- Same order and treatment as the header pair, so the two action
             groups read as one control the user can reach from either end of
             the page rather than two different ones. -->
        <div class="d-flex flex-wrap align-center ga-2">
          <v-spacer></v-spacer>

          <v-btn
            variant="outlined"
            prepend-icon="mdi-arrow-left"
            @click="leaveToLanding"
          >
            Back
          </v-btn>

          <cd-save-button
            :errors="errors"
            :is-valid="isValid"
            :is-submitting="isSubmitting"
            label="Save"
            busy-label="Saving..."
            @click="submit"
          />
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

<script setup lang="ts">
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
import {
  fetchResource,
  getStatusColor,
  onFileDownload,
  onZippedDownload,
  parseDate,
  readRootFolder,
} from "./shared";
import { isFolder } from "./zip-download";
import { createCookieS3Client } from "./cookie-s3-client";
import HsUppy from "./hs-uppy.vue";
import CdSpatialCoverageMap from "@/components/search-results/cd.spatial-coverage-map.vue";
import CdReadmeEditor from "./cd.readme-editor.vue";
import CdSaveButton from "./cd.save-button.vue";
import User from "@/models/user.model";
import { onBeforeRouteLeave, useRoute, useRouter } from "vue-router";
import { contentTypeLabels, contentTypeLogos, S3_PROXY_URL } from "@/constants";
import prettyBytes from "pretty-bytes";

interface FormError {
  title: string;
  message: string;
}

const route = useRoute();
const router = useRouter();

const fileExplorer = useTemplateRef<InstanceType<typeof CzFileExplorer>>("fileExplorer");
const hsUppyRef = useTemplateRef<InstanceType<typeof HsUppy>>("hsUppyRef");

const resourceId = ref<string>("");

const isLoggedIn = computed<boolean>(() => User.$state.isLoggedIn);

const schema = ref<any>();

const isValid = ref(false);
const errors = ref<FormError[]>([]);
const data = ref<Record<string, any>>({});

// Root README name (readme.md/readme.txt, original casing) or null; passed
// to cd.readme-editor.vue.
const readmeFileName = ref<string | null>(null);

// Returns true when the given top-level scope is listed in the schema's
// `required` array — used by the template to programmatically append a
// required-asterisk to section titles instead of hardcoding it. We pass
// hide-label down to <cz-field>, so the underlying input no longer shows
// its own `*`; this method lets the consumer surface the asterisk on the
// template's external title.
function isRequired(scope: string): boolean {
  const required: string[] = schema.value?.required ?? [];
  const m = scope.match(/^#\/properties\/([^/]+)$/);
  if (!m) return false;
  return required.includes(m[1]);
}

// Convenience for templates: returns " *" when the scope is required,
// empty string otherwise. Lets section headings be written as
// `Abstract{{ requiredMark('#/properties/description') }}`.
function requiredMark(scope: string): string {
  return isRequired(scope) ? " *" : "";
}

// Same class strings landing-page.vue uses for Details rows so the edit
// page picks up the identical typography + alignment.
const infoLabelAttr = {
  class:
    "text-caption text-uppercase text-medium-emphasis font-weight-medium dataset-info__label",
};
const infoValueAttr = {
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

// Secondary free-text fields inside array rows. Vuetify's default 5 rows made
// a one-line note ~150px tall; grow from 2 instead.
const compactTextarea = {
  multi: true,
  vuetify: { "v-textarea": { rows: 2, "auto-grow": true } },
};

// HydroShare abstracts routinely run several hundred words; the default 5
// rows meant editing inside a small scrolling box.
const descriptionOptions = {
  multi: true,
  trim: true,
  vuetify: {
    "v-textarea": { "auto-grow": true, rows: 6, "max-rows": 24 },
  },
};

// `geo` is anyOf[GeoCoordinates, GeoShape]. AnyOfRenderer indexes
// `options.detail` by branch, so this must be an index-keyed map — a single
// layout object gets applied to BOTH branches, which is why the point tab
// used to render a stray "Box" field and the box tab rendered "No applicable
// renderer found" where lat/long don't resolve. Keying per branch also lets
// the box tab ask MapLayout for its rectangle draw control.
const spatialCoverageOptions = {
  detail: {
    type: "Object",
    elements: [
      { type: "Control", scope: "#/properties/name" },
      {
        type: "Control",
        scope: "#/properties/geo",
        options: {
          detail: {
            0: {
              type: "VerticalLayout",
              options: { label: "Point" },
              elements: [
                {
                  type: "MapLayout",
                  options: {
                    map: { type: "point", north: "latitude", east: "longitude" },
                  },
                  elements: [
                    {
                      type: "HorizontalLayout",
                      elements: [
                        { type: "Control", scope: "#/properties/latitude" },
                        { type: "Control", scope: "#/properties/longitude" },
                      ],
                    },
                  ],
                },
              ],
            },
            1: {
              type: "VerticalLayout",
              options: { label: "Bounding box" },
              elements: [
                {
                  type: "MapLayout",
                  // `format: GeoShape` selects the single "n e s w" string
                  // code path; without it MapLayout looks for northlimit/
                  // eastlimit/... which this schema doesn't have.
                  options: {
                    map: { type: "box", format: "GeoShape", box: "box" },
                  },
                  elements: [
                    { type: "Control", scope: "#/properties/box" },
                  ],
                },
              ],
            },
          },
        },
      },
    ],
  },
};

// `@type` is a const discriminator, not user input — rendering it dispatches
// to AnyOfRenderer (the item schema is anyOf Person/Organization), whose
// VTabs throws and takes the whole dialog down. `url`/`address` don't exist
// on Creator/Contributor either; they only resolved via the Organization
// branch, so they showed organization copy under a person's name.
const personDetailLayout = {
  type: "VerticalLayout",
  elements: [
    {
      type: "HorizontalLayout",
      elements: [
        { type: "Control", scope: "#/properties/name" },
        { type: "Control", scope: "#/properties/email" },
      ],
    },
    // `label` belongs on the element, not in `options` — computeLabel reads
    // uischema.label; options.label is only consulted for combinator tabs.
    {
      type: "Control",
      scope: "#/properties/identifier",
      label: "ORCID iD",
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

const creatorOptions = computed(() => ({
  elementLabelProp: ["name"],
  childLabelProp: "name",
  showSortButtons: true,
  collapsed: true,
  detail: personDetailLayout,
}));

const contributorOptions = computed(() => ({
  elementLabelProp: ["name"],
  childLabelProp: "name",
  showSortButtons: true,
  collapsed: true,
  detail: personDetailLayout,
}));

const fundingOptions = {
  itemNoun: "funding source",
  description: "Grants or awards that funded this work.",
  elementLabelProp: ["name"],
  // Without childLabelProp the delete prompt falls back to the first string
  // property — `@type` — so every confirmation read "Delete Grant?".
  childLabelProp: "name",
  showSortButtons: true,
  collapsed: true,
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
        options: compactTextarea,
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

const nameUrlDescriptionLayout = {
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
      options: compactTextarea,
    },
  ],
};

const relationOptions = computed(() => ({
  itemNoun: "related resource",
  description: "Other resources related to this one.",
  showSortButtons: true,
  collapsed: true,
  elementLabelProp: ["name"],
  childLabelProp: "name",
  detail: nameUrlDescriptionLayout,
}));

const subjectOfOptions = computed(() => ({
  itemNoun: "document",
  description: "Papers or documents that describe this resource.",
  elementLabelProp: ["name"],
  childLabelProp: "name",
  showSortButtons: true,
  collapsed: true,
  detail: nameUrlDescriptionLayout,
}));

// Lead with the required name/value pair — that's what this section is for.
// measurementTechnique / minValue / maxValue are dropped from the layout:
// they're statistical-variable fields that made a two-string entry eight
// inputs tall. Any existing values round-trip untouched (unrendered keys are
// preserved on save), they're just not editable here.
const additionalPropertyOptions = {
  itemNoun: "entry",
  // The schema says "Additional properties of the place." — copied from a
  // schema.org Place definition and simply wrong here.
  description: "Extra name-and-value details about this resource.",
  showSortButtons: true,
  collapsed: true,
  elementLabelProp: ["name"],
  childLabelProp: "name",
  detail: {
    type: "VerticalLayout",
    elements: [
      {
        type: "HorizontalLayout",
        elements: [
          { type: "Control", scope: "#/properties/name" },
          { type: "Control", scope: "#/properties/value" },
        ],
      },
      {
        type: "HorizontalLayout",
        elements: [
          { type: "Control", scope: "#/properties/unitCode" },
          { type: "Control", scope: "#/properties/propertyID" },
        ],
      },
      {
        type: "Control",
        scope: "#/properties/description",
        options: {
          multi: true,
          vuetify: { "v-textarea": { rows: 2, "auto-grow": true } },
        },
      },
    ],
  },
};

// license is anyOf[CreativeWork, url-string]. Same per-branch indexing as
// spatialCoverage: a single detail object was applied to BOTH branches, so
// the "Custom License" tab rendered "No applicable renderer found" three
// times (name/url/description don't resolve against a plain string) and
// there was no way to enter a custom license URL.
// `dropdown: true` swaps the tab strip for a select, which is what fits the
// 22rem sidebar.
const licenseOptions = {
  dropdown: true,
  detail: {
    0: {
      type: "VerticalLayout",
      options: { label: "Standard license" },
      elements: [
        { type: "Control", scope: "#/properties/name" },
        { type: "Control", scope: "#/properties/url" },
      ],
    },
    1: {
      type: "Control",
      scope: "#",
      options: { label: "Custom license URL" },
    },
  },
};

// Same resource-type-icon mapping the landing page uses, so the visual
// marker next to the status chip is consistent across both pages.
const resourceTypeKey = computed<string>(
  () => data.value?.additionalType || data.value?.["@type"] || "",
);

const resourceTypeLabel = computed<string>(() => {
  const key = resourceTypeKey.value;
  return contentTypeLabels[key] || key;
});

const resourceTypeIcon = computed<string | undefined>(
  () => contentTypeLogos[resourceTypeKey.value],
);

// Total uploaded bytes across the resource's file tree. Same algorithm
// as landing-page so the "Resource size" cell shows the same number.
const contentSize = computed<string | undefined>(() => {
  const sumTree = (nodes: any[]): number =>
    nodes.reduce((acc, n) => {
      if (Array.isArray(n?.children)) return acc + sumTree(n.children);
      return acc + (typeof n?.uploadedSize === "number" ? n.uploadedSize : 0);
    }, 0);
  const fromFiles = sumTree(rootDirectory.value.children || []);
  return fromFiles > 0 ? prettyBytes(fromFiles) : undefined;
});

// Match landing-page.vue's chip colors so the read-only status chip in
// the edit header looks identical to its landing-page counterpart.
function allowLocalhostUrls(node: any): void {
  if (Array.isArray(node)) {
    node.forEach((child) => allowLocalhostUrls(child));
  } else if (node && typeof node === "object") {
    if (
      node.errorMessage?.pattern === 'must match format "url"' &&
      typeof node.pattern === "string"
    ) {
      const host = "[a-z0-9]+([\\-\\.]{1}[a-z0-9]+)*\\.[a-z]{2,5}";
      node.pattern = node.pattern.replace(host, `(localhost|${host})`);
    }
    Object.values(node).forEach((child) => allowLocalhostUrls(child));
  }
}

// Mirror of landing-page.vue's tocItems / scrollToSection / buildToc.
// The desktop TOC drawer (rendered via the `toc` named route view) and
// the inline mobile <v-select> both read from User.$state.toc, so
// building the same list shape lights up both at once.
const tocItems = computed(() => User.$state.toc);

// user_metadata.json holds the generated citation as a top-level string array.
const citations = computed<string[]>(() => {
  const raw = data.value?.citation;
  if (Array.isArray(raw)) return raw.filter((c: any) => typeof c === "string" && c.trim());
  if (typeof raw === "string" && raw.trim()) return [raw];
  return [];
});

const isPublished = computed<boolean>(
  () => data.value?.creativeWorkStatus?.name === "Published",
);

const potentialDoiUrl = computed<string>(
  () => `https://doi.org/10.4211/hs.${resourceId.value}`,
);

const copiedCitation = ref<number | null>(null);
let copiedTimeout: ReturnType<typeof setTimeout> | undefined;

function onCopyCitation(citation: string, index: number) {
  // Collapse line breaks and repeated whitespace so the citation pastes as one line.
  navigator.clipboard.writeText(citation.replace(/\s+/g, " ").trim());
  Notifications.toast({ message: "Copied to clipboard", type: "info" });
  copiedCitation.value = index;
  clearTimeout(copiedTimeout);
  copiedTimeout = setTimeout(() => (copiedCitation.value = null), 2000);
}

function scrollToSection(hash: string | null) {
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

function buildToc() {
  const toc: { text: string; to: string; level?: number }[] = [
    { text: "Overview", to: "#overview" },
    { text: "Details", to: "#details" },
  ];

  toc.push({ text: "Abstract", to: "#description" });
  toc.push({ text: "Subject Keywords", to: "#subject" });
  toc.push({ text: "Spatial Coverage", to: "#spatial" });
  toc.push({ text: "Temporal Coverage", to: "#temporal" });
  toc.push({ text: "Content", to: "#content" });
  toc.push({ text: "Files", to: "#fileExplorer", level: 4 });
  toc.push({ text: "Additional metadata", to: "#additional" });
  toc.push({ text: "Related Resources", to: "#related" });
  toc.push({ text: "Funding", to: "#funding" });

  if (citations.value.length) {
    toc.push({ text: "How to cite", to: "#citation" });
  }

  toc.push({ text: "License", to: "#license" });

  User.$state.toc = toc;
  User.$state.isTocReady = true;
}

onBeforeUnmount(() => {
  // Clean up the global TOC state so the next route doesn't inherit our
  // section list. Mirrors landing-page.vue's beforeUnmount.
  User.$state.toc = [];
  User.$state.isTocReady = false;
  clearTimeout(copiedTimeout);
});

const isLoadingFiles = ref(true);
const isSubmitting = ref(false);
const folderNameRegex = /^[-()\w\s]*$/;
const isFetchingMetadata = ref(true);
const wasLoaded = ref(true);

const s3Client = shallowRef<S3Client>(undefined as unknown as S3Client);
const s3Host = S3_PROXY_URL;
const s3Info = ref({
  bucket: "",
  prefix: "",
});

const config = {
  restrict: true,
  trim: true,
  showUnfocusedDescription: false,
  hideRequiredAsterisk: false,
  collapseNewItems: false,
  breakHorizontal: false,
  initCollapsed: false,
  // Row order is already conveyed by position and the sort buttons; the
  // filled primary index chip was the loudest thing in every array row.
  hideAvatar: true,
  hideArraySummaryValidation: false,
  vuetify: {
    commonAttrs: {
      density: "compact",
      variant: "outlined",
      // Descriptions surface on focus, not permanently. The schema's
      // schema.org prose is long enough that pinning it under every input
      // doubled the height of each field and buried the values the user
      // actually typed. `showUnfocusedDescription: false` above was already
      // asking for this; persistent-hint was quietly overriding it.
      "persistent-hint": false,
      "hide-details": "auto",
    },
  },
  isViewMode: false,
  isReadOnly: false,
  isDisabled: false,
};

const toUpload = ref<any[]>([]);
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

// created()
async function init() {
  loadAlerts();

  if (!resourceId.value && route?.params?.resourceId) {
    resourceId.value = route.params.resourceId as string;
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
        // This page writes the user-editable `.hsmetadata/user_metadata.json`.
        // S3 auth only allows writes under `.hsmetadata/` and `data/contents/`.
        s3Info.value = { bucket, prefix: `${resourceId.value}/.hsmetadata/` };
      }
    } catch {
      isLoadingFiles.value = false;
      isFetchingMetadata.value = false;
    }
  }

  startS3Client();

  // Load the edit schema. Fields marked `readOnly: true` render disabled;
  // the layout itself is composed directly in the template (no uischema).
  /* @ts-ignore */
  const schemaModule = await import(
    `@hs-schemas/resource_edit_schema.json`
  );
  if (import.meta.env.DEV) {
    // Dev serves from localhost; accept it in url validation (prod stays strict).
    const devSchema = structuredClone(schemaModule.default ?? schemaModule);
    allowLocalhostUrls(devSchema);
    schema.value = devSchema;
  } else {
    /* @ts-ignore */
    schema.value = schemaModule;
  }

  loadResource();
}

async function loadResource() {
  isFetchingMetadata.value = true;
  isLoadingFiles.value = true;
  wasLoaded.value = true;

  const resource = await fetchResource(
    resourceId.value,
    s3Client.value,
    s3Info.value.bucket,
    `${s3Info.value.prefix}user_metadata.json`,
  );

  if (resource) {
    data.value = resource.data;
    // @ts-expect-error The key property is generated when the component is initialized
    rootDirectory.value.children = resource.initialStructure;
    buildToc();
    detectReadme();
  } else {
    wasLoaded.value = false;
  }
  isFetchingMetadata.value = false;
  isLoadingFiles.value = false;
}

// Set readmeFileName (case-insensitive readme.md/readme.txt) and sync the TOC
// entry. Re-run whenever the file tree changes so the editor stays current.
function detectReadme() {
  const rootFiles = (rootDirectory.value.children || []).filter(
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
  readmeFileName.value = target ? target.name : null;
  if (target) {
    addReadmeToc();
  } else {
    removeReadmeToc();
  }
}

// Add the "README" TOC entry under "Files". Idempotent.
function addReadmeToc() {
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
function removeReadmeToc() {
  const toc = User.$state.toc;
  if (!toc) return;
  const idx = toc.findIndex((t) => t.to === "#readme");
  if (idx >= 0) {
    toc.splice(idx, 1);
  }
}

// Both coverages are optional, but once the object exists its own `required`
// rules kick in (spatial needs a geo, temporal needs a startDate) — so
// without a way to clear them a half-filled coverage can block Save with no
// way out. Deleting the key entirely is the only correct "no coverage" state.
const hasSpatialCoverage = computed(() => !!data.value?.spatialCoverage);
const hasTemporalCoverage = computed(() => !!data.value?.temporalCoverage);

function clearSpatialCoverage() {
  if (!data.value) return;
  const { spatialCoverage: _drop, ...rest } = data.value as Record<string, any>;
  data.value = rest;
}

function clearTemporalCoverage() {
  if (!data.value) return;
  const { temporalCoverage: _drop, ...rest } = data.value as Record<
    string,
    any
  >;
  data.value = rest;
}

// Resource-level alerts (missing metadata, version/replacement pointers,
// publication state). Same source the landing page reads: the Django view
// injects them onto the host window, so both views agree.
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
const dismissedAlerts = ref<Record<string, boolean>>({});

function loadAlerts() {
  try {
    const parentWin = window.parent as any;
    if (
      parentWin &&
      parentWin !== window &&
      parentWin.HS_RESOURCE_ALERTS &&
      typeof parentWin.HS_RESOURCE_ALERTS === "object"
    ) {
      alerts.value = parentWin.HS_RESOURCE_ALERTS;
    }
  } catch {
    // cross-origin — leave alerts empty
  }
}

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
  Boolean(!dismissedAlerts.value.versionOf && alerts.value.isVersionOf),
);

const showPublishedAlert = computed<boolean>(() =>
  Boolean(alerts.value.isPublished || alerts.value.reviewPending),
);

// The README editor persists to S3 on its own schedule, so its unsaved state
// is invisible to the metadata form. Track it and confirm before any
// navigation that would throw those edits away.
const readmeDirty = ref(false);

function confirmDiscardReadme(): boolean {
  if (!readmeDirty.value) return true;
  return window.confirm(
    "Your README has unsaved changes that will be lost. Leave anyway?",
  );
}

function leaveToLanding() {
  if (!confirmDiscardReadme()) return;
  router.push({ name: "landing", params: { resourceId: resourceId.value } });
}

onBeforeRouteLeave(() => confirmDiscardReadme());

// On an editor write, keep the file tree and TOC in sync without a reload.
function onReadmeChange(payload: {
  action: "created" | "saved" | "converted";
  name: string;
  previousName?: string;
  size: number;
}) {
  const root = rootDirectory.value as any;
  const children: any[] = Array.isArray(root?.children) ? root.children : [];
  readmeFileName.value = payload.name;

  if (payload.action === "created") {
    if (!children.some((c) => c.name === payload.name)) {
      children.push({
        name: payload.name,
        isUploaded: true,
        file: null,
        uploadedSize: payload.size,
        contentKey: `${resourceId.value}/data/contents/${payload.name}`,
      });
    }
    addReadmeToc();
  } else if (payload.action === "converted") {
    const node = children.find((c) => c.name === payload.previousName);
    if (node) {
      node.name = payload.name;
      node.uploadedSize = payload.size;
      node.contentKey = `${resourceId.value}/data/contents/${payload.name}`;
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
function onUppyFileUploaded(file: any) {
  if (!fileExplorer.value || !file) return;
  const root = rootDirectory.value as any;
  if (!root || !Array.isArray(root.children)) return;

  const folderPath: string | null =
    file?.meta?.existing_path_in_resource || null;
  const targetFolder = findExplorerFolder(root, folderPath) || root;

  if (targetFolder.children.some((c: any) => c.name === file.name)) return;
  targetFolder.children.push({
    name: file.name,
    isUploaded: true,
    file: null,
    uploadedSize: file.size,
    contentKey: file?.meta?.dynamic_key,
  });
}

function findExplorerFolder(root: any, path: string | null): any | null {
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

async function submit() {
  try {
    const key = `${s3Info.value.prefix}user_metadata.json`;

    // Stamp the modification time ourselves. Django normally owns this field
    // — write_user_metadata_json_file() regenerates the whole document and
    // sets dateModified from `resource.modified` — but this page writes the
    // object straight to S3, so Django never sees the change and nothing
    // advances the timestamp. Without this, "Updated ..." kept reporting the
    // last server-side write no matter how many times the user saved.
    if (data.value) {
      data.value = {
        ...(data.value as Record<string, any>),
        dateModified: new Date().toISOString(),
      };
    }

    const content = JSON.stringify(data.value, null, 2);
    const command = new PutObjectCommand({
      Bucket: s3Info.value.bucket,
      Key: key,
      Body: content,
      ContentType: "application/json",
    });
    isSubmitting.value = true;
    await s3Client.value.send(command);

    Notifications.toast({
      message: "Changes saved.",
      type: "success",
    });

    // Deliberately stay in edit mode. Saving is not "finishing" — users
    // routinely save partway through a long metadata edit, and bouncing them
    // to the read-only view meant re-entering edit and re-scrolling to
    // continue. "Back" is the explicit way out.
  } catch (error: any) {
    console.error("Error uploading to S3:", error);
    Notifications.toast({
      title: "Error",
      message: `Failed to upload metadata to S3. Details: ${error.message}`,
      type: "error",
    });
  } finally {
    isSubmitting.value = false;
  }
}

async function uploadFiles(files: IFile[]): Promise<boolean[]> {
  if (files.length) {
    // Annotate file paths before uploading
    files.forEach((f) => {
      f.isDisabled = true;
      f.path = fileExplorer.value!.getPathString(f);
    });
    return _uploadFiles(files);
  }
  return [];
}

async function _uploadFiles(
  itemsToUpload: (IFile | IFolder)[],
): Promise<boolean[]> {
  itemsToUpload.forEach((i) => (i.isDisabled = true));
  const filesToUpload = itemsToUpload.filter((i) =>
    Object.prototype.hasOwnProperty.call(i, "file"),
  ) as IFile[];
  const foldersToUpload = itemsToUpload.filter((i) =>
    Object.prototype.hasOwnProperty.call(i, "children"),
  ) as IFolder[];

  // const basePrefix = `${resourceId.value}/data/contents/${currentPath}`;

  // compute folder paths
  let folderPaths = foldersToUpload
    .map((f) => f.path)
    .filter((f) => !!f) as string[];

  // unique + sort deeper first
  folderPaths = [...new Set(folderPaths)].sort(
    (a, b) => b.split("/").length - a.split("/").length,
  );

  let responses: boolean[] = [];
  itemsToUpload.forEach((i) => (i.isDisabled = false));

  if (folderPaths.length) {
    responses = await _createFoldersByDepth(folderPaths, 1);
  } else {
    responses = await _doUploadFiles();
  }

  async function _createFoldersByDepth(
    paths: string[],
    depth: number,
  ): Promise<boolean[]> {
    const depthPaths = paths.filter((p) => p.split("/").length === depth);

    const folderCreatePromises = depthPaths.map((path: string) => {
      const rootPrefix = `${resourceId.value}/data/contents/`;
      const folderKey = `${rootPrefix}${path}/`; // Ensure trailing slash for folder marker

      return s3Client.value.send(
        new PutObjectCommand({
          Bucket: s3Info.value.bucket,
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
      : _doUploadFiles();
  }

  async function _doUploadFiles(): Promise<boolean[]> {
    const fileUploadPromises = filesToUpload.map(async (file: IFile) => {
      const path = fileExplorer.value!.getPathString(file);
      try {
        if (!hsUppyRef.value) {
          throw new Error("HsUppy component not available");
        }

        const uppy = hsUppyRef.value.getUppyInstance();
        if (!uppy) {
          throw new Error("Uppy instance not available");
        }
        uppy.getPlugin("Dashboard")?.openModal();
        const fileId = uppy.addFile({
          name: file.name,
          type: file.file?.type || "application/octet-stream",
          data: file.file,
          meta: {
            bucket_name: s3Info.value.bucket,
            // NOT s3Info.prefix — that points at .hsmetadata/ so the metadata
            // read/write can find user_metadata.json. Content files belong
            // under data/contents/, same as the folder-creation path above.
            dynamic_key: `${resourceId.value}/data/contents/${path}`,
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

async function deleteFileOrFolder(item: IFile | IFolder): Promise<boolean> {
  let path = fileExplorer.value!.getPathString(item);
  const isFolder = Object.prototype.hasOwnProperty.call(item, "children");
  if (isFolder && !path.endsWith("/")) {
    path += "/";
  }
  const basePrefix = `${resourceId.value}/data/contents/`;
  try {
    if (isFolder) {
      let continuationToken: string | undefined;
      const objectsToDelete: { Key: string }[] = [];

      do {
        const listCommand = new ListObjectsV2Command({
          Bucket: s3Info.value.bucket,
          Prefix: `${basePrefix}${path}`,
          ContinuationToken: continuationToken,
        });
        const listResponse = await s3Client.value.send(listCommand);

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
          await s3Client.value.send(
            new DeleteObjectsCommand({
              Bucket: s3Info.value.bucket,
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
        Bucket: s3Info.value.bucket,
        Prefix: `${basePrefix}${path}`,
      });
      const verifyResponse = await s3Client.value.send(verifyCommand);
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
        Bucket: s3Info.value.bucket,
        Prefix: `${resourceId.value}/data/contents/`,
        Delimiter: "/",
      });
      const parentResponse = await s3Client.value.send(listParentCommand);
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
      await s3Client.value.send(
        new DeleteObjectsCommand({
          Bucket: s3Info.value.bucket,
          Delete: { Objects: [{ Key: `${basePrefix}${path}` }] },
        }),
      );
      console.log(`Deleted file: ${basePrefix}${path}`);
    }

    // Deleting the README clears the editor + TOC.
    if (!isFolder && path === readmeFileName.value) {
      readmeFileName.value = null;
      removeReadmeToc();
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

async function renameFileOrFolder(
  item: IFile | IFolder,
  newNameOrPath: string,
): Promise<void> {
  const isFolder = Object.prototype.hasOwnProperty.call(item, "children");

  // s3Info.prefix is set to `<id>/.hsjsonld/` for metadata fetching — the
  // file tree lives under `<id>/data/contents/`. Use the contents path
  // explicitly so copy/head/list/delete operations target the actual
  // objects (matches what deleteFileOrFolder already does).
  const basePrefix = `${resourceId.value}/data/contents/`;

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
  let oldRel = fileExplorer.value!.getPathString(item);
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
        await s3Client.value.send(
          new HeadObjectCommand({
            Bucket: s3Info.value.bucket,
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
          await s3Client.value.send(
            new HeadObjectCommand({
              Bucket: s3Info.value.bucket,
              Key: destFolderKey,
            }),
          );
        } catch (err: any) {
          if (
            err?.name === "NotFound" ||
            err?.$metadata?.httpStatusCode === 404
          ) {
            await s3Client.value.send(
              new PutObjectCommand({
                Bucket: s3Info.value.bucket,
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
        const list = await s3Client.value.send(
          new ListObjectsV2Command({
            Bucket: s3Info.value.bucket,
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
            s3Client.value.send(
              new CopyObjectCommand({
                Bucket: s3Info.value.bucket,
                CopySource: `${s3Info.value.bucket}/${encodeCopySourceKey(obj.Key)}`,
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
        await s3Client.value.send(
          new CopyObjectCommand({
            Bucket: s3Info.value.bucket,
            CopySource: `${s3Info.value.bucket}/${encodeCopySourceKey(oldKey)}`,
            Key: newKey,
          }),
        );
      }
    }

    // verify destination
    if (isFolder) {
      const verify = await s3Client.value.send(
        new ListObjectsV2Command({
          Bucket: s3Info.value.bucket,
          Prefix: newKey,
          MaxKeys: 1,
        }),
      );
      if (!verify.Contents || verify.Contents.length === 0)
        throw new Error(`Verification failed: nothing at ${newKey}`);
    } else {
      await s3Client.value.send(
        new HeadObjectCommand({ Bucket: s3Info.value.bucket, Key: newKey }),
      );
    }

    // delete originals (and clean ancestor markers)
    const cleanupEmptyAncestors = async (startParentRel: string) => {
      let cur = startParentRel;
      while (cur) {
        const markerKey = `${basePrefix}${asFolder(cur)}`;
        const probe = await s3Client.value.send(
          new ListObjectsV2Command({
            Bucket: s3Info.value.bucket,
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
            await s3Client.value.send(
              new DeleteObjectCommand({
                Bucket: s3Info.value.bucket,
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
        const list = await s3Client.value.send(
          new ListObjectsV2Command({
            Bucket: s3Info.value.bucket,
            Prefix: oldKey,
            ContinuationToken: token,
          }),
        );
        const objs = (list.Contents || [])
          .map((o) => ({ Key: o.Key! }))
          .filter((o) => !o.Key!.startsWith(newKey));
        if (objs.length) {
          await s3Client.value.send(
            new DeleteObjectsCommand({
              Bucket: s3Info.value.bucket,
              Delete: { Objects: objs },
            }),
          );
        }
        token = list.NextContinuationToken;
      } while (token);
      try {
        await s3Client.value.send(
          new DeleteObjectCommand({
            Bucket: s3Info.value.bucket,
            Key: oldKey,
          }),
        );
      } catch {}
      if (oldParent) await cleanupEmptyAncestors(oldParent);
    } else {
      await s3Client.value.send(
        new DeleteObjectsCommand({
          Bucket: s3Info.value.bucket,
          Delete: { Objects: [{ Key: oldKey }] },
        }),
      );
      if (oldParent) await cleanupEmptyAncestors(oldParent);
    }

    // refresh
    const root = `${resourceId.value}/data/contents/`;
    // @ts-expect-error The key property is generated when the component is initialized
    rootDirectory.value.children = await readRootFolder(
      root,
      s3Client.value,
      s3Info.value.bucket,
    );

    // Reflect a README rename in the editor.
    detectReadme();

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

init();
</script>

<style lang="scss" scoped>
// Mirror the landing page section styling so the edit view reads as the
// same page with in-place inputs swapped for the read-only text.
.section-heading {
  color: rgb(var(--v-theme-accent));
  letter-spacing: 0.05em;
  padding-bottom: 0.4rem;
  margin-bottom: 0.75rem;
  border-bottom: 2px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

// Sidebar section titles. Mirrors the landing page's sidebar treatment —
// same teal and tracking as .section-heading, without the rule, since the
// sidebar's narrower columns don't need the extra separation.
.sidebar-heading {
  color: rgb(var(--v-theme-accent));
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  line-height: 1.375rem;
  text-transform: uppercase;
}

.details-card {
  border-color: rgba(0, 0, 0, 0.08) !important;
}

.citation-card {
  padding: 1rem 1rem 0.75rem;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-left: 3px solid rgb(var(--v-theme-accent));
  border-radius: 4px;
  background-color: rgba(var(--v-theme-accent), 0.04);

  & + .citation-card {
    margin-top: 0.75rem;
  }
}

.citation-text {
  min-width: 0;
  word-break: break-word;
  font-size: 0.875rem;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.citation-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.75rem;
}

// Fixed width so swapping the label to "Copied" doesn't resize the button.
.citation-copy {
  min-width: 9.5rem;
  letter-spacing: 0.03em;
  text-transform: none;
}

.citation-note {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  min-width: 0;
  font-size: 0.75rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.6);

  // The DOI URL has no break opportunities and would otherwise widen the section.
  > div {
    min-width: 0;
    overflow-wrap: anywhere;
  }
}

.citation-note__icon {
  flex-shrink: 0;
  margin-top: 0.1rem;
  opacity: 0.7;
}

.single-col-layout {
  gap: 1.5rem;

  @media (max-width: 1279px) {
    gap: 0;

    > .page-content,
    > .sidebar,
    > .sidebar > div {
      display: contents;
    }

    #details { order: 1; }
    #description { order: 2; }
    #subject { order: 3; }
    #spatial { order: 4; }
    #temporal { order: 5; }
    #content { order: 6; }
    #additional { order: 7; }
    #related { order: 8; }
    #funding { order: 9; }
    #citation { order: 10; }
    #license { order: 11; }
  }
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

  // These are role="button" targets, so they must show focus. Without this
  // the keyboard path exists but is invisible.
  &:focus-visible {
    outline: 2px solid #4bb5c1;
    outline-offset: 2px;
    background-color: rgba(0, 0, 0, 0.03);
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
