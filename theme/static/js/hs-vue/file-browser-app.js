const file_metadata_alert =
    '<div id="#fb-metadata-default" class="alert alert-info text-center" role="alert">' +
        '<div>Select a file to see file type metadata.</div>' +
        '<hr>' +
        '<span class="fa-stack fa-lg text-center"><i class="fa fa-file-o fa-stack-2x" aria-hidden="true"></i>' +
            '<i class="fa fa-mouse-pointer fa-stack-1x" aria-hidden="true" style="top: 14px;"></i>' +
        '</span>' +
    '</div>';

const no_metadata_alert =
'<div class="alert alert-warning text-center" role="alert">' +
    '<div>No file type metadata exists for this file.</div>' +
    '<hr>' +
    '<i class="fa fa-eye-slash fa-3x" aria-hidden="true"></i>' +
'</div>';

const loading_metadata_alert =
'<div class="text-center" role="alert">' +
    '<br>' +
    '<i class="fa fa-spinner fa-spin fa-3x fa-fw icon-blue"></i>' +
    '<span class="sr-only">Loading...</span>' +
'</div>';

const MAX_FILE_SIZE = 1024; // MB

// Initial state for actions where they can appear.
const initActionState = {
    disabled: false, // When an item is disabled, it is disabled everywhere
    /*-- Used to control where and when the action is visible --*/
    // The main toolbar in the file browser
    toolbar: {
        hidden: false,
    },
    // The menu that shows up when right clicking on a file or folder
    fileMenu: {
        hidden: false,
    },
    // The menu that shows up when clicking on the main container. Typically contains directory specific actions
    containerMenu: {
        hidden: false,
    }
};

const fileBrowserApp = new Vue({
  el: '#hs-file-browser',
    delimiters: ['${', '}'],
    data: {
        sourcePaths: { path: null, selected:[] },
        pathLog: [],
        pathLogIndex: 0,
        isDragging: false,
        isDownloadZipped: false,
        currentAggregations: [],
        removeCitationIntent: false,
        files: [],
        folders: [],
        mode: '',
        canBePublic: false
    },
    watch: {
        resAccess: function (oldVal, newVal) {
           
        },
    },
    computed: {
        // File sorting sort algorithms
        sortedFiles: function() {
            const vue = this
            const directoryItems = [...vue.files, ...vue.folders]

            if (method === "name") {
                // Sort by name
                if (order === "asc") {
                    return directoryItems.sort((fileOrFolder1, fileOrFolder2) => {
                        const name1 = fileOrFolder1.fileName || fileOrFolder1.folderName
                        const name2 = fileOrFolder2.fileName || fileOrFolder2.folderName
                        return (name2).localeCompare(name1)
                    })
                }
                else {
                    return directoryItems.sort((fileOrFolder1, fileOrFolder2) => {
                        const name1 = fileOrFolder1.fileName || fileOrFolder1.folderName
                        const name2 = fileOrFolder2.fileName || fileOrFolder2.folderName
                        return (name1).localeCompare(name2)
                    })
                }
            }
            else if (method === "size") {
                // Sort by size
                return directoryItems.sort((fileOrFolder1, fileOrFolder2) => {
                    const size1 = fileOrFolder1.size
                    const size2 = fileOrFolder2.size
                    return vue.order === 'asc' ? size1 - size2 : size2 - size1
                })
            }
            else if (method === "type") {
                // Sort by type
                if (order === "asc") {
                    return directoryItems.sort((fileOrFolder1, fileOrFolder2) => {
                        const type1 = fileOrFolder1.fileType
                        const type2 = fileOrFolder2.fileType
                        if (type1 !== type2) {
                            return (type2).localeCompare(type1)
                        }
                        else {
                            const name1 = fileOrFolder1.fileName || fileOrFolder1.folderName
                            const name2 = fileOrFolder2.fileName || fileOrFolder2.folderName
                            return (name2).localeCompare(name1)
                        }
                    })
                }
                else {
                    return directoryItems.sort((fileOrFolder1, fileOrFolder2) => {
                        const type1 = fileOrFolder1.fileType
                        const type2 = fileOrFolder2.fileType
                        if (type1 !== type2) {
                            return (type1).localeCompare(type2)
                        }
                        else {
                            const name1 = fileOrFolder1.fileName || fileOrFolder1.folderName
                            const name2 = fileOrFolder2.fileName || fileOrFolder2.folderName
                            return (name1).localeCompare(name2)
                        }
                    })
                }
            }
        },
    },
    methods: {
        getCurrentPath: function() {
            const vue = this;
            return vue.pathLog[pathLogIndex];
        },
        
        clearSourcePaths: function() {
            const vue = this;
            vue.sourcePaths = { path: null, selected: [] };
            $("#fb-files-container li").removeClass("fb-cutting");
        },
        
        getFolderTemplateInstance: function(folder) {
            if (folder['folder_aggregation_type'] === "FileSetLogicalFile" || folder['folder_aggregation_type'] === "ModelProgramLogicalFile"
                || folder['folder_aggregation_type'] === "ModelInstanceLogicalFile") {
                var folderIcons = getFolderIcons();
                let iconTemplate = folderIcons.DEFAULT;
        
                if (folderIcons[folder['folder_aggregation_type']]) {
                    iconTemplate = folderIcons[folder['folder_aggregation_type']];
                }
                return "<li class='fb-folder droppable draggable' data-url='" +
                    folder['url'] + "' data-logical-file-id='" + folder['folder_aggregation_id'] +
                    "' title='" + folder['name'] + "&#13;" + folder['folder_aggregation_name'] + "' >" +
                    iconTemplate +
                    "<span class='fb-file-name'>" + folder['name'] + "</span>" +
                    "<span class='fb-file-type'>File Folder</span>" +
                    "<span class='fb-logical-file-type' data-logical-file-type='" +
                    folder['folder_aggregation_type'] + "' data-logical-file-id='" + folder['folder_aggregation_id'] + "'>" +
                    folder['folder_aggregation_name'] + "</span>" +
                    "<span class='fb-preview-data-url'>" + folder['preview_data_url'] + "</span>" +
                    "<span class='fb-file-size'></span>" +
                    "</li>"
            }
        
            // Default
            return "<li class='fb-folder droppable draggable' data-url='" + folder.url + "' title='" +
                folder.name + "&#13;Type: File Folder'>" +
                "<span class='fb-file-icon fa fa-folder icon-blue'></span>" +
                "<span class='fb-file-name'>" + folder.name + "</span>" +
                "<span class='fb-file-type' data-folder-short-path='" + folder['folder_short_path'] + "'>File Folder</span>" +
                "<span class='fb-logical-file-type' data-logical-file-type-to-set='" +
                folder['folder_aggregation_type_to_set'] + "'></span>" +
                "<span class='fb-preview-data-url'>" + folder['preview_data_url'] + "</span>" +
                "<span class='fb-file-size'></span>" +
                "</li>";
        },
        
        getVirtualFolderTemplateInstance: function(agg) {
            var folderIcons = getFolderIcons();
            let iconTemplate = folderIcons.DEFAULT;
        
            if (folderIcons[agg.logical_type]) {
              iconTemplate = folderIcons[agg.logical_type];
            }
        
            return "<li class='fb-folder droppable draggable' data-url='" + agg.url +
              "' data-logical-file-id='" + agg.logical_file_id + "' title='" +
              agg.name + "&#13;" + agg.aggregation_name + "' data-main-file='" + agg.main_file + "' >" +
              iconTemplate +
              "<span class='fb-file-name'>" + agg.name + "</span>" +
              "<span class='fb-file-type'>File Folder</span>" +
              "<span class='fb-logical-file-type' data-logical-file-type='" + agg.logical_type +
              "' data-logical-file-id='" + agg.logical_file_id + "'>" + agg.logical_type + "</span>" +
              "<span class='fb-preview-data-url'>" + agg.preview_data_url + "</span>" +
              "<span class='fb-file-size'></span>" +
              "</li>";
        },
        
        // Associates file icons with file extensions. Could be improved with a dictionary.
        getFileTemplateInstance: function(file) {
            var fileTypeExt = file.name.substr(file.name.lastIndexOf(".") + 1, file.name.length);
            if (file['logical_type'] === "ModelProgramLogicalFile" && !file.has_model_program_aggr_folder) {
                fileTypeExt = "MP";
            }
            if (file['logical_type'] === "ModelInstanceLogicalFile" && !file.has_model_instance_aggr_folder) {
                fileTypeExt = "MI";
            }
            var iconTemplate;
            var fileIcons = getFileIcons();
        
            if (fileIcons[fileTypeExt.toUpperCase()]) {
                iconTemplate = fileIcons[fileTypeExt.toUpperCase()];
            }
            else if (file.name.toUpperCase().endsWith(".REFTS.JSON")){
                iconTemplate = fileIcons["JSON"];
            }
            else {
                iconTemplate = fileIcons.DEFAULT;
            }
        
            if (file.logical_type.length > 0){
                var title = '' + file.name + "&#13;Type: " + file.type + "&#13;Size: " +
                    formatBytes(parseInt(file.size)) + "&#13;" + file.aggregation_name;
            }
            else {
                var title = '' + file.name + "&#13;Type: " + file.type + "&#13;Size: " +
                    formatBytes(parseInt(file.size));
            }
            return "<li data-pk='" + file.pk + "' data-url='" + file.url + "' data-ref-url='" +
                file.reference_url + "' data-logical-file-id='" + file.logical_file_id +
                "' class='fb-file draggable' title='" + title + "' is-single-file-aggregation='" +
                file.is_single_file_aggregation + "' data-has-model-program-aggr-folder='" +
                file.has_model_program_aggr_folder + "' data-has-model-instance-aggr-folder='" +
                file.has_model_instance_aggr_folder +"'>" +
                iconTemplate +
                "<span class='fb-file-name'>" + file.name + "</span>" +
                "<span class='fb-file-type'>" + file.type + " File</span>" +
                "<span class='fb-logical-file-type' data-logical-file-type='" + file.logical_type + "' data-logical-file-id='" +
                file.logical_file_id +  "'>" + file.aggregation_name + "</span>" +
                "<span class='fb-file-size' data-file-size=" + file.size + ">" + formatBytes(parseInt(file.size)) +
                "</span></li>"
        },
        
        formatBytes: function(bytes) {
            if(bytes < 1024) return bytes + " Bytes";
            else if(bytes < 1048576) return(bytes / 1024).toFixed(1) + " KB";
            else if(bytes < 1073741824) return(bytes / 1048576).toFixed(1) + " MB";
            else return(bytes / 1073741824).toFixed(1) + " GB";
        },
        
        /*
            Updates the state of toolbar and menu buttons when a selection is made.
            All items start as visible and enabled by default. Performs checks and disables as it goes.
        */
        updateSelectionMenuContext: function() {
            var selected = $("#fb-files-container li.ui-selected");
            var resourceType = RES_TYPE;
            var mode = $("#hs-file-browser").attr("data-mode");
            var selectedFileName = selected.children(".fb-file-name").text().toUpperCase();
        
            // correspond to 'data-fb-action' attribute values in the file browser controls that you wish to manage
            const uiActions = [
                "createFolder",
                "cut",
                "delete",
                "download",
                "downloadZipped",
                "getLink",
                "getRefUrl",
                "open",
                "paste",
                "preview",
                "removeAggregation",
                "rename",
                "setFileSetFileType",
                "setGenericFileType",
                "setGeoFeatureFileType",
                "setGeoRasterFileType",
                "setNetCDFFileType",
                "setRefTimeseriesFileType",
                "setTimeseriesFileType",
                "setModelProgramFileType",
                "setModelInstanceFileType",
                "subMenuSetContentType",
                "unzip",
                "updateRefUrl",
                "uploadFiles",
                "zip"
            ];
            var uiActionStates = {};
        
            // Initialize the action states
            $.each(uiActions, function (i, val) {
                uiActionStates[val] = $.extend(true, {}, initActionState);  // Deep copy
            });
        
            var maxSize = MAX_FILE_SIZE * 1024 * 1024; // convert MB to Bytes
        
            if (selected.length > 1) {
                //  ------------- Multiple files selected -------------
                uiActionStates.rename.disabled = true;
                uiActionStates.rename.fileMenu.hidden = true;
        
                uiActionStates.open.disabled = true;
                uiActionStates.open.fileMenu.hidden = true;
        
                uiActionStates.paste.disabled = true;
                uiActionStates.paste.fileMenu.hidden = true;
        
                uiActionStates.zip.disabled = true;
                uiActionStates.zip.fileMenu.hidden = true;
        
                uiActionStates.unzip.disabled = true;
                uiActionStates.unzip.fileMenu.hidden = true;
        
                uiActionStates.downloadZipped.disabled = true;
                uiActionStates.downloadZipped.fileMenu.hidden = true;
        
                uiActionStates.getLink.disabled = true;
                uiActionStates.getLink.fileMenu.hidden = true;
        
                uiActionStates.removeAggregation.disabled = true;
                uiActionStates.removeAggregation.fileMenu.hidden = true;
        
                uiActionStates.setGenericFileType.disabled = true;
                uiActionStates.setGenericFileType.fileMenu.hidden = true;
        
                uiActionStates.setFileSetFileType.disabled = true;
                uiActionStates.setFileSetFileType.fileMenu.hidden = true;
        
                uiActionStates.subMenuSetContentType.disabled = true;
                uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
        
                uiActionStates.getRefUrl.disabled = true;
                uiActionStates.getRefUrl.fileMenu.hidden = true;
        
                uiActionStates.updateRefUrl.disabled = true;
                uiActionStates.updateRefUrl.fileMenu.hidden = true;
        
                uiActionStates.setGeoRasterFileType.disabled = true;
                uiActionStates.setNetCDFFileType.disabled = true;
                uiActionStates.setGeoFeatureFileType.disabled = true;
                uiActionStates.setRefTimeseriesFileType.disabled = true;
                uiActionStates.setTimeseriesFileType.disabled = true;
                uiActionStates.setModelProgramFileType.disabled = true;
                uiActionStates.setModelInstanceFileType.disabled = true;
        
                const foldersSelected = $("#fb-files-container li.fb-folder.ui-selected");
                if(resourceType === 'Composite Resource' && foldersSelected.length > 1) {
                    uiActionStates.removeAggregation.disabled = true;
                    uiActionStates.setFileSetFileType.disabled = true;
                }
                if(resourceType !== 'Composite Resource') {
                    uiActionStates.removeAggregation.disabled = true;
                }
                $("#fileTypeMetaData").html(file_metadata_alert);
                // hide preview option on multiple file selection
                uiActionStates.preview.fileMenu.hidden = true;
            }
            else if (selected.length === 1) {
                // Exactly one item selected
        
                var fileName = $(selected).find(".fb-file-name").text();
        
                //  ------------- The item selected is a folder -------------
                if (selected.hasClass("fb-folder")) {
                    uiActionStates.unzip.disabled = true;
                    uiActionStates.unzip.fileMenu.hidden = true;
        
                    uiActionStates.getRefUrl.disabled = true;
                    uiActionStates.getRefUrl.fileMenu.hidden = true;
        
                    uiActionStates.updateRefUrl.disabled = true;
                    uiActionStates.updateRefUrl.fileMenu.hidden = true;
        
                    // Disable add metadata to file
                    uiActionStates.setGenericFileType.disabled = true;
                    uiActionStates.setGenericFileType.fileMenu.hidden = true;
        
                    // Disable creating aggregations from folders
        
                    uiActionStates.setRefTimeseriesFileType.disabled = true;
                    uiActionStates.setTimeseriesFileType.disabled = true;
                    uiActionStates.setGeoRasterFileType.disabled = true;
                    uiActionStates.setNetCDFFileType.disabled = true;
                    uiActionStates.setGeoFeatureFileType.disabled = true;
                    if (!selected.children('span.fb-logical-file-type').attr("data-logical-file-type") ||
                        !!selected.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set")) {
                        uiActionStates.removeAggregation.disabled = true;
                        uiActionStates.removeAggregation.fileMenu.hidden = true;
                    }
                    else {
                        //  ------------- Folder is a logical file type -------------
                        uiActionStates.zip.disabled = true;
                        uiActionStates.paste.disabled = true;
                        uiActionStates.subMenuSetContentType.disabled = true;
                        uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
                    }
        
                    let previewDataURL = selected.children('span.fb-preview-data-url').text();
                    if (previewDataURL === 'null' || previewDataURL === 'undefined') {
                        uiActionStates.preview.fileMenu.hidden = true;
                    }
        
                    let logicalFileTypeToSet = selected.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set");
                    if (!logicalFileTypeToSet || !logicalFileTypeToSet.length) {
                        uiActionStates.setFileSetFileType.fileMenu.hidden = true;
                        uiActionStates.subMenuSetContentType.disabled = true;
                        uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
                    }
                    else {
                        if (logicalFileTypeToSet !== "ModelProgramLogicalFile" &&
                            logicalFileTypeToSet !== "ModelProgramOrInstanceLogicalFile") {
                            uiActionStates.setModelProgramFileType.fileMenu.hidden = true;
                        }
                        if (logicalFileTypeToSet !=="ModelInstanceLogicalFile" &&
                            logicalFileTypeToSet !=="ModelProgramOrInstanceLogicalFile") {
                            uiActionStates.setModelInstanceFileType.fileMenu.hidden = true;
                        }
                        if (logicalFileTypeToSet === "ModelProgramLogicalFile") {
                            uiActionStates.setFileSetFileType.fileMenu.hidden = true;
                        }
                    }
                }
                //  ------------- The item selected is a file -------------
                else {
                    const logicalFileType = $(selected).find(".fb-logical-file-type").attr("data-logical-file-type").trim();
                    const fileHasModelProgramAggrFolder = $(selected).attr("data-has-model-program-aggr-folder").trim();
                    const fileHasModelInstanceAggrFolder = $(selected).attr("data-has-model-instance-aggr-folder").trim();
                    // Disable add metadata to folder
                    uiActionStates.setFileSetFileType.disabled = true;
                    uiActionStates.setFileSetFileType.fileMenu.hidden = true;
        
                    uiActionStates.preview.disabled = true;
                    uiActionStates.preview.fileMenu.hidden = true;
        
                    if (!fileName.toUpperCase().endsWith(".ZIP")) {
                        uiActionStates.unzip.disabled = true;
                        uiActionStates.unzip.fileMenu.hidden = true;
                    }
        
                    if (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile") {
                        // The file is already part of an aggregation
                        if (logicalFileType === "GenericLogicalFile") {
                            uiActionStates.setGenericFileType.disabled = true;
                            uiActionStates.setGenericFileType.fileMenu.hidden = true;
                        }
                        if (logicalFileType !== "ModelInstanceLogicalFile") {
                            uiActionStates.subMenuSetContentType.disabled = true;
                            uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
                        }
                        if ((logicalFileType === "ModelInstanceLogicalFile" && fileHasModelInstanceAggrFolder !== 'true')
                            || logicalFileType === "ModelProgramLogicalFile") {
                            // the file is part of a model instance aggregation based on a single file or the file is part of
                            // a model program aggregation
                            uiActionStates.setGenericFileType.disabled = true;
                            uiActionStates.setGenericFileType.fileMenu.hidden = true;
                            uiActionStates.subMenuSetContentType.disabled = true;
                            uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
                        }
                        if (logicalFileType !== "ModelInstanceLogicalFile" && fileHasModelInstanceAggrFolder === 'true'){
                            // the file is not a model instance aggregation but part of a model instance aggregation
                            // based on a folder - e.g., a single file aggregation living inside a folder that represents
                            // a model instance aggregation
                            uiActionStates.subMenuSetContentType.disabled = true;
                            uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
                            uiActionStates.setGenericFileType.disabled = true;
                            uiActionStates.setGenericFileType.fileMenu.hidden = true;
                        }
                    }
        
                    if (!fileName.toUpperCase().endsWith(".TIF") && !fileName.toUpperCase().endsWith(".TIFF") ||
                        logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile" &&
                        logicalFileType !== "ModelInstanceLogicalFile") {
                        uiActionStates.setGeoRasterFileType.disabled = true;
                    }
        
                    if (!fileName.toUpperCase().endsWith(".NC") ||
                        (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile" &&
                            logicalFileType !== "ModelInstanceLogicalFile")) {
                        uiActionStates.setNetCDFFileType.disabled = true;
                    }
        
                    if ((!fileName.toUpperCase().endsWith(".SHP")) ||
                        (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile" &&
                            logicalFileType !== "ModelInstanceLogicalFile")) {
                        uiActionStates.setGeoFeatureFileType.disabled = true;
                    }
        
                    if (!fileName.toUpperCase().endsWith(".REFTS.JSON") ||
                        (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile" &&
                            logicalFileType !== "ModelInstanceLogicalFile")) {
                        uiActionStates.setRefTimeseriesFileType.disabled = true;
                    }
        
                    if ((!fileName.toUpperCase().endsWith(".SQLITE") && !fileName.toUpperCase().endsWith(".CSV")) ||
                        (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile" &&
                            logicalFileType !== "ModelInstanceLogicalFile")) {
                        uiActionStates.setTimeseriesFileType.disabled = true;
                    }
        
                    if (logicalFileType === "GeoRasterLogicalFile" || logicalFileType === "NetCDFLogicalFile" ||
                        logicalFileType === "GeoFeatureLogicalFile" || logicalFileType === "TimeSeriesLogicalFile") {
                        uiActionStates.cut.disabled = true;
                        uiActionStates.paste.disabled = true;
                        uiActionStates.createFolder.disabled = true;
                    }
        
                    if (selectedFileName.endsWith('.URL')) {
                        // disable remove aggregation option if it is URL file
                        uiActionStates.removeAggregation.disabled = true;
        
                        if (mode !== "edit") {
                            uiActionStates.updateRefUrl.disabled = true;
                            uiActionStates.updateRefUrl.fileMenu.hidden = true;
                        }
                    }
                    else {
                        uiActionStates.getRefUrl.disabled = true;
                        uiActionStates.getRefUrl.fileMenu.hidden = true;
        
                        uiActionStates.updateRefUrl.disabled = true;
                        uiActionStates.updateRefUrl.fileMenu.hidden = true;
                    }
        
                    if (!logicalFileType) {
                        // The selected file is not part of a logical file type
                        uiActionStates.removeAggregation.disabled = true;
                        uiActionStates.removeAggregation.fileMenu.hidden = true;
                    }
                    else {
                        // The selected file is part of a logical file type
                        if (logicalFileType !== 'RefTimeseriesLogicalFile' && logicalFileType !== "GenericLogicalFile"
                            && logicalFileType !== "ModelProgramLogicalFile" && logicalFileType !== "ModelInstanceLogicalFile") {
                            // if the selected file is not part of the RefTimeseriesLogical or GenericLogicalFile file (aggregation)
                            // ModelInstanceLogicalFile or ModelProgramLogicalFile don't show the Remove Aggregation option
                            uiActionStates.removeAggregation.disabled = true;
                            uiActionStates.removeAggregation.fileMenu.hidden = true;
                        }
                        else {
                            if ((logicalFileType === "ModelProgramLogicalFile" && fileHasModelProgramAggrFolder === "true") ||
                                (logicalFileType === "ModelInstanceLogicalFile" && fileHasModelInstanceAggrFolder === "true")) {
                                // don't show option to remove aggregation for a file that's part of a model program/instance aggregation
                                // created based on a folder
                                uiActionStates.removeAggregation.disabled = true;
                                uiActionStates.removeAggregation.fileMenu.hidden = true;
                                // hide option to create model aggregation
                                uiActionStates.setModelInstanceFileType.fileMenu.hidden = true;
                                uiActionStates.setModelProgramFileType.fileMenu.hidden = true;
                            }
                        }
                    }
                }
            }
            else {
                // ------------- No files selected -------------
                uiActionStates.cut.disabled = true;
                uiActionStates.rename.disabled = true;
                uiActionStates.unzip.disabled = true;
                uiActionStates.zip.disabled = true;
                uiActionStates.delete.disabled = true;
                uiActionStates.download.disabled = true;
                uiActionStates.downloadZipped.disabled = true;
                uiActionStates.getLink.disabled = true;
                uiActionStates.setGenericFileType.disabled = true;
                uiActionStates.setFileSetFileType.disabled = true;
                uiActionStates.setNetCDFFileType.disabled = true;
                uiActionStates.setGeoRasterFileType.disabled = true;
                uiActionStates.setGeoFeatureFileType.disabled = true;
                uiActionStates.setTimeseriesFileType.disabled = true;
                uiActionStates.setModelProgramFileType.disabled = true;
                uiActionStates.setModelInstanceFileType.disabled = true;
                uiActionStates.preview.disabled = true;
        
                if (resourceType === 'Composite Resource') {
                    $("#fb-files-container").find('span.fb-logical-file-type').each(function () {
                        const logicalFileType = $(this).attr("data-logical-file-type");
                        //disable folder creation in aggregation folders
                        //TODO this needs to be updated when new aggregations are added...
                        if (logicalFileType === "GeoRasterLogicalFile" || logicalFileType === "NetCDFLogicalFile" ||
                            logicalFileType === "GeoFeatureLogicalFile" || logicalFileType === "TimeSeriesLogicalFile") {
                            if ($(this).parent().hasClass("fb-file")) {
                                uiActionStates.createFolder.disabled = true;
                                uiActionStates.paste.disabled = true;
                                uiActionStates.uploadFiles.disabled = true;
                            }
                        }
                    })
                }
        
                $("#fileTypeMetaData").html(file_metadata_alert);
            }
        
            // ------------- Any number of items selected ----------------------
        
            // Check if any aggregation was included in the selection
            selected.each(function () {
                if (isVirtualFolder(selected[0])) {
                    uiActionStates.createFolder.disabled = true;
                    uiActionStates.delete.disabled = !selected.hasClass("fb-folder");
                    // uiActionStates.cut.disabled = true;
                    uiActionStates.setGenericFileType.disabled = true;
                }
            });
        
            //  ------------- A file is included in the selection -------------
            if (selected.hasClass("fb-file")) {
                uiActionStates.open.disabled = true;
                uiActionStates.open.fileMenu.hidden = true;
        
                uiActionStates.paste.disabled = true;
                uiActionStates.paste.fileMenu.hidden = true;
        
                uiActionStates.zip.disabled = true;
                uiActionStates.zip.fileMenu.hidden = true;
            }
        
            if (!sourcePaths.selected.length) {
                uiActionStates.paste.disabled = true;
            }
        
            if (getCurrentPath().hasOwnProperty("aggregation")) {
                //  ------------- The current path points to an aggregation -------------
                uiActionStates.setGenericFileType.disabled = true;
                uiActionStates.setGenericFileType.fileMenu.hidden = true;
        
                uiActionStates.setFileSetFileType.disabled = true;
                uiActionStates.setFileSetFileType.fileMenu.hidden = true;
        
                uiActionStates.uploadFiles.disabled = true;
        
                let logicalFileType = getCurrentPath().aggregation.logical_type;
                let aggregationTypes = [
                    "GeoRasterLogicalFile",
                    "NetCDFLogicalFile",
                    "GeoFeatureLogicalFile",
                    "TimeSeriesLogicalFile"
                ];
        
                //  ------------- Logic specific to the aggregation types above -------------
                if ($.inArray(logicalFileType, aggregationTypes) >= 0) {
                    uiActionStates.rename.disabled = true;
                    uiActionStates.delete.disabled = true;
                }
            }
        
            // Toggle properties based on states
            $.each(uiActionStates, function (uiAction, element) {
                $("[data-fb-action='" + uiAction + "']").toggleClass("disabled", element.disabled);
        
                let rightClickMenuItems = $("#right-click-menu").find("[data-fb-action='" + uiAction + "']");
                rightClickMenuItems.toggleClass("hidden", element.fileMenu.hidden);
        
                let containerMenuItems = $("#right-click-container-menu").find("[data-fb-action='" + uiAction + "']");
                containerMenuItems.toggleClass("hidden", element.containerMenu.hidden);
            });
        
            $("#open-separator").toggleClass("hidden", uiActionStates.open.fileMenu.hidden);
            $("#content-type-separator").toggleClass("hidden", mode !== "edit" || uiActionStates.removeAggregation.fileMenu.hidden && uiActionStates.subMenuSetContentType.fileMenu.hidden);
            $("#zip-separator").toggleClass("hidden", uiActionStates.zip.fileMenu.hidden && uiActionStates.unzip.fileMenu.hidden);
        },
        
        // Proxy function when pasting in current directory triggering from menu item or button
        onPaste: function() {
            const folderName = $("#fb-files-container li.ui-selected").find(".fb-file-name").text();
            paste(getCurrentPath().path.concat(folderName))
        },
        
        // Pastes the files currently in the global variable source Paths into a destination path
        paste: function(destPath) {
            let calls = [];
            let localSources = [];
        
            // var localSources = sourcePaths.slice();  // avoid concurrency botch due to call by reference
            sourcePaths.selected.each(function () {
                if (isVirtualFolder(this)) {
                    let item = $(this);
                    const hs_file_type = item.find(".fb-logical-file-type").attr("data-logical-file-type");
                    const file_type_id = item.attr("data-logical-file-id");
                    calls.push(move_virtual_folder_ajax_submit(hs_file_type, file_type_id, destPath.join('/')));
                }
                else {
                    const itemName = $(this).find(".fb-file-name").text();
                    localSources.push(sourcePaths.path.concat(itemName).join('/'));
                    $(this).addClass("fb-cutting");
                }
            });
        
            if (localSources.length) {
                calls.push(move_to_folder_ajax_submit(localSources, destPath.join('/')));
            }
        
            // Wait for the asynchronous call to finish to get new folder structure
            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
                clearSourcePaths();
            });
        
            $.when.apply($, calls).fail(function () {
                refreshFileBrowser();
                clearSourcePaths();
            });
        },
        
        bindFileBrowserItemEvents: function() {
        
            var mode = $("#hs-file-browser").attr("data-mode");
            // Drop
            if (mode === "edit") {
                $(".droppable").droppable({
                    drop: function (event, ui) {
                        var destination = $(event.target);
                        if (isVirtualFolder(destination)) {
                            return; // Moving files into aggregations is not allowed
                        }
                        var selection = $("#fb-files-container li.ui-selected");
                        var destName = destination.find(".fb-file-name").text();
                        var destFileType = destination.find(".fb-file-type").text();
        
                        if (destFileType !== "File Folder") {
                            return;
                        }
        
                        // Load the files to be moved
                        sourcePaths = {path: getCurrentPath().path, selected: selection};
                        paste(getCurrentPath().path.concat(destName));
                        $("#fb-files-container li.ui-selected").fadeOut();
                    },
                    over: function (event, ui) {
                        if (!$(event.target).hasClass("ui-selected")) {
                            $("#fb-files-container li.ui-selected").addClass("fb-drag-cutting");
                            let target = $(event.target);
                            if (!target.attr("data-logical-file-id")) {
                                target.addClass("fb-drag-cutting");
                            }
                        }
                    },
                    out: function (event, ui) {
                        $("#fb-files-container li.ui-selected").removeClass("fb-drag-cutting");
                        $(event.target).removeClass("fb-drag-cutting");
                    },
                    accept: 'li'
                });
            }
        
            // Handle "select" of clicked elements - Mouse Down
            $("#fb-files-container").on("mousedown", "li", function (e) {
                if (e.ctrlKey) {
                    $(this).toggleClass("ui-selected");
                }
                else {
                    if (!$(this).hasClass("ui-selected")) {
                        $("#fb-files-container li").removeClass("ui-selected");
                        $(this).addClass("ui-selected");
                    }
                }
        
                if (!e.shiftKey) {
                    $("#fb-files-container li").removeClass("ui-last-selected");
                    $(this).addClass("ui-last-selected");
                }
            });
        
            $("#fb-files-container").on("mouseup", "li", function (e) {
                // Handle "select" of clicked elements - Mouse Up
                if (!e.ctrlKey && !e.metaKey) {
                    if (!isDragging && e.which == 1) {
                        $("#fb-files-container li").removeClass("ui-selected");
                    }
                    $(this).addClass("ui-selected");
                }
        
                // Handle selecting multiple elements with Shift + Click
                if (!e.shiftKey) { // shift key not engaged
                    $("#fb-files-container li").removeClass("ui-last-selected");
                    $(this).addClass("ui-last-selected");
                }
                else { // shift key is engaged
                    var lastSelected = $("#fb-files-container").find(".ui-last-selected").index();
                    var range = $(this).index();
        
                    var items = $("#fb-files-container li");
                    items.removeClass("ui-selected");
        
                    var maxRange =  Math.max(lastSelected, range);
                    var minRange = Math.min(lastSelected, range);
        
                    for (var i = 0; i < items.length; i++) {
                        if (i >= minRange && i <= maxRange) {
                             $(items[i]).addClass("ui-selected");
                        }
                    }
                }
                updateSelectionMenuContext();
            });
        
            // Drag method
            if (mode === "edit") {
                $(".draggable").draggable({
                        containment: "#fb-files-container",
                        start: function (event, ui) {
                            $(ui.helper).addClass(".ui-selected");
                            isDragging = true;
                        },
                        stop: function (event, ui) {
                            $("#fb-files-container li.ui-selected").removeClass("fb-drag-cutting");
                            // Custom revert to handle multiple selection
                            $('#fb-files-container li').animate({top: 0, left: 0}, 200);
                            isDragging = false;
                        },
                        drag: function (event, ui) {
                            $('.ui-selected').css({
                                top: ui.position.top,
                                left: ui.position.left
                            });
                        }
                    }
                );
            }
        
            // Provides selection by drawing a rectangular area
            $("#fb-files-container").selectable({
                filter: "li", cancel: ".ui-selected",
                stop: function (event, ui) {
                    $(".selection-menu").hide();
                    updateSelectionMenuContext();
        
                    $("#fb-files-container li").removeClass("ui-last-selected");
                    $("#fb-files-container li.ui-selected").first().addClass("ui-last-selected");
                }
            });
        
            // Dismiss right click menu when mouse down outside of it
            $("#fb-files-container, #fb-files-container li, #hsDropzone").mousedown(function () {
                $(".selection-menu").hide();
            });
        
            var timer = 0;
            var delay = 200;
            var prevent = false;
        
            $("#hs-file-browser li.fb-folder").dblclick(function () {
                clearTimeout(timer);
                prevent = true;
                onOpenFolder();
            });
        
            $("#hs-file-browser li.fb-folder, #hs-file-browser li.fb-file").click(function () {
                // Do not load file metadata if the side panel is hidden
                if ($("#fb-metadata").hasClass("hidden")) {
                    return;
                }
                $("#fileTypeMetaData").html(loading_metadata_alert);
                timer = setTimeout(function () {
                    if (!prevent) {
                        showFileTypeMetadata(false, "");
                    }
                    prevent = false;
                }, delay);
            });
        
            $("#hs-file-browser li.fb-file").dblclick(onOpenFile);
        
            // Right click menu for file browser
            $("#hsDropzone").bind("contextmenu", function (event) {
                // Avoid the real one
                event.preventDefault();
        
                var menu;   // The menu to show
                updateSelectionMenuContext();
        
                if ($(event.target).closest("li").length) {     // If a file item was clicked
                    if (!$(event.target).closest("li").hasClass("ui-selected")) {
                        $(".ui-selected").removeClass("ui-selected");
                        $(event.target).closest("li").addClass("ui-selected");
                        $("#fb-files-container li").removeClass("ui-last-selected");
                        $(event.target).closest("li").addClass("ui-last-selected");
                    }
                    menu = $("#right-click-menu");
        
                    var fileAggType = [];
                    let target = $(event.target).closest("li");
        
                    // main-file is available on the aggregation folder and only single file aggregations have a data-pk of 1 on the file
                    if (isVirtualFolder(target) || target.attr("main-file") || target.attr("is-single-file-aggregation") === "true"){
                        fileAggType = target.find("span.fb-logical-file-type").attr("data-logical-file-type");
                    }
                    var fileName = target.find("span.fb-file-name").text();
                    var fileExtension = fileName.substr(fileName.lastIndexOf("."), fileName.length);
        
                    // toggle apps by file extension and aggregations
                    let hasTools = false;
                    menu.find("li.btn-open-with").each(function() {
                        let agg_app = false;
                        if ($(this).attr("data-agg-types")){
                            agg_app = $.inArray(fileAggType, $(this).attr("data-agg-types").split(",")) !== -1;
                        }
                        var extension_app = false;
                        if ($(this).attr("data-file-extensions")){
                            let extensions = $(this).attr("data-file-extensions").split(",");
                            for (let i = 0; i < extensions.length; ++i) {
                                if (fileExtension.toLowerCase() === extensions[i].trim().toLowerCase()){
                                    extension_app = true;
                                    break;
                                }
                            }
                        }
                        $(this).toggle(agg_app || extension_app);
                        hasTools = hasTools || agg_app || extension_app;
                    });
                    $("#tools-separator").toggleClass("hidden", !hasTools);
                }
                else {
                    menu = $("#right-click-container-menu");    // empty space was clicked
                }
        
                $(".selection-menu").hide();    // Hide other menus
        
                var top = event.pageY;
                var left = event.pageX;
        
                menu.css({top: top, left: left});
        
                if (menu.css("display") === "none") {
                    menu.show();
                }
                else {
                    menu.hide();
                }
            });
        },
        
        showFileTypeMetadata: function(file_type_time_series, url){
            // when viewing timeseries file metadata by series id, *file_type_time_series* parameter must be
            // set to true and the *url* must be set
            // remove anything displayed currently for the aggregation metadata
        
            var selectedItem = $("#fb-files-container li.ui-selected");
            var logical_file_id = selectedItem.attr("data-logical-file-id");
            if (getCurrentPath().hasOwnProperty("aggregation") ||
              !logical_file_id || (logical_file_id && logical_file_id.length == 0)) {
                $("#fileTypeMetaData").html(no_metadata_alert);
                // Set corresponding action for "Add metadata" button in side bar
                if (selectedItem.hasClass("fb-file")) {
                    $("#btnSideAddMetadata").attr("data-fb-action", "setGenericFileType");
                }
                else if (selectedItem.hasClass("fb-folder")) {
                    var folderLogicalFileTypeToSet = selectedItem.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set");
                    if (folderLogicalFileTypeToSet === undefined || folderLogicalFileTypeToSet === "ModelProgramLogicalFile" ||
                        folderLogicalFileTypeToSet.length === 0) {
                        $("#fileTypeMetaData").html(no_metadata_alert);
                        $("#btnSideAddMetadata").addClass("disabled");
                    }
                    else {
                        $("#btnSideAddMetadata").attr("data-fb-action", "setFileSetFileType");
                    }
                }
                else {
                    $("#btnSideAddMetadata").attr("data-fb-action", "setFileSetFileType");
                }
        
                if (getCurrentPath().hasOwnProperty("aggregation")) {
                    // Metadata can't be added to aggregation files
                    $("#btnSideAddMetadata").addClass("disabled");
                }
                return;
            }
        
            var logical_type = selectedItem.children('span.fb-logical-file-type').attr("data-logical-file-type");
            if (!logical_type) {
                return;
            }
            if (selectedItem.hasClass("fb-file")) {
                // we need to show file type metadata when a file is selected if that file is not part
                // of a FileSet aggregation
                if (logical_type === "FileSetLogicalFile") {
                    $("#fileTypeMetaData").html(no_metadata_alert);
                    $("#btnSideAddMetadata").attr("data-fb-action", "setGenericFileType");
                    updateSelectionMenuContext();
                    return;
                }
                else if (logical_type === "ModelProgramLogicalFile") {
                    if (selectedItem.attr('data-has-model-program-aggr-folder') === 'true') {
                        $("#fileTypeMetaData").html(no_metadata_alert);
                        $("#btnSideAddMetadata").addClass("disabled");
                        return;
                    }
                }
                else if (logical_type === "ModelInstanceLogicalFile") {
                    if (selectedItem.attr('data-has-model-instance-aggr-folder') === 'true') {
                        $("#fileTypeMetaData").html(no_metadata_alert);
                        $("#btnSideAddMetadata").addClass("disabled");
                        return;
                    }
                }
            }
            else if (selectedItem.hasClass("fb-folder")) {
                var folderLogicalFileTypeToSet = selectedItem.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set");
                if (folderLogicalFileTypeToSet === undefined || folderLogicalFileTypeToSet === "ModelProgramLogicalFile" ||
                    folderLogicalFileTypeToSet.length === 0) {
                    $("#fileTypeMetaData").html(no_metadata_alert);
                    $("#btnSideAddMetadata").addClass("disabled");
                }
            }
        
            var resource_mode = RESOURCE_MODE;
            if (!resource_mode) {
                return;
            }
            resource_mode = resource_mode.toLowerCase();
            if(RESOURCE_PUBLISHED) {
                resource_mode = 'view';
            }
            var $url;
            if (file_type_time_series) {
                $url = url;
            }
            else {
                $url = "/hsapi/_internal/" + logical_type + "/" + logical_file_id + "/" + resource_mode + "/get-file-metadata/";
            }
        
            $(".file-browser-container, #fb-files-container").css("cursor", "progress");
        
            var calls = [];
            calls.push(get_file_type_metadata_ajax_submit($url));
        
            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function (result) {
                 var json_response = JSON.parse(result);
                 if(json_response.status === 'error') {
                     var error_html = '<div class="alert alert-danger alert-dismissible upload-failed-alert" role="alert">' +
                                        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                                            '<span aria-hidden="true">&times;</span></button>' +
                                        '<div>' +
                                            '<strong>File Type Metadata Error</strong>'+
                                        '</div>'+
                                        '<div>'+
                                            '<span>' + json_response.message + '</span>' +
                                        '</div>'+
                                    '</div>';
                     $("#fileTypeMetaData").html(error_html);
                     $(".file-browser-container, #fb-files-container").css("cursor", "auto");
                     return;
                 }
        
                $("#fileTypeMetaData").html(json_response.metadata);
                $(".file-browser-container, #fb-files-container").css("cursor", "auto");
                $("#btn-add-keyword-filetype").click(onAddKeywordFileType);
        
                 $("#txt-keyword-filetype").keypress(function (e) {
                     e.which = e.which || e.keyCode;
                     if (e.which == 13) {
                         onAddKeywordFileType();
                         return false;
                     }
                 });
        
                if (logical_type === 'TimeSeriesLogicalFile') {
                    $("#series_id_file_type").change(function () {
                        var $url = $(this.form).attr('action');
                        $url = $url.replace('series_id', $(this).val());
                        $url = $url.replace('resource_mode', resource_mode);
                        // make a recursive call to this function
                        showFileTypeMetadata(true, $url);
                    });
                }
        
                if (RESOURCE_MODE === "Edit") {
                     $("[data-toggle=tooltip]").tooltip();
                     $("#lst-tags-filetype").find(".icon-remove").click(onRemoveKeywordFileType);
                     $("#id-update-netcdf-file").click(update_netcdf_file_ajax_submit);
                     $("#id-update-sqlite-file").click(update_sqlite_file_ajax_submit);
                     showMetadataFormSaveChangesButton();
                     initializeDatePickers();
                     var bindCoordinatesPicker = true;
                     // show/hide spatial delete option for aggregation in addition to other settings for
                     // aggregation spatial coverage form
                     setFileTypeSpatialCoverageFormFields(logical_type, bindCoordinatesPicker);
                     // show/hide temporal data delete option for the aggregation
                     setFileTypeTemporalCoverageDeleteOption(logical_type);
                     // Bind event handler for submit button
                     setFileTypeMetadataFormsClickHandlers();
        
                     var $spatialRadioBox = $("#id_type_filetype").find('input[type="radio"][value="box"]');
                     var $spatialRadioPoint = $("#id_type_filetype").find('input[type="radio"][value="point"]');
                     if (logical_type === "NetCDFLogicalFile") {
                         // don't let the user open the Projection String Type dropdown list
                         // when editing Original Coverage element
                         $("#id_projection_string_type_filetype").css('pointer-events', 'none');
                         // don't let the user open the Variable type dropdown list when editing
                         // Variable elements
                         $("[id ^=id_Variable-][id $=-type]").css('pointer-events', 'none');
                     }
                     if (logical_type === "RefTimeseriesLogicalFile"){
                         var $startDateElement = $("#id_start_filetype");
                         var $endDateElement = $("#id_end_filetype");
                         $startDateElement.css('pointer-events', 'none');
                         $endDateElement.css('pointer-events', 'none');
                     }
                     if (logical_type === 'TimeSeriesLogicalFile') {
                         if ($("#metadata-dirty").val() !== 'True' || $("#can-update-sqlite-file").val() !== 'True'){
                             $("#div-sqlite-file-update").hide();
                         }
                         $(".hs-coordinates-picker").each(function() {
                                const instance = $(this);
                                instance.coordinatesPicker();
                         });
                         InitializeTimeSeriesFileTypeForms();
                     }
                     if (logical_type === "GeoRasterLogicalFile"){
                         $spatialRadioBox.prop("checked", true);
                         $("#id_type_filetype input:radio").trigger("change");
                         $spatialRadioBox.attr('onclick', 'return false');
                         $spatialRadioPoint.attr('onclick', 'return false');
                     }
                     else {
                         if ($spatialRadioBox.attr('checked') === 'checked'){
                             $spatialRadioBox.prop("checked", true);
                         }
                         else {
                             $spatialRadioPoint.prop("checked", true);
                         }
                     }
                     if (logical_type === "FileSetLogicalFile" || logical_type === "ModelInstanceLogicalFile") {
                         // Submit for aggregation spatial coverage update
                         $("#btn-update-aggregation-spatial-coverage").click(function () {
                            nested_aggregation_coverage_update_ajax_submit(logical_file_id, 'spatial');
                         });
                         // Submit for aggregation temporal coverage update
                         $("#btn-update-aggregation-temporal-coverage").click(function () {
                            nested_aggregation_coverage_update_ajax_submit(logical_file_id, 'temporal');
                         });
                     }
                     if (logical_type === "ModelProgramLogicalFile") {
                          setupModelProgramFileTypeUI();
                          setupModelProgramTypeUI();
                          $("#mi-json-schema-file").change(function () {
                            $(".btn-form-submit").show();
                        })
                     }
                     if (logical_type === "ModelInstanceLogicalFile") {
                          setupModelInstanceTypeUI();
                         $("#btn-mi-schema-update").click(function () {
                            updateModelInstanceMetaSchema();
                         });
                     }
                }
            });
        },
        
        setupModelProgramFileTypeUI: function() {
            // controls the UI for associating aggregation files to specific model program file type
            // (release notes, model engine etc)
            var mpContentFiles = $("#mp_content_files");
            $(mpContentFiles).find("select").change(function (e) {
                var inputElement =  $(mpContentFiles).find("input");
                var selectedOptions = $(mpContentFiles).find("option:selected");
                var inputElementValue = "";
                for(var i=0; i< selectedOptions.length; i++) {
                    var selectedFileType = $(selectedOptions[i]).val();
                    if (!selectedFileType) {
                        selectedFileType = "None";
                    }
                    if(i == 0) {
                        inputElementValue += $(selectedOptions[i]).parents(".file-row").find("p").text() + ":" + selectedFileType;
                    }
                    else {
                        inputElementValue += ";" + $(selectedOptions[i]).parents(".file-row").find("p").text() + ":" + selectedFileType;
                    }
                }
                inputElement.attr("value", inputElementValue);
        
                $(this).parents("form").find(".btn-form-submit").show();
            })
        },
        
        setupModelProgramTypeUI: function() {
            var mpProgramType = $("#mp-program-type");
            $(mpProgramType).find("select").change(function (e) {
                var inputElement =  $(mpProgramType).find("input");
                var selectedOption = $(mpProgramType).find("option:selected");
                inputElement.attr("value", $(selectedOption).val());
                $(this).parents("form").find(".btn-form-submit").show();
             })
        },
        
        setupModelInstanceTypeUI: function() {
            $("#filetype-model-instance").change(function () {
                $(this).find(".btn-form-submit").show();
            });
        
            if($("#id-schema-based-form").length){
                var jsonSchema = $("#id-schema-based-form").find("#id-json-schema").val();
                jsonSchema = JSON.parse(jsonSchema);
                var jsonData = $("#id-schema-based-form").find("#id-metadata-json").val();
                jsonData = JSON.parse(jsonData);
            }
            else {
                jsonSchema = {};
                jsonData = {};
            }
        
            // if there is a metadata schema - create the metadata editing form
            if(!jQuery.isEmptyObject(jsonSchema)) {
                var editor = new JSONEditor(document.getElementById('editor-holder'), {
                    schema: jsonSchema,
                    startval: jsonData,
                    theme: "bootstrap4",
                    no_additional_properties: true,
                    disable_edit_json: true,
                    disable_array_add: false,
                    disable_array_delete: false,
                    // optional fields are not displayed by default in JSONEditor form for editing
                    // user needs to select any optional properties to make it available for editing
                    display_required_only: false,
                    required_by_default: true,
                    object_layout: "table"
                });
                editor.on("change", function () {
                    showJsonEditorSubmitButton();
                    // get all JSONEditor form data as a string
                    var jsonDataString = JSON.stringify(editor.getValue());
                    // set the form field with the form data
                    $("#id-schema-based-form").find("#id-metadata-json").val(jsonDataString);
                });
                // removing the style attribute set by the JSONEditor in order to customize the look of the UI that lists object properties
                $(".property-selector").removeAttr("style");
            }
        },
        
        showJsonEditorSubmitButton: function() {
            var jsonEditorStatus = $("#id-schema-based-form").find("#id-json-editor-load-status").val();
            if(jsonEditorStatus === "loaded")
                $("#id-schema-form-submit").show();
            else {
                $("#id-schema-based-form").find("#id-json-editor-load-status").val("loaded");
            }
        },
        
        InitializeTimeSeriesFileTypeForms: function() {
            var tsSelect = $(".time-series-forms select");
        
            tsSelect.append('<option value="Other">Other...</option>');
        
            tsSelect.parent().parent().append('<div class="controls other-field" style="display:none;"> <label class="text-muted control-label">Specify: </label><input class="form-control input-sm textinput textInput" name="" type="text"> </div>')
        
            tsSelect.change(function(e){
                if (e.target.value === "Other") {
                    let name = e.target.name;
                    $(e.target).parent().parent().find(".other-field").show();
                    $(e.target).parent().parent().find(".other-field input").attr("name", name);
                    $(e.target).removeAttr("name");
                }
                else {
                    if (!e.target.name.length) {
                        let name = $(e.target).parent().parent().find(".other-field input").attr("name");
                        $(e.target).attr("name", name);
                        $(e.target).parent().parent().find(".other-field input").removeAttr("name");
                        $(e.target).parent().parent().find(".other-field").hide();
                    }
                }
            });
        
            processSiteMetadataElement();
            processVariableMetadataElement();
            processMethodMetadataElement();
            processProcessingLevelMetadataElement();
        },
        
        setBreadCrumbs: function(bcPath) {
            var crumbs = $("#fb-bread-crumbs");
            crumbs.empty();
        
            if (bcPath.hasOwnProperty("aggregation")) {
                bcPath.path.push(bcPath.aggregation.name);
            }
        
            if (bcPath.path.length) {
                for (let i = 0; i < bcPath.path.length; i++) {
                    let isActive = i === bcPath.path.length - 1;
                    if (isActive) {
                        if (bcPath.hasOwnProperty("aggregation")) {
                            let logicalType = bcPath.aggregation.logical_type;
                            let icon = getFolderIcons()[logicalType];
        
                            // Crumb for active aggregaqtion (with its icon)
                            crumbs.append('<li class="active crumb-aggregation">' + icon + '<span class="crumb-aggregation-name"> '
                                + bcPath.path[i] + '</span></li>');
                        }
                        else {
                            // Crumb for the active folder
                            crumbs.append('<li class="active"><i class="fa fa-folder-open-o" aria-hidden="true"></i><span> '
                                + bcPath.path[i] + '</span></li>');
                        }
                    }
                    else {
                        // Crumb for inactive folder
                        crumbs.append('<li data-path="' + getCurrentPath().path.slice(0, i + 1).join('/') +
                            '"><i class="fa fa-folder-o" aria-hidden="true"></i><span> ' + bcPath.path[i] + '</span></li>');
                    }
                }
        
                // Prepend root folder
                crumbs.prepend('<li data-path="">' +
                    '<i class="fa fa-folder-o" aria-hidden="true"></i>' +
                    '<span> contents</span></li>');
            }
            else {
                $("#fb-move-up").toggleClass("disabled", true);
                crumbs.prepend('<li class="active">' +
                    '<i class="fa fa-folder-open-o" aria-hidden="true"></i><span> contents</span>' +
                    '</li>');
            }
        },
        onSort: function() {
            const vue = this
            const method = $("#fb-sort li[data-method].active").attr("data-method");
            const order = $("#fb-sort li[data-order].active").attr("data-order");
        
            // vue.sort(method, order);
        },
        
        onOpenFile: function() {
            // Check to see if it is .url web referenced file, if yes, do redirect rather than download
            var file = $("#fb-files-container li.ui-selected");
            var fileName = file.children(".fb-file-name").text();
            if (fileName.toUpperCase().endsWith('.URL')) {
                // do redirect
                $('#redirect-referenced-url-dialog').modal('show');
            }
            else {
                // Check for download agreement
                if ($("#hs-file-browser").attr("data-agreement") == "true") {
                    // Proceed to download through confirmation agreement
                    isDownloadZipped = false;
                    $("#license-agree-dialog-file").modal('show');
                }
                else {
                    // Direct download
                    startDownload();
                }
            }
        },
        
        /** Takes an element and returns true if the element is a virtual folder */ 
        isVirtualFolder: function(item) {
            item = $(item);
            let isFileSet = item.find(".fb-logical-file-type").attr("data-logical-file-type") === "FileSetLogicalFile";
            let isModelProgramFolder = item.find(".fb-logical-file-type").attr("data-logical-file-type") === "ModelProgramLogicalFile";
            let isModelInstanceFolder = item.find(".fb-logical-file-type").attr("data-logical-file-type") === "ModelInstanceLogicalFile";
            return item.hasClass("fb-folder") && item.attr("data-logical-file-id") && !isFileSet && !isModelProgramFolder && !isModelInstanceFolder;
        },
        
        previewData: function() {
            let selected = $("#fb-files-container li.ui-selected");
            let previewDataURL = selected.children('span.fb-preview-data-url').text();
            window.open(previewDataURL, '_blank');
        },
        
        startDownload: function(zipFiles) {
            zipFiles = zipFiles || false;
            const downloadList = $("#fb-files-container li.ui-selected");
        
            if (downloadList.length) {
                // Remove previous temporary download frames
                $(".temp-download-frame").remove();
        
                for (var i = 0; i < downloadList.length; i++) {
                    const item = $(downloadList[i]);
                    let url = item.attr("data-url");
        
                    const fileName = item.children(".fb-file-name").text();
                    const itemIsVirtualFolder = isVirtualFolder(item.first());
                    const isFolder = item.hasClass("fb-folder");
                    let parameters = [];
        
                    if (fileName.toUpperCase().endsWith(".URL")) {
                        parameters.push('url_download=true');
                    }
        
                    if (zipFiles === true) {
                        parameters.push("zipped=true");
                    }
        
                    if (itemIsVirtualFolder) {
                        parameters.push("aggregation=true");
                    }
        
                    if (parameters.length) {
                        url += "?" + parameters.join("&");
                    }
        
                    if (zipFiles || isFolder) {
                        $.ajax({
                            type: "GET",
                            url: url,
                            success: function (task) {
                                notificationsApp.registerTask(task);
                                notificationsApp.show();
                            },
                            error: function (xhr, errmsg, err) {
                                display_error_message('Failed to zip files', xhr.responseText);
                            }
                        });
                    }
                    else {
                        let frameID = "download-frame-" + i;
                        console.log(url);
                        $("body").append("<iframe class='temp-download-frame' id='"
                            + frameID + "' style='display:none;' src='" + url + "'></iframe>");
                    }
                }
            }
        },
        
        onOpenFolder: function() {
            const selectedFolder = $("#fb-files-container li.ui-selected");
            const aggregationId = parseInt(selectedFolder.attr("data-logical-file-id"));
            const logicalFileType = selectedFolder.find(".fb-logical-file-type").attr("data-logical-file-type");
        
            if (aggregationId && logicalFileType !== "FileSetLogicalFile" && logicalFileType !== "ModelProgramLogicalFile" &&
                logicalFileType !== "ModelInstanceLogicalFile") {
                // Remove further paths from the log
                const range = pathLog.length - pathLogIndex;
                pathLog.splice(pathLogIndex + 1, range);
        
                // Aggregations can be loaded from memory
                const selectedAgg = currentAggregations.filter(function(agg){
                    return agg.logical_file_id === aggregationId && agg.logical_type === logicalFileType;
                })[0];
        
                const path = {
                    path: getCurrentPath().path.slice(),
                    aggregation: selectedAgg,
                };
        
                pathLog.push(path);
                pathLogIndex = pathLog.length - 1;
                sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
        
                get_aggregation_folder_struct(selectedAgg);
        
                return;
            }
        
            const folderName = selectedFolder.children(".fb-file-name").text();
            const targetPath = {path: getCurrentPath().path.concat(folderName)};
        
            sessionStorage.currentBrowsepath = JSON.stringify(targetPath);
        
            // Remove further paths from the log
            const range = pathLog.length - pathLogIndex;
            pathLog.splice(pathLogIndex + 1, range);
            pathLog.push(targetPath);
            pathLogIndex = pathLog.length - 1;
        
            const calls = [];
            calls.push(get_irods_folder_struct_ajax_submit(SHORT_ID, targetPath));
        
            $.when.apply($, calls).done(function () {
                updateSelectionMenuContext();
            });
        
            $.when.apply($, calls).fail(function () {
                updateSelectionMenuContext();
            });
        },
        
        updateNavigationState: function() {
            $("#fb-move-back").toggleClass("disabled", pathLogIndex === 0); // we are at the root folder
            $("#fb-move-forward").toggleClass("disabled", pathLogIndex >= pathLog.length - 1);
            $("#fb-move-up").toggleClass("disabled", !(getCurrentPath().path.length || getCurrentPath().hasOwnProperty("aggregation")));    // The root path is an empty string
        },
        
        isSelected: function(fullPaths) {
            const deleteList = $("#fb-files-container li.ui-selected");
            let filesToDelete = [];
        
            if (deleteList.length) {
                for (let i = 0; i < deleteList.length; i++) {
                    const item = $(deleteList[i]);
                    const respath = item.attr("data-url");
                    const pk = item.attr("data-pk");
                    if (respath && pk) {
                        const parsed_path = respath.split(/contents(.+)/).filter(function(el){return el})
                        filesToDelete.push(parsed_path[parsed_path.length-1])
                    } else {
                        if (!isVirtualFolder(item.first())) { // Item is a regular folder
                            let folderName = item.children(".fb-file-name").text();
                            let folder_path = getCurrentPath().path.concat(folderName);
                            filesToDelete.push('/' + folder_path.join('/'))
                        }
                    }
                }
        
                // maximum matches with duplicates (based on parent folder match or top level filename match)
                let matches = fullPaths.map(function(i1) {
                    return filesToDelete.filter(function(i2) {
                        if (i1.split('/')[1] === i2.split('/')[1]) {
                            return i2
                        }
                    })
                }).flat()
                return matches
            }
        },
        
        // Reload the current folder structure
        // Optional argument: file name or folder name to select after reload
        refreshFileBrowser: function(name) {
            var calls = [];
            currentAggregations = [];   // These will be updated
            pathLog[pathLogIndex] = JSON.parse(sessionStorage.currentBrowsepath);
        
            if (getCurrentPath().hasOwnProperty("aggregation")) {
                calls.push(get_aggregation_folder_struct(getCurrentPath().aggregation));
            }
            else {
                calls.push(get_irods_folder_struct_ajax_submit(SHORT_ID, getCurrentPath()));
            }
        
            $.when.apply($, calls).done(function () {
                $(".selection-menu").hide();
                clearSourcePaths();
        
                $("#fileTypeMetaData").html(file_metadata_alert);
        
                if (name) {
                    // Find the item and trigger its selection
                    let items = $("#fb-files-container li");
                    for (let i = 0; i < items.length; i++) {
                        let text = $(items[i]).find(".fb-file-name").text().trim();
                        if (text === name) {
                            // Trigger all relevant events
                            $(items[i]).trigger("mousedown");
                            $(items[i]).trigger("mouseup");
                            $(items[i]).trigger("click");
                            break;
                        }
                    }
                }
                updateSelectionMenuContext();
        
                $.ajax({
                    type: "GET",
                    url: '/hsapi/_internal/' + SHORT_ID + '/list-referenced-content/',
                }).complete(function(res) {
                    if (res.responseText) {
                        let extRefs = JSON.parse(res.responseText).filenames
                        if (extRefs.length && RESOURCE_MODE === 'Edit') {
                            document.getElementById('edit-citation-control').style.display = 'block'
                        } else {
                            document.getElementById('edit-citation-control').style.display = 'none'
                        }
                    }
                })
            });
        
            $.when.apply($, calls).fail(function () {
                $(".selection-menu").hide();
                clearSourcePaths();
                sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
                updateSelectionMenuContext();
            });
        },
        
        warnExternalContent: function(shortId) {
            /*
            Conditionally update the delete modal to include a warning if the last .url file is being deleted as a part of this
            action and inform the user that the custom Citation will be reverted to the standard one.
            Local cookie will be read for the CSRF POST, since this is happening outside the Django template/form/modal
            pattern.
        
            param: shortId HydroShare short_id GUID from server
             */
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            function csrfSafeMethod(method) {
                // these HTTP methods do not require CSRF protection
                return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
            }
            function sameOrigin(url) {
                // test that a given url is a same-origin URL
                // url could be relative or scheme relative or absolute
                var host = document.location.host; // host + port
                var protocol = document.location.protocol;
                var sr_origin = '//' + host;
                var origin = protocol + sr_origin;
                // Allow absolute or scheme relative URLs to same origin
                return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                    (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                    // or any other URL that isn't scheme relative or absolute i.e relative.
                    !(/^(\/\/|http:|https:).*/.test(url));
            }
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                        // Send the token to same-origin, relative URLs only.
                        // Send the token only if the method warrants CSRF protection
                        // Using the CSRFToken value acquired earlier
                        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
                    }
                }
            });
        
            $('#btn-confirm-delete').prop('disabled', true)
            $('#additional-citation-warning').text('Analyzing files . . .')
            $.ajax({
                type: "GET",
                url: '/hsapi/_internal/' + shortId + '/list-referenced-content/',
            }).complete(function(res) {
                if (res.responseText) {
                    let extRefs = JSON.parse(res.responseText).filenames
        
                    // capture external refs within subfolders as just the folder names
                    extRefs = extRefs.map(function(ref) {
                        return ref.split('/').length === 2 ? ref : ref.substr(0, ref.lastIndexOf('/'))
                    })
        
                    const sel = isSelected(extRefs)
                    if (global_custom_citation !== 'None' && global_custom_citation !== '' && global_custom_citation !== '' && sel.length === extRefs.length && extRefs.length > 0) {
                        removeCitationIntent = true;
                        $('#additional-citation-warning').text('Removing all referenced content from this resource will also ' +
                          'remove the custom citation you have entered. Are you sure you want to remove this reference content ' +
                          'and custom citation?')
                        $('#additional-citation-warning').css("color", "red");
                    } else {
                        removeCitationIntent = false;
                        $('#additional-citation-warning').text('')
                        $('#additional-citation-warning').css("color", "black");
                    }
                }
                $('#btn-confirm-delete').prop('disabled', false)
            })
        },
        
        onUploadSuccess: function(file, response) {
            // uploaded files can affect metadata in composite resource.
            // Use the json data returned from backend to update UI
            if (RES_TYPE === 'Composite Resource') {
                updateResourceUI();
            }
            showCompletedMessage(response);
        },
        
        // used for setting various file types within composite resource
        setFileType: function(fileType){
            var url;
            var folderPath = "";
            let selected = $("#fb-files-container li.ui-selected");
            let name = $("#fb-files-container li.ui-selected").find(".fb-file-name").text().trim();
        
            if(selected.hasClass('fb-file')){
                var file_id = selected.attr("data-pk");
                url = "/hsapi/_internal/" + SHORT_ID + "/" + file_id + "/" + fileType + "/set-file-type/";
            }
            else {
                // this must be folder selection for aggregation creation
                folderPath = selected.children('span.fb-file-type').attr("data-folder-short-path");
                url = "/hsapi/_internal/" + SHORT_ID + "/" + fileType + "/set-file-type/";
            }
        
            $(".file-browser-container, #fb-files-container").css("cursor", "progress");
            var calls = [];
            calls.push(set_file_type_ajax_submit(url, folderPath));
        
            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function (result) {
                $(".file-browser-container, #fb-files-container").css("cursor", "auto");
                var json_response = JSON.parse(result);
                $("#fileTypeMetaData").html(file_metadata_alert);
        
                if (json_response.status === 'success') {
                    // Use resource level metadata in json_response to update resource level UI
                    updateResourceUI();
        
                    // Select the clicked element to view metadata entry form after reloading structure
                    refreshFileBrowser(name);
                }
            });
        },
        
        // Get resource metadata and update UI elements
        updateResourceUI: function() {
            var calls = [];
            calls.push(getResourceMetadata());
            $.when.apply($, calls).done(function (result) {
                let UIData = JSON.parse(result);
                $("#id_abstract").val(UIData.abstract);
                $("#txt-title").val(UIData.title);
                updateResourceAuthors(UIData.creators);
                subjKeywordsApp.$data.resKeywords = UIData.keywords;
                updateResourceSpatialCoverage(UIData.spatial_coverage);
                updateResourceTemporalCoverage(UIData.temporal_coverage);
            });
        },
        
        // used for removing aggregation (file type) within composite resource
        removeAggregation: function(){
            var aggregationType = $("#fb-files-container li.ui-selected").children('span.fb-logical-file-type').attr("data-logical-file-type");
            var aggregationID = $("#fb-files-container li.ui-selected").children('span.fb-logical-file-type').attr("data-logical-file-id");
            var url = "/hsapi/_internal/" + SHORT_ID + "/" + aggregationType + "/" + aggregationID + "/remove-aggregation/";
            $(".file-browser-container, #fb-files-container").css("cursor", "progress");
        
            var calls = [];
            calls.push(remove_aggregation_ajax_submit(url));
        
            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function (result) {
               $(".file-browser-container, #fb-files-container").css("cursor", "auto");
               var json_response = JSON.parse(result);
               $("#fileTypeMetaData").html(file_metadata_alert);
               if (json_response.status === 'success'){
                   updateResourceSpatialCoverage(json_response.spatial_coverage);
                   refreshFileBrowser();
               }
            });
        },
        
        // Used to set the previous scroll position after refresh
        setCookie: function(name, value, expires, path, domain, secure) {
            if (!expires) {
                expires = new Date()
            }
            document.cookie = name + "=" + escape(value) +
                ((expires == null) ? "" : "; expires=" + expires.toGMTString()) +
                ((path == null) ? "" : "; path=" + path) +
                ((domain == null) ? "" : "; domain=" + domain) +
                ((secure == null) ? "" : "; secure")
        },
        
        getCookie: function(name) {
            var arg = name + "=";
            var alen = arg.length;
            var clen = document.cookie.length;
            var i = 0;
            while (i < clen) {
                var j = i + alen;
                if (document.cookie.substring(i, j) === arg) {
                    return getCookieVal(j)
                }
                i = document.cookie.indexOf(" ", i) + 1;
                if (i == 0) break
            }
            return null;
        },
        
        getCookieVal: function(offset) {
            var endstr = document.cookie.indexOf(";", offset);
            if (endstr == -1)
                endstr = document.cookie.length;
            return unescape(document.cookie.substring(offset, endstr));
        },
        getIRodsFolderStructure: function(res_id, store_path) {
            const vue = this
            // $("#fb-files-container, #fb-files-container").css("cursor", "progress");
        
            return $.ajax({
                type: "POST",
                url: '/hsapi/_internal/data-store-structure/',
                async: true,
                data: {
                    res_id: res_id,
                    store_path: store_path.path.join('/')
                },
                success: function (result) {
                    const aggregationFileTypes = ["GenericLogicalFile", "FileSetLogicalFile", "ModelProgramLogicalFile", "ModelInstanceLogicalFile"]
                    vue.files = result.files.filter((file) => {
                        const isAggregationFile = aggregationFileTypes.includes(file['logical_type'])
                        return !(file['logical_file_id'] && !isAggregationFile)
                    });
                    vue.folders = result.folders;
                    vue.canBePublic = result.can_be_public;
                    vue.mode = $("#hs-file-browser").attr("data-mode");
        
                    // $('#fb-files-container').empty();
                    vue.currentAggregations = result.aggregations.filter(function(agg) {
                        return agg['logical_type'] !== "FileSetLogicalFile"; // Exclude FileSet aggregations
                    });
        
                    // Render each file. Aggregation files get loaded in memory instead.
                    // $.each(files, function (i, file) {
                    //     // Check if the file belongs to an aggregation. Exclude FileSets and their files.
                    //     if (file['logical_file_id'] && file['logical_type'] !== "GenericLogicalFile" && file['logical_type'] !== "FileSetLogicalFile"
                    //         && file['logical_type'] !== "ModelProgramLogicalFile" && file['logical_type'] !== "ModelInstanceLogicalFile") {
                    //         // const selectedAgg = currentAggregations.filter(function (agg) {
                    //         //     return agg.logical_file_id === file['logical_file_id'] && agg.logical_type === file['logical_type'];
                    //         // })[0];
        
                    //         // if (!selectedAgg.hasOwnProperty('files')) {
                    //         //     selectedAgg.files = [];     // Initialize the array
                    //         // }
                    //         // selectedAgg.files.push(file);   // Push the aggregation files to the collection
                    //     }
                    //     else {
                    //         // Regular files
                    //         // $('#fb-files-container').append(getFileTemplateInstance(file));
                    //     }
                    // });
        
                    // // Display virtual folders for each aggregation.
                    // $.each(currentAggregations, function (i, agg) {
                    //     $('#fb-files-container').append(getVirtualFolderTemplateInstance(agg));
                    // });
        
                    // // Display regular folders
                    // $.each(folders, function (i, folder) {
                    //     $('#fb-files-container').append(getFolderTemplateInstance(folder));
                    // });
        
                    // Default display message for empty directories
                    // if (!files.length && !folders.length) {
                    //     if (mode === "edit") {
                    //         $('#fb-files-container').append(
                    //             '<div>' +
                    //                 '<span class="text-muted fb-empty-dir space-bottom">This directory is empty</span>' +
                    //                 '<div class="hs-upload-indicator text-center">' +
                    //                     '<i class="fa fa-file" aria-hidden="true"></i>' +
                    //                     '<h4>Drop files here or click "Add files" to upload</h4>' +
                    //                 '</div>' +
                    //             '</div>'
                    //         );
                    //     }
                    //     else {
                    //         $('#fb-files-container').append(
                    //             '<span class="text-muted fb-empty-dir">This directory is empty</span>'
                    //         );
                    //     }
                    // }
        
                    // if (canBePublic) {
                    //     $("#missing-metadata-or-file:not(.persistent)").fadeOut();
                    // }
        
                    onSort();
                    bindFileBrowserItemEvents();
                    vue.pathLog[pathLogIndex] = store_path;
                    // $("#hs-file-browser").attr("data-res-id", res_id);
                    setBreadCrumbs({...store_path});
        
                    if ($("#hsDropzone").hasClass("dropzone")) {
                        // If no multiple files allowed and a file already exists, disable upload
                        var allowMultiple = $("#hs-file-browser").attr("data-allow-multiple-files") == "True";
                        if (!allowMultiple && files.length > 0) {
                            $('.dz-input').hide();
                            $(".fb-upload-caption").toggleClass("hidden", true);
                            $(".upload-toggle").toggleClass("hidden", true);
                            $("#irods-group").toggleClass("hidden", true);
                        }
                        else {
                            $('.dz-input').show();
                            $(".fb-upload-caption").toggleClass("hidden", false);
                            $(".upload-toggle").toggleClass("hidden", false);
                            $("#irods-group").toggleClass("hidden", false);
                            Dropzone.forElement("#hsDropzone").files = [];
                        }
                    }
        
                    updateNavigationState();
                    updateSelectionMenuContext();
                    // $(".selection-menu").hide();
                    // $("#flag-uploading").remove();
                    // $("#fb-files-container, #fb-files-container").css("cursor", "default");
        
                    if (mode === "edit" && result.hasOwnProperty('spatial_coverage')){
                        var spatialCoverage = result.spatial_coverage;
                        updateResourceSpatialCoverage(spatialCoverage);
                    }
        
                    if (mode == "edit" && result.hasOwnProperty('temporal_coverage')){
                        var temporalCoverage = result.temporal_coverage;
                        updateResourceTemporalCoverage(temporalCoverage);
                    }
                },
                error: function(xhr, errmsg, err){
                    $(".selection-menu").hide();
                    $("#flag-uploading").remove();
                    $("#fb-files-container, #fb-files-container").css("cursor", "default");
                    $('#fb-files-container').empty();
                    setBreadCrumbs(jQuery.extend(true, {}, store_path));
                    $("#fb-files-container").prepend("<span>No files to display.</span>");
                    updateSelectionMenuContext();
                }
            });
        }
    },
})