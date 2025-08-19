import {
  Uppy,
  Dashboard,
  Tus,
  GoldenRetriever,
  GoogleDrivePicker,
  DropTarget,
} from "https://releases.transloadit.com/uppy/v4.13.0/uppy.min.mjs";

let uppy = null;
if (HS_S_ID === "") {
  uppy = new Uppy({
    id: "uppy",
    // https://github.com/transloadit/uppy/issues/5542
  })
}
else{
  const WARN_ON_FILES_EXCEEDING_SIZE = 10 * 1024**3; // 10 GB
  // MAX_CHUNK should be less than the DATA_UPLOAD_MAX_MEMORY_SIZE but > 0
  let MAX_CHUNK = MAX_CHUNK_SIZE - 1000000; // 1 MB less than the max chunk size, in bytes
  if (MAX_CHUNK <= 0) {
    MAX_CHUNK = 1;
  }

  // Make sure the chunk size is not larger than the max file size
  if (MAX_CHUNK > FILE_UPLOAD_MAX_SIZE) {
    MAX_CHUNK = FILE_UPLOAD_MAX_SIZE;
  }

  // get the least size between max file size and remaining quota
  // remaining quota can be null which effectively means no limit
  let RESTRICTED_SIZE = FILE_UPLOAD_MAX_SIZE;
  if (REMAINING_QUOTA !== null) {
    RESTRICTED_SIZE = Math.min(FILE_UPLOAD_MAX_SIZE, REMAINING_QUOTA);
  }

  const headers = {
    "HS-SID": HS_S_ID
  };

  let quotaNote = `Max file size: ${formatBytes(parseInt(FILE_UPLOAD_MAX_SIZE))}.`;
  if (REMAINING_QUOTA > 0) {
    // `Remaining Quota: ${formatBytes(parseInt(REMAINING_QUOTA))}.
    quotaNote += ` Remaining Quota: ${formatBytes(parseInt(REMAINING_QUOTA))}.`;
  }

  const TUS_ENDPOINT = `${window.location.origin}${UPPY_UPLOAD_PATH}`

  uppy = new Uppy({
    id: "uppy",
    // https://uppy.io/docs/uppy/#autoproceed
    autoProceed: true,
    // debug: true,
    restrictions: {
      maxFileSize: RESTRICTED_SIZE,
      // restrict uploading a FOLDER with a total size larger than the max file size
      maxTotalFileSize: RESTRICTED_SIZE,
      // maxNumberOfFiles: MAX_NUMBER_OF_FILES_IN_SINGLE_LOCAL_UPLOAD,
    },
    // https://uppy.io/docs/dashboard/#locale
    locale: {
      strings: {
        browseFolders: 'upload a folder',
        dropPasteImportBoth: 'Drop files here, %{browseFolders} or import from:',
        // https://github.com/transloadit/uppy/issues/5542
        pluginNameGoogleDrive: 'Google Drive',
      }
    },
    onBeforeUpload: (files) => {
      Object.keys(files).forEach((fileId) => {
        // add metadata to the file
        files[fileId].meta.hs_res_id = RES_ID;
        files[fileId].meta.hs_res_title = RES_TITLE;
        files[fileId].meta.original_file_name = files[fileId].name;
        files[fileId].meta.existing_path_in_resource = JSON.stringify(
          getCurrentPath()
        );
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

      // check if the file size needs to be warned
      const file_size = currentFile.data.size;
      if (file_size >= WARN_ON_FILES_EXCEEDING_SIZE) {
        let message = `File ${currentFile.name} is ${formatBytes(parseInt(file_size))}. ` +
          `For files larger than ${formatBytes(parseInt(WARN_ON_FILES_EXCEEDING_SIZE))}, `+
          "we recommend that you contact help.cuahsi.org for assistance.";
        uppy.info(message, "warning", 5000);
      }
    },
  })
  .use(Dashboard, {
    inline: false,
    closeModalOnClickOutside: true,
    fileManagerSelectionType: "both", // files and folders
    target: "#uppy",
    showProgressDetails: true,
    trigger: "#uppy-modal-trigger",
    note: quotaNote,
    // https://uppy.io/docs/dashboard/#locale
    locale: {
      strings: {
        dropPasteFiles: `Drop files here or %{browseFiles} to upload to ${getCurrentPath()}.`,
        // Used as the screen reader label for buttons that remove a file.
        // removeFile: "Remove file from upload queue",
        // cancel: 'Cancel',
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
    endpoint: TUS_ENDPOINT,
    // https://uppy.io/docs/tus/#headers
    headers: headers,
    // https://uppy.io/docs/tus/#chunksize
    // it is not recommended to set the chunk size
    // however in testing it seems to improve resumability
    chunkSize: MAX_CHUNK, // in bytes
    // https://uppy.io/docs/tus/#limit
    limit: PARALLEL_UPLOADS_LIMIT || 10,
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
      // count the total number of files that are not isRemote thus far and make sure it is less than MAX_NUMBER_OF_FILES_IN_SINGLE_LOCAL_UPLOAD
      const localFiles = uppy.getFiles().filter((f) => !f.isRemote);
      if (localFiles.length > MAX_NUMBER_OF_FILES_IN_SINGLE_LOCAL_UPLOAD) {
        uppy.removeFile(file.id);
        uppy.info(
          `The number of files added exceeds the limit of ${MAX_NUMBER_OF_FILES_IN_SINGLE_LOCAL_UPLOAD}.`,
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

    // check if there are uploads files added with different resource_id
    // this is to prevent the case that the user stages files for upload into one resource and then switches to another resource
    // and unwittingly uploads the staged files into the new resource
    let files = uppy.getFiles();
    if (files) {
      let otherFiles = files.filter((file) => {
        let res_id = file.meta.hs_res_id
        if ( res_id && res_id !== RES_ID) {
          // uppy.removeFile(file.id);
          return file;
        }else{
          return false;
        }
      });
      if (otherFiles.length > 0) {
        let message = `We recovered files that were orignally staged for upload to a different resource. ` +
        'Please ensure that you are uploading to the intended resource.'
        uppy.info(
          message,
          "error",
          5000
        );
      }
    }
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
  .use(GoogleDrivePicker, {
    // https://uppy.io/docs/google-drive-picker/
    target: Dashboard,
    companionUrl: COMPANION_URL,
    clientId: GOOGLE_PICKER_CLIENT_ID,
    apiKey: GOOGLE_PICKER_API_KEY,
    appId: GOOGLE_PICKER_APP_ID,
  });
}

uppy.use(GoldenRetriever)
// on page load, check the uppy state to see if there were pending uploads
// https://uppy.io/docs/uppy/#getstate
const recoveredFiles = uppy.getState()?.recoveredState?.files
if (recoveredFiles && Object.keys(recoveredFiles).length > 0) {
  // check if the recovered files have the same meta.hs_res_id as the current resource
  let recoveredFilesInCurrentResource = {};
  let recoveredFilesInOtherResource = {};
  Object.keys(recoveredFiles).forEach((fileId) => {
    let file_res_id = recoveredFiles[fileId].meta.hs_res_id
    let file_res_title = recoveredFiles[fileId].meta.hs_res_title
    if ( file_res_id === RES_ID) {
      recoveredFilesInCurrentResource[fileId] = recoveredFiles[fileId];
    }else{
      if (file_res_id && file_res_title) {
        recoveredFilesInOtherResource[fileId] = recoveredFiles[fileId];
      }
    }
  });
  if (Object.keys(recoveredFilesInCurrentResource).length > 0) {
    let message = 'It looks like your upload request got interrupted. \n';
    if (Object.keys(recoveredFilesInCurrentResource).length < 10) {
      message += 'The following files were being uploaded: \n<ul>';
      Object.keys(recoveredFilesInCurrentResource).forEach((fileId) => {
        message += `<li>${recoveredFilesInCurrentResource[fileId].name}</li>`
      });
      message += '</ul>';
    }else{
      message += `A total of ${Object.keys(recoveredFilesInCurrentResource).length} files were being uploaded.\n`
    }
    message +=
    '<a href="#" id="resume-uploads">Click here to resume or cancel uploads.</a>';
    customAlert("Recovered Uploads", message, "error", 100000, true);
    document.getElementById("resume-uploads").addEventListener("click", (event) => {
      event.preventDefault();
      uppy.getPlugin("Dashboard").openModal();
      $(".custom-alert").hide();
    }); 
  }
  if (Object.keys(recoveredFilesInOtherResource).length > 0) {
    let message = 'It looks like your upload request got interrupted. \n';
    if (Object.keys(recoveredFilesInOtherResource).length < 10) {
      message += 'The following files were being uploaded to other resources: \n<ul>';
      Object.keys(recoveredFilesInOtherResource).forEach((fileId) => {
        let res_id = recoveredFilesInOtherResource[fileId].meta.hs_res_id;
        let res_title = recoveredFilesInOtherResource[fileId].meta.hs_res_title;
        message += `<li>${recoveredFilesInOtherResource[fileId].name} in <a href="/resource/${res_id}"> ${res_title}</a></li>`
      });
      message += '</ul>';
    }else{
      message += `A total of ${Object.keys(recoveredFilesInOtherResource).length} files were being uploaded to other resources.\n`
    }
    message += "\nPlease go to the respective resources to resume the uploads."
    message += '\nOr <a href="#" id="cancel-uploads">click here to cancel all recovered uploads.</a>';
    customAlert("Recovered Uploads", message, "error", 100000, true);
    document.getElementById("cancel-uploads").addEventListener("click", (event) => {
      event.preventDefault();
      try{
        uppy.cancelAll()
      }
      catch(e){
        console.error(`Error cancelling uploads: ${e}`);
      }
      $(".custom-alert").hide()
    });
  }
}