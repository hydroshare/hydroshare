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
        updateDate: function () {
            let validYear = false;
            this.updateTitle()
        },
        updateTitle: function () {  // Collect all the items and show in the readonly top live title display
            this.evalParenFields();
            let titleBuilder = '';
            let items = [this.$data.regionSelected, this.$data.topics.selectedValues, this.$data.subtopic, this.$data.location, this.$data.startYearParen, this.$data.endYearParen];

            this.$data.errmsg = '';

            items.forEach(function (item) {
                if (item) {
                    titleBuilder = titleBuilder + String(item) + ' - '
                }
            });
            titleBuilder = titleBuilder.substring(0, titleBuilder.length - 3);

            titleBuilder = titleBuilder.replace(" - (", " (");
            this.$data.title = titleBuilder.trim()
        },
        saveTitle: function () {
            if (this.valid()) {
                this.$data.errmsg = '';

                $("#txt-title").val(this.$data.title);
                $("#txt-title").trigger("change");
                $("#title-save-button").trigger("click");
                $("#title-modal").modal('hide');

            } else {
                this.$data.errmsg = "Error: must make a selection for all components"
            }
        },
        valid: function () {
            let isValid = false;
            if (this.$data.regionSelected && this.$data.topics.selectedValues && this.$data.subtopic && this.$data.locationParen && this.$data.startYearParen && this.$data.endYearParen) {
                isValid = true
            }
            return isValid
        }
    }
});

// When a CZO User clicks on the Resource Title show the Title Assistant modal
function titleClick() {
    $("#title-modal").modal('show');
    topics_from_page.forEach(function (item) {  //topics is made available in the Django template, by passing serialized JSON data
        this.$data.topics.unselectedItems.push({value: item, displayValue: item, isSelected: false});
        this.$data.topics.itemsList.push({value: item, displayValue: item, isSelected: false});
        this.$data.errmsg = ''
    }.bind(TitleAssistantApp));
}
