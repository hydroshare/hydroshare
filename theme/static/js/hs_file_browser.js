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

    if (selected.length > 1) {
        flagDisableRename = true;   // 'rename' menu item
        flagDisableOpen = true;
        flagDisablePaste = true;
    }

    if (selected.hasClass("fb-file")) {
        flagDisableOpen = true;
        flagDisablePaste = true;
    }

    if (selected.hasClass("fb-file")) {
        flagDisableOpen = true;
        flagDisablePaste = true;
    }

    if (selected.hasClass("fb-folder")) {
        flagDisableDownload = true;
    }

    if (!sourcePaths.length) {
        flagDisablePaste = true;
    }

    $("#right-click-menu").children("li[data-menu-name='open']").toggleClass("disabled", flagDisableOpen);
    $("#right-click-menu").children("li[data-menu-name='download']").toggleClass("disabled", flagDisableDownload);
    $("#right-click-menu").children("li[data-menu-name='rename']").toggleClass("disabled", flagDisableRename);
    $(".selection-menu").children("li[data-menu-name='paste']").toggleClass("disabled", flagDisablePaste);
}

function bindFileBrowserItemEvents() {
    // Drop
    $(".droppable").droppable({
        drop: function (event, ui) {

        },
        accept: 'li'
    });

    $("#fb-files-container")
        .droppable({
            greedy: true
        })
        .sortable({
            handle: ".fb-handle",
            containment: "parent",
            // helper: function (e, item) { //create custom helper
            //     // clone selected items before hiding
            //     var elements = $('.ui-selected').not(".ui-sortable-helper").clone();
            //     //hide selected items
            //     item.siblings('.ui-selected').addClass('hidden');
            //     return item.append(elements);
            // },
            // start: function (e, ui) {
            //     var elements = ui.item.siblings('.ui-selected.hidden').not('.ui-sortable-placeholder');
            //     //store the selected items to item being dragged
            //     ui.item.data('items', elements);
            // },
            // receive: function (e, ui) {
            //     //manually add the selected items before the one actually being dragged
            //     ui.item.before(ui.item.data('items'));
            // },
            // stop: function (e, ui) {
            //     //show the selected items after the operation
            //     ui.item.siblings('.selected').removeClass('hidden');
            //     //unselect since the operation is complete
            //     $('.selected').removeClass('selected');
            // },
        })
        .selectable({
            filter: "li", cancel: ".fb-handle, .ui-selected",
            selected: function (event, ui) {

            },
            unselected: function (event, ui) {
                $(".selection-menu").hide();
            }
        });

    $(".fb-handle").click(function () {
        selectSelectableElement($("#fb-files-container"), $(this).parent());    // Mark item as selected
        $(".selection-menu").hide();
    });

    // Dismiss right click menu when mouse down outside of it
    $("#fb-files-container, #fb-files-container li, #fbContainmentWrapper").mousedown(function () {
        $(".selection-menu").hide();
    });

    $("#hs-file-browser li.fb-folder").dblclick(function() {
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
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
        var resID = $("#fb-files-container").attr("data-res-id");
        var path = $(this).attr("data-path");
        get_irods_folder_struct_ajax_submit(resID, path);
    });
}

$(document).ready(function () {
    var previewNode = $("#flag-uploading").clone();
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

    // File sorting algorithms
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

        var method = $("#fb-sort li[data-method].active").attr("data-method");
        var order = $("#fb-sort li[data-order].active").attr("data-order");

        sort(method, order);
    });

    // Filter files on search input text change
    function filter(){
        var items = $('#fb-files-container li').children('span.fb-file-name');
        var search = $("#txtDirSearch").val().toLowerCase();
        for (var i = 0; i < items.length; i++) {
            if ($(items[i]).text().toLowerCase().indexOf(search) >= 0) {
                $(items[i]).parent().show();
            }
            else {
                $(items[i]).parent().hide();
            }
        }
    }
    $("#txtDirSearch").on("input", filter);

    // Clear search input
    $("#btn-clear-search-input").click(function(){
        $("#txtDirSearch").val("");
        filter();
    });

    // Create folder at current directory
    $("#btn-create-folder").click(function () {
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
        var folderName = $("#txtFolderName").val();
        if (folderName) {
            create_irods_folder_ajax_submit(resID, currentPath + "/" + folderName);
            refreshFileBrowser();
            setBreadCrumbs(currentPath);
        }

        return false;
    });

    // Reload the current folder structure
    function refreshFileBrowser () {
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
        get_irods_folder_struct_ajax_submit(resID, currentPath);
        $(".selection-menu").hide();
    }

    // Move up one directory
    $("#fb-move-up").click(function () {
        var resID = $("#fb-files-container").attr("data-res-id");
        var upPath = $("#fb-files-container").attr("data-current-path");
        upPath = upPath.substr(0, upPath.lastIndexOf("/"));
        get_irods_folder_struct_ajax_submit(resID, upPath);
    });

    $("#btn-open").click(function () {
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
        var folderName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        get_irods_folder_struct_ajax_submit(resID, currentPath + "/" + folderName);
    });

    $("#btn-cut").click(function () {
        var currentPath = $("#fb-files-container").attr("data-current-path");
        $("#fb-files-container li").removeClass("fb-cutting");
        sourcePaths = [];

        var selection = $("#fb-files-container li.ui-selected");

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
        var resID = $("#fb-files-container").attr("data-res-id");
        var targetPath = $("#fb-files-container").attr("data-current-path");

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
        var resID = $("#fb-files-container").attr("data-res-id");
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
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
        var oldName = $("#fb-files-container li.ui-selected").children(".fb-file-name").text();
        var newName = $("#txtName").val();

        var calls = [];
        calls.push(move_or_rename_irods_file_or_folder_ajax_submit(resID, currentPath + "/" + oldName, currentPath + "/" + newName));

        // Wait for the asynchronous calls to finish to get new folder structure
        $.when.apply($, calls).done(function () {
            refreshFileBrowser();
        });
    });
});