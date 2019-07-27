/**
* Created by Mauriel on 5/19/2019.
*/

let relevantToolsApp = new Vue({
    el: '#apps-dropdown',
    delimiters: ['${', '}'],
    data: {
        tools: [],
        resId: SHORT_ID,
        isLoading: true,
    },
    mounted: function () {
        let vue = this;
        $.get("/hsapi/_internal/" + this.resId + "/relevant-tools/", function (response) {
            response = JSON.parse(response);
            vue.tools = response['tool_list'].map(function(tool) {
                tool.url = encodeURIComponent(tool.url); // We need to encode special characters
                return tool;
            });
            vue.isLoading = false;
        });
    }
});