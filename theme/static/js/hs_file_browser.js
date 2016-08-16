/**
 * Created by Mauriel on 8/16/2016.
 */

$(document).ready(function () {
    // Drop
    $(".droppable").droppable({
        drop: function (event, ui) {

        },
        accept: 'li'
    });

    $("#fb-list")
        .droppable({
            greedy: true
        })
        .sortable({
            handle: ".handle"
        })
        .selectable({
            filter: "li", cancel: ".handle",
            selected:function(event, ui){
                var top = $("#fb-list .ui-selected").position().top - 70;
                var left = $("#fb-list .ui-selected").position().left - 80;
                $("#selection-menu").css({top: top, left: left});
                $("#selection-menu").show();
            },
            unselected: function( event, ui ) {
                $("#selection-menu").hide();
            }
        })
        .find("li.fb-folder, li.fb-file").prepend("<div class='handle'><span class='fa fa-arrows'></span></div>");

});