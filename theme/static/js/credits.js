$(document).ready(function () {
    function errorLabel(message) {
        return "<div class='label label-danger error-label'>" + message + "</div>";
    }

    function flagUnique(index, awardNumber, agencyName, awardTitle, agencyURL) {
        var awardNumbers;
        var awardTitles;
        var agencyNames;
        var agencyURLs;

        var entriesTable = $(".funding-agencies-table");

        if (index) {
            // Get the list of field values currently in use, excluding the one we are editing
            agencyNames = entriesTable.find("tr:not([data-index='" + index + "']) td:nth-child(1)");
            awardTitles = entriesTable.find("tr:not([data-index='" + index + "']) td:nth-child(2)");
            awardNumbers = entriesTable.find("tr:not([data-index='" + index + "']) td:nth-child(3)");
            agencyURLs = entriesTable.find("tr:not([data-index='" + index + "']) td:nth-child(1) a");
        }
        else {
            // Get the list of field values currently in use (when adding new funding agency)
            agencyNames = entriesTable.find("tr td:nth-child(1)");
            awardTitles = entriesTable.find("tr td:nth-child(2)");
            awardNumbers = entriesTable.find("tr td:nth-child(3)");
            agencyURLs = entriesTable.find("tr td:nth-child(1) a");
        }

        // Verify that entry is unique
        for (var i = 0; i < awardNumbers.length; i++) {
            awardNumbers[i] = $(awardNumbers[i]).text().trim();
            agencyNames[i] = $(agencyNames[i]).text().trim();
            awardTitles[i] = $(awardTitles[i]).text().trim();
            agencyURLs[i] = ($(agencyURLs[i]).attr("href") != null ? $(agencyURLs[i]).attr("href") : "" );
            if (awardNumbers[i] == awardNumber && agencyNames[i] == agencyName && awardTitles[i] == awardTitle && agencyURLs[i] == agencyURL) {
                return false;
            }
        }

        return true;
    }

    function validateFundingAgency() {
        $(this).closest("form").find(".modal-body").find(".error-label").remove();

        var awardNumber = $(this).closest("form").find("input[name='award_number']").val();
        var agencyName = $(this).closest("form").find("input[name='agency_name']").val();
        var awardTitle = $(this).closest("form").find("input[name='award_title']").val();
        var agencyURL = $(this).closest("form").find("input[name='agency_url']").val();

        var index = $(this).attr("data-index");

        if (!flagUnique(index, awardNumber, agencyName, awardTitle, agencyURL)) {
            $(this).closest("form").find(".modal-body").append(errorLabel("This entry already exists."));
            return false;
        }
    }

    $(".btn-save-funding-agency").click(validateFundingAgency);
});