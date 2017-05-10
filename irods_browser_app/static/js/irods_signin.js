$('#btn-signin-irods').on('click',function() {
    if(sessionStorage.IRODS_username) {
        $("#username").val(sessionStorage.IRODS_username);
    }
    else {
        $("#username").val('');
    }
    if(sessionStorage.IRODS_password) {
        $("#password").val(sessionStorage.IRODS_password);
    }
    else {
        $("#password").val('');
    }
    if(sessionStorage.IRODS_host) {
        $("#host").val(sessionStorage.IRODS_host);
    }
    else {
        $('#host').val('');
    }
    if(sessionStorage.IRODS_port) {
        $("#port").val(sessionStorage.IRODS_port);
    }
    else {
        $("#port").val('1247');
    }
    if(sessionStorage.IRODS_zone) {
        $("#zone").val(sessionStorage.IRODS_zone);
    }
    else {
        $('#zone').val('');
    }
});

$('#btn-signout-irods').on('click', function() {
    $("#sign-in-name").text('');
    $("#sign-in-info").removeClass();
    $("#sign-in-info").addClass("hidden");
    sessionStorage.IRODS_signininfo = '';
    $("#irods-sel-file").text('');
    $("#btn-select-irods-file").toggleClass("hidden", true);
    $("#log-into-irods").show();
    $("#btn-signout-irods").hide();
    $('#irods-copy-move').hide();
});

function irods_login() {
    $.ajax({
        url: "/irods/login/",
        type: "POST",
        data: {
            username: $('#username').val(),
            password: $('#password').val(),
            zone: $('#zone').val(),
            host: $('#host').val(),
            port: $('#port').val()
        },
        success: function(json) {
            if(json.irods_loggedin) {
                var signInStr = "Signed in as " + json.user;
                $("#sign-in-info").removeClass();
                $("#sign-in-info").addClass("alert alert-info");
                $("#sign-in-name").text(signInStr);
                $("#irods_content_label").text(json.user);
                $('#root_store').val(json.datastore);
                $("#log-into-irods").hide();
                $("#btn-signout-irods").show();
                $("#btn-select-irods-file").toggleClass("hidden", false);
                $("#irods-sel-file").text("No file selected.");
                sessionStorage.IRODS_signininfo = signInStr;
                sessionStorage.IRODS_datastore = json.datastore;
                sessionStorage.IRODS_username = json.user;
                sessionStorage.IRODS_password = json.password;
                sessionStorage.IRODS_port = json.port;
                sessionStorage.IRODS_host = json.host;
                sessionStorage.IRODS_zone = json.zone;
            }
            else {
                $("#sign-in-name").text('iRODS login failed');
                $("#sign-in-info").removeClass();
                $("#sign-in-info").addClass("alert alert-danger");
                sessionStorage.IRODS_signininfo = '';
                $("#btn-select-irods-file").toggleClass("hidden", true);
                $("#irods-sel-file").text('');
            }
            $('#irodsSignin').modal('hide');
        },
        error: function(xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
            sessionStorage.IRODS_signininfo = 'iRODS login failed';
            sessionStorage.IRODS_datastore = '';
            sessionStorage.IRODS_username = '';
            sessionStorage.IRODS_password = '';
            sessionStorage.IRODS_port = '1247';
            sessionStorage.IRODS_host = '';
            sessionStorage.IRODS_zone = '';
            $("#sign-in-name").text('iRODS login failed');
            $("#sign-in-info").removeClass();
            $("#sign-in-info").addClass("alert alert-danger");
            $("#btn-select-irods-file").toggleClass("hidden", true);
            $("#irods-sel-file").text('');
            $('#irodsSignin').modal('hide');
        }
    });
}

$('#irodsLogin').on('submit', function(event) {
    event.preventDefault();
    irods_login();
});