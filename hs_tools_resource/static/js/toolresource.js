$(document).ready(function() {
    var checked_res_str=$("#checked_res_div").text();
    var checked_res_array=checked_res_str.split(",");
    for (var i = 0; i < checked_res_array.length; i++) {
        var checked_res_item=checked_res_array[i];
        $("input[value='"+checked_res_item+"']").attr("checked","true");
    }
    // Getter for icon_url input element
    var get_icon_input_element = function() {
        return $('#resourceSpecificTab #div_id_url');
    };
    // If the "Preview" elements don't exist, add them
    if ($('#tool-icon-preview').length == 0) {
        get_icon_input_element().after('<span id="icon-preview-label" class="control-label">Preview</span><br>' +
            '<img id="tool-icon-preview" src="' + get_icon_input_element().val() + '">');
    }
    // Set a key-up event that changes the preview picture each time the icon_url input is changed
    get_icon_input_element().keyup(function() {
        $('#tool-icon-preview').attr('src', $('#resourceSpecificTab #id_url').val());
    });
    // When the page first loads, if there is a url already stored in the database, show the preview of the image
    if ($('#resourceSpecificTab #id_url').val() != "") {
        $('#tool-icon-preview').attr('src', $('#resourceSpecificTab #id_url').val());
    }
});
