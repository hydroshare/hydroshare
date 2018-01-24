function cleanIdentifiers() {
    var identifiers = $(".edit-identifiers-container .well:not(.identifier-template)");

    identifiers.each(function (index, item) {
        if ($(item).find("[name='identifier_link']").val().trim() == "" ||
            $(item).find("[name='identifier_name']").val().trim() == "") {
            $(item).remove();
        }
    });
}

$(document).ready(function () {
    $(".edit-identifiers-container").on("change", ".select-identifier", function () {
        var value = $(this).val();
        var showOther = value === "Other";

        var other = $(this).closest(".well").find(".identifier-specify");

        other.toggleClass("hidden", !showOther);

        if (showOther) {
            other.find("input").attr("name", $(this).attr("name"));
            $(this).removeAttr("name");
        }
        else {
            $(this).attr("name", other.find("input").attr("name"));
            other.find("input").removeAttr("name");
        }
    });

    $(".edit-identifiers-container").on("click", ".close", function () {
        $(this).closest(".well").remove();
        updateIdentifierFormIndexes(this);
    });

    $(".btn-add-identifier").click(function () {
        var templateInstance = $(this).parent().find(".identifier-template").clone();
        templateInstance.toggleClass("hidden", false);
        templateInstance.removeAttr("id");

        templateInstance.find("#selectIdentifier").attr("name", "identifier_name");
        templateInstance.find(".identifier-link-container input").attr("name", "identifier_link");


        $(this).parent().find(".edit-identifiers-container").append(templateInstance).hide().fadeIn(350);
        updateIdentifierFormIndexes(this);
    });

    function updateIdentifierFormIndexes(obj) {
        var identifiers = $(obj).closest(".edit-identifiers-container").find(".well:not(.dentifier-template)");
        identifiers.each(function (index, item) {
            // Set labels and references for screen readers
            $(item).find(".identifier-specify input").attr("id", "identifier_name" + index);
            $(item).find(".identifier-specify label").attr("for", "identifier_name" + index);

            $(item).find(".select-identifier-fieldset select").attr("id", "select_identifier" + index);
            $(item).find(".select-identifier-fieldset label").attr("for", "select_identifier" + index);

            $(item).find(".identifier-link-container input").attr("id", "identifier_link" + index);
            $(item).find(".identifier-link-container label").attr("for", "identifier_link" + index);
        });
    }
});