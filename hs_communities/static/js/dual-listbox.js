var TitleAssistantApp = new Vue({
    el: "#title-assistant",
    data: {
        title: '',
        regionSelected: '',
        subtopic: '',
        startYear: '',
        endYear: '',
        yearOngoing: '',
        location: '',
        errmsg: '',  // Inline feedback for the user in red
        topics: {
            itemsList: [], // hold the master list of topics relayed by the HTML template
            unselectedItems: [],
            selectedItems: [],
            selectedValues: ''
        },
        startYearParen: '',  // Paren items are for special display, requested by the customer to appear that way
        endYearParen: ''
    },
    methods: {
        evalParenFields: function () {  // Parenthetical fields are specified by customer to be surrounded by parentheses
            if (this.$data.startYear) {
                this.$data.startYearParen = "(" + this.$data.startYear
            } else {
                this.$data.startYearParen = ""
            }
            if (this.$data.endYear) {
                this.$data.endYearParen = this.$data.endYear + ")"
            } else {
                this.$data.endYearParen = ""
            }
        },
        itemMoved: function () {  // User has selected some topics so concat them with commas for display
            this.$data.topics.selectedValues = this.$data.topics.selectedItems.map(x => x.value).join(', ');
            this.updateTitle()
        },
        checkOngoing: function () {  // Checking Ongoing box indicates End Year contains the string Ongoing
            this.$data.endYear = this.$data.yearOngoing;
            this.updateTitle()
        },
        updateRegion: function () {
            this.updateTitle(items.join(','))
        },
        updateEndDate: function () {
            $("#end-date-ongoing").prop("checked", false);
            this.updateDate()
        },
        updateDate: function () {
            if (isValidYear(this.$data.startYear) && isValidYear(this.$data.endYear)) {
                this.$data.errmsg = "";
                this.updateTitle()
            } else {
                this.$data.errmsg = "Year entry is not valid"
            }
        },
        updateTitle: function () {  // Collect all the items and show in the readonly top live title display
            this.evalParenFields();
            let titleBuilder = '';
            let items = [this.$data.regionSelected, this.$data.topics.selectedValues, this.$data.subtopic, this.$data.location, this.$data.startYearParen, this.$data.endYearParen];

            this.$data.errmsg = '';
            let i = 0;
            items.forEach(function (item) {
                if (item) {
                    if (String(item).includes("(") && !String(item).includes(")")) {  // more customer formatting requirements
                        titleBuilder = titleBuilder + String(item) + '-'
                    } else {
                        titleBuilder = titleBuilder + String(item) + ' -- '
                    }
                    i++
                }
            });
            if (titleBuilder.endsWith(' -- ')) {
                titleBuilder = titleBuilder.substring(0, titleBuilder.length - 2);
            }
            if (titleBuilder.endsWith('-')) {
                titleBuilder = titleBuilder.substring(0, titleBuilder.length - 1);
            }

            this.$data.title = titleBuilder.trim()
        },
        saveTitle: function () {
            if (this.valid()) {
                this.$data.errmsg = '';

                $("#txt-title").val(this.$data.title);
                $("#txt-title").trigger("change");
                $("#title-save-button").trigger("click");
                $("#title-modal").modal('hide');
            }
        },
        valid: function () {
            let isValid = false;
            let validYears = (isValidYear(this.$data.startYear) && isValidYear(this.$data.endYear));
            validYears = validYears && this.$data.startYear.length === 4;
            if (validYears && this.$data.regionSelected && this.$data.topics.selectedValues && this.$data.location && this.$data.startYearParen && this.$data.endYearParen) {
                isValid = true
            }

            if (!isValid) {
                this.$data.errmsg = "Must make a valid selection for all components"
            }

            if (this.subtopic.includes("--") || this.location.includes("--")) {
                this.$data.errmsg = "Entries may not contain a double hyphen";
                isValid = false;
            }
            return isValid
        }
    }
});

function isValidYear(n) {
    if (n.length === 0 || n === "Ongoing") {
        return true
    } else {
        let validYear = (!isNaN(parseFloat(n)) && isFinite(n));
        return validYear && n.length <= 4
    }
}

// When a CZO User clicks on the Resource Title show the Title Assistant modal and prepopulate UI
function titleClick() {
    (function () {
        /*
        Optional text might be provided, affecting the Array index of what is stored

        0: CZO selection
        1: Topics
        2: Optional text (or Location)
        3: Location (or Dates if Optional text was provided in 2)
        4: Dates (if Optional text was provided in 2)
        */
        let sections = $("#txt-title").val().split(" -- ");
        let topics;
        let yearsSection;

        if (!this.$data.title) {  // don't repopulate modal if user never browsed away; UI will already contain previous selections
            if (sections.length === 5) { // title contains optional subtopic
                this.$data.regionSelected = sections[0];
                topics = sections[1].split(",");
                this.$data.subtopic = sections[2];
                this.$data.location = sections[3];
                yearsSection = sections[4]
            } else if (sections.length === 4) {
                this.$data.regionSelected = sections[0];
                topics = sections[1].split(",");
                this.$data.location = sections[2];
                yearsSection = sections[3];
            }

            if (sections.length === 4 || sections.length === 5) {  // only 4 or 5 sections accepted; no other quantity is valid
                topics.forEach(function (topic) {
                    this.$data.topics.selectedItems.push({value: topic.trim(), displayValue: topic.trim(), isSelected: false});
                }.bind(this));

                yearsSection = yearsSection.substring(1, yearsSection.length - 1).split("-");
                this.$data.startYear = yearsSection[0];
                this.$data.endYear = yearsSection[1];
                if (this.$data.endYear === "Ongoing") {
                    $("#end-date-ongoing").prop("checked", true)
                }
                this.itemMoved();
            }
        }
        if (!this.subtopic) {
            this.$data.subtopic = 'clear';
            this.$data.subtopic = '';
        }
        $("#title-modal").modal('show');
    }.bind(TitleAssistantApp)());
}

topics_from_page.forEach(function (item) {  // topics is made available in the Django template, by passing serialized JSON data
    TitleAssistantApp.$data.topics.itemsList.push({value: item, displayValue: item, isSelected: false});
});
