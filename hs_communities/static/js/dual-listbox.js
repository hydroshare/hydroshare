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
        errmsg: '',
        topics: {
            itemsList: [],
            unselectedItems: [],
            selectedItems: [],
            selectedValues: ''
        },
        startYearParen: '',
        endYearParen: '',
        locationParen: ''
    },
    methods: {
        evalParenFields: function () {
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
            if (this.$data.location) {
                this.$data.locationParen = "(" + this.$data.location + ")"
            } else {
                this.$data.locationParen = ""
            }
        },
        itemMoved: function () {
            this.$data.topics.selectedValues = this.$data.topics.selectedItems.map(x => x.value).join(', ');
            this.updateTitle()
        },
        checkOngoing: function () {
            console.log(this.$data.yearOngoing);
            this.$data.endYear = this.$data.yearOngoing;
            this.updateTitle()
        },
        updateRegion: function () {
            console.log("Updating input on region select");
            this.updateTitle(items.join(','))
        },
        updateTitle: function () {
            this.evalParenFields();
            let titleBuilder = '';
            let items = [this.$data.regionSelected, this.$data.topics.selectedValues, this.$data.subtopic, this.$data.locationParen, this.$data.startYearParen, this.$data.endYearParen];

            this.$data.errmsg = '';

            items.forEach(function (item) {
                if (item) {
                    titleBuilder = titleBuilder + String(item) + ' - '
                }
            });
            titleBuilder = titleBuilder.substring(0, titleBuilder.length - 3);

            titleBuilder = titleBuilder.replace(") - (", ") (");
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

function titleClick() {
    $("#title-modal").modal('show');
    topics_from_page.forEach(function (item) {  //topics is made available in the Django template, by passing serialized JSON data
        this.$data.topics.unselectedItems.push({value: item, displayValue: item, isSelected: false});
        this.$data.topics.itemsList.push({value: item, displayValue: item, isSelected: false})
    }.bind(TitleAssistantApp));
}
