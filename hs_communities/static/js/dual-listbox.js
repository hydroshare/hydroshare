var TitleAssistantApp = new Vue({
    el: "#title-assistant",
    data: {
        regionSelected: 'none',
        vm: {
            unselectedItems: [],
            selectedItems: []
        }
    },
    mounted() {
        topics.forEach( function(item) {  //topics is made available in the Django template, by passing serialized JSON data
            this.$data.vm.unselectedItems.push({value: item, displayValue: item, isSelected: false})
        }.bind(this))
    },
    methods: {
        saveItems: function () {
            let s = "";
            for (let i = 0; i < this.$data.vm.selectedItems.length; i++) {
                let element = this.$data.vm.selectedItems[i];
                s += element.displayValue + "\r\n";
            }
            alert('ready to save ' + this.$data.vm.selectedItems.length + ' items from Top Mover.\r\n' + s);
        },
        itemMoved: function (itemInfo) {
            let item = itemInfo.Item;
            let targetList = itemInfo.targetList;
            console.log("Item moved to the " + itemInfo.listType, itemInfo);
        },
        updateRegion: function () {
            console.log("Updating input on region select")
        }
    }
});