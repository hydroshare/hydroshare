/**
 * Created by Mauriel on 3/9/2017.
 */

function request_join_group_ajax_submit() {
    var target = $(this);
    var dataFormID = $(this).attr("data-form-id");
    var form = $("#" + dataFormID);
    var datastring = form.serialize();
    var url = form.attr('action');
    if($(this).attr("requires_explanation") === 'True'){
        // show a modal requesting explanation
        $('#explanation-dialog').modal('show');
        $('#explanation').unbind('.group_ns');

        // on modal submission
        $('#explanation_btn').click(()=>{
            let explanation = $("#explanation").val().trim();
        
            let sanitized_explanation = $("<div/>").html(explanation.trim()).text();
            if (sanitized_explanation !== explanation) {
                showError("The explanation text contains html code and cannot be saved.");
                return;
            }else if (sanitized_explanation == 0) {
                showError("Justificaiton is a required field that cannot be left blank.");
                return;
            }else if(sanitized_explanation.length > 300){
                showError("The justificaiton is too long. Please shorten to 300 characters.")
                return;
            }else{
                submitGroupRequest(datastring + "&" + $('#explanation').serialize());
                $('#explanation-dialog').modal('hide');
            }
        });
        function showError(errorText){
            $("#explanation").addClass("form-invalid");
            $("#explanation_msg").html(
                "<div class='alert alert-danger'>" + errorText + "</div>");
            $("#explanation_msg").show();
            $('#explanation').bind('input propertychange.group_ns', function() {
                $("#explanation").removeClass("form-invalid");
                $("#explanation_msg").hide();
            });
        }
    }else{
        submitGroupRequest(datastring);
    }

    function submitGroupRequest(data){
        $.ajax({
            type: "POST",
            url: url,
            dataType: 'html',
            data: data,
            success: function (result) {
                var container = target.parent().parent();
                target.parent().remove();
                container.append('<h4 class="flag-joined"><span class="glyphicon glyphicon-send"></span> Request Sent</h4>');
            },
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                console.log("error");
            }
        });
    }
    return false;
}

function act_on_request_ajax_submit() {
    var target = $(this);
    var form = $(this).closest("form");
    var datastring = form.serialize();
    var url = form.attr('action');
    $.ajax({
        type: "POST",
        url: url,
        dataType: 'html',
        data: datastring,
        success: function (result) {
            var container = target.parent().parent().parent().parent();
            target.parent().parent().parent().remove();
            if (target.attr("data-user-action") == "Accept") {
                container.append('<div class="text-center"><h4 class="flag-joined"><span class="glyphicon glyphicon-ok"></span> You have joined this group</h4></div>');
            } else {
                container.append('<div class="text-center"><h4 class="flag-declined"><span class="glyphicon glyphicon-remove"></span> You have declined to join this group.</h4></div>');
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("error");
        }
    });
    //don't submit the form
    return false;
}

// File name preview for picture field, change method
$(document).on('change', '.btn-file :file', function () {
    var input = $(this);
    var numFiles = input.get(0).files ? input.get(0).files.length : 1;
    var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});

$(document).ready(function () {
    $("#id-Group-Search-Result-Msg").hide();
    $(".btn-ask-to-join").click(request_join_group_ajax_submit);
    $(".btn-act-on-request").click(act_on_request_ajax_submit);

    $("#txt-search-groups").keyup(function () {
        $("#id-Group-Search-Result-Msg").hide();
        let is_match_found = false;
        var searchStringOrig = $("#txt-search-groups").val();
        var searchString = searchStringOrig.toLowerCase();
        $(".group-container").show();
        var groups = $(".group-container");
        for (var i = 0; i < groups.length; i++) {
            var groupName = $(groups[i]).find(".group-name").text().toLowerCase();
            if (groupName.indexOf(searchString) < 0) {
                $(groups[i]).hide();
            } else {
                is_match_found = true;
            }
        }
        if (!is_match_found && searchString.trim().length > 0) {
            $("#id-Group-Search-Result-Msg").show();
            show_not_found(searchStringOrig);
        }
    });


    // File name preview for picture field, file select method
    $('.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });
    
    // Hide explanation checkbox if auto-approval is enabled
    if($('#auto-approve').is(':checked')){
        $('#requires_explanation').prop( "checked", false );
        $('#requires_explanation').parent().hide();
    }
    $('#auto-approve').change(function() {
        if(this.checked) {
            $('#requires_explanation').prop( "checked", false );
            $('#requires_explanation').parent().hide();
        }else{
            $('#requires_explanation').parent().show();
        }
    });
});

/**
 * display search feedback
 * @param searchString
 */
function show_not_found(searchString) {
    let not_found_message = "We couldn't find anything for <strong>" + searchString + "</strong>.";
    $("#id-Group-Search-Result-Msg").html(not_found_message);
}
