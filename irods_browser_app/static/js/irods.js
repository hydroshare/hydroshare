$('#btn-signin-irods').on('click',function(){
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

$('#btn-select-irods-file').on('click',function(){
    $('#res_type').val($('#resource-type').val());
    $('#file_struct').children().remove();
    $('.ajax-loader').hide();
    var store = '';
    if (sessionStorage.IRODS_signininfo) {
        $("#irods_content_label").text(sessionStorage.IRODS_username);
        $('#root_store').val(sessionStorage.IRODS_datastore);
        store = sessionStorage.IRODS_datastore;
    }
    
    // Setting up the view tab
    $('#file_struct').attr('name',store);
    $('#irods_view_store').val(store);
    // loading file structs
    var parent = $('#file_struct');
    get_store(store,parent,0);
    $('body').on('click', '.folder', click_folder_opr);
});

function get_store(store, parent, margin){
    $.ajax({
        mode: "queue",
        url: '/irods/store/',
        async: true,
        type: "POST",
        data: {
            store: store,
            user: sessionStorage.IRODS_username,
            password: sessionStorage.IRODS_password,
            zone: sessionStorage.IRODS_zone,
            port: sessionStorage.IRODS_port,
            host: sessionStorage.IRODS_host
        },
        success: function (json) {
            var files = json.files;
            var folder = json.folder;
            if (files.length == 0 && folder.length == 0) {
                $(parent).append("<div class='file' style='margin-left:" + margin + "px;'></div>");
            }
            else {
                $.each(folder, function(i,v) {
                    $(parent).append("<div class='folder' id='irods_folder_" + v + "' name='" + store + "/" + v + "' style='margin-left:" + margin + "px;'><img src='/static/img/folder.png' width='15' height='15'>&nbsp; " + v + "</div>");
                });

                $.each(files, function(i,v) {
                    $(parent).append("<div class='file' id='irods_file_" + v + "' name='" + store + "/" + v + "' style='margin-left:" + margin + "px;'><img src='/static/img/file.png' width='15' height='15'>&nbsp; " + v + "</div>")
                    $('.file').on('click',function(e){
                        $('.file').css('background','');
                        $('.file').removeClass('selected');
                        $(e.target).css('background','#cecece');
                        $(e.target).addClass('selected');
                        set_datastore($(this).parent('div')[0], 0)
                        return false
                    });
                });
            }
        },

        error: function(status) {
            console.error(status);
            return false;
        }
    });
    return true;
}

function click_folder_opr() {
    var margin_left = parseInt($(this).css('margin-left')) + 10;
        if($(this).hasClass('isOpen')) {
            $(this).addClass('isClose');
            $(this).removeClass('isOpen');
            $(this).children('div').hide();
            set_datastore($(this).attr('name'), 'folder');
        }
        else if($(this).hasClass('isClose')) {
            $(this).addClass('isOpen');
            $(this).removeClass('isClose');
            $(this).children('div').show();
        }
        else {
            var store = $(this).attr('name');
            var parent = $(this)
            get_store(store, parent, margin_left);
            $(this).addClass('isOpen');
            set_datastore($(this).attr('name'), 1);
        }
        return false;
}

function set_datastore(store,isFolder) {
    if (!isFolder) {
        store = $(store).attr('name');
    }
    $('#irods_view_store').val(store);
}

// ### IRODS FUNCTION FOR VIEWING INPUT BOX UPON PRESSING RETURN ###
$('#irods_view_store').keypress(function(e) {
    if(e.which == 13) {
        var store = $(this).val();
        if (store=='') {
            store = $('#root_store').val();
        }
        // Setting up the view tab
        $('#file_struct').attr('name',store);
        $('#irods_view_store').val(store);

        // loading file structs
        var parent = $('#file_struct');
        var got_store = get_store(store,parent,0);
        if (got_store) {
            $('#file_struct').children().remove();
            click_folder_opr();
        }
        else {
            alert('Datastore does not exist');
        }
    }
});

$("#irodsContent form").bind("keypress", function (e) {
    if (e.keyCode == 13) {
        $("#btnSearch").attr('value');
        //add more buttons here
        return false;
    }
});

$('#iget_irods').on('click',function(){
    var name = $('.selected').attr('name');
    $('#upload_store').val(name);
    $("#irods-username").val(sessionStorage.IRODS_username)
    $("#irods-password").val(sessionStorage.IRODS_password)
    $("#irods-host").val(sessionStorage.IRODS_host)
    $("#irods-zone").val(sessionStorage.IRODS_zone)
    $("#irods-port").val(sessionStorage.IRODS_port)
    $('#irodsContent .modal-backdrop.up-load').show();
    $('#irodsContent .ajax-loader').show();
});

// Submit post on submit
$('#post-form').on('submit', function(event){
    event.preventDefault();
    console.log("form submitted!")  // sanity check
    create_post();
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
                $("#sign-in-info").text(signInStr);
                $("#irods_content_label").text(json.user);
                $('#root_store').val(json.datastore);
                $("#btn-select-irods-file").show();
                $("#irods-sel-file").text("No file selected");
                sessionStorage.IRODS_signininfo = signInStr;
                sessionStorage.IRODS_datastore = json.datastore;
                sessionStorage.IRODS_username = json.user;
                sessionStorage.IRODS_password = json.password;
                sessionStorage.IRODS_port = json.port;
                sessionStorage.IRODS_host = json.host;
                sessionStorage.IRODS_zone = json.zone;
            }
            else {
                $("#sign-in-info").text('iRODS login failed');
                sessionStorage.IRODS_signininfo ='';
                $("#btn-select-irods-file").hide();
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
            $("#sign-in-info").text('iRODS login failed');
            $("#btn-select-irods-file").hide();
            $("#irods-sel-file").text("No file selected");
            $('#irodsSignin').modal('hide');
        }
    });
}

$('#irodsLogin').on('submit', function(event){
    event.preventDefault();
    irods_login();
});

function irods_upload() {
    $.ajax({
        url: "/irods/upload/",
        type: "POST",
        data: {
            upload: $('#upload_store').val(),
            res_type: $('#res_type').val()
        },
        success: function(json) {
            $("#irods-sel-file").text(json.irods_file_name);
            $("#file-type-error").text(json.file_type_error);
            $('#irodsContent').modal('hide');
            $('#irods_file_name').val(json.irods_file_name)
        },
        error: function(xhr, errmsg, err) {
            console.log(xhr.status + ": " + xhr.responseText + ". Error message: " + errmsg);
            $("#irods-sel-file").text("No file selected");
            $('#irodsContent').modal('hide');
        }
    });
}

$('#irodsUpload').on('submit', function(event){
    event.preventDefault();
    irods_upload();
});