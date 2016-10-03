/**
 * Created by Mauriel on 8/16/2016.
 */

var sourcePaths = [];

function selectSelectableElement (selectableContainer, elementsToSelect) {
    // add unselecting class to all elements in the styleboard canvas except the ones to select
    $(".ui-selected", selectableContainer).not(elementsToSelect).removeClass("ui-selected").addClass("ui-unselecting");

    // add ui-selecting class to the elements to select
    $(elementsToSelect).not(".ui-selected").addClass("ui-selected");

    // trigger the mouse stop event (this will select all .ui-selecting elements, and deselect all .ui-unselecting elements)
    selectableContainer.data("selectable")._mouseStop(null);
}

function updateSelectionMenuContext() {
    var selected = $("#fb-files-container li.ui-selected");

    var flagDisableOpen = false;
    var flagDisableDownload = false;
    var flagDisableRename = false;
    var flagDisablePaste = false;
    var flagDisableZip = false;
    var flagDisableUnzip = false;

    if (selected.length > 1) {
        flagDisableRename = true;   // 'rename' menu item
        flagDisableOpen = true;
        flagDisablePaste = true;
        flagDisableZip = true;
    }

    if (selected.hasClass("fb-file")) {
        flagDisableOpen = true;
        flagDisablePaste = true;
        flagDisableZip = true;
    }

    if (selected.hasClass("fb-folder")) {
        flagDisableDownload = true;
        flagDisableUnzip = true;
    }

    if (!sourcePaths.length) {
        flagDisablePaste = true;
    }

    for (var i = 0; i < selected.length; i++) {
        var fileName = $(selected[i]).children(".fb-file-name").text();
        var fileExt = fileName.substr(fileName.lastIndexOf(".") + 1, fileName.length);
        if (fileExt.toUpperCase() != "ZIP") {
            flagDisableUnzip = true;
        }
    }

    $("#right-click-menu").children("li[data-menu-name='open']").toggleClass("disabled", flagDisableOpen);
    $("#right-click-menu").children("li[data-menu-name='download']").toggleClass("disabled", flagDisableDownload);
    $("#right-click-menu").children("li[data-menu-name='rename']").toggleClass("disabled", flagDisableRename);
    $("#right-click-menu").children("li[data-menu-name='zip']").toggleClass("disabled", flagDisableZip);
    $("#right-click-menu").children("li[data-menu-name='unzip']").toggleClass("disabled", flagDisableUnzip);
    $(".selection-menu").children("li[data-menu-name='paste']").toggleClass("disabled", flagDisablePaste);
}

var isDragging = false;

function bindFileBrowserItemEvents() {
    // Drop
    $(".droppable").droppable({
        drop: function (event, ui) {
            var resID = $("#hs-file-browser").attr("data-res-id");
            var source = $(ui.helper);
            var destination = $(event.target);
            var sourceName = source.children(".fb-file-name").text();
            var destName = destination.children(".fb-file-name").text();
            var destFileType = destination.children(".fb-file-type").text();

            if (destFileType != "File Folder") {
                return;
            }

            var currentPath = $("#hs-file-browser").attr("data-current-path");

            var sourcePath = currentPath + "/" + sourceName;
            var destPath = currentPath + "/" + destName;

            var calls = [];
            calls.push(move_or_rename_irods_file_or_folder_ajax_submit(resID, sourcePath, destPath));

            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
                destination.removeClass("fb-drag-cutting");
            });

        },
        over: function(event, ui) {
            $(ui.helper).addClass("fb-drag-cutting");
            $(event.target).addClass("fb-drag-cutting");
        },
        out: function(event, ui) {
            $(ui.helper).removeClass("fb-drag-cutting");
            $(event.target).removeClass("fb-drag-cutting");
        },
        accept: 'li'
    });

    // Handle "select" of clicked elements
    $("#fb-files-container li").mousedown(function (e) {
        if (!e.ctrlKey) {
            $(this).addClass("ui-selected");
        }

    });

    // Handle "select" of clicked elements
    $("#fb-files-container li").mouseup(function (e) {
        if (!e.ctrlKey) {
            if (!isDragging) {
                $("#fb-files-container li").removeClass("ui-selected");
            }
            $(this).addClass("ui-selected");
        }
        else {
            $(this).toggleClass("ui-selected");
        }
    });

    $(".draggable").draggable({
            containment: "parent",
            start: function( event, ui ) {
                $(ui.helper).addClass(".ui-selected");
                isDragging = true;
            },
            stop: function( event, ui ) {
                $(ui.helper).removeClass("fb-drag-cutting");
                $('#fb-files-container li').animate({ top:0, left:0 }, 200);    // Custom revert to handle multiple selection
                isDragging = false;
            },
            drag: function (event, ui) {
                $('.ui-selected').css({
                    top : ui.position.top,
                    left: ui.position.left
                });
            },
        }
    );

    // Provides selection by drawing a rectangular area
    $("#fb-files-container")
        .selectable({
            filter: "li", cancel: ".ui-selected",
            selected: function (event, ui) {

            },
            unselected: function (event, ui) {
                $(".selection-menu").hide();
            }
        });

    // Dismiss right click menu when mouse down outside of it
    $("#fb-files-container, #fb-files-container li, #fbContainmentWrapper").mousedown(function () {
        $(".selection-menu").hide();
    });

    $("#hs-file-browser li.fb-folder").dblclick(function() {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var folderName = $(this).children(".fb-file-name").text();
        get_irods_folder_struct_ajax_submit(resID, currentPath + "/" + folderName);
    });

    // Right click menu for file browser
    $("#fbContainmentWrapper").bind("contextmenu", function (event) {
        // Avoid the real one
        event.preventDefault();

        var menu;   // The menu to show
        updateSelectionMenuContext();

        if ($(event.target).closest("li").length) {     // If a file item was clicked
            if (!$(event.target).closest("li").hasClass("ui-selected")) {
                $(".ui-selected").removeClass("ui-selected");
                $(event.target).closest("li").addClass("ui-selected");
            }
            menu = $("#right-click-menu");
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

function setBreadCrumbs(path) {
    var crumbs = $("#fb-bread-crumbs");
    crumbs.empty();

    if (path.lastIndexOf("/") == "-1") {
        $("#fb-move-up").attr("disabled", true)
    }
    else {
        $("#fb-move-up").attr("disabled", false)
    }

    var setFirstActive = false;
    while (path){
        var folder = path.substr(path.lastIndexOf("/") + 1, path.length);
        var currentPath = path;
        path = path.substr(0, path.lastIndexOf("/"));
        if (setFirstActive) {
            crumbs.prepend('<li data-path="' + currentPath + '"><i class="fa fa-folder-o" aria-hidden="true"></i><span> ' + folder + '</span></li>');
        }
        else {
            crumbs.prepend('<li class="active"><i class="fa fa-folder-open-o" aria-hidden="true"></i><span> ' + folder + '</span></li>');
            setFirstActive = true;
        }
    }

    // Bind click events
    $("#fb-bread-crumbs li").click(function() {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var path = $(this).attr("data-path");
        get_irods_folder_struct_ajax_submit(resID, path);
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
        if (order == "asc") {
            sorted = $('#fb-files-container li').sort(function (element1, element2) {
                return $(element2).children('span.fb-file-type').text().localeCompare($(element1).children('span.fb-file-type').text());
            });
        }
        else {
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
    });
    }

$(document).ready(function () {
    var previewNode = $("#flag-uploading").removeClass("hidden").clone();
    $("#flag-uploading").remove();

    // Show file drop visual feedback
    Dropzone.options.fbContainmentWrapper = {
        paramName: "files", // The name that will be used to transfer the file
        previewsContainer: "#previews", // Define the container to display the previews
        init: function () {
            this.on("dragenter", function (file) {
                $(".fb-drag-flag").show();
            });

            this.on("dragleave", function (file) {
                $(".fb-drag-flag").hide();
            });

            this.on("addedfile", function (file) {
                $(".fb-drag-flag").hide();
            });

            this.on("processing", function (file) {
                if (!$("#flag-uploading").length) {
                    $("#fbContainmentWrapper").prepend(previewNode);
                }
            });
            this.on("queuecomplete", function () {
                 refreshFileBrowser();
                $("#previews").empty();
            })
        }
    };

    // Toggle between grid and list view
    $("#toggle-list-view").change(function () {
        if ($("#fb-files-container").hasClass("fb-view-list")) {
            // ------- Switch to grid view -------
            $("#fb-files-container").removeClass("fb-view-list");
            $("#fb-files-container").addClass("fb-view-grid");
        }
        else {
            // ------- switch to table view -------
            $("#fb-files-container").removeClass("fb-view-grid");
            $("#fb-files-container").addClass("fb-view-list");
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
        $('#txtFolderName').focus();
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
        }
        return false;
    });

    // Move up one directory
    $("#fb-move-up").click(function () {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var upPath = $("#hs-file-browser").attr("data-current-path");
        upPath = upPath.substr(0, upPath.lastIndexOf("/"));
        get_irods_folder_struct_ajax_submit(resID, upPath);
    });

    $("#btn-open").click(function () {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        get_irods_folder_struct_ajax_submit(resID, currentPath + "/" + folderName);
    });

    $("#btn-cut").click(function () {
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
        }

        $(".selection-menu").hide();
    });

    $(".selection-menu li[data-menu-name='paste']").click(function () {
        var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        var resID = $("#hs-file-browser").attr("data-res-id");
        var targetPath = $("#hs-file-browser").attr("data-current-path");

        if (folderName) {
            targetPath = targetPath + "/" + folderName
        }

        var calls = [];
        for (var i = 0; i < sourcePaths.length; i++) {
            calls.push(move_or_rename_irods_file_or_folder_ajax_submit(resID, sourcePaths[i], targetPath));
        }

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });

        sourcePaths = [];

        $("#fb-files-container li").removeClass("fb-cutting");
        $(".selection-menu").hide();
    });

    // File(s) delete method
    $("#btn-confirm-delete").click(function () {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var deleteList = $("#fb-files-container li.ui-selected");
        if (deleteList.length) {
            var calls = [];
            for (var i = 0; i < deleteList.length; i++) {
                var pk = $(deleteList[i]).attr("data-pk");
                if (pk) {
                    calls.push(delete_file_ajax_submit(resID, pk));
                }
            }

            // Wait for the asynchronous calls to finish to get new folder structure
            $.when.apply($, calls).done(function () {
                refreshFileBrowser();
                $('#confirm-delete-dialog').modal('toggle');
            });
        }
    });

    $(".selection-menu li[data-menu-name='rename']").click(function(){
        $('.selection-menu').hide();
        var name = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        $("#txtName").val(name);
    });

    // Rename method
    $("#btn-rename").click(function () {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var oldName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        var newName = $("#txtName").val();

        var calls = [];
        calls.push(move_or_rename_irods_file_or_folder_ajax_submit(resID, currentPath + "/" + oldName, currentPath + "/" + newName));

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });
    });

     // Download method
    $("#btn-download").click(function () {
        var downloadList = $("#fb-files-container li.ui-selected");
        if (downloadList.length) {
            for (var i = 0; i < downloadList.length; i++) {
                downloadFiles($(downloadList[i]).attr("data-url"))
                // $("#download-frame").attr("src", downloadList.attr(data-url));
            }
        }
    });

    // Zip method
    $("#btn-zip").click(function() {
        var resID = $("#hs-file-browser").attr("data-res-id");
        var currentPath = $("#hs-file-browser").attr("data-current-path");
        var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();

        var calls = [];
        calls.push(zip_irods_folder_ajax_submit(resID, currentPath + "/" + folderName));

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });
    });

    // Unzip method
    $("#btn-unzip").click(function () {
        var resID = $("#hs-file-browser").attr("data-res-id");
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
    });

    function downloadFiles(url) {
        document.getElementById('download-frame').src = url;
    };

    $(".selection-menu li[data-menu-name='refresh']").click(function () {
        refreshFileBrowser();
        $(".selection-menu").hide();
    });

    $(".selection-menu li[data-menu-name='select-all']").click(function () {
        $("#fb-files-container > li").removeClass("ui-selected");
        $("#fb-files-container > li:not(.hidden)").addClass("ui-selected");
        $(".selection-menu").hide();
    });
});