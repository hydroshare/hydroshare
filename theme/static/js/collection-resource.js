/**
* Created by Mauriel on 3/9/2017.
*/

var paging = false;
var page_length = 15;
var page_type = "numbers";

$(document).ready(function() {

    //------------------ table headers ------------
    //                <th>Add</th>             0
    //                <th>Title</th>           1
    //                <th>Type</th>            2
    //                <th>Owners</th>          3
    //                <th>Sharing status</th>  4
    //                <th>My Permission</th>   5
    //                <th>Remove</th>          6

    var edit_mode = $("#edit-mode").val();
    if (edit_mode.toLowerCase() == "false") {
        resourceTable = $("#collection-table").DataTable({
            "order": [[2, "asc"]],
            "paging": paging,
            "bLengthChange": false,
            "pagingType": page_type,
            "pageLength": page_length,
            "info": false,
            "bFilter": false,
            "bInfo": false,
            "columnDefs": [
                {
                    "targets": [0],     // <th>Add</th>
                    "visible": false,
                },
                {
                    "targets": [6],     // <th>Remove</th>
                    "visible": false,
                }
            ],
            "language": {
                "emptyTable": "This collection is empty"
            }
        });
    }
    else {
        resourceTable = $("#collection-table").DataTable({
            "order": [[2, "asc"]],
            "paging": paging,
            "bLengthChange": false,
            "pagingType": page_type,
            "pageLength": page_length,
            "info": false,
            "bFilter": false,
            "bInfo": false,
            "columnDefs": [
                {
                    "targets": [0],     // <th>Add</th>
                    "visible": false,
                },
            ],
            "language": {
                "emptyTable": "This collection is empty"
            }
        });
    }

    resourceTable = $("#collection-table-candidate").DataTable({
        "order": [[2, "asc"]],
        "paging": paging,
        "bLengthChange": false,
        "pagingType": page_type,
        "pageLength": page_length,
        "info": false,
        "columnDefs": [
            {
                "targets": [6],     // <th>Remove</th>
                "visible": false,
            }
        ],
        "language": {
            "emptyTable": "No resource available in this table"
        }
    });

    resourceTable = $("#deleted-resources-table").DataTable({
        "paging": paging,
        "bLengthChange": false,
        "pagingType": page_type,
        "pageLength": page_length,
        "info": false,
        "bFilter": false,
        "bInfo": false,
        "language": {
            "emptyTable": "All deleted resources have been cleared"
        }
    });

    // Mark checkbox when row is clicked
    $("#collection-table-candidate td").click(onCollectionTableRowClick);

    if (edit_mode.toLowerCase() == "true") {
        $("#coverage-header").append($('<div><input id="btn-calc-coverage" value="Calculate Coverages" class="btn btn-info" type="button"/></div>'));
    }

    $("#btn-calc-coverage").click(collection_coverages_calculate_ajax);

    $("#btn-add-collection-resources").click(function () {
        $('#collection-candidate').modal('show');
    });

    $("#save-collection-btn-ok").click(add_collection_item_ajax);

    $(".btn-remove-collection-item").click(function() {
        var resID = $(this).attr("data-res-id");
        remove_collection_item_popup(resID);
    });

    $("#view_deleted_res_btn").click(function() {
        $('#deleted-resources-modal').modal('show');
    });

    $("#clear-deleted-res-btn").click(function() {
        var resID = $(this).attr("data-res-id");
        clear_deleted_resources_table_ajax(resID);
    });
});

function onCollectionTableRowClick(e) {
    if (e.target.tagName != "TD") {
        return;
    }
    if ($(this).parent().find("input[type='checkbox']:checked").length > 0) {
        $(this).parent().find("input[type='checkbox']").prop("checked", false);
    }
    else {
        $(this).parent().find("input[type='checkbox']").prop("checked", true);
    }
}

function remove_collection_item_popup(res_id) {
    // get row obj is being removed from collection
    var removed_row_from_colletion = $('#collection-table').DataTable().row('#' + res_id);

    if(removed_row_from_colletion.data()[5].toLowerCase().indexOf("none") >= 0) {
         // if "My Permission" cell is "None"
        $('#remove-collection-btn-cancel').off("click");
        $('#remove-collection-btn-ok').off("click").on("click", function(){
            remove_collection_item_ajax(res_id, false);
        });

        waning_message = "You have NO PERMISSION over the resource you are about to remove, which means you CAN NOT add it back later.";

        $('#remove-collection-warning-body').text(waning_message);
        $('#remove-collection-warning').modal('show');
    }
    else if(removed_row_from_colletion.data()[4].toLowerCase().indexOf("shareable") < 0 &&
    removed_row_from_colletion.data()[5].toLowerCase().indexOf("owner") < 0) {
        // if "My Permission" cell has no "Shareable" and no "Owner"
        $('#remove-collection-btn-cancel').off("click");
        $('#remove-collection-btn-ok').off("click").on("click", function(){
            remove_collection_item_ajax(res_id, false);
        });

        waning_message = "The resource you are about to remove from the collection is Non-Shareable, which means you CAN NOT add it back later";

        $('#remove-collection-warning-body').text(waning_message);
        $('#remove-collection-warning').modal('show');
    }
    else {
        $('#remove-collection-btn-cancel').off("click");
        $('#remove-collection-btn-ok').off("click").on("click", function(){
            remove_collection_item_ajax(res_id, true);
        });

        waning_message = "Remove this resource from collection?";

        $('#remove-collection-warning-body').text(waning_message);
        $('#remove-collection-warning').modal('show');
    }
}

function remove_collection_item_ajax(res_id, move_to_candidate_list) {
    document.body.style.cursor='wait';
    $("#remove-collection-btn-ok").prop("disabled", true);
    $("#remove-collection-btn-cancel").prop("disabled", true);
    $("#remove-collection-btn-warning").show();
    var resource_id_list = [res_id];

    const successMsg = "Collection updated.";
    const errorMsg = "Collection failed to update.";

    $form = $('#collector-new');
    $.ajax({
        type: "POST",
        url: $form.attr('action'),
        dataType: "json",
        data: {"resource_id_list": resource_id_list, "update_type": "remove"},
        success: function(result) {
            /* The div contains now the updated form */
            json_response = result;
            if (json_response.status === 'success') {
                $(document).trigger("submit-success");
                if (json_response.hasOwnProperty('metadata_status')) {
                    if (json_response.metadata_status !== $('#metadata-status').text()) {
                        $('#metadata-status').text(json_response.metadata_status);
                        if (json_response.metadata_status.toLowerCase().indexOf("insufficient") == -1) {
                            var res_is_discoverable = $("#discoverable").val();
                            // published, public and discoverable all have discoverable = True
                            if (res_is_discoverable.toLowerCase() != "true") {
                                customAlert("Collection Status:", "Sufficient to publish or make public", "success", 3000);
                            }
                        }
                        else {
                            manageAccessApp.onMetadataInsufficient();
                        }
                    }
                }
                updateCoverageMetadataTabpage(json_response.new_coverage_list, true, false);
                customAlert("Success!", successMsg, "success", 3000);

                // get row obj is being removed from collection
                var removed_row_from_colletion = $('#collection-table').DataTable().row('#' + res_id);
                if(move_to_candidate_list)
                {
                    // copy row data and add to collection-candidate table
                    $('#collection-table-candidate').DataTable().row.add(removed_row_from_colletion.data()).draw(false);
                    // Rebind click event for new row
                    $("#collection-table-candidate td").click(onCollectionTableRowClick);
                }
                // remove row obj
                removed_row_from_colletion.remove().draw(false);
                $('#remove-collection-warning').modal('hide');
            }
            else {
                customAlert("Error!", errorMsg, "error", 3000);
                console.log(json_response.msg);
                $('#remove-collection-warning').modal('hide');
            }
            $("#remove-collection-btn-ok").prop("disabled", false);
            $("#remove-collection-btn-cancel").prop("disabled", false);
            $("#remove-collection-btn-warning").hide();
            document.body.style.cursor='default';
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            customAlert("Error!", errorMsg, "error", 3000);
            $('#remove-collection-warning').modal('hide');
            $("#remove-collection-btn-ok").prop("disabled", false);
            $("#remove-collection-btn-cancel").prop("disabled", false);
            $("#remove-collection-btn-warning").hide();
            document.body.style.cursor='default';
        }
    });
    //don't submit the form
    return false;
}

function add_collection_item_ajax() {
    document.body.style.cursor='wait';
    $("#save-collection-btn-ok").prop("disabled", true);
    $("#save-collection-btn-cancel").prop("disabled", true);
    $("#save-collection-btn-warning").show();

    var resource_id_list = [];
    $.each($(".row-selector:checked"), function( index, chkbox ) {
            var res_id = chkbox.id;
            resource_id_list.push(this.id);
    });

    const alert_success = "Collection updated.";
    const alert_error = "Collection failed to update.";

    $form = $('#collector-new');
    $.ajax({
        type: "POST",
        url: $form.attr('action'),
        dataType: "json",
        data: {"resource_id_list": resource_id_list, "update_type": "add"},
        success: function(result) {
            /* The div contains now the updated form */
            json_response = result;
            if (json_response.status === 'success') {
                $(document).trigger("submit-success");
                if (json_response.hasOwnProperty('metadata_status')) {
                    if (json_response.metadata_status !== $('#metadata-status').text()) {
                        $('#metadata-status').text(json_response.metadata_status);
                        if (json_response.metadata_status.toLowerCase().indexOf("insufficient") == -1) {
                            var res_is_discoverable = $("#discoverable").val();
                            // published, public and discoverable all have discoverable = True
                            if (res_is_discoverable.toLowerCase() != "true") {
                                customAlert("Collection Status:", "Sufficient to publish or make public", "success", 3000);
                            }
                        }
                    }
                }
                updateCoverageMetadataTabpage(json_response.new_coverage_list, true, false);
                customAlert("Success!", alert_success, "success", 3000);

                $.each($("#collection-candidate .row-selector:checked"), function (index, chkbox) {
                    var res_id = chkbox.id;
                    var added_row = $('#collection-table-candidate').DataTable().row('#' + res_id);
                    $('#collection-table').DataTable().row.add(added_row.data()).draw(false);
                    added_row.remove().draw(false);
                });
                $('#collection-candidate').modal('hide');

                // Rebind click events
                $(".btn-remove-collection-item").click(function () {
                    var resID = $(this).attr("data-res-id");
                    remove_collection_item_popup(resID);
                });
            }
            else {
                customAlert("Error!", alert_error, "error", 3000);
                console.log(json_response.msg);
                $('#collection-candidate').modal('hide');
            }
            $("#save-collection-btn-ok").prop("disabled", false);
            $("#save-collection-btn-cancel").prop("disabled", false);
            $("#save-collection-btn-warning").hide();
            document.body.style.cursor='default';
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            customAlert("Error!", alert_error, "error", 3000);
             $('#collection-candidate').modal('hide');
             $("#save-collection-btn-ok").prop("disabled", false);
             $("#save-collection-btn-cancel").prop("disabled", false);
             $("#save-collection-btn-warning").hide();
             document.body.style.cursor='default';
        }
    });
    //don't submit the form
    return false;
}

function clear_deleted_resources_table_ajax(collection_id) {
    document.body.style.cursor='wait';
    // hide view deleted
    $("#view_deleted_res_div").hide();
    $("#clear-deleted-res-btn").hide();
    $("#clear-deleted-res-btn-cancel").prop("disabled", true);
    $("#clear-deleted-res-warning").show();

    url = "/hsapi/_internal/" + collection_id +"/update-collection-for-deleted-resources/";
    $.ajax({
    type: "POST",
    url: url,
    dataType: "json",
    data: {},
    success: function(result) {
        /* The div contains now the updated form */
        json_response = result;
        if (json_response.status === 'success') {
            $('#deleted-resources-table').DataTable().rows().remove().draw(false);
            $("#clear-deleted-res-warning").hide();
            var edit_mode = $("#edit-mode").val();
            if (edit_mode.toLowerCase() == "true")
            {
                updateCoverageMetadataTabpage(json_response.new_coverage_list, true, false);
            }
        }
        $("#clear-deleted-res-btn-cancel").prop("disabled", false);
        document.body.style.cursor='default';
    },
    error: function(XMLHttpRequest, textStatus, errorThrown) {
       $('#clear-deleted-res-warning').html("<font color='red'>Failed to clear deleted resource links.</font>");
       $('#clear-deleted-res-warning').show();
       $("#clear-deleted-res-btn-cancel").prop("disabled", false);
       document.body.style.cursor='default';
    }
    });
}

function collection_coverages_calculate_ajax() {
    const alert_success = 'Please click the "Save changes" button to save changes.';
    const alert_error = 'Calculate coverages failed.';

    var res_id = $("#collection-res-id").val();
    var url = "/hsapi/_internal/calculate-collection-coverages/" + res_id + "/";
    $.ajax({
        type: "POST",
        url: url,
        dataType: "json",
        data: {},
        success: function(result) {
            /* The div contains now the updated form */
            json_response = result;
            if (json_response.status === 'success') {
                updateCoverageMetadataTabpage(json_response.new_coverage_list, false, true);
                customAlert("Success!", alert_success, "success", 3000);
            }
            else {
                customAlert("Error!", alert_error, "error", 3000);
            }
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
             customAlert("Error!", alert_error, "error", 3000);
        }
    });
    //don't submit the form
    return false;
}

function updateCoverageMetadataTabpage(new_coverage_list, change_coverage_metadata_form_action, show_save_btn) {
    // new_coverage_list: a list contains new coverage metadata dicts; empty list means no coverage metadata
    // change_coverage_metadata_form_action: The backend always removes all existing coverage metadata element objs and then creates new ones. So the element ids may change.
    // If new coverage metadata has been saved to DB on backend, this parameter should be set to true, informing frontend to update element id in forms.action;
    // show_save_btn: If new coverage metadata has been saved to DB on backend, this parameter should be set to false, informing frontend not to display save btn;

    var found_spatial = false;
    var found_temporal = false;
    for (var i=0; i<new_coverage_list.length; i++)
    {
        var coverage =  new_coverage_list[i];
        if (coverage.type == 'point')
        {
            found_spatial = true;
            cleanSpatialCoverageUI();
            document.getElementById("id_east").value = coverage.value.east;
            document.getElementById("id_north").value = coverage.value.north;
            if (change_coverage_metadata_form_action) {
                changeMetadataFormAction2Update('id-coverage-spatial', coverage.element_id_str);
            }
            document.getElementById("id_type_2").checked = true;
            $("#id_type_2").trigger("change");

        }
        else if (coverage.type == 'box')
        {
            found_spatial = true;
            cleanSpatialCoverageUI();
            document.getElementById('id_northlimit').value = coverage.value.northlimit;
            document.getElementById('id_eastlimit').value = coverage.value.eastlimit;
            document.getElementById('id_southlimit').value = coverage.value.southlimit;
            document.getElementById('id_westlimit').value = coverage.value.westlimit;
            if (change_coverage_metadata_form_action) {
                changeMetadataFormAction2Update('id-coverage-spatial', coverage.element_id_str);
            }
            document.getElementById("id_type_1").checked = true;
            $("#id_type_1").trigger("change");

        }
        else if (coverage.type == 'period')
        {
            found_temporal = true;
            document.getElementById('id_start').value = coverage.value.start;
            document.getElementById('id_end').value = coverage.value.end;
            if (change_coverage_metadata_form_action) {
                changeMetadataFormAction2Update('id-coverage-temporal', coverage.element_id_str);
            }
        }
    } // for

    if (! found_spatial) {
        if (change_coverage_metadata_form_action) {
            changeMetadataFormAction2Add("id-coverage-spatial");
        }
        cleanSpatialCoverageUI();
    }

    if (! found_temporal)
    {
        if (change_coverage_metadata_form_action) {
            changeMetadataFormAction2Add("id-coverage-temporal");
        }
        cleanTemporalCoverageUI();
    }

    if (show_save_btn)
    {
        $("#id-coverage-temporal").find('button').show();
        $("#id-coverage-spatial").find('button').show()
    }
    else {
        $("#id-coverage-temporal").find('button').hide();
        $("#id-coverage-spatial").find('button').hide()
    }
}

var empty_value = '';

function cleanSpatialCoverageUI() {
    document.getElementById('id_northlimit').value = empty_value;
    document.getElementById('id_eastlimit').value = empty_value;
    document.getElementById('id_southlimit').value = empty_value;
    document.getElementById('id_westlimit').value = empty_value;
    document.getElementById('id_east').value = empty_value;
    document.getElementById('id_north').value = empty_value;
}

function cleanTemporalCoverageUI() {
    document.getElementById('id_start').value = empty_value;
    document.getElementById('id_end').value = empty_value;
}

function changeMetadataFormAction2Update(form_id, new_element_id_str) {
    if (new_element_id_str.length > 0 && new_element_id_str != "-1")
    {
        var url_old = $('#'+form_id).attr('action');
        var new_part = '/coverage/' + new_element_id_str + "/update-metadata/";
        var url_new = url_old.replace(/\/coverage\/.+\/update-metadata\//, new_part);
        url_new = url_new.replace(/\/coverage\/add-metadata\//, new_part);
        $('#'+form_id).attr('action', url_new);
    }
}

function changeMetadataFormAction2Add(form_id) {
    var url_old = $('#'+form_id).attr('action');
    var new_part = '/coverage/add-metadata/';
    var url_new = url_old.replace(/\/coverage\/.+\/update-metadata\//, new_part);
    $('#'+form_id).attr('action', url_new);
}