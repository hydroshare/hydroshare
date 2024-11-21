import {
  Uppy,
  Dashboard,
  Tus,
  GoldenRetriever,
  GoogleDrive,
  DropTarget,
} from "https://releases.transloadit.com/uppy/v4.4.0/uppy.min.mjs";

let MAX_CHUNK = MAX_CHUNK_MB * 1024 * 1024; // in bytes
const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024; // in bytes

// Make sure the chunk size is not larger than the max file size
if (MAX_CHUNK > MAX_FILE_SIZE) {
  MAX_CHUNK = MAX_FILE_SIZE;
}

const headers = {
  "HS-SID": HS_S_ID
};

let uppy = new Uppy({
  id: "uppy",
  // autoProceed: true,
  // debug: true,
  restrictions: {
    maxFileSize: MAX_FILE_SIZE,
    // restrict uploading a FOLDER with a total size larger than the max file size
    maxTotalFileSize: MAX_FILE_SIZE,
    // maxNumberOfFiles: MAX_NUMBER_OF_FILES,
  },
  onBeforeUpload: (files) => {
    Object.keys(files).forEach((fileId) => {
      // add metadata to the file
      files[fileId].meta.hs_res_id = RES_ID;
      files[fileId].meta.original_file_name = files[fileId].name;
      files[fileId].meta.existing_path_in_resource = JSON.stringify(
        getCurrentPath()
      );
      // add the file size to the metadata
      files[fileId].meta.file_size = files[fileId].data.size;
    });
    return files;
  },
  onBeforeFileAdded: (currentFile, files) => {
    // https://uppy.io/docs/uppy/#onbeforefileaddedfile-files
    // check for existing files before adding to the resource
    // window.fbFiles and fbFolders are set in the file_browser.html template

    let path = currentFile?.meta?.relativePath

    // check existing dirs if uploading a folder
    if (window.fbFolders){
      // strip the filename from the currentFile.meta.relativePath
      // we only check the first level directory
      if (path) {
        path = path.split("/")[0];
        const existingFolders = window.fbFolders.map((folder) => folder.name);
        if (existingFolders.includes(path)) {
          uppy.info(
            `Folder ${path} already exists in the resource. Remove or rename.`
          );
          return false;
        }
      }
    }

    // check existing files
    if (window.fbFiles) {
      const existingFiles = window.fbFiles.map((f) => f.name);
      if (existingFiles.includes(currentFile.name) && !path) {
        uppy.info(
          `File ${currentFile.name} already exists in the resource. Remove or rename.`
        );
        return false;
      }
    }
  },
})
  .use(GoldenRetriever)
  .use(Dashboard, {
    inline: false,
    closeModalOnClickOutside: true,
    fileManagerSelectionType: "both", // files and folders
    target: "#uppy",
    showProgressDetails: true,
    trigger: "#uppy-modal-trigger",
    note: `Max file size: ${(MAX_FILE_SIZE_MB / 1024).toFixed(2)} GB`,
    // https://uppy.io/docs/dashboard/#locale
    locale: {
      strings: {
        dropPasteFiles: `Drop files here or %{browseFiles} to upload to ${getCurrentPath()}.`,
      },
    },
  })
  .use(DropTarget, {
    target: "#hsDropzone",
    onDrop: (event) => {
      // open the dashboard when files are dropped
      if (getCurrentPath().hasOwnProperty("aggregation")) {
        // get the file from the event and remove it from the files list
        let file = event.dataTransfer.files[0];
        uppy.removeFile(file.id);
        // Display an error here
        $("#fb-alerts .upload-failed-alert").remove();
        $("#hsDropzone").toggleClass("glow-blue", false);

        $("#fb-alerts")
          .append(
            '<div class="alert alert-danger alert-dismissible upload-failed-alert" role="alert">' +
              '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                '<span aria-hidden="true">&times;</span></button>' +
              "<div>" +
                "<strong>File Upload Failed</strong>" +
              "</div>" +
              "<div>" +
                "<span>File upload is not allowed. Target folder seems to contain aggregation(s).</span>" +
              "</div>" +
            "</div>"
          )
          .fadeIn(200);
        $(".fb-drag-flag").hide();
        return
      }
      uppy.getPlugin("Dashboard").openModal();
    },
    onDragOver: (event) => {
      event.preventDefault();
      event.stopPropagation();
      $(".fb-drag-flag").show();
      $("#hsDropzone").toggleClass("glow-blue", true);
    },
    onDragLeave: (event) => {
      $(".fb-drag-flag").hide();
      $("#hsDropzone").toggleClass("glow-blue", false);
    },
  });
  uppy
  .use(Tus, {
    endpoint: UPPY_UPLOAD_ENDPOINT,
    // https://uppy.io/docs/tus/#headers
    headers: headers,
    // https://uppy.io/docs/tus/#chunksize
    // it is not recommended to set the chunk size
    // however in testing it seems to improve resumability
    chunkSize: MAX_CHUNK, // in bytes
  })
  // https://uppy.io/docs/uppy/#events
  .on("file-added", (file) => {
    if (getCurrentPath().hasOwnProperty("aggregation")) {
      // Remove the file from the upload list
      uppy.removeFile(file.id);
      uppy.info("File upload is not allowed. Target folder seems to contain aggregation(s).", "error");
    }
    
    // if the file source is "local" then impose the file number limit
    // this is because local uploads are more resource intensive than remote (ex google drive) uploads
    if (!file.isRemote ) {
      // count the total number of files that are not isRemote thus far and make sure it is less than MAX_NUMBER_OF_FILES
      const localFiles = uppy.getFiles().filter((f) => !f.isRemote);
      if (localFiles.length > MAX_NUMBER_OF_FILES) {
        uppy.removeFile(file.id);
        uppy.info(
          `The number of files added exceeds the limit of ${MAX_NUMBER_OF_FILES}.`,
          "error"
        );
      }
    }
  })
  .on("dashboard:modal-closed", () => {
    // if there are pending uploads, show an alert that they will continue in the background
    if (Object.keys(uppy.getState().currentUploads).length > 0) {
      $("#fb-alerts")
          .append(
            '<div class="alert alert-info alert-dismissible upload-continue-alert" role="alert">' +
              '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                '<span aria-hidden="true">&times;</span></button>' +
              "<div>" +
                "<strong>Files Uploading</strong>" +
              "</div>" +
              "<div>" +
                "<span>Your files will continue to upload in the background.</span>" +
              "</div>" +
            "</div>"
          )
          .fadeIn(200);
    }
    $(".fb-drag-flag").hide();
    $("#hsDropzone").toggleClass("glow-blue", false);
  })
  .on("dashboard:modal-open", () => {
    $(".fb-drag-flag").show();
    $("#hsDropzone").toggleClass("glow-blue", true);
    $("#fb-alerts .upload-continue-alert").remove();
  })
  .on("upload-success", (file, response) => {
    // handle when a single file is uploaded, for example:
    // uppy.info(
    //   `File ${file.name} was transferered successfully. Adding into HydroShare...`
    // );
  })
  .on("complete", (result) => {
    let resourceType = $("#resource-type").val();
    // Remove further paths from the log
    let range = pathLog.length - pathLogIndex;
    pathLog.splice(pathLogIndex + 1, range);
    pathLog.push(JSON.parse(sessionStorage.currentBrowsepath));
    pathLogIndex = pathLog.length - 1;

    // updateResourceUI() appears not to be needed here
    if (resourceType === "Resource") {
      sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
      refreshFileBrowser();
    } else {
      refreshFileBrowser();
      $("#previews").empty();
    }
  })
  .on("error", (error) => {
    let errorMsg = "";
    if (typeof errorMessage === "object") {
      for (const [key, value] of Object.entries(errorMessage)) {
        errorMsg += `${key}: ${value}`;
      }
    } else {
      errorMsg = JSON.stringify(errorMessage);
    }
    try {
      let errorMessageJSON = JSON.parse(errorMessage);
      if (errorMessageJSON.hasOwnProperty("validation_error")) {
        errorMsg = errorMessageJSON.validation_error;
      } else if (errorMessageJSON.hasOwnProperty("file_size_error")) {
        errorMsg = errorMessageJSON.file_size_error;
      }
    } catch (e) {}

    $("#fb-alerts .upload-failed-alert").remove();
    $("#hsDropzone").toggleClass("glow-blue", false);
    $("#fb-alerts")
      .append(
        '<div class="alert alert-danger alert-dismissible upload-failed-alert" role="alert">' +
          '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
          '<span aria-hidden="true">&times;</span></button>' +
          "<div>" +
          "<strong>File Upload Failed</strong>" +
          "</div>" +
          "<div>" +
          "<span>" +
          errorMsg +
          "</span>" +
          "</div>" +
          "</div>"
      )
      .fadeIn(200);
  })
  .on("progress", (progress) => {
    $("#upload-progress").text(`${progress}%`);
  })
  .use(GoogleDrive, {
    target: Dashboard,
    companionUrl: COMPANION_URL,
  });
