let missingMetadataDiv = $("#missing-metadata-file-type-container");
let checkingMissingMetadataDiv = $("#checking-missing-metadata");

missingMetadataDiv.hide();

if (!checkingMissingMetadataDiv.length || !missingMetadataDiv.length || !SHORT_ID) {
    checkingMissingMetadataDiv.hide();
} else {
    let missingMetadataUrl = "/hsapi/_internal/" + SHORT_ID + "/missing-file-type-metadata/";

    $.ajax({
        type: "GET",
        url: missingMetadataUrl,
        dataType: "json",
        data: {},
        async: true,
        success: function (result) {
            checkingMissingMetadataDiv.hide();
            result = JSON.stringify(result);
            let jsonResponse = JSON.parse(result);
            if (jsonResponse.status === "SUCCESS") {
                if (jsonResponse.file_type_missing_metadata.length) {
                    let alert = document.createElement("DIV");
                    alert.className = "alert alert-warning alert-dismissible";
                    alert.setAttribute("role", "alert");

                    let closeBtn = document.createElement("BUTTON");
                    closeBtn.type = "button";
                    closeBtn.className = "close";
                    closeBtn.setAttribute("data-dismiss", "alert");
                    closeBtn.setAttribute("aria-label", "Close");
                    closeBtn.innerHTML = '<span aria-hidden="true">&times;</span>';
                    alert.appendChild(closeBtn);

                    let introText = document.createElement("SPAN");
                    introText.textContent = "The following content type metadata are still required to make this resource public or discoverable:";
                    alert.appendChild(introText);

                    for (let i = 0; i < jsonResponse.file_type_missing_metadata.length; i++) {
                        let item = jsonResponse.file_type_missing_metadata[i];
                        let outerUl = document.createElement("UL");
                        let outerLi = document.createElement("LI");
                        outerLi.appendChild(document.createTextNode("Content type name: " + item.file_path));

                        let innerUl = document.createElement("UL");
                        for (let j = 0; j < item.missing_elements.length; j++) {
                            let innerLi = document.createElement("LI");
                            innerLi.appendChild(document.createTextNode(item.missing_elements[j]));
                            innerUl.appendChild(innerLi);
                        }

                        outerLi.appendChild(innerUl);
                        outerUl.appendChild(outerLi);
                        alert.appendChild(outerUl);
                    }

                    if (RESOURCE_MODE !== "Edit") {
                        let divider = document.createElement("HR");
                        alert.appendChild(divider);

                        let icon = document.createElement("SPAN");
                        icon.className = "glyphicon glyphicon-question-sign";
                        alert.appendChild(icon);

                        let helpText = document.createElement("SMALL");
                        helpText.innerHTML = ' Click on the edit button ( <span class="glyphicon glyphicon-pencil"></span> ) below to edit this resource.';
                        alert.appendChild(helpText);
                    }

                    missingMetadataDiv.empty();
                    missingMetadataDiv.append(alert);
                    missingMetadataDiv.show();
                }
            } else if (jsonResponse.status === "ERROR") {
                console.log(jsonResponse.error);
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            checkingMissingMetadataDiv.hide();
            missingMetadataDiv.hide();
            console.error(textStatus, errorThrown);
        }
    });
}
