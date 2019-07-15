var TitleAssistantApp = new Vue({
    el: "#title-assistant",
    data: {
        title: '',
        regionSelected: '',
        subtopic: '',
        topics: {
            itemsList: [],
            unselectedItems: [],
            selectedItems: [],
            selectedValues: ''
        },
    },
    methods: {
        itemMoved: function () {
            // ES6 - let's discuss:
            this.$data.topics.selectedValues = this.$data.topics.selectedItems.map(x => x.value).join(', ');
            this.updateTitle()
        },
        updateRegion: function() {
            console.log("Updating input on region select");
            this.updateTitle(items.join(','))
        },
        updateTitle: function() {
            this.$data.title = (String(this.$data.regionSelected) + " " + String(this.$data.topics.selectedValues) + " " + String(this.$data.subtopic)).trim()
        },
        saveTitle: function() {
            $("#txt-title").val(this.$data.title);
            $("#txt-title").trigger( "change" );
            $("#title-save-button").trigger("click");
            $("#title-modal").modal('hide');
        }
    }
});

function titleClick() {
    if ($("#txt-title").val() === 'Untitled resource') {
        $("#title-modal").modal('show');
        topics_from_page.forEach(function (item) {  //topics is made available in the Django template, by passing serialized JSON data
            this.$data.topics.unselectedItems.push({value: item, displayValue: item, isSelected: false});
            this.$data.topics.itemsList.push({value: item, displayValue: item, isSelected: false})
        }.bind(TitleAssistantApp));
    }
}
