/**
 * Created by Mauriel on 3/9/2017.
 */
var del_msg_shp_shx_dbf = "<div class='extra-caption message-type-1 alert alert-danger'>" +
    "<strong><i class='fa fa-exclamation-triangle' aria-hidden='true'></i> Warning!</strong>" +
    "<div>The 'shp', 'shx' and 'dbf' are three mandatory files." +
    " Missing of any of them will corrupt data integrity. So this operation is about to permanently " +
    "<strong>DELETE ALL EXISTING FILES</strong> of this resource! You may upload new shapefiles later.</div></div>";

var del_msg_prj = "<div class='extra-caption message-type-2 alert alert-danger'>" +
    "<strong><i class='fa fa-exclamation-triangle' aria-hidden='true'></i> Warning!</strong>" +
    "<div>This operation is about to <strong>REMOVE COORDINATE SYSTEM METADATA!</strong></div></div>";

$(document).ready(function () {
    $('#confirm-delete-dialog').on('shown.bs.modal', function () {
        $(this).find(".extra-caption").remove();
        var list = $(this).find(".warnings-list");
        var selected = $("#fb-files-container li.ui-selected");

        for (var i = 0; i < selected.length; i++) {
            var fileName = $(selected[i]).children(".fb-file-name").text();
            var fileExt = fileName.substr(fileName.lastIndexOf(".") + 1, fileName.length).toUpperCase();

            if (!list.find(".message-type-1").length && (fileExt == "SHP" || fileExt == "SHX" || fileExt == "DBF")) {
                list.append(del_msg_shp_shx_dbf);
            }
            else if (!list.find(".message-type-2").length && fileExt == "PRJ") {
                list.append(del_msg_prj);
            }
        }
    });
});