/**
* Created by Mauriel on 3/9/2017.
*/

// Preview profile picture
function readURL(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
            var profilePicContainer = $("#profile-pic-container");
            profilePicContainer.empty();
            profilePicContainer.append(
                '<div style="background-image: url(\'' + e.target.result +  '\')"' +
                     'class="profile-pic round-image">' +
                '</div>'
            );
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function validateForm() {
    var flagRequiredElements = validateRequiredElements();
    var flagEmail = validateEmail();

    return  flagRequiredElements && flagEmail;
}

function validateRequiredElements() {
    var requiredElements = $(".form-required");
    for (var i = 0; i < requiredElements.length; i++) {
        if (!$(requiredElements[i]).val()) {
            $(requiredElements[i]).addClass("form-invalid");
            $(requiredElements[i]).parent().find(".error-label").remove();
            $(requiredElements[i]).parent().append(errorLabel("This field is required."));
            return false;
        }
    }

    return true;
}

function validateEmail() {
    var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
    var email = $("#id_email");

    if (!email.val()) {
        return false;
    }

    if (!regex.test(email.val())) {
        email.parent().find(".error-label").remove();
        email.parent().append(errorLabel("Not a valid email address."));
        return false;
    }

    return true;
}

function errorLabel(message) {
    return "<div class='error-label'><div class='label label-danger'>" + message + "</div></div>";
}


function setEditMode() {
    $("[data-page-mode='view']").hide();
    $("[data-page-mode='edit']").fadeIn();
    $("[data-page-mode='on-edit-blur']").fadeTo("fast", 0.5, function () {
        $(this).addClass("blured-out");
    });

    var userTypeValue = $("#db-user-type").text();
    var selectedUserType = $('#selectUserType option[value="' + userTypeValue + '"]');

    if (selectedUserType.length > 0) {
        selectedUserType.attr('selected', 'selected');
    }
    else if (userTypeValue) {
        $('#selectUserType option[value="' + 'Other' + '"]').attr('selected', 'selected');
        $("#user-type-other").show();
        $("#selectUserType").removeAttr("name");
        var userTypeOther =  $("#user-type-other input");
        userTypeOther.attr("name", "user_type");
        userTypeOther.val(userTypeValue);
        userTypeOther.addClass("form-required");
    }

    $(".form-required").change(onFormRequiredChange);
    $("#id_email").change(validateEmail);

    // Switch to overview tab
    $('.nav-tabs a[href="#overview"]').tab('show'); // Select first tab
}

function setViewMode() {
    $("[data-page-mode='edit']").hide();
    $("[data-page-mode='view']").fadeIn();
    $("[data-page-mode='on-edit-blur']").fadeTo("fast", 1, function () {
        $(this).removeClass("blured-out");
    });
}

$(document).on('change', '#cv-custom-upload :file', function () {
    var input = $(this);
    var numFiles = input.get(0).files ? input.get(0).files.length : 1;
    var label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
    input.trigger('fileselect', [numFiles, label]);
});

function onFormRequiredChange() {
    if ($(this).val()) {
        $(this).removeClass("form-invalid");
        $(this).parent().find(".error-label").remove();
    }
    else {
        $(this).addClass("form-invalid");
        $(this).parent().find(".error-label").remove();
        $(this).parent().append(errorLabel("This field is required."));
    }
}

function irods_account_link(data_target, text) {
    return "<a data-toggle='modal' data-target='" + data_target + "'>" + text + "</a>";
}

function irods_status_info(alert_type, status, title) {
    return "<div class=\"col-sm-12\">" +
            "<div class=\"alert " + alert_type + " alert-dismissible\" role=\"alert\">" +
            "<button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-label=\"Close\"><span aria-hidden=\"true\">&times;</span></button>" +
            "<strong>" + title + "</strong><div>" + status + "</div></div></div>"
}

function create_irods_account() {
    var url = $("#url-create-irods-account").val();

    $.ajax({
        url: url,
        type: "POST",
        data: {
            password: $('#id_irods_password').val()
        },
        success: function(json) {
            if(json.success) {
                $('#create-irods-account-dialog').modal('hide');
                var irodsContainer = $("#irods-account-container");
                irodsContainer.empty();
                irodsContainer.append(irods_account_link("#delete-irods-account-dialog", "Delete your iRODS user account"));
                irodsContainer.append(irods_status_info('alert-success', json.success, 'Success'));
            }
            if(json.error) {
                $('#create-irods-account-dialog').modal('hide');
                var irodsContainer = $("#irods-account-container");
                irodsContainer.append(irods_status_info('alert-danger', json.error, 'Failure'));
            }
        },
        error: function(xhr, errmsg, err) {
            err_info = xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg;
            $('#create-irods-account-dialog').modal('hide');
            var irodsContainer = $("#irods-account-container");
            irodsContainer.append(irods_status_info('alert-danger', err_info, 'Failure'));
        }
    });
    return false;
}

function delete_irods_account() {
    var url = $("#url-delete-irods-account").val();
    $.ajax({
        url: url,
        type: "POST",
        data: {},
        success: function(json) {
            if(json.success) {
                var irodsContainer = $("#irods-account-container");
                irodsContainer.empty();
                irodsContainer.append(irods_account_link("#create-irods-account-dialog", "Create your iRODS user account"));
                irodsContainer.append(irods_status_info('alert-success', json.success, 'Success'));
            }
            if(json.error) {
                var irodsContainer = $("#irods-account-container");
                irodsContainer.append(irods_status_info('alert-warning', json.error, 'Failure'));
            }
            $('#delete-irods-account-dialog').modal('hide');
        },
        error: function(xhr, errmsg, err) {
            err_info = xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg;
            $('#delete-irods-account-dialog').modal('hide');
            var irodsContainer = $("#irods-account-container");
            irodsContainer.append(irods_status_info('alert-warning', err_info, 'Failure'));
        }
    });
}

$(document).ready(function () {
    // Change country first empty option to 'Unspecified'
    var option = $("select[name='country'] option:first-child");
    option.val("Unspecified");
    option.text("Unspecified");

    // TODO: TESTING
    $("#btn-create-irods-account").click(create_irods_account);
    // TODO: TESTING
    $("#btn-delete-irods-account").click(delete_irods_account);

    // Only enable Confirm button when input password is longer than 8 characters
    $("#id_irods_password").keyup(function () {
        pwdlen = $("input#id_irods_password").val().length;
        if (pwdlen >= 8)
            $('#btn-create-irods-account').removeAttr('disabled');
        else
            $('#btn-create-irods-account').attr('disabled', 'disabled');
    });

    // File name preview for Add CV
    $('.btn-primary.btn-file :file').on('fileselect', function (event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text');
        input.val(label);
    });

    // Empty password input. Necessary because some browsers (ex:Firefox) now ignore 'autocomplete=off'
    setTimeout(function () {
        $("input[type=password]").val('');
    }, 500);

    $(".upload-picture").change(function(){
        readURL(this);
    });

    $("#selectUserType").change(function () {
         var inputOther = $("#user-type-other input");
        if ($(this).val() == "Other") {
            $("#user-type-other").show();
            $("#selectUserType").removeAttr("name");
            inputOther.attr("name", "user_type");
            inputOther.addClass("form-required");
            inputOther.change(onFormRequiredChange);
        }
        else {
            $("#user-type-other").hide();
            inputOther.removeAttr("name");
            inputOther.removeClass("form-required");
            $("#selectUserType").attr("name", "user_type");
        }
    });

    $("[data-page-mode='edit']").hide();
    $("#btn-edit-profile").click(function () {
        setEditMode();
    });

    $("#btn-cancel-profile-edit").click(function () {
        setViewMode();
    });

    // Abstract collapse toggle
    $(".show-more-btn").click(function () {
        if ($(this).parent().find(".activity-description").css("max-height") == "50px") {
            var block = $(this).parent().find(".activity-description");

            block.css("max-height", "initial"); // Set max-height to initial temporarily.
            var maxHeight = block.height();    // Save the max height
            block.css("max-height", "50px");    // Restore

            block.animate({'max-height': maxHeight}, 300); // Animate to max height
            $(this).text("▲");
            $(this).attr("title", "Show less");
        }
        else {
            $(this).parent().find(".activity-description").animate({'max-height': "50px"}, 300);
            $(this).attr("title", "Show more");
            $(this).text("···");
        }
    });

    // Filter list listener
    $(".table-user-contributions tbody > tr").click(function () {
        $(".table-user-contributions tbody > tr").removeClass("active");
        $(this).addClass("active");
        var res_type = $(this).attr("data-type");
        if (res_type == "all") {
            $(".contribution").fadeIn();
        }
        else {
            $(".contribution").hide();
            $(".contribution[data-type='" + res_type + "']").fadeIn();
        }
    });

    // Initialize filters
    var collection = [];
    collection["total"] = 0;

    var rows = $(".contribution");
    for (var i = 0; i < rows.length; i++) {
        if (collection[$(rows[i]).attr("data-type")]) {
            collection[$(rows[i]).attr("data-type")]++;
        }
        else {
            collection[$(rows[i]).attr("data-type")] = 1;
        }
        collection["total"]++;
    }

    for (var item in collection) {
        $("tr[data-type='" + item + "']").find(".badge").text(collection[item]);
    }

    $("tr[data-type='all']").find(".badge").text(collection["total"]);


    // Unspecified goes away as soon as a user clicks.
    $("input[name='state']").click(function () {
            if ($(this).val() == "Unspecified") {
                $(this).val("");
            }
        }
    );
});