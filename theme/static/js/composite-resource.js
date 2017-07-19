/**
 * Created by Mauriel on 3/9/2017.
 */

$(document).ready(function () {
    // Don't allow the user to change the coverage type
    var $id_type_div = $("#div_id_type");
    var $box_radio = $id_type_div.find("#id_type_1");
    var $point_radio = $id_type_div.find("#id_type_2");
    if ($box_radio.attr("checked") !== "checked") {
        $box_radio.parent().closest("label").addClass("text-muted");
        $box_radio.attr('disabled', true);
    }
    else {
        $point_radio.parent().closest("label").addClass("text-muted");
        $point_radio.attr('disabled', true);
    }

    $id_type_div.css('pointer-events', 'none');
    $point_radio.attr('onclick', 'return false');
    $box_radio.attr('onclick', 'return false');

    // make the spatial coverage readonly
    $("#coverage-spatial :input").prop('readonly', true);
    // make the temporal coverage readonly
    $("#coverage-temporal :input").prop('disabled', true);
    // hide the submit button for resource level temporal coverage
    $("#id-coverage-temporal").find("button.btn-primary").hide();
});
