/**
 * Created by Mauriel on 8/16/2016.
 */

function selectSelectableElement (selectableContainer, elementsToSelect) {
    // add unselecting class to all elements in the styleboard canvas except the ones to select
    $(".ui-selected", selectableContainer).not(elementsToSelect).removeClass("ui-selected").addClass("ui-unselecting");

    // add ui-selecting class to the elements to select
    $(elementsToSelect).not(".ui-selected").addClass("ui-selected");

    // trigger the mouse stop event (this will select all .ui-selecting elements, and deselect all .ui-unselecting elements)
    selectableContainer.data("selectable")._mouseStop(null);
}

function bindFileBrowserItemEvents() {
    $(".fb-dropdown-toggle").click(function () {
        var menu = $("#selection-menu");
        var offsetTop = 170;
        var offsetLeft = 10;
        var top = $(this).position().top - offsetTop;
        var left = $(this).position().left - offsetLeft;

        menu.css({top: top, left: left});

        if (menu.css("display") == "none")
            menu.show();
        else {
            menu.hide();
        }

        if (!$(this).parent().hasClass("ui-selected")) {
            selectSelectableElement($("#fb-files-container"), $(this).parent());    // Mark item as selected
        }
    });

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
            containment: "parent"
        })
        .selectable({
            filter: "li", cancel: ".fb-dropdown-toggle, .fb-handle",
            cancel: '.ui-selected',
            selected: function (event, ui) {

            },
            unselected: function (event, ui) {
                $("#selection-menu").hide();
            }
        });

    $(".fb-handle").click(function () {
        selectSelectableElement($("#fb-files-container"), $(this).parent());    // Mark item as selected
        $("#selection-menu").hide();
    });

    // Dismiss dropdown when clicking on empty space
    $("#fbContainmentWrapper").click(function () {
        if (event.target.tagName == "FORM") {
            $(".ui-selected").removeClass("ui-selected");
            $("#selection-menu").hide();
        }
    });

    $("#hs-file-browser li.fb-folder").dblclick(function() {
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
        var folderName = $(this).children(".fb-file-name").text();
        get_irods_folder_struct_ajax_submit(resID, currentPath + "/" + folderName);
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
    // Show file drop visual feedback
    Dropzone.options.fbContainmentWrapper = {
        paramName: "files", // The name that will be used to transfer the file
        clickable: ".fb-upload-caption",
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
        }
    };
    
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

    bindFileBrowserItemEvents();

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
    $("#fb-create-folder").click(function() {
        var resID = $("#fb-files-container").attr("data-res-id");
        var currentPath = $("#fb-files-container").attr("data-current-path");
        var folderName = "Test Folder";
        create_irods_folder_ajax_submit(resID, currentPath + "/" + folderName);
        get_irods_folder_struct_ajax_submit(resID, currentPath);
        // setBreadCrumbs(currentPath);
    });

     // Move up one directory
    $("#fb-move-up").click(function() {
        var resID = $("#fb-files-container").attr("data-res-id");
        var upPath = $("#fb-files-container").attr("data-current-path");
        upPath = upPath.substr(0,upPath.lastIndexOf("/"));
        get_irods_folder_struct_ajax_submit(resID, upPath);
    });
});