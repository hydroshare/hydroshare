/**
 * Created by Mauriel on 8/16/2016.
 */

var sourcePaths = [];
var pathLog = [];
var pathLogIndex = 0;
var isDragging = false;
var file_metadata_alert = '<div class="alert alert-warning alert-dismissible" role="alert">' +
    '<h4>Select content in the file browser to see metadata specific to that content. Metadata will only display here when the the content is selected above. Content specific metadata does not display on the Discover page.</h4>' +
    '</div>';

const MAX_FILE_SIZE = 1024; // MB

function getFolderTemplateInstance(folderName, url, folderAgrregationType, folderAggregationName, folderAggregationID, folderAggregationTypeToSet, folderShortPath, mainFile) {
    if(folderAgrregationType.length >0){
        var folderIcons = getFolderIcons();
        iconTemplate = folderIcons.DEFAULT;

        if (folderIcons[folderAgrregationType]) {
            iconTemplate = folderIcons[folderAgrregationType];
        }
        return "<li class='fb-folder droppable draggable' data-url='" + url + "' data-logical-file-id='" + folderAggregationID+ "' main-file='" + mainFile + "' title='" + folderName + "&#13;" + folderAggregationName + "' >" +
                iconTemplate +
                "<span class='fb-file-name'>" + folderName + "</span>" +
                "<span class='fb-file-type'>File Folder</span>" +
                "<span class='fb-logical-file-type' data-logical-file-type='" + folderAgrregationType + "' data-logical-file-id='" + folderAggregationID +  "'>" + folderAggregationName + "</span>" +
                "<span class='fb-file-size'></span>" +
            "</li>"
    }
    else {
        return "<li class='fb-folder droppable draggable' data-url='" + url + "' title='" + folderName + "&#13;Type: File Folder'>" +
            "<span class='fb-file-icon fa fa-folder icon-blue'></span>" +
            "<span class='fb-file-name'>" + folderName + "</span>" +
            "<span class='fb-file-type' data-folder-short-path='" + folderShortPath + "'>File Folder</span>" +
            "<span class='fb-logical-file-type' data-logical-file-type-to-set='" + folderAggregationTypeToSet + "'></span>" +
            "<span class='fb-file-size'></span>" +
            "</li>"
    }
}

// Associates file icons with file extensions. Could be improved with a dictionary.
function getFileTemplateInstance(fileName, fileType, aggregation_name, logical_type, logical_file_id, fileSize, pk, url) {
    var fileTypeExt = fileName.substr(fileName.lastIndexOf(".") + 1, fileName.length);

    var iconTemplate;

    var fileIcons = getFileIcons();

    if (fileIcons[fileTypeExt.toUpperCase()]) {
        iconTemplate = fileIcons[fileTypeExt.toUpperCase()];
    }
    else if (fileName.toUpperCase().endsWith(".REFTS.JSON")){
        iconTemplate = fileIcons["JSON"];
    }
    else {
        iconTemplate = fileIcons.DEFAULT;
    }

    if (logical_type.length > 0){
        var title = '' + fileName + "&#13;Type: " + fileType + "&#13;Size: " + formatBytes(parseInt(fileSize)) + "&#13;" + aggregation_name;
    }
    else {
        var title = '' + fileName + "&#13;Type: " + fileType + "&#13;Size: " + formatBytes(parseInt(fileSize));
    }
    return "<li data-pk='" + pk + "' data-url='" + url + "' data-logical-file-id='" + logical_file_id + "' class='fb-file draggable' title='" + title + "'>" +
        iconTemplate +
        "<span class='fb-file-name'>" + fileName + "</span>" +
        "<span class='fb-file-type'>" + fileType + " File</span>" +
        "<span class='fb-logical-file-type' data-logical-file-type='" + logical_type + "' data-logical-file-id='" + logical_file_id +  "'>" + aggregation_name + "</span>" +
        "<span class='fb-file-size' data-file-size=" + fileSize + ">" + formatBytes(parseInt(fileSize)) + "</span></li>"
}

function formatBytes(bytes) {
    if(bytes < 1024) return bytes + " Bytes";
    else if(bytes < 1048576) return(bytes / 1024).toFixed(1) + " KB";
    else if(bytes < 1073741824) return(bytes / 1048576).toFixed(1) + " MB";
    else return(bytes / 1073741824).toFixed(1) + " GB";
}

// Updates the state of toolbar and menu buttons when a selection is made
function updateSelectionMenuContext() {
    var selected = $("#fb-files-container li.ui-selected");
    var resourceType = $("#resource-type").val();

    var flagDisableOpen = false;
    var flagDisableDownload = false;
    var flagDisableRename = false;
    var flagDisablePaste = false;
    var flagDisableZip = false;
    var flagDisableUnzip = false;
    var flagDisableCut = false;
    var flagDisableDelete = false;
    var flagDisableSetGenericFileType = false;
    var flagDisableSetGeoRasterFileType = false;
    var flagDisableSetNetCDFFileType = false;
    var flagDisableSetGeoFeatureFileType = false;
    var flagDisableSetRefTimeseriesFileType = false;
    var flagDisableSetTimeseriesFileType = false;
    var flagDisableRemoveAggregation = false;
    var flagDisableGetLink = false;
    var flagDisableCreateFolder = false;

    var maxSize = MAX_FILE_SIZE * 1024 * 1024; // convert MB to Bytes

    if (selected.length > 1) {          // Multiple files selected
        flagDisableRename = true;
        flagDisableOpen = true;
        flagDisablePaste = true;
        flagDisableZip = true;
        flagDisableSetGenericFileType = true;
        flagDisableSetGeoRasterFileType = true;
        flagDisableSetNetCDFFileType = true;
        flagDisableSetGeoFeatureFileType = true;
        flagDisableSetRefTimeseriesFileType = true;
        flagDisableSetTimeseriesFileType = true;
        flagDisableRemoveAggregation = true;
        flagDisableGetLink = true;

        for (var i = 0; i < selected.length; i++) {
            var size = parseInt($(selected[i]).find(".fb-file-size").attr("data-file-size"));
            if (size > maxSize) {
                flagDisableDownload = true;
            }
        }
        $("#fb-download-help").toggleClass("hidden", !flagDisableDownload);

        var foldersSelected = $("#fb-files-container li.fb-folder.ui-selected");
        if(resourceType === 'Composite Resource' && foldersSelected.length > 1) {
            flagDisableRemoveAggregation = true;
        }
        if(resourceType !== 'Composite Resource') {
            flagDisableRemoveAggregation = true;
        }
    }
    else if (selected.length == 1) {    // Exactly one file selected
        var size = parseInt(selected.find(".fb-file-size").attr("data-file-size"));
        if (size > maxSize) {
            flagDisableDownload = true;
            $("#fb-download-help").toggleClass("hidden", false);
        }
        else {
            $("#fb-download-help").toggleClass("hidden", true);
        }
    }
    else {                              // No files selected
        flagDisableCut = true;
        flagDisableRename = true;
        flagDisableUnzip = true;
        flagDisableZip = true;
        flagDisableDelete = true;
        flagDisableDownload = true;
        flagDisableGetLink = true;
        flagDisableSetGenericFileType = true;
        flagDisableSetNetCDFFileType = true;
        flagDisableSetGeoRasterFileType = true;
        flagDisableSetGeoFeatureFileType = true;
        flagDisableSetTimeseriesFileType = true;

        var foldersSelected = $("#fb-files-container li.fb-folder.ui-selected");
        if(resourceType === 'Composite Resource' && foldersSelected.length > 0) {
            flagDisableDelete = false;
        }
        if(resourceType === 'Composite Resource') {
            $("#fb-files-container").find('span.fb-logical-file-type').each(function() {
                var logicalFileType = $(this).attr("data-logical-file-type");
                //disable folder creation in aggregation folders
                //TODO this needs to be updated when new aggregations are added...
                if(logicalFileType === "GeoRasterLogicalFile" || logicalFileType === "NetCDFLogicalFile" ||
                    logicalFileType === "GeoFeatureLogicalFile" || logicalFileType === "TimeSeriesLogicalFile"){
                    if($(this).parent().hasClass("fb-file")){
                        flagDisableCreateFolder = true;
                    }
                }
            });
        }

        $("#fb-download-help").toggleClass("hidden", true);
    }

    if (selected.hasClass("fb-file")) {
        flagDisableOpen = true;
        flagDisablePaste = true;
        flagDisableZip = true;
        if (!selected.children('span').hasClass('fb-logical-file-type')){
            flagDisableRemoveAggregation = true;
        }
        else {
            var logicalFileType = selected.children('span.fb-logical-file-type').attr("data-logical-file-type");
            // if the selected file is part of the RefTimeseriesLogical or GenericLogicalFile file (aggregation) we
            // want the remove aggregation option not to show up
            if(logicalFileType !== 'RefTimeseriesLogicalFile' && logicalFileType !== "GenericLogicalFile"){
                flagDisableRemoveAggregation = true;
            }
        }
    }
    var isFolderSelected = false;
    if (selected.hasClass("fb-folder")) {
        flagDisableDownload = false;
        flagDisableUnzip = true;
        flagDisableGetLink = false;
        isFolderSelected = true;
        flagDisableSetGenericFileType = true;
        flagDisableSetRefTimeseriesFileType = true;
        if(!selected.children('span.fb-logical-file-type').attr("data-logical-file-type") ||
            selected.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set") ){
            flagDisableRemoveAggregation = true;
        }
        if(selected.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set")){
            var logicalFileTypeToSet = selected.children('span.fb-logical-file-type').attr("data-logical-file-type-to-set");
            if(logicalFileTypeToSet.length){
                if(logicalFileTypeToSet !== "NetCDFLogicalFile"){
                    flagDisableSetNetCDFFileType = true;
                }
                if(logicalFileTypeToSet !== "GeoRasterLogicalFile"){
                    flagDisableSetGeoRasterFileType = true;
                }
                if(logicalFileTypeToSet !== "GeoFeatureLogicalFile"){
                    flagDisableSetGeoFeatureFileType = true;
                }
                if(logicalFileTypeToSet !== "TimeSeriesLogicalFile"){
                    flagDisableSetTimeseriesFileType = true;
                }
            }
            else {
                flagDisableSetNetCDFFileType = true;
                flagDisableSetGeoRasterFileType = true;
                flagDisableSetGeoFeatureFileType = true;
                flagDisableSetTimeseriesFileType = true;
            }
        }
        else {
            flagDisableSetNetCDFFileType = true;
            flagDisableSetGeoRasterFileType = true;
            flagDisableSetGeoFeatureFileType = true;
            flagDisableSetTimeseriesFileType = true;
        }
    }

    if (!sourcePaths.length) {
        flagDisablePaste = true;
    }

    if(!isFolderSelected){
        for (var i = 0; i < selected.length; i++) {
            var fileName = $(selected[i]).children(".fb-file-name").text();
            var logicalFileType = $(selected[i]).children(".fb-logical-file-type").text();
            var currentPath = $("#hs-file-browser").attr("data-current-path");

            if(logicalFileType != "") {
                flagDisableSetGenericFileType = true;
            }
            if (!fileName.toUpperCase().endsWith("ZIP")) {
                flagDisableUnzip = true;
            }
            if ((!fileName.toUpperCase().endsWith("TIF") && !fileName.toUpperCase().endsWith("ZIP")) || logicalFileType != "") {
                flagDisableSetGeoRasterFileType = true;
            }

            if (!fileName.toUpperCase().endsWith("NC")  || logicalFileType != "") {
                flagDisableSetNetCDFFileType = true;
            }

            if ((!fileName.toUpperCase().endsWith("SHP") && !fileName.toUpperCase().endsWith("ZIP")) || logicalFileType != "") {
                flagDisableSetGeoFeatureFileType = true;
            }
            if (!fileName.toUpperCase().endsWith("REFTS.JSON")  || logicalFileType != "") {
                flagDisableSetRefTimeseriesFileType = true;
            }
            if ((!fileName.toUpperCase().endsWith("SQLITE") && !fileName.toUpperCase().endsWith("CSV")) || logicalFileType != "") {
                flagDisableSetTimeseriesFileType = true;
            }
            if(logicalFileType === "GeoRasterLogicalFile" || logicalFileType === "NetCDFLogicalFile" ||
                logicalFileType === "GeoFeatureLogicalFile" || logicalFileType === "TimeSeriesLogicalFile") {
                flagDisableCut = true;
                flagDisablePaste = true;
                flagDisableCreateFolder = true;
            }
        }
    }


    var logicalFileType = $("#fb-files-container li.fb-file.ui-selected").children('span.fb-logical-file-type').attr("data-logical-file-type");

    if (logicalFileType === "GeoRasterLogicalFile" || logicalFileType === "NetCDFLogicalFile" ||
        logicalFileType === "GeoFeatureLogicalFile" || logicalFileType === "TimeSeriesLogicalFile") {
            flagDisableCreateFolder = true;
            flagDisableRename = true;
            if(isFolderSelected){
                flagDisableDelete = false;
            }
            else {
                flagDisableDelete = true;
            }

            flagDisableCut = true;
            flagDisableSetGenericFileType = true;
        }
    // set Create folder toolbar option
    $("#fb-create-folder").toggleClass("disabled", flagDisableCreateFolder);

    var menu = $("#right-click-menu");
    var menu2 = $("#right-click-container-menu");

    // Open
    menu.children("li[data-menu-name='open']").toggleClass("hidden", flagDisableOpen);
    $("#open-separator").toggleClass("hidden", flagDisableOpen);
    if (!menu.children("li[data-menu-name='delete']").length) {
        $("#open-separator").toggleClass("hidden", true);
    }

    // Download
    menu.children("li[data-menu-name='download']").toggleClass("disabled", flagDisableDownload);
    $("#fb-download").toggleClass("disabled", flagDisableDownload);

    // Get file URL
    menu.children("li[data-menu-name='get-link']").toggleClass("disabled", flagDisableGetLink);
    $("#fb-get-link").toggleClass("disabled", flagDisableGetLink);

    // set Generic file type
    menu.children("li[data-menu-name='setgenericfiletype']").toggleClass("disabled", flagDisableSetGenericFileType);
    $("#fb-generic-file-type").toggleClass("disabled", flagDisableSetGenericFileType);

    // set Geo Raster file type
    menu.children("li[data-menu-name='setgeorasterfiletype']").toggleClass("disabled", flagDisableSetGeoRasterFileType);
    $("#fb-geo-file-type").toggleClass("disabled", flagDisableSetGeoRasterFileType);

    // set NetCDF file type
    menu.children("li[data-menu-name='setnetcdffiletype']").toggleClass("disabled", flagDisableSetNetCDFFileType);
    $("#fb-set-netcdf-file-type").toggleClass("disabled", flagDisableSetNetCDFFileType);

    // set GeoFeature file type
    menu.children("li[data-menu-name='setgeofeaturefiletype']").toggleClass("disabled", flagDisableSetGeoFeatureFileType);
    $("#fb-set-geofeature-file-type").toggleClass("disabled", flagDisableSetGeoFeatureFileType);

    // set RefTimeseries file type
    menu.children("li[data-menu-name='setreftsfiletype']").toggleClass("disabled", flagDisableSetRefTimeseriesFileType);
    $("#fb-set-refts-file-type").toggleClass("disabled", flagDisableSetRefTimeseriesFileType);

    // set Timeseries file type
    menu.children("li[data-menu-name='settimeseriesfiletype']").toggleClass("disabled", flagDisableSetTimeseriesFileType);
    $("#fb-set-timeseries-file-type").toggleClass("disabled", flagDisableSetTimeseriesFileType);

    // set Remove aggregation (file type)
    menu.children("li[data-menu-name='removeaggregation']").toggleClass("disabled", flagDisableRemoveAggregation);

    // Rename
    menu.children("li[data-menu-name='rename']").toggleClass("disabled", flagDisableRename);
    $("#fb-rename").toggleClass("disabled", flagDisableRename);

    // Zip
    menu.children("li[data-menu-name='zip']").toggleClass("hidden", flagDisableZip);
    $("#fb-zip").toggleClass("disabled", flagDisableZip);

    // Unzip
    menu.children("li[data-menu-name='unzip']").toggleClass("hidden", flagDisableUnzip);
    $("#fb-unzip").toggleClass("disabled", flagDisableUnzip);

    // Cut
    menu.children("li[data-menu-name='cut']").toggleClass("disabled", flagDisableCut);
    $("#fb-cut").toggleClass("disabled", flagDisableCut);

    // Paste
    menu.children("li[data-menu-name='paste']").toggleClass("disabled", flagDisablePaste);
    menu2.children("li[data-menu-name='paste']").toggleClass("disabled", flagDisablePaste);
    $("#fb-paste").toggleClass("disabled", flagDisablePaste);

    // set create folder right click menu option
    menu2.children("li[data-menu-name='new-folder']").toggleClass("disabled", flagDisableCreateFolder);

    // Delete
    $("#fb-delete").toggleClass("disabled", flagDisableDelete);
    menu.children("li[data-menu-name='delete']").toggleClass("disabled", flagDisableDelete);
    $("#delete-separator").toggleClass("hidden", flagDisableUnzip && flagDisableZip);
}

function bindFileBrowserItemEvents() {
    var mode = $("#hs-file-browser").attr("data-mode");

    // Drop
    if (mode == "edit") {
        $(".droppable").droppable({
            drop: function (event, ui) {
                var resID = $("#hs-file-browser").attr("data-res-id");
                var destination = $(event.target);
                var sources = $("#fb-files-container li.ui-selected").children(".fb-file-name");
                var destName = destination.children(".fb-file-name").text();
                var destFileType = destination.children(".fb-file-type").text();

                if (destFileType != "File Folder") {
                    return;
                }

                var currentPath = $("#hs-file-browser").attr("data-current-path");
                var destFolderPath = currentPath + "/" + destName;

                var calls = [];
                var callSources = [];
                for (var i = 0; i < sources.length; i++) {
                    var sourcePath = currentPath + "/" + $(sources[i]).text();
                    var destPath = destFolderPath + "/" + $(sources[i]).text();
                    if (sourcePath != destPath) {
                        callSources.push(sourcePath);
                    }
                }
                // use same entry point as cut/paste
                calls.push(move_to_folder_ajax_submit(resID, callSources, destFolderPath));

                $.when.apply($, calls).done(function () {
                    refreshFileBrowser();
                    destination.removeClass("fb-drag-cutting");
                });

                $.when.apply($, calls).fail(function () {
                    refreshFileBrowser();
                    destination.removeClass("fb-drag-cutting");
                });

                $("#fb-files-container li.ui-selected").fadeOut();
            },
            over: function (event, ui) {
                if (!$(event.target).hasClass("ui-selected")) {
                    $("#fb-files-container li.ui-selected").addClass("fb-drag-cutting");
                    $(event.target).addClass("fb-drag-cutting");
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
    $("#fb-files-container li").mousedown(function (e) {
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

    $("#fb-files-container li").mouseup(function (e) {
        // Handle "select" of clicked elements - Mouse Up
        if (!e.ctrlKey && !e.metaKey) {
            if ($(this).hasClass("fb-folder")) {
                // check if this is a left mouse button click
                if(e.which == 1) {
                    // showFileTypeMetadata(false, "");
                    $("#id_northlimit_filetype").attr("data-map-item", "northlimit");
                    $("#id_eastlimit_filetype").attr("data-map-item", "eastlimit");
                    $("#id_southlimit_filetype").attr("data-map-item", "southlimit");
                    $("#id_westlimit_filetype").attr("data-map-item", "westlimit");
                    $("#id_east_filetype").attr("data-map-item", "longitude");
                    $("#id_north_filetype").attr("data-map-item", "latitude");

                    updateEditCoverageState();

                    $("#id-coverage-spatial-filetype").coordinatesPicker();
                }
            }
            else{
                $("#fileTypeMetaDataTab").html(file_metadata_alert);
            }

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
    if (mode == "edit") {
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
    $("#fb-files-container")
        .selectable({
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
         timer = setTimeout(function() {
             if(!prevent){
                 showFileTypeMetadata(false, "");
             }
             prevent = false;
         }, delay)
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

            var fileAggType = $(event.target).closest("li").find("span.fb-logical-file-type").attr("data-logical-file-type");
            var fileName = $(event.target).closest("li").find("span.fb-file-name").text();
            var fileExtension = fileName.substr(fileName.lastIndexOf("."), fileName.length);
            var isFolder = $(event.target).closest("li").hasClass("fb-folder");

            // toggle apps by file extension and aggregations
            menu.find("li.btn-open-with").each(function() {
                var agg_app = false;
                if ($(this).attr("agg-types").trim() !== ""){
                    agg_app = $.inArray(fileAggType, $(this).attr("agg-types").split(",")) !== -1;
                }
                var extension_app = false;
                if ($(this).attr("file-extensions").trim() !== ""){
                    var extensions = $(this).attr("file-extensions").split(",")
                    for (var i = 0; i < extensions.length; ++i) {
                        if (fileExtension.toLowerCase() === extensions[i].trim().toLowerCase()){
                            extension_app = true;
                            break;
                        }
                    }
                }
                $(this).toggle(agg_app || extension_app);
            });
            menu.find("li#btn-download").each(function() {
                if(isFolder){
                    $(this).toggle(false);
                }
                else{
                    $(this).toggle(true);
                }
            });
        }
        else {
            menu = $("#right-click-container-menu");    // empty space was clicked
        }

        $(".selection-menu").hide();    // Hide other menus

        var top = event.pageY;
        var left = event.pageX;

        menu.css({top: top, left: left});

        if (menu.css("display") == "none") {
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
     $("#fileTypeMetaDataTab").html(file_metadata_alert);

     var selectedItem = $("#fb-files-container li.ui-selected");
     var logical_file_id = selectedItem.attr("data-logical-file-id");
     if (!logical_file_id || (logical_file_id && logical_file_id.length == 0)){
         return;
     }

     var logical_type = selectedItem.children('span.fb-logical-file-type').attr("data-logical-file-type");
     if (!logical_type){
        return; 
     }
     if(selectedItem.hasClass("fb-file")){
         // only in the case Ref TimeSeries file type or generic file type we need to show
         // file type metadata when a file is selected
         if(logical_type !== "RefTimeseriesLogicalFile" && logical_type !== "GenericLogicalFile"){
             return;
         }
     }
     var resource_mode = $("#resource-mode").val();
     if (!resource_mode){ 
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
             $("#fileTypeMetaDataTab").html(error_html);
             $(".file-browser-container, #fb-files-container").css("cursor", "auto");
             return;
         }

         $("#fileTypeMetaDataTab").html(json_response.metadata);
         $(".file-browser-container, #fb-files-container").css("cursor", "auto");
         $("#btn-add-keyword-filetype").click(onAddKeywordFileType);

         $("#txt-keyword-filetype").keypress(function (e) {
             e.which = e.which || e.keyCode;
             if (e.which == 13) {
                 onAddKeywordFileType();
                 return false;
             }
         });

         $(".icon-remove").click(onRemoveKeywordFileType);
         $("#id-update-netcdf-file").click(update_netcdf_file_ajax_submit);
         $("#id-update-sqlite-file").click(update_sqlite_file_ajax_submit);
         showMetadataFormSaveChangesButton();
         initializeDatePickers();
         setFileTypeSpatialCoverageFormFields(logical_type);
         // Bind event handler for submit button
         setFileTypeMetadataFormsClickHandlers();

         var $spatial_type_radio_button_1 = $("#div_id_type_filetype").find("#id_type_1");
         var $spatial_type_radio_button_2 = $("#div_id_type_filetype").find("#id_type_2");
         if (logical_type === "NetCDFLogicalFile") {
             // don't let the user open the Projection String Type dropdown list
             // when editing Oroginal Coverage element
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
             $("#series_id_file_type").change(function () {
                 var $url = $(this.form).attr('action');
                 $url = $url.replace('series_id', $(this).val());
                 $url = $url.replace('resource_mode', resource_mode);
                 // make a recursive call to this function
                 showFileTypeMetadata(true, $url);
             });
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
             $spatial_type_radio_button_1.prop("checked", true);
             $("#div_id_type_filetype input:radio").trigger("change");
             $spatial_type_radio_button_1.attr('onclick', 'return false');
             $spatial_type_radio_button_2.attr('onclick', 'return false');
         }
         else {
             if ($spatial_type_radio_button_1.attr('checked') == 'checked'){
                 $spatial_type_radio_button_1.prop("checked", true);
             }
             else {
                 $spatial_type_radio_button_2.prop("checked", true);
             }
         }

         $("#div_id_type_filetype input:radio").trigger("change");
    });
}

function InitializeTimeSeriesFileTypeForms() {
    var tsSelect = $(".time-series-forms select");

    tsSelect.append('<option value="Other">Other...</option>');

    tsSelect.parent().parent().append('<div class="controls other-field" style="display:none;"> <label class="text-muted control-label">Specify: </label><input class="form-control input-sm textinput textInput" name="" type="text"> </div>')

    tsSelect.change(function(e){
        if (e.target.value == "Other") {
            var name = e.target.name;
            $(e.target).parent().parent().find(".other-field").show();
            $(e.target).parent().parent().find(".other-field input").attr("name", name);
            $(e.target).removeAttr("name");
        }
        else {
            if (!e.target.name.length) {
                var name = $(e.target).parent().parent().find(".other-field input").attr("name");
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
function setBreadCrumbs(path) {
    var crumbs = $("#fb-bread-crumbs");
    crumbs.empty();

    if(!path) {
        return;
    }

    if (path && path.lastIndexOf("/") == "-1") {
        $("#fb-move-up").toggleClass("disabled", true)
    }
    else {
        $("#fb-move-up").toggleClass("disabled", false)
    }

    var setFirstActive = false;
    while (path){
        var folder = path.substr(path.lastIndexOf("/") + 1, path.length);
        var currentPath = path;
        path = path.substr(0, path.lastIndexOf("/"));
        if (setFirstActive) {
            crumbs.prepend('<li data-path="data/' + currentPath + '"><i class="fa fa-folder-o" aria-hidden="true"></i><span> ' + folder + '</span></li>');
        }
        else {
            crumbs.prepend('<li class="active"><i class="fa fa-folder-open-o" aria-hidden="true"></i><span> ' + folder + '</span></li>');
            setFirstActive = true;
        }
    }

    // Bind click events
    $("#fb-bread-crumbs li:not(.active)").click(function() {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var path = $(this).attr("data-path");

        pathLog.push(path);
        pathLogIndex = pathLog.length - 1;
        get_irods_folder_struct_ajax_submit(resID, path);
        $("#fileTypeMetaDataTab").html(file_metadata_alert);
    });
}

// File sorting sort algorithms
function sort(method, order) {
    var sorted;
    if (method == "name") {
        // Sort by name
        if (order == "asc") {
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
    else if (method == "size") {
        // Sort by size
        var size1, size2;

        sorted = $('#fb-files-container li').sort(function (element1, element2) {
            if (order == "asc") {
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
    else if (method == "type") {
        // Sort by type
        if (order == "asc") {
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
    startDownload();
}

function startDownload(zipped) {
    var downloadList = $("#fb-files-container li.ui-selected");

    // Remove previous temporary download frames
    $(".temp-download-frame").remove();

    if (downloadList.length) {
        // Workaround for Firefox and IE
        for (var i = 0; i < downloadList.length; i++) {
            var url = $(downloadList[i]).attr("data-url");
            if(zipped === true){
                url += "?zipped=True"
            }
            var frameID = "download-frame-" + i;
            $("body").append("<iframe class='temp-download-frame' id='"
                + frameID + "' style='display:none;' src='" + url + "'></iframe>");
        }
    }
}

function onOpenFolder() {
    var resID = $("#hs-file-browser").attr("data-res-id");
    var currentPath = $("#hs-file-browser").attr("data-current-path");
    var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
    var targetPath = currentPath + "/" + folderName;

    var flagDisableCreateFolder = false;
    // Remove further paths from the log
    var range = pathLog.length - pathLogIndex;
    pathLog.splice(pathLogIndex + 1, range);
    pathLog.push(targetPath);
    pathLogIndex = pathLog.length - 1;
    // remove any aggregation metadata display
    $("#fileTypeMetaDataTab").html(file_metadata_alert);

    var calls = [];
    calls.push(get_irods_folder_struct_ajax_submit(resID, targetPath));

    $.when.apply($, calls).done(function () {
        updateSelectionMenuContext();
        var logicalFileType = $("#fb-files-container li").children('span.fb-logical-file-type').attr("data-logical-file-type");
        if (logicalFileType.length > 0){
            flagDisableCreateFolder = true;
        }
        else {
            flagDisableCreateFolder = false;
        }

        // Set Create folder toolbar option
        $("#fb-create-folder").toggleClass("disabled", flagDisableCreateFolder);
    });

    $.when.apply($, calls).fail(function () {
        updateSelectionMenuContext();
    });
}

function updateNavigationState() {
    $("#fb-move-back").toggleClass("disabled", pathLogIndex == 0);
    $("#fb-move-forward").toggleClass("disabled", pathLogIndex >= pathLog.length - 1);

    var upPath = $("#hs-file-browser").attr("data-current-path");
    upPath = upPath.substr(0, upPath.lastIndexOf("/"));

    $("#fb-move-up").toggleClass("disabled", upPath == "data");
}

// Reload the current folder structure
function refreshFileBrowser() {
    var resID = $("#hs-file-browser").attr("data-res-id");
    var currentPath = $("#hs-file-browser").attr("data-current-path");
    var calls = [];
    calls.push(get_irods_folder_struct_ajax_submit(resID, currentPath));

    $.when.apply($, calls).done(function () {
        $("#fb-files-container li").removeClass("fb-cutting");
        $(".selection-menu").hide();
        sourcePaths = [];
        updateSelectionMenuContext();
        $("#fileTypeMetaDataTab").html(file_metadata_alert);
    });

    $.when.apply($, calls).fail(function () {
        $("#fb-files-container li").removeClass("fb-cutting");
        $(".selection-menu").hide();
        sourcePaths = [];
        updateSelectionMenuContext();
    });
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

    // Set initial folder structure
    var resID = $("#hs-file-browser").attr("data-res-id");
    if (resID) {
        get_irods_folder_struct_ajax_submit(resID, 'data/contents');
        pathLog.push('data/contents');
    }

    var previewNode = $("#flag-uploading").removeClass("hidden").clone();
    $("#flag-uploading").remove();

    // Show file drop visual feedback
    var mode = $("#hs-file-browser").attr("data-mode");
    var acceptedFiles = $("#hs-file-browser").attr("data-supported-files").replace(/\(/g, '').replace(/\)/g, '').replace(/'/g, ''); // Strip undesired characters

    if (mode == "edit" && acceptedFiles.length > 0) {
        var allowMultiple = null;
        if ($("#hs-file-browser").attr("data-allow-multiple-files") != "True") {
            allowMultiple = 1;
        }
        if (acceptedFiles == ".*") {
            acceptedFiles = null; // Dropzone default to accept all files
        }

        Dropzone.options.hsDropzone = {
            paramName: "files", // The name that will be used to transfer the file
            clickable: "#upload-toggle",
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
            success: function (file, response) {
                // console.log(response);
            },
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
                    $(".fb-drag-flag").hide();
                });

                // When a file gets processed
                this.on("processing", function (file) {
                    if (!$("#flag-uploading").length) {
                        var currentPath = $("#hs-file-browser").attr("data-current-path");
                        previewNode.find("#upload-folder-path").text(currentPath);
                        $("#fb-inner-controls").append(previewNode);
                    }
                    $("#hsDropzone").toggleClass("glow-blue", false);
                });

                // Called when all files in the queue finish uploading.
                this.on("queuecomplete", function () {
                    if ($("#hs-file-browser").attr("data-refresh-on-upload") == "true") {
                        // Page refresh is needed to show updated metadata
                        location.reload(true);
                    }
                    else {
                        var resourceType = $("#resource-type").val();
                        // Remove further paths from the log
                        var range = pathLog.length - pathLogIndex;
                        pathLog.splice(pathLogIndex + 1, range);
                        pathLog.push("data/contents");
                        pathLogIndex = pathLog.length - 1;

                        if(resourceType === 'Composite Resource') {
                            // uploaded files can affect metadata in composite resource.
                            // a full refresh is needed to reflect those changes
                            refreshResourceEditPage();
                        }
                        else {
                            refreshFileBrowser();
                            $("#previews").empty();
                        }
                    }
                });

                // An error occured. Receives the errorMessage as second parameter and if the error was due to the XMLHttpRequest the xhr object as third.
                this.on("error", function (error, errorMessage, xhr) {
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
                                    '<span>' + errorMessage + '</span>' +
                                '</div>'+
                            '</div>').fadeIn(200);
                });

                // Called with the total uploadProgress (0-100), the totalBytes and the totalBytesSent
                this.on("totaluploadprogress", function (uploadProgress, totalBytes , totalBytesSent) {
                    $("#upload-progress").text(formatBytes(totalBytesSent) + " / " +  formatBytes(totalBytes) + " (" + parseInt(uploadProgress) + "%)" );
                });

                this.on('sending', function (file, xhr, formData) {
                    formData.append('file_folder', $("#upload-folder-path").text());
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
        if ($(this).attr("data-view") == "list") {
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

    $('#zip-folder-dialog').on('shown.bs.modal', function () {
        $('#txtFolderName').focus();

        // Select the file name by default
        var input = document.getElementById("txtZipName");
        var startPos = 0;
        var endPos = $("#txtZipName").val().length;

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

        $('#txtName').closest(".modal-content").find(".btn-primary").toggleClass("disabled", false);
    });

    $('#get-file-url-dialog').on('shown.bs.modal', function () {
        $('#txtFileURL').focus();

        // Select the file name by default
        var input = document.getElementById("txtFileURL");
        var startPos = 0;
        var endPos = $("#txtFileURL").val().length;

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
    });

    $(".click-select-all").click(function () {
        var input = $(this);
        var startPos = 0;
        var endPos = input.val().length;

        if (typeof this.selectionStart != "undefined") {
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
        var resID = $("#hs-file-browser").attr("data-res-id");
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var folderName = $("#txtFolderName").val();
        if (folderName) {
            var calls = [];
            calls.push(create_irods_folder_ajax_submit(resID, currentPath + "/" + folderName));

            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
            });

            $.when.apply($, calls).fail(function () {
                refreshFileBrowser();
            });
        }
        return false;
    });

    // Move up one directory
    $("#fb-move-up").click(function () {
        var upPath = $("#hs-file-browser").attr("data-current-path");
        upPath = upPath.substr(0, upPath.lastIndexOf("/"));
        pathLog.push(upPath);
        pathLogIndex = pathLog.length - 1;
        get_irods_folder_struct_ajax_submit(resID, upPath);
    });

    // Move back
    $("#fb-move-back").click(function () {
        if (pathLogIndex > 0) {
            pathLogIndex--;
            if (pathLogIndex == 0) {
                $("#fb-move-back").addClass("disabled");
            }
            get_irods_folder_struct_ajax_submit(resID, pathLog[pathLogIndex]);
        }
    });

    // Move forward
    $("#fb-move-forward").click(function () {
        if (pathLogIndex < pathLog.length) {
            pathLogIndex++;
            if (pathLogIndex == pathLog.length - 1) {
                $("#fb-move-forward").addClass("disabled");
            }
            get_irods_folder_struct_ajax_submit(resID, pathLog[pathLogIndex]);
        }
    });

    $("#btn-open").click(onOpenFolder);

    $("#btn-cut, #fb-cut").click(onCut);

    function onCut() {
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        $("#fb-files-container li").removeClass("fb-cutting");
        sourcePaths = [];

        var selection = $("#fb-files-container li.ui-selected:not(.hidden)");

        for (var i = 0; i < selection.length; i++) {
            var itemName = $(selection[i]).children(".fb-file-name").text();
            sourcePaths.push(currentPath + "/" + itemName);

            $(selection[i]).addClass("fb-cutting");
        }

        if (sourcePaths.length) {
            $(".selection-menu").children("li[data-menu-name='paste']").toggleClass("disabled", false);
            $("#fb-paste").toggleClass("disabled", false);
        }

        $("#fb-cut").toggleClass("disabled", true);
    }

    $(".selection-menu li[data-menu-name='paste'], #fb-paste").click(onPaste);

    function onPaste() {
        var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        var currentPath = $("#hs-file-browser").attr("data-current-path");

        targetPath = currentPath + "/" + folderName
        
        var calls = [];
        var localSources = sourcePaths.slice()  // avoid concurrency botch due to call by reference
        calls.push(move_to_folder_ajax_submit(resID, localSources, targetPath));

        // Wait for the asynchronous call to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
            sourcePaths = [];
            $("#fb-files-container li").removeClass("fb-cutting");
            updateSelectionMenuContext();
        });

        $.when.apply($, calls).fail(function () {
            refreshFileBrowser();
            sourcePaths = [];
            $("#fb-files-container li").removeClass("fb-cutting");
            updateSelectionMenuContext();
        });
    }

    // File(s) delete method
    $("#btn-confirm-delete").click(function () {
        var deleteList = $("#fb-files-container li.ui-selected");
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var filesToDelete = "";
        $(".file-browser-container, #fb-files-container").css("cursor", "progress");
        if (deleteList.length) {
            var calls = [];
            for (var i = 0; i < deleteList.length; i++) {
                var pk = $(deleteList[i]).attr("data-pk");
                if (pk) {
                    if (filesToDelete != "") {
                        filesToDelete += ",";
                    }
                    filesToDelete += pk;
                }
                else {  // item is a folder
                    var folderName = $(deleteList[i]).children(".fb-file-name").text();
                    var folder_path = currentPath + "/" + folderName;
                    calls.push(delete_folder_ajax_submit(resID, folder_path));
                }
            }

            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function () {
                if (filesToDelete != "") {
                    $("#fb-delete-files-form input[name='file_ids']").val(filesToDelete);
                    $("#fb-delete-files-form").submit();
                }
                else {
                    refreshFileBrowser();
                }
            });

            $.when.apply($, calls).fail(function () {
                if (filesToDelete != "") {
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
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var oldName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        var newName = $("#txtName").val();

        if ($("#file-type-addon").length) {
            newName = newName + $("#file-type-addon").text();
        }

        var calls = [];
        calls.push(rename_file_or_folder_ajax_submit(resID, currentPath + "/" + oldName, currentPath + "/" + newName));

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });

        $.when.apply($, calls).fail(function () {
            refreshFileBrowser();
        });
    });

    // Download method
    $(" #btn-download, #download-file-btn, #fb-download").click(function (e) {
        if(e.currentTarget.id === "download-file-btn"){
            $("#license-agree-dialog-file").modal('hide');
        }

        startDownload();
    });

    // Download method
    $(" #btn-download-zip").click(function (e) {
        if(e.currentTarget.id === "download-file-btn"){
            $("#license-agree-dialog-file").modal('hide');
        }

        startDownload(true);
    });

    // Get file URL method
    $("#btn-get-link, #fb-get-link").click(function () {
        var file = $("#fb-files-container li.ui-selected");
        var URL = file.attr("data-url");
        var basePath = window.location.protocol + "//" + window.location.host;
        // currentURL = currentURL.substring(0, currentURL.length - 1); // Strip last "/"
        $("#txtFileURL").val(basePath + URL);
    });

    // Open with method
    $(".btn-open-with").click(function () {
        var file = $("#fb-files-container li.ui-selected");
        // only need that path after /data/contents/
        var path = file.attr("data-url").split('/data/contents/')[1];
        var fullURL;
        if (~$(this).attr("url_aggregation").indexOf("HS_JS_AGG_KEY")) {
            fullURL = $(this).attr("url_aggregation").replace("HS_JS_AGG_KEY", path);
            if (file.children('span.fb-file-type').text() === 'File Folder') {
                fullURL = fullURL.replace("HS_JS_MAIN_FILE_KEY", file.attr("main-file"));
            }
            else {
                fullURL = fullURL.replace("HS_JS_MAIN_FILE_KEY", file.children('span.fb-file-name').text());
            }
        }
        else {
            // not an aggregation
            fullURL = $(this).attr("url_file").replace("HS_JS_FILE_KEY", path);
        }
        window.open(fullURL);
    });

    // set generic file type method
     $("#btn-set-generic-file-type").click(function () {
         setFileType("SingleFile");
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
     $("#btn-remove-aggregation").click(function () {
         removeAggregation();
     });

    // Zip method
    $("#btn-confirm-zip").click(function () {
        if ($("#txtZipName").val().trim() != "") {
            var currentPath = $("#hs-file-browser").attr("data-current-path");
            var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
            var fileName = $("#txtZipName").val() + ".zip";

            var calls = [];
            calls.push(zip_irods_folder_ajax_submit(resID, currentPath + "/" + folderName, fileName));

            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
            });

            $.when.apply($, calls).fail(function () {
                refreshFileBrowser();
            });
        }
    });

    $("#btn-zip").click(function() {
        var folderName =$("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        $("#txtZipName").val(folderName);
    });

    // Unzip method
    $("#btn-unzip, #fb-unzip").click(function () {
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var files = $("#fb-files-container li.ui-selected");

        var calls = [];
        for (var i = 0; i < files.length; i++) {
            var fileName = $(files[i]).children(".fb-file-name").text()
            calls.push(unzip_irods_file_ajax_submit(resID, currentPath + "/" + fileName));
        }

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });

        $.when.apply($, calls).fail(function () {
            refreshFileBrowser();
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
});

var cookieName = "page_scroll";
var expdays = 365;

// used for setting various file types within composite resource
function setFileType(fileType){
    var resID = $("#hs-file-browser").attr("data-res-id");
    var url;
    var folderPath = "";
    if($("#fb-files-container li.ui-selected").hasClass('fb-file')){
        var file_id = $("#fb-files-container li.ui-selected").attr("data-pk");
        url = "/hsapi/_internal/" + resID + "/" + file_id + "/" + fileType + "/set-file-type/";
    }
    else {
        // this must be folder selection for aggregation creation
        var folderPath = $("#fb-files-container li.ui-selected").children('span.fb-file-type').attr("data-folder-short-path");
        url = "/hsapi/_internal/" + resID + "/" + fileType + "/set-file-type/";
    }

    $(".file-browser-container, #fb-files-container").css("cursor", "progress");
    var calls = [];
    calls.push(set_file_type_ajax_submit(url, folderPath));
    // Wait for the asynchronous calls to finish to get new folder structure
    $.when.apply($, calls).done(function (result) {
       $(".file-browser-container, #fb-files-container").css("cursor", "auto");
       var json_response = JSON.parse(result);
       $("#fileTypeMetaDataTab").html(file_metadata_alert);
       // page refresh is needed to show any extracted metadata used at the resource level
       if (json_response.status === 'success'){
           refreshResourceEditPage();
       }
    });
}

// used for removing aggregation (file type) within composite resource
function removeAggregation(){
    var aggregationType = $("#fb-files-container li.ui-selected").children('span.fb-logical-file-type').attr("data-logical-file-type");
    var aggregationID = $("#fb-files-container li.ui-selected").children('span.fb-logical-file-type').attr("data-logical-file-id");
    var resID = $("#hs-file-browser").attr("data-res-id");
    var url = "/hsapi/_internal/" + resID + "/" + aggregationType + "/" + aggregationID + "/remove-aggregation/";
    $(".file-browser-container, #fb-files-container").css("cursor", "progress");
    var calls = [];
    calls.push(remove_aggregation_ajax_submit(url));
    // Wait for the asynchronous calls to finish to get new folder structure
    $.when.apply($, calls).done(function (result) {
       $(".file-browser-container, #fb-files-container").css("cursor", "auto");
       var json_response = JSON.parse(result);
       $("#fileTypeMetaDataTab").html(file_metadata_alert);
       // page refresh is needed to show any extracted metadata used at the resource level
       if (json_response.status === 'success'){
           refreshResourceEditPage();
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
        if (document.cookie.substring(i, j) == arg) {
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
