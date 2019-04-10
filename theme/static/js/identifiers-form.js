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
    $(".edit-identifiers-container").on("click", ".close", function () {
        $(this).closest(".well").remove();
    });

    $(".btn-add-identifier").click(function () {
        var templateInstance = $(this).parent().find(".identifier-template").clone();
        templateInstance.toggleClass("hidden", false);
        templateInstance.toggleClass("identifier-template", false);

        templateInstance.find(".select-identifier").attr("name", "identifier_name");
        templateInstance.find(".identifier-link-container input").attr("name", "identifier_link");

        $(this).parent().find(".edit-identifiers-container").append(templateInstance);
    });
});