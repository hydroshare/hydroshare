/**
* Created by Mauriel on 3/9/2017.
*/


// These event bindings will work even for elements created dynamically
$(document).on('click', '.btn-unshare-resource', function () {
    var formID = $(this).closest("form").attr("id");
    unshare_resource_ajax_submit(formID);
});

$( "#confirm-res-id-text" ).keyup(function() {
    $("#btn-delete-resource").prop("disabled", this.value !== "DELETE");
});

$("#delete-resource-dialog").on('hidden.bs.modal', function () {
  $("#confirm-res-id-text").val('');
  $("#btn-delete-resource").prop("disabled", true);
});

$(document).on('click', '.btn-undo-share', function () {
    var formID = $(this).closest("form").attr("id");
    undo_share_ajax_submit(formID);
});

$(document).ready(function() {
    var resID = $("#resID").val();

    var btnDisabledTexts = {
        'delete': 'Deleting...',
        'add content': 'Adding Content...',
        'save changes': 'Saving Changes...',
    };

    function setButtonDisabledText(btn) {
        let buttonText = btn.text().toLowerCase().trim();
        btn.text(btnDisabledTexts[buttonText] !== null ? btnDisabledTexts[buttonText] : "Saving Changes...");
        btn.addClass("disabled");
    }

    $("#download-bag-btn").click(function() {
        $("#license-agree-dialog-bag").modal('hide');
        $("#agree-chk-download-bag").prop( "checked", false );
    });

    $("#btn-add-hydroshare-user").click(function () {
        $(this).text("Saving Changes...");
        $(this).addClass("disabled");
        var response = get_user_info_ajax_submit('/hsapi/_internal/get-user-or-group-data/', this);
        if (!response) {
            $(this).text("Save Changes");
            $(this).removeClass("disabled");
        }
    });

    // Disables the button after it has been clicked and its closest form was found to be valid
    $(".btn-disable-after-valid").click(function () {
        if ($(this).closest("form")[0].checkValidity()) {
            setButtonDisabledText($(this));
        }
    });

    // Disables the button after it is clicked
    $(".btn-disable-after").click(function () {
        setButtonDisabledText($(this));
    });

    $("#btn-confirm-extended-metadata").click(addEditExtraMeta2Table);
    $("#btn-confirm-delete-extended-metadata").click(removeExtraMetaTable);

    $("#btn-confirm-delete-comment").click(removeComment);

    $("input#user-autocomplete").addClass("form-control");

    $('#usage-info').on('hidden.bs.collapse', function () {
        $("a[data-target='#usage-info']").text("Show More");
    }).on('shown.bs.collapse', function () {
        $("a[data-target='#usage-info']").text("Show Less");
    });
});
