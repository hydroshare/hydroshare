/**
* Created by Mauriel on 5/19/2019.
*/
let subjKeywordsApp = new Vue({
    el: '#app-keyword',
    components: {
        VueBootstrapTypeahead
    },
    delimiters: ['${', '}'],
    data: {
        newKeyword: '',
        resMode: RESOURCE_MODE,
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
            this.error = "";
            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/", {value: newVal}, function (resp) {
                if (resp.status === "success") {
                    // Append new keywords to our data array
                    let newKeywordsArray = this.newKeyword.trim().split(",");

                    this.showIsDuplicate = false;  // Reset
                    for (let i = 0; i < newKeywordsArray.length; i++) {
                        if ($.inArray(newKeywordsArray[i].trim(), this.resKeywords) >= 0) {
                            this.showIsDuplicate = true;
                        }
                        else {
                            this.resKeywords.push(newKeywordsArray[i].trim());
                            this.$refs.newKeyword.inputValue = "";  // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
                            this.$data.newKeyword = ""
                        }
                    }
                    // Reset input
                    // console.log(this.$data.newKeyword);
                    // this.$data.newKeyword = "";
                    // console.log(this.$data.newKeyword);
                }
                else {
                    this.error = resp.message;
                    console.log(resp);
                }
                showCompletedMessage(resp);
            }.bind(this), "json");
        },
        removeKeyword: function (resIdShort, keywordName) {
            // TODO this feels sluggish in the UI. Consider removing in VueJS then handling the database. In the event of a failure, simply log. UX will be that keyword reappeared (rare case of failure or losing db conn)
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