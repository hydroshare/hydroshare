$(document).ready(function() {
    var checked_res_str=$("#checked_res_div").text();
    var checked_res_array=checked_res_str.split(",");
    for (var i = 0; i < checked_res_array.length; i++) {
        var checked_res_item=checked_res_array[i];
        $("input[value='"+checked_res_item+"']").attr("checked","true");
    }
    var get_icon_input_element = function() {
        return $('#id_icon');
    };
    if ($('#tool-icon-preview-').length == 0) {
        get_icon_input_element().after('<span id="icon-preview-label" class="control-label">Preview</span><br>' +
            '<img id="icon-preview-img" src="' + get_icon_input_element().val() + '">');
    }
    get_icon_input_element().keyup(function() {
        $('#tool-icon-preview').attr('src', $('#id_icon').val());
    })
});
