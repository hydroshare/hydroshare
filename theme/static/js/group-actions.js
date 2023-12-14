function group_invite_ajax_submit() {
  if (!$("#id_user-deck > .hilight").length) {
    return false; // If no user selected, ignore the request
  }
  var share_with = $("#id_user-deck > .hilight")[0].getAttribute("data-value");
  var form = $("#invite-to-group");
  var datastring = form.serialize();
  var url = form.attr("action") + share_with + "/";

  $.ajax({
    type: "POST",
    url: url,
    dataType: "html",
    data: datastring,
    success: function (result) {
      $(".hilight > span").click(); // Clears the search field
      $("#invite-dialog .modal-body").prepend(
        '<div class="alert alert-success" role="alert"><span class="glyphicon glyphicon-ok glyphicon"></span> An invitation to join has been sent.</strong></div>'
      );

      setTimeout(function () {
        $("#invite-dialog .modal-body .alert").fadeOut();
      }, 3000);
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      $("#invite-dialog .modal-body").prepend(
        '<div class="alert alert-error" role="alert"><span class="glyphicon glyphicon-ok glyphicon"></span> This invitation could not be sent.</strong></div>'
      );

      setTimeout(function () {
        $("#invite-dialog .modal-body .alert").fadeOut();
      }, 3000);
    },
  });
  //don't submit the form
  return false;
}

function onRoleSelect(event) {
  var el = $(event.target);
  $("#selected_role").text(el.text());
  $("#selected_role")[0].setAttribute(
    "data-role",
    el[0].getAttribute("data-role")
  );
}

function request_join_group_ajax_submit() {
  var target = $(this);
  var dataFormID = $(this).attr("data-form-id");
  var form = $("#" + dataFormID);
  // var datastring = form.serialize();

  const formData = form.serializeArray();
  const dataToSend = {};
  $(formData).each(function(index, obj){
      dataToSend[obj.name] = obj.value;
  });

  var url = form.attr("action");

  if ($(this).attr("requires_explanation") === "True") {
    // show a modal requesting explanation
    $("#explanation-dialog").modal("show");
    $("#explanation").unbind(".group_ns");

    // on modal submission
    $("#explanation_btn").click(() => {
      const explanation = $("#explanation").val().trim();
      const sanitized_explanation = $("<div/>").html(explanation).text();

      if (sanitized_explanation !== explanation) {
        showError(
          "The explanation text contains html code and cannot be saved."
        );
      } else if (sanitized_explanation == 0) {
        showError(
          "Justificaiton is a required field that cannot be left blank."
        );
      } else if (sanitized_explanation.length > 300) {
        showError(
          "The justificaiton is too long. Please shorten to 300 characters."
        );
      } else {
        const explanationData = $("#explanation").serializeArray();
        $(explanationData).each(function(index, obj){
            dataToSend[obj.name] = obj.value;
        });

        submitGroupRequest(dataToSend);
        $("#explanation-dialog").modal("hide");
      }
    });
    function showError(errorText) {
      $("#explanation").addClass("form-invalid");
      $("#explanation_msg").html(
        "<div class='alert alert-danger'>" + errorText + "</div>"
      );
      $("#explanation_msg").show();
      $("#explanation").bind("input propertychange.group_ns", function () {
        $("#explanation").removeClass("form-invalid");
        $("#explanation_msg").hide();
      });
    }
  } else {
    submitGroupRequest(dataToSend);
  }

  /** Submit a request to join a group or an invitation and handles the response */
  async function submitGroupRequest(data) {
    try {
      const response = await $.post(url, data);
      if (response.status === 'success') {
        const container = target.parent().parent();
        target.parent().remove();

        if (response.message === 'You are now a member of this group') {
          // The requestt was auto-approved
          if (window.location.pathname.startsWith('/group/')) {
            // From the Group page we need to refresh the page
            location.reload() ;
          }
          else if (window.location.pathname === '/groups') {
            // From the Find Groups page we need to update UI
            container.append(
              '<div class="flag-joined text-right"><i class="fa fa-check-circle-o"></i></span> <b>You have joined this group</b></div>'
            );
          }
        }
        else {
          // The request was sent
          container.append(
            '<span class="badge badge-success"><i class="fa fa-paper-plane"></i> Request Sent</span>'
          );
        }
      }
      else {
        console.log(response.message)
      }
    }
    catch (e) {
      console.log("Failed to submit group request", e);
    }
  }
}

function act_on_request_ajax_submit() {
  var target = $(this);
  var form = $(this).closest("form");
  var datastring = form.serialize();
  var url = form.attr("action");
  $.ajax({
    type: "POST",
    url: url,
    dataType: "html",
    data: datastring,
    success: function (result) {
      if (target.attr("data-user-action") == "Accept") {
        // Get a copy of the member row template
        var rowTemplate = $("#templateRow").clone();

        var name = target.attr("data-name");
        var title = target.attr("data-title");
        var picture = target
          .parent()
          .parent()
          .parent()
          .find("[data-id='picture']");

        rowTemplate.find("[data-id='name']").text(name);
        rowTemplate
          .find("[data-id='name']")
          .attr("href", "/user/" + target.attr("data-member-id") + "/");
        rowTemplate.find("[data-id='title']").text(title);
        var forms = rowTemplate.find("form");
        for (var i = 0; i < forms.length; i++) {
          var newAction = $(forms[i])
            .attr("action")
            .replace("member_id", target.attr("data-member-id"));
          $(forms[i]).attr("action", newAction);
        }
        rowTemplate.prepend(picture);

        $("#all-members-table tbody").append(
          $(
            "<tr data-filter-by='view-user' style='display: none;'>" +
              rowTemplate.html() +
              "</tr>"
          )
        );
        $(".btn-share-group").click(share_group_ajax_submit);
        $(".btn-unshare-group").click(unshare_group_ajax_submit);
      }

      target.parent().parent().parent().remove();
      updateMembersLabelCount();
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      console.log("error");
    },
  });
  //don't submit the form
  return false;
}

function share_group_ajax_submit() {
  var target = $(this);
  var form = target.closest("form");
  var role = target.attr("data-role");
  var datastring = form.serialize();
  var url = form.attr("action");
  $.ajax({
    type: "POST",
    url: url,
    dataType: "html",
    data: datastring,
    success: function (result) {
      var dropdownButton = target
        .parent()
        .parent()
        .parent()
        .parent()
        .find(".dropdown-toggle");
      dropdownButton.text(role);
      dropdownButton.append('&nbsp;<span class="caret"></span>');

      var row = target.parent().parent().parent().parent().parent().parent();
      if (role == "Owner") {
        row.attr("data-filter-by", "edit-user");
      } else if (role == "Member") {
        row.attr("data-filter-by", "view-user");
      }

      dropdownButton.dropdown("toggle");
      updateMembersLabelCount();
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      console.log("error");
    },
  });
  //don't submit the form
  return false;
}

function unshare_group_ajax_submit() {
  var target = $(this);
  var form = target.closest("form");
  var datastring = form.serialize();
  var url = form.attr("action");
  $.ajax({
    type: "POST",
    url: url,
    dataType: "html",
    data: datastring,
    success: function (result) {
      var row = target.parent().parent().parent().parent().parent().parent();
      row.remove();
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      console.log("error");
    },
  });
  //don't submit the form
  return false;
}

function updateMembersLabelCount() {
  var viewCount =
    $("#all-members-table tr[data-filter-by='view-user']").length - 1; // Subtract hidden template row
  var editCount = $("#all-members-table tr[data-filter-by='edit-user']").length;
  var pendingCount = $(
    "table[data-filter-by='pending'] tr:not('.no-pending-requests')"
  ).length;

  $("#members-filter .badge[data-filter-by='All']").text(viewCount + editCount);
  $("#members-filter .badge[data-filter-by='Owners']").text(editCount);
  
  const pendingBadge = $("#members-filter .badge[data-filter-by='Pending']")
  pendingBadge.text(pendingCount);
  if (pendingCount > 0) {
    pendingBadge.css('background-color', '#428BCA');
  }

  // Disable options to leave or remove for last owner item.
  if (editCount == 1) {
    $(
      "#all-members-table tr[data-filter-by='edit-user'] .dropdown-toggle"
    ).attr("disabled", true);
  } else {
    $(
      "#all-members-table tr[data-filter-by='edit-user'] .dropdown-toggle"
    ).attr("disabled", false);
  }
}

// Preview profile picture
function readURL(input) {
  if (input.files && input.files[0]) {
    var reader = new FileReader();
    reader.onload = function (e) {};

    reader.readAsDataURL(input.files[0]);
  }
}
