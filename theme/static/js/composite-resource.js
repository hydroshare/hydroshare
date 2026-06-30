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
        bindResourceSpatialDeleteOption(SHORT_ID);
        bindResourceTemporalDeleteOption(SHORT_ID);
        // show/hide spatial coverage delete option
        setResourceSpatialCoverageDeleteOption();
        // show/hide temporal coverage delete option
        setResourceTemporalCoverageDeleteOption();
    }
});
