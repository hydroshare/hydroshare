<template>
  <div id="uppy" class="hs-uppy-dashboard"></div>
</template>

<script lang="ts">
import { Component, Vue, toNative, Prop, Watch } from "vue-facing-decorator";
import { CzFileExplorer } from "@cznethub/cznet-vue-core";
import Uppy from "@uppy/core";
import GoldenRetriever from "@uppy/golden-retriever";
import GoogleDrivePicker from "@uppy/google-drive-picker";
import Dashboard from "@uppy/dashboard";
import AwsS3 from "@uppy/aws-s3";
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { Sha256 } from "@aws-crypto/sha256-js";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import {
  COMPANION_URL,
  GOOGLE_PICKER_CLIENT_ID,
  GOOGLE_PICKER_API_KEY,
  GOOGLE_PICKER_APP_ID,
} from "@/constants";

import "@uppy/core/css/style.min.css";
import "@uppy/dashboard/css/style.min.css";

let uppyInstance: Uppy | null = null;

@Component({
  name: "hs-uppy",
  components: {},
  expose: ["getUppyInstance", "addFile", "upload"],
  emits: ["file-uploaded"],
})
class HsUppy extends Vue {
  @Prop({
    required: false,
    // default: () => ({
    //   prefix: "1dbbbacc036044c5970440b135f185c2/data/contents/",
    //   bucket: "asdf",
    // }),
  })
  s3Info!: { prefix: string; bucket: string };

  @Prop({
    type: String,
    required: false,
    default: "http://localhost:9000",
  })
  s3Host!: string;

  @Prop({ type: String, required: false, default: "minioadmin" })
  accessKey!: string;

  @Prop({ type: String, required: false, default: "minioadmin" })
  secretKey!: string;

  @Prop({ type: String, required: false, default: "" })
  sessionToken!: string;

  /**
   * S3 key prefix that user-uploaded files should land under (e.g.
   * `<resourceId>/data/contents/`). This is intentionally different from
   * `s3Info.prefix`, which the edit page sets to the metadata directory
   * (`<resourceId>/.hsjsonld/`) for reading dataset_metadata.json. Without
   * this prop the upload `dynamic_key` would point at the metadata path and
   * files wouldn't appear when readRootFolder walks `data/contents/`.
   */
  @Prop({ type: String, required: false, default: "" })
  uploadPrefix!: string;

  // `default: null` (not `false`) — the parent `@Ref("fileExplorer")` is
  // `undefined` until the explorer mounts, and HsUppy renders BEFORE that
  // (it's now a slot child of cz-file-explorer). Falsy default + a non-Object
  // value would trip Vue's prop validator with the boolean `false`. Allow
  // both Object and null/undefined, since registerUploadedFile already
  // guards against the falsy case at call time.
  @Prop({ type: Object, required: false, default: null })
  fileExplorer!: InstanceType<typeof CzFileExplorer> | null;

  @Watch("fileExplorer.selected")
  onFileSelect() {
    // if the selected is a folder, set selectedFolder
    let selected = this.fileExplorer.selected;
    // if selected is an array, take the first element
    if (Array.isArray(selected)) {
      if (selected.length > 0) {
        selected = selected[0];
      } else {
        this.selectedFolder = null;
        return;
      }
    }
    // const isFolder = Object.prototype.hasOwnProperty.call(selected, "children");
    const isFolder = this.fileExplorer.isFolder(selected);
    if (isFolder) {
      this.selectedFolder = this.fileExplorer.getPathString(selected);
    } else {
      this.selectedFolder = null;
    }
    console.log("selectedFolder set to:", this.selectedFolder);
  }

  private selectedFolder: string | null = null;
  private signatureV4: SignatureV4 | null = null;

  // Method to expose the Uppy instance
  getUppyInstance(): Uppy | null {
    return uppyInstance;
  }


  // Add files through the component
  addFile(fileData: any): string | null {
    if (uppyInstance) {
      try {
        return uppyInstance.addFile(fileData);
      } catch (error) {
        console.error("Error adding file to Uppy:", error);
        return null;
      }
    }
    return null;
  }

  upload(): Promise<void> {
    if (uppyInstance) {
      return uppyInstance.upload();
    }
    return Promise.reject(new Error("Uppy instance not available"));
  }

  // Watch for credential changes and recreate Uppy instance
  @Watch("accessKey")
  @Watch("secretKey")
  @Watch("sessionToken")
  onCredentialsChange() {
    console.log("Credentials changed, recreating Uppy instance");
    this.initializeUppy();
  }

  mounted() {
    this.initializeUppy();
  }

  // Method to get or create the SignatureV4 instance
  getSigner(): SignatureV4 {
    if (!this.signatureV4) {
      this.signatureV4 = new SignatureV4({
        service: "s3",
        region: "us-east-1",
        credentials: {
          accessKeyId: this.accessKey,
          secretAccessKey: this.secretKey,
          sessionToken: this.sessionToken || undefined,
        },
        sha256: Sha256,
      });
    }
    return this.signatureV4;
  }
  initializeUppy() {
    if (uppyInstance) {
      try {
        // Uppy v5 renamed `destroy()` to `close()`. Guard both for safety.
        const inst = uppyInstance as unknown as {
          close?: (opts?: { reason?: string }) => void;
          destroy?: () => void;
        };
        if (typeof inst.close === "function") {
          inst.close({ reason: "unmount" });
        } else if (typeof inst.destroy === "function") {
          inst.destroy();
        }
        uppyInstance = null;
      } catch (error) {
        console.error("Error destroying current Uppy instance:", error);
      }
    }
    const uppyComponent = this;
    const headers = {
      "s3-key": this.accessKey,
      "s3-secret": this.secretKey,
      "s3-bucket": this.s3Info.bucket,
    };
    console.log("Initializing Uppy");
    const that = this;
    uppyInstance = new Uppy({
      id: "uppy",
      autoProceed: true,
      onBeforeUpload: (files) => {
        // Build the S3 key from `uploadPrefix` (e.g. `<id>/data/contents/`),
        // any selected subfolder, and the filename. Falls back to s3Info.prefix
        // only when uploadPrefix wasn't passed — preserves the old contract.
        const basePrefix =
          uppyComponent.uploadPrefix || uppyComponent.s3Info.prefix || "";
        Object.keys(files).forEach((fileId) => {
          const file = files[fileId];
          file.meta.bucket_name =
            file?.meta?.bucket_name || uppyComponent.s3Info.bucket;
          if (!file.meta.dynamic_key) {
            const folder =
              file.meta.existing_path_in_resource || that.selectedFolder || "";
            const folderPart = folder ? `${folder.replace(/^\/+|\/+$/g, "")}/` : "";
            file.meta.dynamic_key = `${basePrefix}${folderPart}${file.name}`;
          }
          console.log(
            "Uppy upload key:",
            file.meta.dynamic_key,
            "bucket:",
            file.meta.bucket_name,
          );
        });
        return files;
      },
    }).use(Dashboard, {
      inline: true,
      fileManagerSelectionType: "both",
      target: "#uppy",
      showProgressDetails: true,
      width: "100%",
      height: 320,
      note: `TODO: quota?`,
    });

    uppyInstance
      .use(AwsS3, {
        // Do NOT use Companion for signing here: companion generates a UUID
        // S3 key (e.g. `92a92f6b-...-foo.txt`) and hardcodes it into the
        // signature policy. Our `dynamic_key` then only lives in
        // `x-amz-meta-dynamic_key`, not the actual object key, so files land
        // at random root paths instead of `<resourceId>/data/contents/`.
        // Sign client-side with the real key instead.
        shouldUseMultipart: false,
        getUploadParameters: async (file: any) => {
          const s3 = new S3Client({
            region: "us-east-1",
            endpoint: that.s3Host,
            forcePathStyle: true,
            credentials: {
              accessKeyId: that.accessKey,
              secretAccessKey: that.secretKey,
              sessionToken: that.sessionToken || undefined,
            },
          });
          const url = await getSignedUrl(
            s3,
            new PutObjectCommand({
              Bucket: file.meta.bucket_name || that.s3Info.bucket,
              Key: file.meta.dynamic_key,
              ContentType: file.type || "application/octet-stream",
            }),
            { expiresIn: 3600 },
          );
          return {
            method: "PUT",
            url,
            fields: {},
            headers: {
              "Content-Type": file.type || "application/octet-stream",
            },
          };
        },
      })
      .on("dashboard:modal-open", () => {
        // this is a hack to set the folder when the modal is opened
        // because the selectedFolder will change when the user clicks in the dashboard
        if (that.selectedFolder) {
          uppyInstance.setMeta({
            existing_path_in_resource: that.selectedFolder,
          });
          console.log("Set dashboard folder state to:", that.selectedFolder);
        }
      })
      .on("upload-success", (file: any) => {
        // Hand off to the parent (which owns the file-explorer ref directly).
        // The `fileExplorer` prop passed in here doesn't reliably propagate
        // as a reactive value through vue-facing-decorator, so accessing it
        // from inside this Uppy handler is unsafe; an event side-steps that.
        that.$emit("file-uploaded", file);
      })
      .on("error", (errorMessage) => {
        console.error("Uppy error:", errorMessage);
        let errorMsg = "";
        if (typeof errorMessage === "object") {
          for (const [key, value] of Object.entries(errorMessage)) {
            errorMsg += `${key}: ${value}`;
          }
        } else {
          errorMsg = JSON.stringify(errorMessage);
        }
        try {
          let errorMessageJSON = JSON.parse(errorMessage.message);
          if (errorMessageJSON.hasOwnProperty("validation_error")) {
            errorMsg = errorMessageJSON.validation_error;
          } else if (errorMessageJSON.hasOwnProperty("file_size_error")) {
            errorMsg = errorMessageJSON.file_size_error;
          }
        } catch (e) {}
      })
      .use(GoldenRetriever)
      .use(GoogleDrivePicker, {
        target: Dashboard,
        companionUrl: COMPANION_URL,
        clientId: GOOGLE_PICKER_CLIENT_ID,
        apiKey: GOOGLE_PICKER_API_KEY,
        appId: GOOGLE_PICKER_APP_ID,
        companionHeaders: headers,
      });
  }
}
export default toNative(HsUppy);
</script>
