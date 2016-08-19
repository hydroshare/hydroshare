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
    $("#fbContainmentWrapper").click(function() {
        if (event.target.tagName == "FORM") {
            $(".ui-selected").removeClass("ui-selected");
            $("#selection-menu").hide();
        }
    })
});