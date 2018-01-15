/**
 * Created by Mauriel on 3/9/2017.
 */

$(document).ready(function () {
    // Don't allow the user to change the coverage type
    // var $id_type_div = $("#div_id_type");
    // var $box_radio = $id_type_div.find("#id_type_1");
    // var $point_radio = $id_type_div.find("#id_type_2");
    // if ($box_radio.attr("checked") !== "checked") {
    //     $box_radio.parent().closest("label").addClass("text-muted");
    //     $box_radio.attr('disabled', true);
    // }
    // else {
    //     $point_radio.parent().closest("label").addClass("text-muted");
    //     $point_radio.attr('disabled', true);
    // }
    //
    // $id_type_div.css('pointer-events', 'none');
    // $point_radio.attr('onclick', 'return false');
    // $box_radio.attr('onclick', 'return false');
    //
    // // make the spatial coverage readonly
    // $("#coverage-spatial :input").prop('readonly', true);
    // // make the temporal coverage readonly
    // $("#coverage-temporal :input").prop('disabled', true);
    // // hide the submit button for resource level temporal coverage
    // $("#id-coverage-temporal").find("button.btn-primary").hide();

    // Submit for resource spatial coverage update
    $("#btn-update-resource-spatial-coverage").click(function () {
        var resourceID = $("#short-id").val();
        resource_coverage_update_ajax_submit(resourceID, 'spatial');
    });

    // Submit for resource temporal coverage update
    $("#btn-update-resource-temporal-coverage").click(function () {
        var resourceID = $("#short-id").val();
        resource_coverage_update_ajax_submit(resourceID, 'temporal');
    });
});

function resource_coverage_update_ajax_submit(resourceID, coverageType) {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Resource coverage was updated successfully.\
    </div>';

    var waitDialog = showWaitDialog();
    var update_url = "/hsapi/_internal/" + resourceID + "/" + coverageType + "/update-coverage/";
    return $.ajax({
        type: "POST",
        url: update_url,
        dataType: 'html',
        async: true,
        success: function (result) {
            waitDialog.dialog("close");

            var json_response = JSON.parse(result);
            if(coverageType === 'spatial'){
                $("#btn-update-resource-spatial-coverage").hide();
                var spatialCoverage = json_response.spatial_coverage;
                updateResourceSpatialCoverage(spatialCoverage);
            }
            else {
                $("#btn-update-resource-temporal-coverage").hide();
                var temporalCoverage = json_response.temporal_coverage;
                updateResourceTemporalCoverage(temporalCoverage);
            }
            $alert_success = $alert_success.replace("Resource coverage was updated successfully.", json_response.message);
            $("#fb-inner-controls").before($alert_success);
            $(".alert-success").fadeTo(2000, 500).slideUp(1000, function(){
                $(".alert-success").alert('close');
            });
        },
        error: function (xhr, textStatus, errorThrown) {
            waitDialog.dialog("close");
            var jsonResponse = JSON.parse(xhr.responseText);
            display_error_message('Failed to update resource coverage', jsonResponse.message);
            $(".file-browser-container, #fb-files-container").css("cursor", "auto");
        }
    });
}