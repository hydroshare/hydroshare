let aggrFilesToSyncDiv = $("#aggr-files-to-sync");
aggrFilesToSyncDiv.hide();
if (CAN_CHANGE && !RESOURCE_PUBLISHED_OR_UNDER_REVIEW) {
    let url = "/hsapi/_internal/" + SHORT_ID + "/aggregation-files-to-sync/";

    $.ajax({
        type: "GET",
        url: url,
        dataType: 'json',
        data: {},
        async: true,
        success: function (result) {
            result = JSON.stringify(result);
            let json_response = JSON.parse(result);
            if (json_response.status === "SUCCESS") {
                let ncFiles = json_response.files_to_sync["nc_files"];
                let tsFiles = json_response.files_to_sync["ts_files"];
                let modalBody;
                if (ncFiles.length || tsFiles.length) {
                    aggrFilesToSyncDiv.show();
                    modalBody = aggrFilesToSyncDiv.find(".modal-body");
                }
                if (ncFiles.length) {
                    let aggrHeading = document.createElement("P");
                    let aggrHeadingText = document.createTextNode("Multidimensional Content type files:");
                    aggrHeading.appendChild(aggrHeadingText);
                    modalBody.append(aggrHeading);
                    let list = document.createElement("UL");
                    for (let i = 0; i < ncFiles.length; i++) {
                        let listItem = document.createElement("LI");
                        let code = document.createElement("CODE");
                        code.classList.add("path-align");
                        let itemText = document.createTextNode(ncFiles[i]);
                        code.appendChild(itemText);
                        listItem.appendChild(code);
                        list.appendChild(listItem);
                    }
                    modalBody.append(list);
                }
                if (tsFiles.length) {
                    let aggrHeading = document.createElement("P");
                    let aggrHeadingText = document.createTextNode("Time Series Content type files:");
                    aggrHeading.appendChild(aggrHeadingText);
                    modalBody.append(aggrHeading);
                    let list = document.createElement("UL");
                    for (let i = 0; i < tsFiles.length; i++) {
                        let listItem = document.createElement("LI");
                        let code = document.createElement("CODE");
                        code.classList.add("path-align");
                        let itemText = document.createTextNode(tsFiles[i]);
                        code.appendChild(itemText);
                        listItem.appendChild(code);
                        list.appendChild(listItem);
                    }
                    modalBody.append(list);
                }
            } else if (json_response.status === "ERROR") {
                console.log(json_response.error);
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            aggrFilesToSyncDiv.hide();
            console.error(textStatus, errorThrown);
        }
    });
}
else {
   aggrFilesToSyncDiv.hide();
}
