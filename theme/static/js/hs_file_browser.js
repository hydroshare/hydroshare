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

$.extend({
    replaceTag: function (currentElem, newTagObj, keepProps) {
        var $currentElem = $(currentElem);
        var i, $newTag = $(newTagObj).clone();
        if (keepProps) {//{{{
            newTag = $newTag[0];
            newTag.className = currentElem.className;
            $.extend(newTag.classList, currentElem.classList);
            $.extend(newTag.attributes, currentElem.attributes);
        }//}}}
        $currentElem.wrapAll($newTag);
        $currentElem.contents().unwrap();
        // return node; (Error spotted by Frank van Luijn)
        return this; // Suggested by ColeLawrence
    }
});

$.fn.extend({
    replaceTag: function (newTagObj, keepProps) {
        // "return" suggested by ColeLawrence
        return this.each(function() {
            jQuery.replaceTag(this, newTagObj, keepProps);
        });
    }
});

function initializeViewComponents() {
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
            selectSelectableElement($("#fb-grid"), $(this).parent());    // Mark item as selected
        }
    });

    // Drop
    $(".droppable").droppable({
        drop: function (event, ui) {

        },
        accept: 'li'
    });

    $("#fb-grid")
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

    $("#fb-table tbody")
        .droppable({
            greedy: true
        })
        .sortable({
            handle: ".fb-handle",
            containment: "parent"
        })
        .selectable({
            filter: "tr", cancel: ".fb-dropdown-toggle, .fb-handle",
            selected: function (event, ui) {

            },
            unselected: function (event, ui) {
                $("#selection-menu").hide();
            }
        });


    $(".fb-handle").click(function () {
        selectSelectableElement($("#fb-grid"), $(this).parent());    // Mark item as selected
        $("#selection-menu").hide();
    });
}

$(document).ready(function () {

    var fbTable;

    initializeViewComponents();


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

    $("#toggle-list-view").click(function () {
        if ($("#fb-table tbody tr").length) {
            // ------- Switch to grid view -------

            $("#fb-table tbody tr > td").replaceTag("<span>", false);
            $("#fb-table tbody tr").replaceTag("<li>", true);

            $("#fb-grid").append($("#fb-table tbody").html());

            // Move dropdown toggles to the beginning of the list
            var items = $(".fb-dropdown-toggle").parent().parent();
            $(".fb-dropdown-toggle").parent().remove();
            items.prepend('<span class="glyphicon glyphicon-chevron-right fb-dropdown-toggle fb-help-icon"></span>');


            $("#fb-grid").show();

            if ($.fn.dataTable.isDataTable('#fb-table')) {
                fbTable.destroy();
            }

            $("#fb-table tbody").empty();
            $("#fb-table").hide();
        }
        else {
            // ------- switch to table view -------

            // Move dropdown toggles to end of list
            var items = $(".fb-dropdown-toggle").parent();
            for (var i = 0; i < items.length; i++) {
                var curr = $(items[i]);
                curr.find(".fb-dropdown-toggle").appendTo(curr)
            }

            $("#fb-grid li > span").replaceTag("<td>", false);
            $("#fb-grid > li").replaceTag("<tr>", true);

            $("#fb-table tbody").append($("#fb-grid").html());
            $("#fb-grid").empty();
            $("#fb-grid").hide();
            $("#fb-table").show();


            // Initialize DataTables for column sorting
            var colDefs = [
                {
                    "targets": [0],
                    "orderable": false,
                    "width": "10px"
                },
                {
                    "targets": [1],
                    "orderable": false,
                    "width": "10px"
                },
                {
                    "targets": [5],
                    "orderable": false,
                },
            ];

            fbTable = $("#fb-table").DataTable({
                "paging": false,
                "info": false,
                "searching": false,
                "order": [[2, "desc"]],
                "columnDefs": colDefs
            });

        }

        initializeViewComponents();

    });

    // Dismiss dropdown when clicking on empty space
    $("#fbContainmentWrapper").click(function() {
        if (event.target.tagName == "FORM") {
            $(".ui-selected").removeClass("ui-selected");
            $("#selection-menu").hide();
        }
    })
});