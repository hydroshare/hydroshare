$(document).ready(function () {
    var form = $("#reset-password-form");
    form.on('submit', function (event) {
        if (validatePasswords() === false) {
            event.preventDefault();
            event.stopPropagation();
        }
    });

    $("#id_password1, #id_password2").on("input", function(event) {
        resetValidationState();
    });

});

function validatePasswords() {
    // Password
    var password1 = $("#id_password1");
    var password2 = $("#id_password2");

    resetValidationState();

    var validation = true;

    if (password1.val() != password2.val()) {
        password1.addClass("form-invalid");
        password2.addClass("form-invalid");
        password2.parent().append(errorLabel("Passwords do not match"));
        validation = false;
    }

    if (password1.val().length < 6) {
        password1.addClass("form-invalid");
        password1.parent().append(errorLabel("Passwords must be at least 6 characters long"));
        validation = false;
    }

    if (password2.val().length < 6) {
        password2.addClass("form-invalid");
        password2.parent().append(errorLabel("Passwords must be at least 6 characters long"));
        validation = false;
    }

    return validation;
}

function resetValidationState() {
    var password1 = $("#id_password1");
    var password2 = $("#id_password2");

    password1.parent().find(".error-label").remove();
    password2.parent().find(".error-label").remove();

    password1.removeClass("form-invalid");
    password2.removeClass("form-invalid");
}

function errorLabel(message) {
    return "<div class='error-label'><div class='label label-danger'>" + message + "</div></div>";
}