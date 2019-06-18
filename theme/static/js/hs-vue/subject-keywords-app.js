/**
* Created by Mauriel on 5/19/2019.
*/

let subjKeywordsApp = new Vue({
    el: '#app-keyword',
    delimiters: ['${', '}'],
    data: {
        newKeyword: '',
        resKeywords: RES_KEYWORDS,   // global constant defined in template
        showIsDuplicate: false,
        error: ''
    },
    methods: {
        addKeyword: function (resIdShort) {
            // Remove any empty keywords from the list
            let newKeywords = this.newKeyword.split(",");
            newKeywords = newKeywords.filter(function(a) {
               return a.trim() !== "";
            });

            // Update to cleaned up string
            this.newKeyword = newKeywords.join(",").trim();

            if (this.newKeyword.trim() === "") {
                return; // Empty string detected
            }

            let newVal =  (this.resKeywords.join(",").length ? this.resKeywords.join(",") + ",": "") + this.newKeyword;
            let vue = this;
            vue.error = "";

            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/", {value: newVal}, function (resp) {
                if (resp.status === "success") {
                    // Append new keywords to our data array
                    let newKeywordsArray = vue.newKeyword.trim().split(",");

                    vue.showIsDuplicate = false;  // Reset
                    for (var i = 0; i < newKeywordsArray.length; i++) {
                        if ($.inArray(newKeywordsArray[i].trim(), vue.resKeywords) >= 0) {
                            vue.showIsDuplicate = true;
                        }
                        else {
                            vue.resKeywords.push(newKeywordsArray[i].trim());
                        }
                    }

                    // Reset input
                    vue.newKeyword = '';
                }
                else {
                    vue.error = resp.message;
                    console.log(resp);
                }
                showCompletedMessage(resp);
            }, "json");
        },
        removeKeyword: function (resIdShort, keywordName) {
            let newVal = this.resKeywords.slice(); // Get a copy
            newVal.splice($.inArray(keywordName, this.resKeywords), 1);   // Remove the keyword

            let vue = this;
            vue.error = "";

            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/",
                {value: newVal.join(",")}, function (resp) {
                    if (resp.status === "success") {
                        vue.resKeywords = newVal;
                        if (!newVal.length) {
                            // If no keywords, the metadata is no longer sufficient to make the resource public
                            manageAccessApp.onMetadataInsufficient();
                        }
                    }
                    else {
                        vue.error = resp.message;
                        console.log(resp);
                    }
                }, "json");
        }
    }
});