<template>
  <div id="uppy"></div>
  <v-btn id="uppy-button" @click.prevent>Upload files with Uppy</v-btn>
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

  @Prop({ type: CzFileExplorer, required: false, default: false })
  fileExplorer!: InstanceType<typeof CzFileExplorer>;

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
        Object.keys(files).forEach((fileId) => {
          const file = files[fileId];
          console.log("adding metadata for", file.name);
          console.log("s3Info:", uppyComponent.s3Info);
          if (that.selectedFolder) {
            console.log(
              `selectedFolder is set, using it as prefix: ${that.selectedFolder}`,
            );
            file.meta.dynamic_key = file.meta.dynamic_key
              ? file.meta.dynamic_key
              : `${uppyComponent.s3Info.prefix}${that.selectedFolder}/${file.name}`;
            console.log("file.meta.dynamic_key set to:", file.meta.dynamic_key);
          }
          if (file.meta.existing_path_in_resource) {
            console.log(
              "existing_path_in_resource is set, using it as prefix:",
              file.meta.existing_path_in_resource,
            );
            file.meta.dynamic_key = file.meta.dynamic_key
              ? file.meta.dynamic_key
              : `${uppyComponent.s3Info.prefix}${file.meta.existing_path_in_resource}/${file.name}`;
            console.log("file.meta.dynamic_key set to:", file.meta.dynamic_key);
          }
          file.meta.bucket_name =
            file?.meta?.bucket_name || uppyComponent.s3Info.bucket;
          file.meta.dynamic_key = file?.meta?.dynamic_key
            ? file.meta.dynamic_key
            : `${uppyComponent.s3Info.prefix}${file.name}`;
        });
        return files;
      },
    }).use(Dashboard, {
      inline: false,
      fileManagerSelectionType: "both",
      target: "#uppy",
      showProgressDetails: true,
      trigger: "#uppy-button",
      note: `TODO: quota?`,
    });

    uppyInstance
      .use(AwsS3, {
        headers: headers,
        allowedMetaFields: true,
        endpoint: COMPANION_URL,
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
