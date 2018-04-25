/**
 * Created by Mauriel on 3/9/2017.
 */

$(document).ready(function () {

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