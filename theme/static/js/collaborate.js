/**
 * Created by Mauriel on 3/9/2017.
 */

// File name preview for picture field, change method
$(document).on("change", ".btn-file :file", function () {
  var input = $(this);
  var numFiles = input.get(0).files ? input.get(0).files.length : 1;
  var label = input.val().replace(/\\/g, "/").replace(/.*\//, "");
  input.trigger("fileselect", [numFiles, label]);
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
  $(".btn-file :file").on("fileselect", function (event, numFiles, label) {
    var input = $(this).parents(".input-group").find(":text");
    input.val(label);
  });

  // Hide explanation checkbox if auto-approval is enabled
  if ($("#auto-approve").is(":checked")) {
    $("#requires_explanation").prop("checked", false);
    $("#requires_explanation").parent().hide();
  }
  $("#auto-approve").change(function () {
    if (this.checked) {
      $("#requires_explanation").prop("checked", false);
      $("#requires_explanation").parent().hide();
    } else {
      $("#requires_explanation").parent().show();
    }
  });
});

/**
 * display search feedback
 * @param searchString
 */
function show_not_found(searchString) {
  let not_found_message =
    "We couldn't find anything for <strong>" + searchString + "</strong>.";
  $("#id-Group-Search-Result-Msg").html(not_found_message);
}
