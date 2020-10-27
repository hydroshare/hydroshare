/**
 * Created by Mauriel on 8/16/2016.
 */

var sourcePaths = {path: null, selected:[]};
var pathLog = [];
var pathLogIndex = 0;
var isDragging = false;
var isDownloadZipped = false;
var currentAggregations = [];

var file_metadata_alert =
    '<div id="#fb-metadata-default" class="alert alert-info text-center" role="alert">' +
        '<div>Select a file to see file type metadata.</div>' +
        '<hr>' +
        '<span class="fa-stack fa-lg text-center"><i class="fa fa-file-o fa-stack-2x" aria-hidden="true"></i>' +
            '<i class="fa fa-mouse-pointer fa-stack-1x" aria-hidden="true" style="top: 14px;"></i>' +
        '</span>' +
    '</div>';

var no_metadata_alert =
    '<div class="alert alert-warning text-center" role="alert">' +
        '<div>No file type metadata exists for this file.</div>' +
        '<hr>' +
        '<i class="fa fa-eye-slash fa-3x" aria-hidden="true"></i>' +
    '</div>';

var loading_metadata_alert =
    '<div class="text-center" role="alert">' +
        '<br>' +
        '<i class="fa fa-spinner fa-spin fa-3x fa-fw icon-blue"></i>' +
        '<span class="sr-only">Loading...</span>' +
    '</div>';

const MAX_FILE_SIZE = 1024; // MB

function getCurrentPath() {
    return pathLog[pathLogIndex];
}

function clearSourcePaths() {
    sourcePaths = {path: null, selected: []};
    $("#fb-files-container li").removeClass("fb-cutting");
}

function getFolderTemplateInstance(folder) {
    if (folder['folder_aggregation_type'] === "FileSetLogicalFile") {
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
        "<span class='fb-file-size'></span>" +
        "</li>";
}

function getVirtualFolderTemplateInstance(agg) {
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
      "<span class='fb-file-size'></span>" +
      "</li>";
}

// Associates file icons with file extensions. Could be improved with a dictionary.
function getFileTemplateInstance(file) {
    var fileTypeExt = file.name.substr(file.name.lastIndexOf(".") + 1, file.name.length);
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
        file.is_single_file_aggregation + "'>" +
        iconTemplate +
        "<span class='fb-file-name'>" + file.name + "</span>" +
        "<span class='fb-file-type'>" + file.type + " File</span>" +
        "<span class='fb-logical-file-type' data-logical-file-type='" + file.logical_type + "' data-logical-file-id='" +
        file.logical_file_id +  "'>" + file.aggregation_name + "</span>" +
        "<span class='fb-file-size' data-file-size=" + file.size + ">" + formatBytes(parseInt(file.size)) +
        "</span></li>"
}

function formatBytes(bytes) {
    if(bytes < 1024) return bytes + " Bytes";
    else if(bytes < 1048576) return(bytes / 1024).toFixed(1) + " KB";
    else if(bytes < 1073741824) return(bytes / 1048576).toFixed(1) + " MB";
    else return(bytes / 1073741824).toFixed(1) + " GB";
}

// Initial state for actions where they can appear.
var initActionState = {
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

/*
    Updates the state of toolbar and menu buttons when a selection is made.
    All items start as visible and enabled by default. Performs checks and disables as it goes.
*/
function updateSelectionMenuContext() {
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
        "removeAggregation",
        "rename",
        "setFileSetFileType",
        "setGenericFileType",
        "setGeoFeatureFileType",
        "setGeoRasterFileType",
        "setNetCDFFileType",
        "setRefTimeseriesFileType",
        "setTimeseriesFileType",
        "subMenuSetContentType",
        "unzip",
        "updateRefUrl",
        "uploadFiles",
        "zip",
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

        for (let i = 0; i < selected.length; i++) {
            const size = parseInt($(selected[i]).find(".fb-file-size").attr("data-file-size"));
            if (size > maxSize) {
                // Some file is too large for direct download
                // Here we just disable, but keep the menu item visible
                uiActionStates.download.disabled = true;
                $("#fb-download-help").toggleClass("hidden", true);
                break;
            }
        }

        const foldersSelected = $("#fb-files-container li.fb-folder.ui-selected");
        if(resourceType === 'Composite Resource' && foldersSelected.length > 1) {
            uiActionStates.removeAggregation.disabled = true;
            uiActionStates.setFileSetFileType.disabled = true;
        }
        if(resourceType !== 'Composite Resource') {
            uiActionStates.removeAggregation.disabled = true;
        }
        $("#fileTypeMetaData").html(file_metadata_alert);
    }
    else if (selected.length == 1) {
        // Exactly one item selected
        var size = parseInt(selected.find(".fb-file-size").attr("data-file-size"));
        if (size > maxSize) {
            uiActionStates.download.disabled = false;
            $("#fb-download-help").toggleClass("hidden", false);
        }
        else {
            $("#fb-download-help").toggleClass("hidden", true);
        }

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
            uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
            uiActionStates.subMenuSetContentType.disabled = true;

            uiActionStates.setRefTimeseriesFileType.disabled = true;
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

            let logicalFileTypeToSet = selected.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set");
            if (!logicalFileTypeToSet || !logicalFileTypeToSet.length) {
                uiActionStates.setFileSetFileType.fileMenu.hidden = true;
            }
        }
        //  ------------- The item selected is a file -------------
        else {
            const logicalFileType = $(selected).find(".fb-logical-file-type").attr("data-logical-file-type").trim();

            // Disable add metadata to folder
            uiActionStates.setFileSetFileType.disabled = true;
            uiActionStates.setFileSetFileType.fileMenu.hidden = true;

            if (!fileName.toUpperCase().endsWith(".ZIP")) {
                uiActionStates.unzip.disabled = true;
                uiActionStates.unzip.fileMenu.hidden = true;
            }

            if (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile") {
                // The file is already part of an aggregation
                uiActionStates.setGenericFileType.disabled = true;
                uiActionStates.setGenericFileType.fileMenu.hidden = true;

                uiActionStates.subMenuSetContentType.disabled = true;
                uiActionStates.subMenuSetContentType.fileMenu.hidden = true;
            }

            if (!fileName.toUpperCase().endsWith(".TIF") && !fileName.toUpperCase().endsWith(".TIFF") ||
                logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile") {
                uiActionStates.setGeoRasterFileType.disabled = true;
            }

            if (!fileName.toUpperCase().endsWith(".NC") ||
                (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile")) {
                uiActionStates.setNetCDFFileType.disabled = true;
            }

            if ((!fileName.toUpperCase().endsWith(".SHP")) ||
                (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile")) {
                uiActionStates.setGeoFeatureFileType.disabled = true;
            }

            if (!fileName.toUpperCase().endsWith(".REFTS.JSON") ||
                (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile")) {
                uiActionStates.setRefTimeseriesFileType.disabled = true;
            }

            if ((!fileName.toUpperCase().endsWith(".SQLITE") && !fileName.toUpperCase().endsWith(".CSV")) ||
                (logicalFileType !== "" && logicalFileType !== "FileSetLogicalFile")) {
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

                if (mode != "edit") {
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
                if (logicalFileType !== 'RefTimeseriesLogicalFile' && logicalFileType !== "GenericLogicalFile") {
                    // if the selected file is not part of the RefTimeseriesLogical or GenericLogicalFile file (aggregation)
                    // dont't show the Remove Aggregation option
                    uiActionStates.removeAggregation.disabled = true;
                    uiActionStates.removeAggregation.fileMenu.hidden = true;
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

        $("#fb-download-help").toggleClass("hidden", true);
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
}

// Proxy function when pasting in current directory triggering from menu item or button
function onPaste() {
    let folderName = $("#fb-files-container li.ui-selected").find(".fb-file-name").text();
    paste(getCurrentPath().path.concat(folderName))
}

// Pastes the files currently in the global variable source Paths into a destination path
function paste(destPath) {
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
}

function bindFileBrowserItemEvents() {
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
        if (!e.shiftKey) {
            $("#fb-files-container li").removeClass("ui-last-selected");
            $(this).addClass("ui-last-selected");
        }
        else {
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
                    $('#fb-files-container li').animate({top: 0, left: 0}, 200);    // Custom revert to handle multiple selection
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
}

function showFileTypeMetadata(file_type_time_series, url){
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
    }
    var resource_mode = RESOURCE_MODE;
    if (!resource_mode) {
        return;
    }
    resource_mode = resource_mode.toLowerCase();
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
             if (logical_type === "FileSetLogicalFile") {
                 // Submit for aggregation spatial coverage update
                 $("#btn-update-aggregation-spatial-coverage").click(function () {
                    fileset_coverage_update_ajax_submit(logical_file_id, 'spatial');
                 });
                 // Submit for aggregation temporal coverage update
                 $("#btn-update-aggregation-temporal-coverage").click(function () {
                    fileset_coverage_update_ajax_submit(logical_file_id, 'temporal');
                 });
             }
        }
    });
}

function InitializeTimeSeriesFileTypeForms() {
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
}

function setBreadCrumbs(bcPath) {
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
}

// File sorting sort algorithms
function sort(method, order) {
    var sorted;
    if (method === "name") {
        // Sort by name
        if (order === "asc") {
            sorted = $('#fb-files-container li').sort(function (element1, element2) {
                return $(element2).children('span.fb-file-name').text().localeCompare($(element1).children('span.fb-file-name').text());
            });
        }
        else {
            sorted = $('#fb-files-container li').sort(function (element1, element2) {
                return $(element1).children('span.fb-file-name').text().localeCompare($(element2).children('span.fb-file-name').text());
            });
        }
    }
    else if (method === "size") {
        // Sort by size
        var size1, size2;

        sorted = $('#fb-files-container li').sort(function (element1, element2) {
            if (order === "asc") {
                size1 = parseInt($(element2).children('span.fb-file-size').attr("data-file-size"));
                size2 = parseInt($(element1).children('span.fb-file-size').attr("data-file-size"));
            }
            else {
                size1 = parseInt($(element1).children('span.fb-file-size').attr("data-file-size"));
                size2 = parseInt($(element2).children('span.fb-file-size').attr("data-file-size"));
            }

            if (isNaN(size1)) size1 = 0;
            if (isNaN(size2)) size2 = 0;

            if (size1 < size2) {
                return -1;
            }
            if (size1 > size2) {
                return 1;
            }
            // Both sizes are equal
            return 0;
        });
    }
    else if (method === "type") {
        // Sort by type
        if (order === "asc") {
            sort("name", "desc");    // First sort by name
            sorted = $('#fb-files-container li').sort(function (element1, element2) {
                return $(element2).children('span.fb-file-type').text().localeCompare($(element1).children('span.fb-file-type').text());
            });
        }
        else {
            sort("name", order);    // First sort by name
            sorted = $('#fb-files-container li').sort(function (element1, element2) {
                return $(element1).children('span.fb-file-type').text().localeCompare($(element2).children('span.fb-file-type').text());
            });
        }
    }

    // Move elements to the new order
    for (var i = 0; i < sorted.length; i++) {
        $(sorted[i]).prependTo("#fb-files-container");
    }
}

function onSort() {
    var method = $("#fb-sort li[data-method].active").attr("data-method");
    var order = $("#fb-sort li[data-order].active").attr("data-order");

    sort(method, order);
}

function onOpenFile() {
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
}

// Takes an element and returns true if the element is a virtual folder
function isVirtualFolder(item) {
    item = $(item);
    let isFileSet = item.find(".fb-logical-file-type").attr("data-logical-file-type") === "FileSetLogicalFile";
    return item.hasClass("fb-folder") && item.attr("data-logical-file-id") && !isFileSet;
}

function startDownload(zipFiles) {
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
}

function onOpenFolder() {
    let selectedFolder = $("#fb-files-container li.ui-selected");
    let aggregationId = parseInt(selectedFolder.attr("data-logical-file-id"));
    let logicalFileType = selectedFolder.find(".fb-logical-file-type").attr("data-logical-file-type");

    if (aggregationId && logicalFileType !== "FileSetLogicalFile") {
        // Remove further paths from the log
        let range = pathLog.length - pathLogIndex;
        pathLog.splice(pathLogIndex + 1, range);

        // Aggregations can be loaded from memory
        let selectedAgg = currentAggregations.filter(function(agg){
            return agg.logical_file_id === aggregationId && agg.logical_type === logicalFileType;
        })[0];

        let path = {
            path: getCurrentPath().path.slice(),
            aggregation: selectedAgg,
        };

        pathLog.push(path);
        pathLogIndex = pathLog.length - 1;
        sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());

        get_aggregation_folder_struct(selectedAgg);

        return;
    }

    let folderName = selectedFolder.children(".fb-file-name").text();
    var targetPath = {path: getCurrentPath().path.concat(folderName)};

    sessionStorage.currentBrowsepath = JSON.stringify(targetPath);

    // Remove further paths from the log
    var range = pathLog.length - pathLogIndex;
    pathLog.splice(pathLogIndex + 1, range);
    pathLog.push(targetPath);
    pathLogIndex = pathLog.length - 1;

    var calls = [];
    calls.push(get_irods_folder_struct_ajax_submit(SHORT_ID, targetPath));

    $.when.apply($, calls).done(function () {
        updateSelectionMenuContext();
    });

    $.when.apply($, calls).fail(function () {
        updateSelectionMenuContext();
    });
}

function updateNavigationState() {
    $("#fb-move-back").toggleClass("disabled", pathLogIndex === 0); // we are at the root folder
    $("#fb-move-forward").toggleClass("disabled", pathLogIndex >= pathLog.length - 1);
    $("#fb-move-up").toggleClass("disabled", !(getCurrentPath().path.length || getCurrentPath().hasOwnProperty("aggregation")));    // The root path is an empty string
}

// Reload the current folder structure
// Optional argument: file name or folder name to select after reload
function refreshFileBrowser(name) {
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
    });

    $.when.apply($, calls).fail(function () {
        $(".selection-menu").hide();
        clearSourcePaths();
        sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
        updateSelectionMenuContext();
    });
}

function onUploadSuccess(file, response) {
    // uploaded files can affect metadata in composite resource.
    // Use the json data returned from backend to update UI
    if (RES_TYPE === 'Composite Resource') {
        updateResourceUI();
    }
    showCompletedMessage(response);
}

$(document).ready(function () {
    if (!$("#hs-file-browser").length) {
        return;
    }

    if (localStorage.getItem('file-browser-view')) {
        var view = localStorage.getItem('file-browser-view');
        // ------- switch to table view -------
        $("#fb-files-container").removeClass("fb-view-grid fb-view-list");
        $("#fb-files-container").addClass(view);

        $("#btn-group-view button").removeClass("active");

        if (view == "fb-view-list") {
            $("#btn-group-view button[data-view='list']").addClass("active");
        }
        else {
            $("#btn-group-view button[data-view='grid']").addClass("active");
        }
    }

    $('#file_redirect_url').click(function() {
        $('#redirect-referenced-url-dialog').modal('hide');
    });

    // Set initial folder structure
    if (!sessionStorage.currentBrowsepath || sessionStorage.resID !== SHORT_ID) {
        sessionStorage.currentBrowsepath = JSON.stringify({path: []});
    }
    if (sessionStorage.resID !== SHORT_ID) {
        sessionStorage.resID = SHORT_ID;
    }

    let currentPath = JSON.parse(sessionStorage.currentBrowsepath);
    pathLog.push(currentPath);
    pathLogIndex = pathLog.length - 1;

    if (currentPath.hasOwnProperty("aggregation")) {
        get_aggregation_folder_struct(currentPath.aggregation);
    }
    else {
        get_irods_folder_struct_ajax_submit(SHORT_ID, currentPath);
    }

    updateNavigationState();

    var previewNode = $("#flag-uploading").removeClass("hidden").clone();
    $("#flag-uploading").remove();

    // Show file drop visual feedback
    var mode = $("#hs-file-browser").attr("data-mode");
    var acceptedFiles = $("#hs-file-browser").attr("data-supported-files").replace(/\(/g, '').replace(/\)/g, '').replace(/'/g, ''); // Strip undesired characters

    if (mode === "edit") {
        no_metadata_alert +=
        '<div class="text-center">' +
            '<a id="btnSideAddMetadata" type="button" class="btn btn-success" data-fb-action="">' +
                '<i class="fa fa-plus"></i> Add metadata' +
            '</a>' +
        '</div>'
    }

    if (mode === "edit" && acceptedFiles.length > 0) {
        var allowMultiple = null;
        if ($("#hs-file-browser").attr("data-allow-multiple-files") != "True") {
            allowMultiple = 1;
        }
        if (acceptedFiles === ".*") {
            acceptedFiles = null; // Dropzone default to accept all files
        }

        Dropzone.options.hsDropzone = {
            paramName: "files", // The name that will be used to transfer the file
            clickable: ".upload-toggle",
            previewsContainer: "#previews", // Define the container to display the previews
            maxFilesize: MAX_FILE_SIZE, // MB
            acceptedFiles: acceptedFiles,
            maxFiles: allowMultiple,
            autoProcessQueue: true,
            uploadMultiple: true,
            parallelUploads : 10,
            error: function (file, response) {
                // console.log(response);
            },
            success: onUploadSuccess,
            successmultiple: onUploadSuccess,
            init: function () {
                // The user dragged a file onto the Dropzone
                this.on("dragenter", function (file) {
                    $(".fb-drag-flag").show();
                    $("#hsDropzone").toggleClass("glow-blue", true);
                });

                this.on("drop", function (event) {
                    var myDropzone = this;
                    myDropzone.options.autoProcessQueue = false;    // Disable autoProcess queue so we can wait for the files to reach the queue before processing.

                    (function () {
                        // Wait for the files to reach the queue from the drop event. Check every 200 milliseconds
                        if (myDropzone.files.length > 0) {
                            myDropzone.processQueue();
                            myDropzone.options.autoProcessQueue = true; // Restore autoprocess
                            return;
                        }
                        setTimeout(arguments.callee, 200);
                    })();
                });

                // The user dragged a file out of the Dropzone
                this.on("dragleave", function (event) {
                    $(".fb-drag-flag").hide();
                    $("#hsDropzone").toggleClass("glow-blue", false);
                });

                // When a file is added to the list
                this.on("addedfile", function (file) {
                    var myDropzone = this;
                    if (getCurrentPath().hasOwnProperty("aggregation")) {
                        myDropzone.removeFile(file);
                        // Display an error here
                        $("#fb-alerts .upload-failed-alert").remove();
                        $("#hsDropzone").toggleClass("glow-blue", false);

                        $("#fb-alerts").append(
                            '<div class="alert alert-danger alert-dismissible upload-failed-alert" role="alert">' +
                                '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                                    '<span aria-hidden="true">&times;</span></button>' +
                                '<div>' +
                                    '<strong>File Upload Failed</strong>'+
                                '</div>'+
                                '<div>'+
                                    '<span>File upload is not allowed. Target folder seems to contain aggregation(s).</span>' +
                                '</div>'+
                            '</div>').fadeIn(200);
                        }

                    $(".fb-drag-flag").hide();
                });

                // When a file gets processed
                this.on("processing", function (file) {
                    if (!$("#flag-uploading").length) {
                        $("#root-path").text(getCurrentPath().path.length > 0 ? "contents/" : "contents");
                        $("#fb-inner-controls").append(previewNode);
                    }
                    $("#hsDropzone").toggleClass("glow-blue", false);
                });

                // Called when all files in the queue finish uploading.
                this.on("queuecomplete", function () {
                    let resourceType = $("#resource-type").val();
                    // Remove further paths from the log
                    let range = pathLog.length - pathLogIndex;
                    pathLog.splice(pathLogIndex + 1, range);
                    pathLog.push(JSON.parse(sessionStorage.currentBrowsepath));
                    pathLogIndex = pathLog.length - 1;

                    if (resourceType === 'Composite Resource') {
                        sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
                        refreshFileBrowser();
                    }
                    else {
                        refreshFileBrowser();
                        $("#previews").empty();
                    }
                });

                // An error occured. Receives the errorMessage as second parameter and if the error was due to the XMLHttpRequest the xhr object as third.
                this.on("error", function (error, errorMessage) {
                    $("#fb-alerts .upload-failed-alert").remove();
                    $("#hsDropzone").toggleClass("glow-blue", false);

                    $("#fb-alerts").append(
                            '<div class="alert alert-danger alert-dismissible upload-failed-alert" role="alert">' +
                                '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                                    '<span aria-hidden="true">&times;</span></button>' +
                                '<div>' +
                                    '<strong>File Upload Failed</strong>'+
                                '</div>'+
                                '<div>'+
                                    '<span>' + JSON.stringify(errorMessage) + '</span>' +
                                '</div>'+
                            '</div>').fadeIn(200);
                });

                // Called with the total uploadProgress (0-100), the totalBytes and the totalBytesSent
                this.on("totaluploadprogress", function (uploadProgress, totalBytes , totalBytesSent) {
                    $("#upload-progress").text(formatBytes(totalBytesSent) + " / " +  formatBytes(totalBytes) + " (" + parseInt(uploadProgress) + "%)" );
                });

                this.on('sending', function (file, xhr, formData) {
                    formData.append('file_folder', getCurrentPath().path.join('/'));
                });

                // Applies allowing upload of multiple files to OS upload dialog
                if (allowMultiple) {
                    this.hiddenFileInput.removeAttribute('multiple');
                    var fileCount = parseInt($("#hs-file-browser").attr("data-initial-file-count"));
                    if (fileCount > 0) {
                        $('.dz-input').hide();
                    }
                }
            }
        };
    }

    // Toggle between grid and list view
    $("#btn-group-view button").click(function () {
        $("#btn-group-view button").toggleClass("active");
        if ($(this).attr("data-view") === "list") {
            // ------- switch to table view -------
            $("#fb-files-container").removeClass("fb-view-grid");
            $("#fb-files-container").addClass("fb-view-list");
            localStorage.setItem('file-browser-view', 'fb-view-list');
        }
        else {
            // ------- Switch to grid view -------
            $("#fb-files-container").removeClass("fb-view-list");
            $("#fb-files-container").addClass("fb-view-grid");
            localStorage.setItem('file-browser-view', 'fb-view-grid');
        }
    });

    // Bind click events
    $("#fb-bread-crumbs").on("click", "li:not(.active)", function () {
        let path = $(this).attr("data-path").length ? $(this).attr("data-path").split('/') : [];
        path = {path: path};

        sessionStorage.currentBrowsepath = JSON.stringify(path);
        pathLog.push(path);
        pathLogIndex = pathLog.length - 1;
        get_irods_folder_struct_ajax_submit(SHORT_ID, path);
        $("#fileTypeMetaDataTab").html(file_metadata_alert);
    });

    // Bind file browser gui events
    bindFileBrowserItemEvents();

    // Bind sort method
    $("#fb-sort li").click(function () {
        if ($(this).attr("data-method")) {
            $("#fb-sort li[data-method]").removeClass("active");
            $(this).addClass("active");
        }

        if ($(this).attr("data-order")) {
            $("#fb-sort li[data-order]").removeClass("active");
            $(this).addClass("active");
        }
        onSort();
    });

    // Filter files on search input text change
    function filter(){
        var items = $('#fb-files-container li').children('span.fb-file-name');
        var search = $("#txtDirSearch").val().toLowerCase();
        for (var i = 0; i < items.length; i++) {
            if ($(items[i]).text().toLowerCase().indexOf(search) >= 0) {
                $(items[i]).parent().removeClass("hidden");
            }
            else {
                $(items[i]).parent().addClass("hidden");
            }
        }
    }
    $("#txtDirSearch").on("input", filter);

    // Clear search input
    $("#btn-clear-search-input").click(function(){
        $("#txtDirSearch").val("");
        filter();
    });

    $('#create-folder-dialog').on('shown.bs.modal', function () {
        $('#txtFolderName').val("");
        $('#txtFolderName').closest(".modal-content").find(".btn-primary").toggleClass("disabled", true);
        $('#txtFolderName').focus();
    });

    $('#add-reference-url-dialog').on('shown.bs.modal', function () {
        $('#txtRefName').val("");
        $('#txtRefName').closest(".modal-content").find(".btn-primary").toggleClass("disabled", true);
        $('#txtRefName').focus();
    });

    $('#redirect-referenced-url-dialog').on('shown.bs.modal', function () {
        let file = $("#fb-files-container li.ui-selected");
        // do redirect
        let ref_url = file.attr("data-ref-url");
        $('#file_redirect_url').prop('href', ref_url);
    });

    $("[data-fb-action='zip']").click(function() {
         var folderName =$("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        $("#txtZipName").val(folderName);
    });

    $('#zip-folder-dialog').on('shown.bs.modal', function () {
        $('#txtZipName').focus();

        // Select the file name by default
        var input = document.getElementById("txtZipName");
        var startPos = 0;
        var endPos = $("#txtZipName").val().length;

        if (typeof input.selectionStart !== "undefined") {
            input.selectionStart = startPos;
            input.selectionEnd = endPos;
        } else if (document.selection && document.selection.createRange) {
            // IE branch
            input.select();
            var range = document.selection.createRange();
            range.collapse(true);
            range.moveEnd("character", endPos);
            range.moveStart("character", startPos);
            range.select();
        }
    });

    $('#edit-referenced-url-dialog').on('shown.bs.modal', function () {
        var file = $("#fb-files-container li.ui-selected");
        var ref_url = file.attr("data-ref-url");
        $('#txtNewRefURL').val(ref_url);
        $('#txtNewRefURL').focus();

        // Select the reference url by default
        var input = document.getElementById("txtNewRefURL");
        var startPos = 0;
        var endPos = $("#txtNewRefURL").val().length;

        if (typeof input.selectionStart != "undefined") {
            input.selectionStart = startPos;
            input.selectionEnd = endPos;
        } else if (document.selection && document.selection.createRange) {
            // IE branch
            input.select();
            var range = document.selection.createRange();
            range.collapse(true);
            range.moveEnd("character", endPos);
            range.moveStart("character", startPos);
            range.select();
        }

        $('#txtNewRefURL').closest(".modal-content").find(".btn-primary").toggleClass("disabled", false);
    });

    $('#rename-dialog').on('shown.bs.modal', function () {
        $('#txtName').focus();

        // Select the file name by default
        var input = document.getElementById("txtName");
        var startPos = 0;
        var endPos = $("#txtName").val().lastIndexOf(".");

        if (endPos == -1 || $("#file-type-addon").length) {
            endPos = $("#txtName").val().length;
        }

        if (typeof input.selectionStart !== "undefined") {
            input.selectionStart = startPos;
            input.selectionEnd = endPos;
        } else if (document.selection && document.selection.createRange) {
            // IE branch
            input.select();
            var range = document.selection.createRange();
            range.collapse(true);
            range.moveEnd("character", endPos);
            range.moveStart("character", startPos);
            range.select();
        }

        $('#txtName').closest(".modal-content").find(".btn-primary").toggleClass("disabled", false);
    });

    $('#get-file-url-dialog').on('shown.bs.modal', function () {
        $('#txtFileURL').focus();

        // Select the file name by default
        var input = document.getElementById("txtFileURL");
        var startPos = 0;
        var endPos = $("#txtFileURL").val().length;

        if (typeof input.selectionStart !== "undefined") {
            input.selectionStart = startPos;
            input.selectionEnd = endPos;
        } else if (document.selection && document.selection.createRange) {
            // IE branch
            input.select();
            var range = document.selection.createRange();
            range.collapse(true);
            range.moveEnd("character", endPos);
            range.moveStart("character", startPos);
            range.select();
        }
    });

    $(".click-select-all").click(function () {
        var input = $(this);
        var startPos = 0;
        var endPos = input.val().length;

        if (typeof this.selectionStart !== "undefined") {
            this.selectionStart = startPos;
            this.selectionEnd = endPos;
        } else if (document.selection && document.selection.createRange) {
            // IE branch
            this.select();
            var range = document.selection.createRange();
            range.collapse(true);
            range.moveEnd("character", endPos);
            range.moveStart("character", startPos);
            range.select();
        }
    });

    // Create folder at current directory
    $("#btn-create-folder").click(function () {
        var folderName = $("#txtFolderName").val();
        var newFolderPath;
        if (folderName) {
            var calls = [];
            newFolderPath = {path: getCurrentPath().path.concat(folderName)};
            calls.push(create_irods_folder_ajax_submit(SHORT_ID, newFolderPath.path.join('/')));

            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
            });

            $.when.apply($, calls).fail(function () {
                refreshFileBrowser();
            });
        }
        return false;
    });

    // Add web url reference content at current directory
    $("#btn-add-reference-url").click(function () {
        var refName = $("#txtRefName").val();
        var refURL = $("#txtRefURL").val();
        if (refName && refURL) {
            var calls = [];
            calls.push(add_ref_content_ajax_submit(SHORT_ID, getCurrentPath().path.join('/'), refName, refURL, true));

            // Disable the Cancel button until request has finished
            $(this).parent().find(".btn[data-dismiss='modal']").addClass("disabled");

            function afterRequest() {
                refreshFileBrowser();
                $("#btn-add-reference-url").removeClass("disabled").text("Add Content");
                $("#btn-add-reference-url").parent().find(".btn[data-dismiss='modal']").removeClass("disabled");
            }

            $.when.apply($, calls).done(afterRequest);
            $.when.apply($, calls).fail(afterRequest);
        }
        return false;
    });

    // User clicked Proceed button on invalid URL warning dialog - need to add url without validation
    $("#btn-reference-url-without-validation").click(function () {
        var refName = $("#ref_name_passover").val();
        var refURL = $("#ref_url_passover").val();
        var newRefURL = $("#new_ref_url_passover").val();
        var calls = [];
        if (refName && refURL) {
            calls.push(add_ref_content_ajax_submit(SHORT_ID, getCurrentPath().path.join('/'), refName, refURL, false));

            // Disable the Cancel button until request has finished
            $(this).parent().find(".btn[data-dismiss='modal']").addClass("disabled");

            function afterRequest() {
                refreshFileBrowser();
                $("#btn-reference-url-without-validation").parent().find(".btn[data-dismiss='modal']").removeClass("disabled");
            }

            $.when.apply($, calls).done(afterRequest);
            $.when.apply($, calls).fail(afterRequest);
        }
        else if (refName && newRefURL) {
            var file = $("#fb-files-container li.ui-selected");
            var oldurl = file.attr("data-ref-url");
            if (oldurl != newRefURL) {
                calls.push(update_ref_url_ajax_submit(SHORT_ID, getCurrentPath().path.join('/'), refName, newRefURL, false));
                $.when.apply($, calls).done(function () {
                    refreshFileBrowser();
                });

                $.when.apply($, calls).fail(function () {
                    refreshFileBrowser();
                });
            }
        }
        return false;
    });

    // Update reference URL method
    $("#btn-edit-url").click(function () {
        var file = $("#fb-files-container li.ui-selected");
        var oldurl = file.attr("data-ref-url");
        var oldName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        var newurl = $("#txtNewRefURL").val().trim();
        if (oldurl != newurl) {
            var calls = [];
            calls.push(update_ref_url_ajax_submit(SHORT_ID, getCurrentPath().path.join('/'), oldName, newurl, true));

            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
            });

            $.when.apply($, calls).fail(function () {
                refreshFileBrowser();
            });
        }
    });

    // Move up one directory
    $("#fb-move-up").click(function () {
        var upPath = {path: getCurrentPath().path.slice()};
        upPath.path.pop();  // Remove last item

        pathLog.push(upPath);
        pathLogIndex = pathLog.length - 1;

        if (getCurrentPath().hasOwnProperty("aggregation")) {
            get_aggregation_folder_struct(getCurrentPath().aggregation);
        }
        else {
            get_irods_folder_struct_ajax_submit(SHORT_ID, getCurrentPath());
        }
        sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
    });

    // Move back
    $("#fb-move-back").click(function () {
        if (pathLogIndex > 0) {
            pathLogIndex--;
            if (pathLogIndex == 0) {
                // we are at the root folder
                $("#fb-move-back").addClass("disabled");
            }
            if (pathLog[pathLogIndex].hasOwnProperty("aggregation")) {
                get_aggregation_folder_struct(getCurrentPath().aggregation);
            }
            else {
                get_irods_folder_struct_ajax_submit(SHORT_ID, getCurrentPath());
            }

            sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
        }
    });

    // Move forward
    $("#fb-move-forward").click(function () {
        if (pathLogIndex < pathLog.length) {
            pathLogIndex++;
            if (pathLogIndex == pathLog.length - 1) {
                $("#fb-move-forward").addClass("disabled");
            }

            if (getCurrentPath().hasOwnProperty("aggregation")) {
                get_aggregation_folder_struct(getCurrentPath().aggregation);
            }
            else {
                get_irods_folder_struct_ajax_submit(SHORT_ID, getCurrentPath());
            }
            sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
        }
    });

    $("#btn-open").click(onOpenFolder);
    $("#btn-cut, #fb-cut").click(onCut);
    $(".selection-menu li[data-menu-name='paste'], #fb-paste").click(onPaste);

    function onCut() {
        let selection = $("#fb-files-container li.ui-selected:not(.hidden)");
        clearSourcePaths();

        selection.addClass("fb-cutting");
        sourcePaths = {path: getCurrentPath().path, selected: selection};

        if (selection.length) {
            $(".selection-menu").children("li[data-menu-name='paste']").toggleClass("disabled", false);
            $("#fb-paste").toggleClass("disabled", false);
        }

        $("#fb-cut").toggleClass("disabled", true);
    }

    // File(s) delete method
    $("#btn-confirm-delete").click(function () {
        var deleteList = $("#fb-files-container li.ui-selected");
        var filesToDelete = "";
        $(".file-browser-container, #fb-files-container").css("cursor", "progress");
        if (deleteList.length) {
            var calls = [];
            for (var i = 0; i < deleteList.length; i++) {
                let item = $(deleteList[i]);
                var pk = item.attr("data-pk");
                if (pk) {
                    if (filesToDelete !== "") {
                        filesToDelete += ",";
                    }
                    filesToDelete += pk;
                }
                else {
                    if (isVirtualFolder(item.first())) {
                        // Item is a virtual folder
                        let hs_file_type = item.find(".fb-logical-file-type").attr("data-logical-file-type");
                        let file_type_id = item.attr("data-logical-file-id");
                        calls.push(delete_virtual_folder_ajax_submit(hs_file_type, file_type_id));
                    }
                    else {
                        // Item is a regular folder
                        let folderName = item.children(".fb-file-name").text();
                        let folder_path = getCurrentPath().path.concat(folderName);
                        calls.push(delete_folder_ajax_submit(SHORT_ID, folder_path.join('/')));
                    }
                }
            }

            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function () {
                if (filesToDelete !== "") {
                    $("#fb-delete-files-form input[name='file_ids']").val(filesToDelete);
                    $("#fb-delete-files-form").submit();
                }
                else {
                    refreshFileBrowser();
                }
            });

            $.when.apply($, calls).fail(function () {
                if (filesToDelete !== "") {
                    $("#fb-delete-files-form input[name='file_ids']").val(filesToDelete);
                    $("#fb-delete-files-form").submit();
                }
                else {
                    refreshFileBrowser();
                }
            });
        }
    });

    // Populate name field when menu item is clicked
    $(".selection-menu li[data-menu-name='rename'], #fb-rename").click(function(){
        $('.selection-menu').hide();
        var name = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();

        if ($("#file-type-addon").length) {
            var ext = name.substr(name.lastIndexOf("."), name.length);
            $("#file-type-addon").text(ext);
            name = name.substr(0, name.lastIndexOf("."));
        }

        $("#txtName").val(name);
    });

    // Rename method
    $("#btn-rename").click(function () {
        let selected = $("#fb-files-container li.ui-selected");
        var oldName = selected.children(".fb-file-name").text().trim();
        var newName = $("#txtName").val();

        let fileTypeAddon = $("#file-type-addon");
        if (fileTypeAddon.length) {
            newName = newName + fileTypeAddon.text();
        }

        // make sure .url file has .url extension after renaming
        if (oldName.endsWith('.url') && !newName.endsWith('.url')) {
            newName = newName + '.url';
        }

        var calls = [];
        var oldNamePath = getCurrentPath().path.concat(oldName);
        var newNamePath = getCurrentPath().path.concat(newName);

        if (isVirtualFolder(selected.first())){
            let fileType = selected.children(".fb-logical-file-type").attr("data-logical-file-type");
            let fileTypeId = selected.attr("data-logical-file-id");
            calls.push(rename_virtual_folder_ajax_submit(fileType, fileTypeId, newName));
        }
        else {
            calls.push(rename_file_or_folder_ajax_submit(SHORT_ID, oldNamePath.join('/'), newNamePath.join('/')));
        }

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            $("#btn-rename").text("Save Changes");
            $("#rename-dialog").modal('hide');
            refreshFileBrowser();
        });

        $.when.apply($, calls).fail(function () {
            sessionStorage.currentBrowsepath = JSON.stringify(getCurrentPath());
            $("#btn-rename").text("Save Changes");
            $("#rename-dialog").modal('hide');
            refreshFileBrowser();
        });
    });

    // Download method
    $("[data-fb-action='download']").click(function () {
        if ($("#hs-file-browser").attr("data-agreement") === "true") {
            isDownloadZipped = false;
            $("#license-agree-dialog-file").modal('show');
            return;
        }

        startDownload();
    });

    // Download zipped method
    $("[data-fb-action='downloadZipped']").click(function () {
        if ($("#hs-file-browser").attr("data-agreement") === "true") {
            isDownloadZipped = true;
            $("#license-agree-dialog-file").modal('show');
            return;
        }

        startDownload(true);
    });

    $("#download-file-btn").click(function() {
        $("#license-agree-dialog-file").modal('hide');
        startDownload(isDownloadZipped);
    });

    // Get file or folder URL
    $("#btn-get-link, #fb-get-link").click(function () {
        var item = $("#fb-files-container li.ui-selected");
        var url = item.attr("data-url");
        var basePath = window.location.protocol + "//" + window.location.host;

        if (item.hasClass("fb-folder") && item.attr("data-logical-file-id") &&
            item.find(".fb-logical-file-type").attr("data-logical-file-type") !== "FileSetLogicalFile") {
            // The selected item is a virtual folder
            let parameters = ["zipped=true", "aggregation=true"];
            url += "?" + parameters.join("&");
        }

        $("#txtFileURL").val(basePath + url);
    });

    // set generic file type method
    $("#hs-file-browser, #right-click-menu").on("click", "[data-fb-action='setGenericFileType']", function () {
        setFileType("SingleFile");
    });

    // set fileset file type method
    $("#hs-file-browser, #right-click-menu").on("click", "[data-fb-action='setFileSetFileType']", function () {
        setFileType("FileSet");
    });

    // set geo raster file type method
    $("#btn-set-geo-file-type").click(function () {
        setFileType("GeoRaster");
    });

    // set NetCDF file type method
    $("#btn-set-netcdf-file-type").click(function () {
        setFileType("NetCDF");
    });

    // set GeoFeature file type method
    $("#btn-set-geofeature-file-type").click(function () {
        setFileType("GeoFeature");
    });
    // set RefTimeseries file type method
    $("#btn-set-refts-file-type").click(function () {
        setFileType("RefTimeseries");
    });

    // set Timeseries file type method
    $("#btn-set-timeseris-file-type").click(function () {
        setFileType("TimeSeries");
    });

    // set remove aggregation (file type) method
    $("#btnRemoveAggregation").click(function () {
        removeAggregation();
    });

    // Zip method
    $("#btn-confirm-zip").click(async function () {
        if ($("#txtZipName").val().trim() !== "") {
            const folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
            const fileName = $("#txtZipName").val() + ".zip";
            const path = getCurrentPath().path.concat(folderName);
            await zip_irods_folder_ajax_submit(SHORT_ID, path.join('/'), fileName);
            refreshFileBrowser();
        }
    });

    // Unzip method
    $("#btn-unzip, #fb-unzip").click(function () {
        var files = $("#fb-files-container li.ui-selected");

        var calls = [];
        for (let i = 0; i < files.length; i++) {
            let fileName = $(files[i]).children(".fb-file-name").text();
            calls.push(unzip_irods_file_ajax_submit(SHORT_ID, getCurrentPath().path.concat(fileName).join('/')));
        }

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });

        $.when.apply($, calls).fail(function () {
            refreshFileBrowser();
        });
    });

    // Download All method
    $("#btn-download-all, #download-bag-btn").click(function (event) {
        $(event.currentTarget).toggleClass("disabled", true);
        const bagUrl = event.currentTarget.dataset ? event.currentTarget.dataset.bagUrl : null;

        if (!bagUrl) {
            return; // If no url, it means download will be triggered from Agreement modal
        }

        $.ajax({
            type: "GET",
            url: bagUrl,
            success: function (task) {
                notificationsApp.registerTask(task);
                notificationsApp.show();
                $(event.currentTarget).toggleClass("disabled", false);
            }
        });
    });

    $(".selection-menu li").click(function () {
        $(".selection-menu").hide();
    });

    $(".selection-menu li[data-menu-name='refresh'], #fb-refresh").click(function () {
        refreshFileBrowser();
    });

    $(".selection-menu li[data-menu-name='select-all'], #fb-select-all").click(function () {
        $("#fb-files-container > li").removeClass("ui-selected");
        $("#fb-files-container > li:not(.hidden)").addClass("ui-selected");
        updateSelectionMenuContext();
    });

    $(".modal input.modal-only-required").keyup(function(event) {
        var submitBtn = $(this).closest(".modal-content").find(".btn-primary");
        submitBtn.toggleClass("disabled", $(this).val().trim() == "");
        var key = event.which;
        if (key == 13) {    // The enter key
            submitBtn.trigger('click');
        }
    });

    updateSelectionMenuContext();

    $(".fb-dropzone-wrapper.ui-resizable").resizable({
        resize: function (event, ui) {
            $("#fb-metadata").height(ui.size.height);
        },
        handles: "e, s, se",
        minHeight: 300,
    });

    $("#fb-metadata").resizable({
        resize: function (event, ui) {
            $(".fb-dropzone-wrapper").height(ui.size.height);
        },
        minHeight: 300,
        handles: "s",
    });

    $(".fb-metadata-collapse").click(function() {
        $(".fb-metadata-collapse").toggleClass("hidden");
        $(".fb-metadata").toggleClass("hidden");
        $(".fb-dropzone-wrapper").toggleClass("fb-collapsed");
        $(".ui-resizable-e").toggleClass("hidden");
        $("#fb-metadata-helper .ui-icon-grip-dotted-vertical").toggleClass("hidden");

        const selected = $("#fb-files-container li.ui-selected");

        if (!($("#fb-metadata").hasClass("hidden"))) {
            if (selected.length == 1) {
                $("#fileTypeMetaData").html(loading_metadata_alert);
                showFileTypeMetadata(false, "");
            }
            else {
                $("#fileTypeMetaData").html(file_metadata_alert);
            }
        }
    });
});

var cookieName = "page_scroll";
var expdays = 365;

// used for setting various file types within composite resource
function setFileType(fileType){
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
}

// Get resource metadata and update UI elements
function updateResourceUI() {
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
}

// used for removing aggregation (file type) within composite resource
function removeAggregation(){
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
}

// Used to set the previous scroll position after refresh
function setCookie(name, value, expires, path, domain, secure) {
    if (!expires) {
        expires = new Date()
    }
    document.cookie = name + "=" + escape(value) +
        ((expires == null) ? "" : "; expires=" + expires.toGMTString()) +
        ((path == null) ? "" : "; path=" + path) +
        ((domain == null) ? "" : "; domain=" + domain) +
        ((secure == null) ? "" : "; secure")
}

function getCookie(name) {
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
}

function getCookieVal(offset) {
    var endstr = document.cookie.indexOf(";", offset);
    if (endstr == -1)
        endstr = document.cookie.length;
    return unescape(document.cookie.substring(offset, endstr));
}
