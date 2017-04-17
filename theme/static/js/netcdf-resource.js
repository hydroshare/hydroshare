/**
 * Created by Mauriel on 3/9/2017.
 */

// original coverage metadata check
function check_ori_meta_status() {
    var form_action = $("form[id='id-originalcoverage']").attr('action');
    if (form_action.indexOf('update-metadata') > -1) {
        var new_action = form_action.replace('update-metadata', 'delete-metadata');
        var modal_body_text = '<strong>Are you sure you want to delete this metadata element?</strong>'
        $("#delete-original-coverage-element-dialog").find(".modal-body").html(modal_body_text);
        $("#delete-original-coverage-element-dialog").find(".modal-footer").children("a").attr('href', new_action);
        $("#delete-original-coverage-element-dialog").find(".modal-footer").children("a").show()
    }
    else {
        var modal_body_text = '<strong>There is no original coverage metadata for this resource to delete.</strong>'
        $("#delete-original-coverage-element-dialog").find(".modal-body").html(modal_body_text);
        $("#delete-original-coverage-element-dialog").find(".modal-footer").children("a").hide()
    }
};

$(document).ready(function () {
    $("#btn-delete-spatial-coverage").click(check_ori_meta_status);
});
