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
                    let modalBody = missingMetadataDiv.find(".modal-body");
                    modalBody.empty();

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
                        modalBody.append(outerUl);
                    }
                    missingMetadataDiv.show();
                } else {
                    missingMetadataDiv.hide();
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
