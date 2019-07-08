var TitleAssistantApp = new Vue({
    el: "#title-assistant",
    data: {
        title: '',
        regionSelected: '',
        subtopic: '',
        topics: {
            unselectedItems: [],
            selectedItems: [],
            selectedValues: ''
        }
    },
    mounted() {
        topics_from_page.forEach(function(item) {  //topics is made available in the Django template, by passing serialized JSON data
            this.$data.topics.unselectedItems.push({value: item, displayValue: item, isSelected: false})
        }.bind(this))
    },
    methods: {
        itemMoved: function (itemInfo) {
            // let item = itemInfo.Item;
            // let targetList = itemInfo.targetList;
            let items = [];
            this.$data.topics.selectedItems.forEach(function(item){
                items.push(item.value);
            });
            this.$data.topics.selectedValues = items.join(',');
            this.updateTitle()
        },
        updateRegion: function () {
            console.log("Updating input on region select");
            this.updateTitle(items.join(','))
        },
        updateTitle: function() {
            this.$data.title = String(this.$data.regionSelected) + String(this.$data.subtopic) + String(this.$data.topics.selectedValues)
        }
    }
});