/**
 * Created by Mauriel on 3/9/2017.
 */

$(document).ready(function () {
    const mode = $("#hs-file-browser").attr("data-mode");

    // Submit for resource spatial coverage update
    $("#btn-update-resource-spatial-coverage").click(function () {
        resource_coverage_update_ajax_submit(SHORT_ID, 'spatial');
    });

    // Submit for resource temporal coverage update
    $("#btn-update-resource-temporal-coverage").click(function () {
        resource_coverage_update_ajax_submit(SHORT_ID, 'temporal');
    });

    if (mode == "edit") {
        bindResourceSpatialDeleteOption();
        bindResourceTemporalDeleteOption();
        // show/hide spatial coverage delete option
        setResourceSpatialCoverageDeleteOption();
        // show/hide temporal coverage delete option
        setResourceTemporalCoverageDeleteOption();
    }
});

function bindResourceSpatialDeleteOption() {
    var $deleteSpatialCoverageResource = $("#id-delete-spatial-resource");
    $deleteSpatialCoverageResource.unbind('click');
    $deleteSpatialCoverageResource.click(function () {
        resource_coverage_delete_ajax_submit(SHORT_ID, 'spatial');
    })
}

function bindResourceTemporalDeleteOption() {
    var $deleteTemporalCoverageResource = $("#id-delete-temporal-resource");
    $deleteTemporalCoverageResource.unbind('click');
    $deleteTemporalCoverageResource.click(function () {
        resource_coverage_delete_ajax_submit(SHORT_ID, 'temporal');
    })
}
function setResourceSpatialCoverageDeleteOption() {
    // show/hide spatial coverage delete option at the resource level
    var $deleteSpatialCoverageResource = $("#id-delete-spatial-resource");
    var $id_type_div = $("#div_id_type");
    var $box_radio = $id_type_div.find("#id_type_1");
    if($box_radio.prop("checked")) {
        if ($("#id_northlimit").val().length > 0) {
            $deleteSpatialCoverageResource.show();
        }
        else {
            $deleteSpatialCoverageResource.hide();
        }
    }
    else {
        // coverage is a point
        if ($("#id_north").val().length > 0) {
            $deleteSpatialCoverageResource.show();
        }
        else {
            $deleteSpatialCoverageResource.hide();
        }
    }
}

function setResourceTemporalCoverageDeleteOption() {
    // show/hide temporal coverage delete option at the resource level
    var $deleteTemporalCoverageResource = $("#id-delete-temporal-resource");
    if ($("#id_start").val().length > 0) {
        $deleteTemporalCoverageResource.show();
    }
    else {
        $deleteTemporalCoverageResource.hide();
    }
}

function resource_coverage_delete_ajax_submit(resourceID, coverageType) {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Coverage was deleted.\
    </div>';

    var update_url = "/hsapi/_internal/" + resourceID + "/" + coverageType + "/delete-coverage/";
    return $.ajax({
        type: "POST",
        url: update_url,
        dataType: 'html',
        async: true,
        success: function (result) {
            var json_response = JSON.parse(result);
            if(coverageType === 'spatial'){
                var $deleteSpatialCoverageResource = $("#id-delete-spatial-resource");
                $deleteSpatialCoverageResource.hide();
                var spatialCoverage = json_response.spatial_coverage;
                updateResourceSpatialCoverage(spatialCoverage);
            }
            else {
                var $deleteTemporalCoverageResource = $("#id-delete-temporal-resource");
                $deleteTemporalCoverageResource.hide();
                var temporalCoverage = json_response.temporal_coverage;
                updateResourceTemporalCoverage(temporalCoverage);
            }
            $("#fb-inner-controls").after($alert_success);
            $(".alert-success").fadeTo(3000, 500).slideUp(1000, function(){
                $(".alert-success").alert('close');
            });
        },
        error: function (xhr, textStatus, errorThrown) {
            var jsonResponse = JSON.parse(xhr.responseText);
            display_error_message('Failed to update resource coverage', jsonResponse.message);
            $(".file-browser-container, #fb-files-container").css("cursor", "auto");
        }
    });
}

function resource_coverage_update_ajax_submit(resourceID, coverageType) {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Coverage has been set to the spatial/temporal window that includes all of the data in the resource.\
    </div>';

    var update_url = "/hsapi/_internal/" + resourceID + "/" + coverageType + "/update-coverage/";
    return $.ajax({
        type: "POST",
        url: update_url,
        dataType: 'html',
        async: true,
        success: function (result) {
            var json_response = JSON.parse(result);
            if(coverageType === 'spatial'){
                var spatialCoverage = json_response.spatial_coverage;
                updateResourceSpatialCoverage(spatialCoverage);
                // show/hide spatial coverage delete option
                setResourceSpatialCoverageDeleteOption();
            }
            else {
                var temporalCoverage = json_response.temporal_coverage;
                updateResourceTemporalCoverage(temporalCoverage);
                // show/hide temporal coverage delete option
                setResourceTemporalCoverageDeleteOption();
            }
            $("#fb-inner-controls").after($alert_success);
            $(".alert-success").fadeTo(3000, 500).slideUp(1000, function(){
                $(".alert-success").alert('close');
            });
        },
        error: function (xhr, textStatus, errorThrown) {
            var jsonResponse = JSON.parse(xhr.responseText);
            display_error_message('Failed to update resource coverage', jsonResponse.message);
            $(".file-browser-container, #fb-files-container").css("cursor", "auto");
        }
    });
}

function fileset_coverage_update_ajax_submit(logicalFileID, coverageType) {
    var $alert_success = '<div class="alert alert-success" id="error-alert"> \
        <button type="button" class="close" data-dismiss="alert">x</button> \
        <strong>Success! </strong> \
        Coverage has been set to the spatial/temporal window that includes all of the data in the aggregation.\
    </div>';

    var update_url = "/hsapi/_internal/" + logicalFileID + "/" + coverageType + "/update-coverage-fileset/";
    return $.ajax({
        type: "POST",
        url: update_url,
        dataType: 'html',
        async: true,
        success: function (result) {
            var json_response = JSON.parse(result);
            var logicalFileType = json_response.logical_file_type;
            var coverageElementID = json_response.element_id;
                var logicalFileID = json_response.logical_file_id;
            if(coverageType === 'spatial'){
                var spatialCoverage = json_response.spatial_coverage;
                updateAggregationSpatialCoverageUI(spatialCoverage, logicalFileID, coverageElementID);
                var bindCoordinatesPicker = false;
                setFileTypeSpatialCoverageFormFields(logicalFileType, bindCoordinatesPicker);
            }
            else {
                var temporalCoverage = json_response.temporal_coverage;
                updateAggregationTemporalCoverage(temporalCoverage, logicalFileID, coverageElementID);
                setFileTypeTemporalCoverageDeleteOption(logicalFileType);
            }
            $("#fb-inner-controls").after($alert_success);
            $(".alert-success").fadeTo(3000, 500).slideUp(1000, function(){
                $(".alert-success").alert('close');
            });
        },
        error: function (xhr, textStatus, errorThrown) {
            var jsonResponse = JSON.parse(xhr.responseText);
            display_error_message('Failed to update aggregation coverage', jsonResponse.message);
            $(".file-browser-container, #fb-files-container").css("cursor", "auto");
        }
    });
}