/**
 * Created by Mauriel on 3/9/2017.
 */

$(document).ready(function () {
    // Don't allow the user to change the coverage type
    $("#div_id_type").css('pointer-events', 'none');
    $("#id_type_1").attr('onclick', 'return false');
    $("#id_type_2").attr('onclick', 'return false');
    // make the spatial coverage readonly
    $("#coverage-spatial :input").prop('readonly', true);
    // make the temporal coverage readonly
    $("#coverage-temporal :input").prop('disabled', true);
    // hide the submit button for resource level temporal coverage
    $("#id-coverage-temporal").find("button.btn-primary").hide();
});
