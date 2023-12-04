let fundingAgenciesApp = new Vue({
    el: '#add-agency-app',
    delimiters: ['${', '}'],
    components: {
        VueBootstrapTypeahead
    },
    data: {
        newAgency: '',
        fundingAgencies: RES_FUNDING_AGENCIES, // global constant defined in parent template of subject template
        showIsDuplicate: false,
        error: '',
    },
    mounted() {
        console.log(this.fundingAgencies)
        // Until Django / VueJS cleaned up across RLP wait for VueJS state to finalize before trying to display dynamic elements
        document.getElementById('agency-inline-error').style.display = "block";
        document.getElementById('agency-tags').style.display = "block";
    },
    methods: {
        addAgency: function (resIdShort) {
            this.showIsDuplicate = false;  // Reset
            
            // Remove any empty funders from the list
            let newAgencies = this.newAgency.split(",");
            newAgencies = newAgencies.filter(function(a) {
               return a.trim() !== "";
            });

            // Update to cleaned up string
            this.newAgency = newAgencies.join(",").trim();

            if (this.newAgency.trim() === "") {
                return; // Empty string detected
            }else if (this.newAgency.length > 100) {
                this.error = "Your funder is too long. Ensure it has at most 100 characters.";
                return;
            }

            let newVal =  (this.fundingAgencies.join(",").length ? this.fundingAgencies.join(",") + ",": "") + this.newAgency;
            this.error = "";
            let vue = this;
            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/", {value: newVal}, function (resp) {
                if (resp.status === "success") {
                    // Append new funders to our data array
                    let newAgenciesArray = this.newAgency.trim().split(",");

                    for (let i = 0; i < newAgenciesArray.length; i++) {
                        if ($.inArray(newAgenciesArray[i].trim(), this.fundingAgencies) >= 0) {
                            this.showIsDuplicate = true;
                        }
                        else {
                            this.fundingAgencies.push(newAgenciesArray[i].trim());
                            this.$refs.newAgency.inputValue = "";  // open source bug https://github.com/alexurquhart/vue-bootstrap-typeahead/issues/19
                            this.$data.newAgency = ""
                        }
                    }
                }
                else {
                    vue.error = resp.message.slice(0, -1);
                }
                showCompletedMessage(resp);
            }.bind(this), "json");
        },
        removeAgency: function (resIdShort, agencyName) {
            let newVal = this.fundingAgencies.slice(); // Get a copy
            newVal.splice($.inArray(agencyName, this.fundingAgencies), 1);   // Remove the funder

            let vue = this;
            vue.error = "";

            $.post("/hsapi/_internal/" + resIdShort + "/subject/add-metadata/",
                {value: newVal.join(",")}, function (resp) {
                    if (resp.status === "success") {
                        vue.fundingAgencies = newVal;
                        if (!newVal.length) {
                            // If no funders, the metadata is no longer sufficient to make the resource public
                            manageAccessApp.onMetadataInsufficient();
                        }
                    }
                    else {
                        if (vue.fundingAgencies.length){
                            // vue.error = resp.message;
                            // Response message is not very user-friendly so:
                            vue.error = "There was a problem removing your funder.";
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
