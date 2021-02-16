/**
* Created by Mauriel on 5/19/2019.
*/
let subjKeywordsApp = new Vue({
    el: '#app-keyword',
    components: {
        VueBootstrapTypeahead
    },
    data: {
        newKeyword: '',
        resMode: RESOURCE_MODE,
        resKeywords: RES_KEYWORDS, // global constant defined in parent template of subject template
        showIsDuplicate: false,
        error: '',
    },
    mounted() {
        // Until Django / VueJS cleaned up across RLP wait for VueJS state to finalize before trying to display dynamic elements
        document.getElementById('subj-inline-error').style.display = "block";
        document.getElementById('lst-tags').style.display = "block";
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
                }
                else {
                    this.error = resp.message;
                }
                showCompletedMessage(resp);
            }.bind(this), "json");
        },
        removeKeyword: function (resIdShort, keywordName) {
            let newVal = this.resKeywords.slice(); // Get a copy
            newVal.splice($.inArray(keywordName, this.resKeywords), 1);   // Remove the keyword

            this.error = "";

            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/",
                {value: newVal.join(",")}, function (resp) {
                    if (resp.status === "success") {
                        this.resKeywords = newVal;
                        if (!newVal.length) {
                            // If no keywords, the metadata is no longer sufficient to make the resource public
                            manageAccessApp.onMetadataInsufficient();
                        }
                    }
                    else {
                        if (this.resKeywords.length){
                            this.error = this.message;
                        }
                    }
                }.bind(this), "json");
        },
        safeJS: function (input) {
            input.replace("\\", "\\\\")
            return encodeURIComponent(input)
        }
    }
});
