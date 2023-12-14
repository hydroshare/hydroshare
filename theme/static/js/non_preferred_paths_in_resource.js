let nonPreferredPathDiv = $("#non-preferred-paths");
nonPreferredPathDiv.hide();
if (CAN_CHANGE && !RESOURCE_PUBLISHED_OR_UNDER_REVIEW) {
    let url = "/hsapi/_internal/" + SHORT_ID + "/non-preferred-paths/";

    $.ajax({
        type: "GET",
        url: url,
        dataType: 'json',
        data: {},
        async: true,
        success: function (result) {
            $("#checking-for-paths").hide();
            result = JSON.stringify(result);
            let json_response = JSON.parse(result);
            if (json_response.status === "SUCCESS") {
                if (json_response.non_preferred_paths.length) {
                    nonPreferredPathDiv.show();
                    let modalBody = nonPreferredPathDiv.find(".modal-body");
                    let list = document.createElement("UL");
                    for (let i = 0; i < json_response.non_preferred_paths.length; i++) {
                        let listItem = document.createElement("LI");
                        let code = document.createElement("CODE");
                        code.classList.add("path-align");
                        let itemText = document.createTextNode(json_response.non_preferred_paths[i]);
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
            $("#checking-for-paths").hide();
            nonPreferredPathDiv.hide();
            console.error(textStatus, errorThrown);
        }
    });
}
else {
   $("#checking-for-paths").hide();
   nonPreferredPathDiv.hide();
}