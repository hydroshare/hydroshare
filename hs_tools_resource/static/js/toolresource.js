$(document).ready(function() {

    /*
    This part enables icon preview in WebApp Res's EDIT mode
    */
    // Getter for icon_url input element
    var get_icon_input_element = function() {
        return $("#tool_icon").find("#id_value");
    };

    // use button to toggle hidden file input
    $('#icon-select-btn').click(function(){
        $('#icon-select').trigger("click");
    });

    $('#icon-delete-btn').click(function(){
        get_icon_input_element().val("");
        $('#tool-icon-preview').attr('src', "");
        $("#tool_icon").find("#id_data_url").val("")
        $(this).parents("form").find(".btn-form-submit").show();
    });

    // Listen for file input element and update preview when editing
    $('#icon-select').change(function(ev) {
        const [file] = ev.target.files;
        let reader = new FileReader();
        if (file) {
            reader.onload = () => {
                imgBase64 = reader.result;
                $('#tool-icon-preview').attr('src', imgBase64);
                $("#tool_icon").find("#id_data_url").val(imgBase64)
                get_icon_input_element().val("");
              }
            reader.readAsDataURL(file);
            $(this).parents("form").find(".btn-form-submit").show();
        }
    });

    //// If the "Preview" elements don't exist, add them
    //if ($('#tool-icon-preview').length == 0) {
    //    get_icon_input_element().after('<span id="icon-preview-label" class="control-label">Preview</span><br>' +
    //        '<img id="tool-icon-preview" src="' + get_icon_input_element().val() + '">');
    //}

    // Set a key-up event that changes the preview picture each time the icon_url input is changed
    get_icon_input_element().keyup(function() {
        $('#tool-icon-preview').attr('src', get_icon_input_element().val());
        $("#tool_icon").find("#id_data_url").val("")
    });

    //// When the page first loads, if there is a url already stored in the database, show the preview of the image
    //if (get_icon_input_element().val() != "") {
    //    $('#tool-icon-preview').attr('src', get_icon_input_element().val());
    //}

    /*
    * The following code is only meant to affect resources landing pages other than
    * Web Apps themselves, as it formats the "Open with..." dropdown button on the
    * landing page of resources that have a web app associated with them.
    */
    var setDefaultIcon = function($this) {
        var style = $this.hasClass('user-webapp-icon') ? "" : "dropdown-";
        $this
            .attr('src', '/static/img/web-app-default-icon.png')
            .removeClass(style + 'user-webapp-icon')
            .addClass(style + 'default-webapp-icon');
    };
    $('.user-webapp-icon, .dropdown-user-webapp-icon').each(function() {
        if ($(this).attr('src') == '') {
            setDefaultIcon($(this));
        }
    }).on('error', function() {
        setDefaultIcon($(this));
    });
    $('#resource-title').attr('style', 'width: calc(100% - 110px);');
});
