var TitleAssistantApp = new Vue({
    el: "#title-assistant",
    computed: {
        startyears() {
            const year = new Date().getFullYear();
            let numericalYears = Array.from({length: year - 1900}, (value, index) => 1901 + index);
            return numericalYears.reverse()
        },
        endyears() {
            const year = new Date().getFullYear();
            let numericalYears = Array.from({length: year - 1900}, (value, index) => 1901 + index);
            numericalYears.push('Ongoing');
            return numericalYears.reverse()
        }
    },
    data: {
        title: '',
        regionSelected: '',
        subtopic: '',
        startYear: '',
        endYear: '',
        errmsg: '',
        topics: {
            itemsList: [],
            unselectedItems: [],
            selectedItems: [],
            selectedValues: ''
        },
    },
    methods: {
        itemMoved: function () {
            this.$data.topics.selectedValues = this.$data.topics.selectedItems.map(x => x.value).join(', ');
            this.updateTitle()
        },
        updateRegion: function () {
            console.log("Updating input on region select");
            this.updateTitle(items.join(','))
        },
        updateTitle: function() {
            this.$data.title = (String(this.$data.regionSelected) + " " + String(this.$data.topics.selectedValues) + " " + String(this.$data.subtopic)) + " (" + String(this.$data.startYear) + " - " + String(this.$data.endYear) + ")".trim()
            this.$data.errmsg = ''
        },
        saveTitle: function () {  // TODO make more robust to select/deselect or clear out items or leaving whitespace and also add the reset of the items to the if statement (date and such)
            if (this.$data.title === '' || this.$data.regionSelected === '' || this.$data.subtopic === '') {
                this.$data.errmsg = "Error: All items must be selected";
            } else {
                $("#txt-title").val(this.$data.title);
                $("#txt-title").trigger("change");
                $("#title-save-button").trigger("click");
                $("#title-modal").modal('hide');
            }
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
