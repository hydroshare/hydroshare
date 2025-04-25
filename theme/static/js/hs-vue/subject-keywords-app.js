/**
* Created by Mauriel on 5/19/2019.
*/
let subjKeywordsApp = new Vue({
    el: '#app-keyword',
    delimiters: ['${', '}'],
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
        onKeywordInput: function (event) {
            let newKWLength =  this.newKeywordsLength();
            if(newKWLength > 500){
                this.newKeyword = this.newKeyword.slice(0, -1);
                event.preventDefault();
                this.error = `The character limit for the subject keywords field is 500 characters, you have currently added ${newKWLength}. Please reduce keywords to below the character limit`;
            }else if(this.error != '' || newKWLength == 0){
                this.error = '';
            }
        },
        addKeyword: function (resIdShort) {
            if(this.newKeywordsLength() > 500){
                return;
            }

            this.showIsDuplicate = false;  // Reset
            
            // Remove any empty keywords from the list
            let newKeywords = this.newKeyword.split(",");
            newKeywords = newKeywords.filter(function(a) {
               return a.trim() !== "";
            });

            // Update to cleaned up string
            this.newKeyword = newKeywords.join(",").trim();

            if (this.newKeyword.trim() === "") {
                return; // Empty string detected
            }else if (this.newKeyword.length > 100) {
                this.error = "Your keyword is too long. Ensure it has at most 100 characters.";
                return;
            }

            let newVal =  (this.resKeywords.join(",").length ? this.resKeywords.join(",") + ",": "") + this.newKeyword;
            this.error = "";
            let vue = this;
            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/", {value: newVal}, function (resp) {
                if (resp.status === "success") {
                    // Append new keywords to our data array
                    let newKeywordsArray = this.newKeyword.trim().split(",");

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
                    vue.error = resp.message.slice(0, -1);
                }
                showCompletedMessage(resp);
            }.bind(this), "json");
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
                        if (vue.resKeywords.length){
                            // vue.error = resp.message;
                            // Response message is not very user-friendly so:
                            vue.error = "There was a problem removing your keyword.";
                        }
                    }
                }.bind(this), "json");
        },
        safeJS: function (input) {
            input.replace("\\", "\\\\")
            return encodeURIComponent(input)
        },
        newKeywordsLength: function () {
            let newVal =  this.resKeywords.join("") + this.newKeyword.split(",").join("");
            return newVal.length;
        }
    }
});
