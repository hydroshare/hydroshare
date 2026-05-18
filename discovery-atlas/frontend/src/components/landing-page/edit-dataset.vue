<template>
  <v-container>
    <div class="d-flex gap-1">
      <div class="text-h5">Edit Resource</div>
      <v-spacer></v-spacer>
      <template v-if="!isLoadingFiles && !isFetchingMetadata">
        <v-menu width="500" :close-on-content-click="false">
          <template v-slot:activator="{ props }">
            <v-btn
              size="small"
              v-bind="props"
              color="primary"
              prepend-icon="mdi-cog"
              variant="plain"
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
                :accessKey="accessKey"
                :secret-key="secretKey"
                @apply-changes="onS3FormUpdate"
                @restore-defaults="onRestoreDefaults"
              ></s3-form>
            </v-card-text>
          </v-card>
        </v-menu>
      </template>
    </div>
    <v-divider class="mb-6"></v-divider>

    <template v-if="wasLoaded">
      <cz-file-explorer
        v-if="!isLoadingFiles"
        ref="fileExplorer"
        id="cz-folder-structure"
        v-model:valid-items="toUpload"
        :root-directory="rootDirectory"
        :has-folders="fileExplorerConfig.hasFolders"
        :is-read-only="false"
        :has-file-metadata="() => false"
        :folder-name-regex="folderNameRegex"
        :canDownloadItem="() => true"
        :upload="uploadFiles"
        :delete-file-or-folder="deleteFileOrFolder"
        :rename-file-or-folder="renameFileOrFolder"
        @download="onFileDownload($event, resourceId, s3Client, s3Info.bucket)"
      >
        <template #prepend>
          <span />
        </template>
      </cz-file-explorer>
      <HsUppy
        v-if="wasLoaded && !isLoadingFiles"
        ref="hsUppyRef"
        :s3Info="s3Info"
        :s3Host="s3Host"
        :accessKey="accessKey"
        :secretKey="secretKey"
        :fileExplorer="fileExplorer"
      />
      <v-skeleton-loader class="mb-12" v-else type="card"></v-skeleton-loader>

      <v-skeleton-loader
        v-if="isFetchingMetadata"
        type="card"
      ></v-skeleton-loader>
      <cz-form
        v-else
        :schema="schema"
        :uischema="uischema"
        v-model="data"
        :errors.sync="errors"
        @update:errors="onUpdateErrors"
        v-model:is-valid="isValid"
        :config="config"
        ref="form"
        class="mt-14"
      />

      <div v-if="!isFetchingMetadata" class="d-flex gap-1">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="$router.push({ name: 'landing', params: { resourceId } })"
        >
          Cancel
        </v-btn>
        <v-menu
          :disabled="!errors.length"
          open-on-hover
          bottom
          left
          offset-y
          transition="fade"
        >
          <template #activator="{ props }">
            <div
              v-bind="props"
              class="d-flex form-controls flex-column flex-sm-row"
            >
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
      <v-skeleton-loader v-else type="actions"></v-skeleton-loader>
    </template>
    <v-empty-state
      v-else
      icon="mdi-cloud-cancel"
      text="Try adjusting your settings."
      title="We couldn't load this resource."
    ></v-empty-state>
  </v-container>
</template>

<script lang="ts">
import { Component, Vue, toNative, Ref } from "vue-facing-decorator";
import {
  CzForm,
  CzFileExplorer,
  Notifications,
} from "@cznethub/cznet-vue-core";
import type { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";
import {
  S3Client,
  PutObjectCommand,
  DeleteObjectsCommand,
  ListObjectsV2Command,
  _Object,
  HeadObjectCommand,
  DeleteObjectCommand,
  CopyObjectCommand,
} from "@aws-sdk/client-s3";
import { stringify } from "@/utils";
import { fetchResource, onFileDownload, readRootFolder } from "./shared";
import HsUppy from "./hs-uppy.vue";
import User from "@/models/user.model";

interface FormError {
  title: string;
  message: string;
}

@Component({
  components: { CzForm, CzFileExplorer, HsUppy },
  name: "App",
})
class App extends Vue {
  resourceId!: string;

  @Ref("form") form!: InstanceType<typeof CzForm>;
  @Ref("fileInput") fileInput!: HTMLInputElement;
  @Ref("folderInput") folderInput!: HTMLInputElement;
  @Ref("fileExplorer") fileExplorer!: InstanceType<typeof CzFileExplorer>;
  @Ref("hsUppyRef") hsUppyRef!: InstanceType<typeof HsUppy>;

  protected get isLoggedIn(): boolean {
    return User.$state.isLoggedIn;
  }

  schema!: any;
  uischema!: any;
  defaults!: any;
  onFileDownload = onFileDownload;

  isValid: boolean = false;
  errors: FormError[] = [];
  data: Record<string, any> = {};
  stringify = stringify;

  accessKey = localStorage.getItem("s3AccessKey") || "minioadmin";
  secretKey = localStorage.getItem("s3SecretKey") || "minioadmin";

  isLoadingFiles: boolean = true;
  isSubmitting: boolean = false;
  currentPath: string = "";
  folderNameRegex = /^[-()\w\s]*$/;
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
    this.s3Client = new S3Client({
      region: "us-central-2",
      endpoint: `${this.s3Host}`,
      forcePathStyle: true,
      credentials: {
        accessKeyId: this.accessKey,
        secretAccessKey: this.secretKey,
      },
    });
  }

  async created() {
    if (!this.resourceId && this.$route?.params?.resourceId) {
      this.resourceId = this.$route.params.resourceId as string;
    }

    const fetchCredentials = async () => {
      const { access_key, secret_key } = await User.getOrCreateS3Credentials();
      this.accessKey = access_key;
      this.secretKey = secret_key;
    };

    if (this.isLoggedIn) {
      console.log("user is already logged in, fetching S3 credentials");
      fetchCredentials();
    } else {
      console.log(
        "checking if we just returned from HydroShare login redirect",
      );
      User.checkLoginStatus().then((loggedIn) => {
        if (loggedIn) {
          fetchCredentials();
        }
      });
    }

    // temporary local storage for S3 keys (will move to Pinia later)
    if (!this.accessKey || !this.secretKey) {
      this.accessKey = prompt("Enter your S3 Access Key:") || "minioadmin";
      this.secretKey = prompt("Enter your S3 Secret Key:") || "minioadmin";

      if (this.accessKey && this.secretKey) {
        localStorage.setItem("s3AccessKey", this.accessKey);
        localStorage.setItem("s3SecretKey", this.secretKey);
      } else {
        alert("Access key and secret key are required to proceed.");
        return;
      }
    }

    // if (!this.s3Info.bucket || !this.s3Info.prefix) {
    //   User.getResourceS3prefix(this.resourceId).then((s3info) => {
    //     this.s3Info = s3info;
    //     this.s3Info.prefix = `${this.resourceId}/data/contents/`; // TODO: overriding wrong api response value
    //   });
    // }

    // this.startS3Client();

    if (!this.s3Info.bucket || !this.s3Info.prefix) {
      try {
        const s3info = await User.getResourceS3prefix(this.resourceId);
        if (s3info) {
          this.s3Info = s3info;
          this.s3Info.prefix = `${this.resourceId}/data/contents/`; // TODO: overriding wrong api response value
        }
      } catch (e) {
        this.isLoadingFiles = false;
        this.isFetchingMetadata = false;
      }
    }

    this.startS3Client();

    // Load schema + uischema
    /* @ts-ignore */
    this.schema = await import(
      `@/schemas/hydroshare/scientific_dataset_json_schema.json`
    );

    /* @ts-ignore */
    this.uischema = await import(`@/schemas/hydroshare/edit-uischema.json`);

    /* @ts-ignore */
    this.defaults = await import(`@/schemas/hydroshare/defaults.json`);

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
      `${this.s3Info.prefix}hs_user_meta.json`,
    );

    if (resource) {
      this.data = resource.data;
      // @ts-expect-error The key property is generated when the component is initialized
      this.rootDirectory.children = resource.initialStructure;
    } else {
      this.wasLoaded = false;
    }
    this.isFetchingMetadata = false;
    this.isLoadingFiles = false;
  }

  onUpdateErrors(errors: FormError[]) {
    this.errors = errors;
  }

  async onS3FormUpdate(params: any) {
    this.isFetchingMetadata = true;
    this.isLoadingFiles = true;
    this.s3Info.bucket = params.bucket;
    this.s3Info.prefix = params.prefix;
    this.hydroshareHost = params.hydroshareHost;
    this.s3Host = params.s3Host;

    this.secretKey = params.secretKey;
    this.accessKey = params.accessKey;
    localStorage.setItem("s3AccessKey", this.accessKey);
    localStorage.setItem("s3SecretKey", this.secretKey);

    this.startS3Client();
    this.loadResource();
  }

  async onRestoreDefaults() {
    this.isFetchingMetadata = true;
    this.isLoadingFiles = true;
    this.s3Host = "http://localhost:9000";
    this.hydroshareHost = "http://localhost:8000";
    const s3Info = await User.getResourceS3prefix(this.resourceId);
    if (s3Info) {
      this.s3Info = s3Info;
      this.s3Info.prefix = `${this.resourceId}/.hsjsonld/`; // TODO: overriding wrong api response value
      this.startS3Client();
      this.loadResource();
    }
  }

  async submit() {
    try {
      const resourceId = this.resourceId;
      const key = `${resourceId}/data/contents/hs_user_meta.json`;

      const content = JSON.stringify(
        { name: this.data.name, description: this.data.description },
        null,
        2,
      );
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
            const successHandler = (successFileId: string, response: any) => {
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
              Key: `${this.s3Info.prefix}${asFolder(candidate)}`,
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

    const oldKey = `${this.s3Info.prefix}${oldRel}`;
    const newKey = `${this.s3Info.prefix}${newRel}`;

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
          const destFolderKey = `${this.s3Info.prefix}${asFolder(destParent)}`;
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
          const markerKey = `${this.s3Info.prefix}${asFolder(cur)}`;
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

<style lang="scss" scoped></style>
