<template>
  <div id="uppy" class="hs-uppy-dashboard"></div>
</template>

<script lang="ts">
import { CzFileExplorer } from "@cznethub/cznet-vue-core";
import Uppy from "@uppy/core";
import GoldenRetriever from "@uppy/golden-retriever";
import GoogleDrivePicker from "@uppy/google-drive-picker";
import Dashboard from "@uppy/dashboard";
import AwsS3 from "@uppy/aws-s3";
import User from "@/models/user.model";
import {
  COMPANION_URL,
  GOOGLE_PICKER_CLIENT_ID,
  GOOGLE_PICKER_API_KEY,
  GOOGLE_PICKER_APP_ID,
} from "@/constants";

import "@uppy/core/css/style.min.css";
import "@uppy/dashboard/css/style.min.css";

let uppyInstance: Uppy | null = null;

/**
 * Drop-in replacement for AwsS3's static uploadPartBytes, with two changes
 * for the cookie-authenticated hs-s3-proxy:
 *
 * - `withCredentials` so the sessionid/csrftoken cookies ride along on the
 *   cross-origin PUT (the proxy authenticates the session, not a signature);
 * - a missing ETag response header is not fatal. Upstream never settles the
 *   promise when CORS hides ETag; we only do single-part PUTs, and nothing
 *   downstream consumes the tag.
 */
function cookieUploadPartBytes({
  signature: { url, expires, headers, method = "PUT" },
  body,
  size = (body as Blob).size,
  onProgress,
  onComplete,
  signal,
}: any): Promise<any> {
  if (url == null) {
    return Promise.reject(new Error("Cannot upload to an undefined URL"));
  }
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.withCredentials = true;
    if (headers) {
      Object.keys(headers).forEach((key) => {
        xhr.setRequestHeader(key, headers[key]);
      });
    }
    xhr.responseType = "text";
    if (typeof expires === "number") {
      xhr.timeout = expires * 1000;
    }
    function onabort() {
      xhr.abort();
    }
    function cleanup() {
      signal?.removeEventListener("abort", onabort);
    }
    signal?.addEventListener("abort", onabort);
    xhr.upload.addEventListener("progress", (ev) => {
      onProgress?.(ev);
    });
    xhr.addEventListener("abort", () => {
      cleanup();
      reject(new DOMException("Aborted", "AbortError"));
    });
    xhr.addEventListener("timeout", () => {
      cleanup();
      reject(new Error("Request has expired"));
    });
    xhr.addEventListener("load", () => {
      cleanup();
      if (xhr.status < 200 || xhr.status >= 300) {
        const error = new Error("Non 2xx") as Error & { source: unknown };
        error.source = xhr;
        reject(error);
        return;
      }
      onProgress?.({ loaded: size, lengthComputable: true });
      const etag = xhr.getResponseHeader("ETag") ?? "";
      onComplete?.(etag);
      resolve({ ETag: etag });
    });
    xhr.addEventListener("error", () => {
      cleanup();
      const error = new Error("Unknown error") as Error & { source: unknown };
      error.source = xhr;
      reject(error);
    });
    xhr.send(body);
  });
}
</script>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    s3Info: { prefix: string; bucket: string };
    s3Host?: string;
    /**
     * S3 key prefix that user-uploaded files should land under (e.g.
     * `<resourceId>/data/contents/`). This is intentionally different from
     * `s3Info.prefix`, which the edit page sets to the metadata directory
     * (`<resourceId>/.hsjsonld/`) for reading dataset_metadata.json. Without
     * this prop the upload `dynamic_key` would point at the metadata path and
     * files wouldn't appear when readRootFolder walks `data/contents/`.
     */
    uploadPrefix?: string;
    // `default: null` (not `false`) — the parent's `fileExplorer` ref is
    // `undefined` until the explorer mounts, and HsUppy renders BEFORE that
    // (it's now a slot child of cz-file-explorer). Falsy default + a non-Object
    // value would trip Vue's prop validator with the boolean `false`. Allow
    // both Object and null/undefined, since registerUploadedFile already
    // guards against the falsy case at call time.
    fileExplorer?: InstanceType<typeof CzFileExplorer> | null;
  }>(),
  {
    s3Host: "http://localhost:9000",
    uploadPrefix: "",
    fileExplorer: null,
  },
);

const emit = defineEmits(["file-uploaded"]);

const selectedFolder = ref<string | null>(null);

watch(() => props.fileExplorer?.selected, onFileSelect);

function onFileSelect() {
  // if the selected is a folder, set selectedFolder
  let selected = props.fileExplorer!.selected;
  // if selected is an array, take the first element
  if (Array.isArray(selected)) {
    if (selected.length > 0) {
      selected = selected[0];
    } else {
      selectedFolder.value = null;
      return;
    }
  }
  // const isFolder = Object.prototype.hasOwnProperty.call(selected, "children");
  const isFolder = props.fileExplorer!.isFolder(selected);
  if (isFolder) {
    selectedFolder.value = props.fileExplorer!.getPathString(selected);
  } else {
    selectedFolder.value = null;
  }
  console.log("selectedFolder set to:", selectedFolder.value);
}

// Method to expose the Uppy instance
function getUppyInstance(): Uppy | null {
  return uppyInstance;
}

// Add files through the component
function addFile(fileData: any): string | null {
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

function upload(): Promise<void> {
  if (uppyInstance) {
    return uppyInstance.upload();
  }
  return Promise.reject(new Error("Uppy instance not available"));
}

defineExpose({ getUppyInstance, addFile, upload });

onMounted(() => {
  initializeUppy();
});

function initializeUppy() {
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
    // Companion imports (Google Drive picker) previously carried the user's
    // S3 keys in these headers. Cookie auth can't reach Companion — it
    // uploads server-side — so only the bucket hint remains; Drive imports
    // need a Companion-side follow-up.
    const headers = {
      "s3-bucket": props.s3Info.bucket,
    };
    console.log("Initializing Uppy");
    uppyInstance = new Uppy({
      id: "uppy",
      autoProceed: true,
      onBeforeUpload: (files) => {
        // Build the S3 key from `uploadPrefix` (e.g. `<id>/data/contents/`),
        // any selected subfolder, and the filename. Falls back to s3Info.prefix
        // only when uploadPrefix wasn't passed — preserves the old contract.
        const basePrefix =
          props.uploadPrefix || props.s3Info.prefix || "";
        Object.keys(files).forEach((fileId) => {
          const file = files[fileId];
          file.meta.bucket_name =
            file?.meta?.bucket_name || props.s3Info.bucket;
          if (!file.meta.dynamic_key) {
            const folder =
              file.meta.existing_path_in_resource || selectedFolder.value || "";
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
        // Do NOT use Companion here: companion generates a UUID S3 key
        // (e.g. `92a92f6b-...-foo.txt`) and files would land at random root
        // paths instead of `<resourceId>/data/contents/`. Upload straight to
        // the hs-s3-proxy with the real key instead — the proxy
        // authenticates the session cookies (plus X-CSRFToken for writes),
        // so no signing or access keys are involved.
        shouldUseMultipart: false,
        getUploadParameters: async (file: any) => {
          const bucket = file.meta.bucket_name || props.s3Info.bucket;
          const key = String(file.meta.dynamic_key || file.name);
          const objectPath = key.split("/").map(encodeURIComponent).join("/");
          const csrfToken = (await User.getCSRFToken()) || "";
          return {
            method: "PUT",
            url: `${props.s3Host}/${bucket}/${objectPath}`,
            fields: {},
            headers: {
              "Content-Type": file.type || "application/octet-stream",
              "X-CSRFToken": csrfToken,
            },
          };
        },
        uploadPartBytes: cookieUploadPartBytes,
      })
      .on("dashboard:modal-open", () => {
        // this is a hack to set the folder when the modal is opened
        // because the selectedFolder will change when the user clicks in the dashboard
        if (selectedFolder.value) {
          uppyInstance.setMeta({
            existing_path_in_resource: selectedFolder.value,
          });
          console.log("Set dashboard folder state to:", selectedFolder.value);
        }
      })
      .on("upload-success", (file: any) => {
        // Hand off to the parent (which owns the file-explorer ref directly).
        // The `fileExplorer` prop passed in here doesn't reliably propagate
        // as a reactive value, so accessing it from inside this Uppy handler
        // is unsafe; an event side-steps that.
        emit("file-uploaded", file);
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
</script>
