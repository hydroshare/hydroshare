/**
* Created by Mauriel on 3/9/2017.
*/

var CHECK_PROFILE_IMAGE_SIZE = true;
const KILO_BYTE = 1024;
const MEGA_BYTE = KILO_BYTE * KILO_BYTE;
const PROFILE_IMAGE_SIZE_BYTE_LIMIT = DATA_UPLOAD_MAX_MEMORY_SIZE;
const MEGA_BYTE_STR="MB";
var PROFILE_IMAGE_SIZE_MB_LIMIT_MSG = PROFILE_IMAGE_SIZE_BYTE_LIMIT/MEGA_BYTE
                + " " + MEGA_BYTE_STR;

// avoid tying error, define it as variable
var errorElementID = "errorSizeLoadFile";

function clearSizeErrorMsg() {
    $("#" + errorElementID).remove();
}

function displaySizeErrorMsg() {
     let errorMsg = "Error: Photo size can not exceed " + PROFILE_IMAGE_SIZE_MB_LIMIT_MSG;
     let elementOpen = '<div style="display: block;" id="' + errorElementID + '"> <p ' +
                       'class="label label-danger profile-photo-error">';
     let elementClose = '</p></div>';
     $(elementOpen + errorMsg + elementClose).insertAfter($("#photo-control"));;

}

// Preview profile picture
function readURL(input) {
    if (input.files && input.files[0]) {
        let reader = new FileReader();
        let file = input.files[0];

        clearSizeErrorMsg();

        if (
            file.size > PROFILE_IMAGE_SIZE_BYTE_LIMIT &&
            CHECK_PROFILE_IMAGE_SIZE === true
        ) {
            displaySizeErrorMsg();
            // clear the file
            input.value = "";
            return;
        }

        reader.onload = function (e) {
            let profilePicContainer = $("#profile-pic-container");
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

    cleanIdentifiers();

    return  flagRequiredElements && flagEmail;
}

function validateRequiredElements() {
    var requiredElements = $(".form-required");
    for (var i = 0; i < requiredElements.length; i++) {
        if (!$(requiredElements[i]).val() || !$(requiredElements[i]).val().trim()) {
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

    var userTypeValue = $("#db-user-type").text().trim();
    var selectedUserType = $('#selectUserType option[value="' + userTypeValue + '"]');

    if (selectedUserType.length > 0) {
        selectedUserType.attr('selected', 'selected');
        $('#selectUserType').val(userTypeValue).change();
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
    if ($(this).val().trim()) {
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
            $('#create-irods-account-dialog').modal('hide');
            var irodsContainer = $("#irods-account-container");
            const errorText = JSON.parse(xhr.responseText).error
            errorText && irodsContainer.append(irods_status_info('alert-danger', errorText , 'Failure'));
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
            var irodsContainer = $("#irods-account-container");
            if(json.success) {
                irodsContainer.empty();
                irodsContainer.append(irods_account_link("#create-irods-account-dialog", "Create your iRODS user account"));
                irodsContainer.append(irods_status_info('alert-success', json.success, 'Success'));
            }
            if(json.error) {
                irodsContainer.append(irods_status_info('alert-warning', json.error, 'Failure'));
            }
            $('#delete-irods-account-dialog').modal('hide');
        },
        error: function(xhr, errmsg, err) {
            $('#delete-irods-account-dialog').modal('hide');
            var irodsContainer = $("#irods-account-container");
            const errorText = JSON.parse(xhr.responseText).error
            errorText && irodsContainer.append(irods_status_info('alert-warning', errorText, 'Failure'));
        }
    });
    return false;
}

function getUrlVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function isPhoneValidInCountry(phone, country){
    if (!BFHPhoneFormatList.hasOwnProperty(country)) return false;
    let BFHString = BFHPhoneFormatList[country];

    // Turn the string into a regex
    stringFormat = BFHString.replace(/\s/g, String.fromCharCode(92)+"s");
    stringFormat = stringFormat.replace("+", String.fromCharCode(92)+"+");
    stringFormat = stringFormat.replace("(", String.fromCharCode(92)+"(");
    stringFormat = stringFormat.replace(")", String.fromCharCode(92)+")");
    stringFormat = stringFormat.replace(/d/g, String.fromCharCode(92)+"d");
    stringFormat = new RegExp(stringFormat);
    return stringFormat.test(phone) || BFHString;
}

function isPhoneCountryCodeOnly(phone, country){
    if (!BFHPhoneFormatList.hasOwnProperty(country)) return false;
    let BFHString = BFHPhoneFormatList[country];
    let stringFormat = BFHString.replace(/d/g, '');
    stringFormat = stringFormat.replace(/[\(\)-]/g, '');
    return phone.trim().length === stringFormat.trim().length
}

function resetPhoneValues(){
    // Bootstrap-formhelper will erase existing values if they don't conform to the expected country format
    // So we update with the original values where necessary
    $('input[type="tel"]').each(function(){
        const oldPhones = PHONES || null;
        if (!oldPhones || oldPhones === 'None') return;
        const phoneObj = $(this);
        if (oldPhones[phoneObj[0].name] === 'None') return;
        phoneObj.val(oldPhones[phoneObj[0].name]);
    });
}

function checkForInvalidPhones(){
    $('input[type="tel"]').each(function(){
        checkPhone(this, false);
    });
}

function checkPhone(phoneField, isInputEvent=true){
    const country = $("#country").val();
    phoneField = $(phoneField);
    phoneField.siblings('.error-label').remove();
    phoneField.removeClass('form-invalid');
    if (! country ) {
        if (isInputEvent){
            phoneField
            .addClass('form-invalid')
            .parent().append(errorLabel("Please add a country before adding phone to your profile"));
        }
        return;
    }
    const phoneValue = phoneField.val();
    if( !phoneValue ) return;
    const phoneValidation = isPhoneValidInCountry(phoneValue, country);
    const onlyCode = isPhoneCountryCodeOnly(phoneValue, country);
    onlyCode ? phoneField.addClass('only-country-code') : phoneField.removeClass('only-country-code');
    if ( phoneValidation !== true && !onlyCode ){
        phoneField
            .addClass('form-invalid')
            .parent().append(errorLabel(`Please update to format: [${phoneValidation}]`));
    }
}

function isStateInCountry(stateCode, country){
    if (!BFHStatesList.hasOwnProperty(country)) return false;
    const asArray = Object.entries(BFHStatesList[country]);
    const filtered = asArray.filter(([key, state]) => state.code === stateCode);
    return filtered.length > 0;
}

function checkForInvalidStates(country){
    const oldState = OLD_STATE || null;
    if (!oldState || oldState === 'None') return;
    country = country || $("#country").val()
    const stateField = $('#state');
    if ( !isStateInCountry(oldState, country)){
        stateField.append($('<option>', {
            value: oldState,
            text: oldState,
            class: "old-state-option"
        }));
        stateField.val(oldState)
            .change()
            .addClass('form-invalid')
            .parent().append(errorLabel("No longer valid, please update."));

        // Register one-time listener to clear the message and old option
        stateField.one('change', function(){
            $(this).siblings('.error-label').remove();
            $(this).removeClass('form-invalid');
            $(".old-state-option").remove();
        });
    }

    // Update for view mode
    if (! $('#db-state').text()) {
        $('#db-state').text(OLD_STATE);
    }
}

$(document).ready(function () {
    // Multiple orgs are a string delimited by ";" --wrap them so we can style them
    $("#organization").splitAndWrapWithClass(";", "organization-divider");
    
    $("#btn-create-irods-account").click(create_irods_account);
    $("#btn-delete-irods-account").click(delete_irods_account);

    // Only enable Confirm button when input password is longer than 8 characters
    $("#id_irods_password").keyup(function () {
        var pwdlen = $("input#id_irods_password").val().length;
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

    $(".btn-cancel-profile-edit").click(function () {
        location.reload(true);
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

    $('#organization_input').tagsInput({
      interactive: true,
      placeholder: "Organization(s)",
      delimiter: [";"],
      autocomplete: {
        source: "/hsapi/dictionary/universities/",
        minLength: 3,
        delay: 500,
        classes: {
            "ui-autocomplete": "minHeight"
        }
      }
    });

    $('#subject_areas').tagsInput({
        interactive: true,
        placeholder: "Subject Area(s)",
        delimiter: [","],
        autocomplete: {
          source: "/hsapi/dictionary/subject_areas/",
          minLength: 3,
          delay: 500,
          classes: {
              "ui-autocomplete": "minHeight"
          }
        }
      });

    $('.ui-autocomplete-input').on('blur', function(e) {
      e.preventDefault();
      $(this).trigger(jQuery.Event('keypress', { which: $.ui.keyCode.ENTER }));
    });

    $('.ui-autocomplete-input').on('keydown', function(e) {
      if(e.keyCode === 9 && $(this).val() !== '') {
        e.preventDefault();
        $(this).trigger(jQuery.Event('keypress', { which: $.ui.keyCode.ENTER }));
      }
    });

    if(getUrlVars()["edit"] == 'true'){
        setEditMode();
        // clear out the edit query params so edit mode isn't reopened on save
        history.pushState('', document.title, window.location.pathname);
    }

    // Event listeners for profile phone changes
    $('input[type="tel"]').on('keyup', (e)=>checkPhone(e.target));
    $('#country').on('change', function(){
        resetPhoneValues();
        checkForInvalidPhones();
    });

    $('.btn-save-profile').click(function(e){
        // clear phones that only have country codes before submit
        $('.only-country-code').val("");
    });

    resetPhoneValues();
    checkForInvalidPhones();
    checkForInvalidStates();

    $('#revoke-quota-request').click(function(e){
        revokeQuota($(this).data("action"))
    });
    let profileMissing = localStorage.getItem('missing-profile-fields')
    let profileUser = localStorage.getItem('profile-user')
    if (!profileUser){
        checkProfileComplete().then(([user, missing])=>{
            profileMissing = missing.join(', ');
            profileUser = user;
            updateQuotaMessage(profileMissing);
        });
    }else{
        profileMissing = profileMissing.split(',').join(', ')
        updateQuotaMessage(profileMissing);
    }
    function updateQuotaMessage(profileMissing){
        if (profileMissing){
            const button = $('#quota-request-storage');
            button.prop("disabled",true);
            button.after(
                "<br><div class='alert alert-warning' style='margin-top: 20px;'>" +
                    "You can request additional quota once your profile is complete. " +
                    `Your profile is missing: ${profileMissing}.` +
                "</div>")
        }
    }
    checkQuotaStatus();
});

async function revokeQuota(url) {
    // workaround to handle embeded forms in profile.html template
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken')
      }
    });

    if (response.ok) {
        if ( response?.url ) {
            localStorage.setItem("quota-status", "revoked")
            window.location.replace(response.url);
        }
    }
    else {
      customAlert("Quota Request", 'Failed to revoke request', "error", 6000, true);
    }
    this.isApproving = false
}

function checkQuotaStatus() {
    const status = localStorage.getItem("quota-status")
    if(status !== null ) {
        customAlert("Quota Request", `Your quota request was successfully ${status}.`, "success", 6000, true);
        localStorage.removeItem("quota-status");
    }
}