var TitleAssistantApp = new Vue({
    el: "#title-assistant",
    data: {
        vm: {

            unselectedItems: [
                {
                    value: "vitem1",
                    displayValue: "vItem 1",
                    isSelected: false
                },
                {
                    value: "vitem2",
                    displayValue: "vItem 2",
                    isSelected: true
                },
                {
                    value: "vitem3",
                    displayValue: "vItem 3",
                    isSelected: false
                },
                {
                    value: "vitem4",
                    displayValue: "vItem 4",
                    isSelected: false
                },
                {
                    value: "vitem5",
                    displayValue: "vItem 5",
                    isSelected: false
                },
                {
                    value: "vitem6",
                    displayValue: "vItem 6",
                    isSelected: false
                },
                {
                    value: "vitem7",
                    displayValue: "vItem 7",
                    isSelected: false
                },
                {
                    value: "vitem8",
                    displayValue: "vItem 8",
                    isSelected: false
                },
                {
                    value: "vitem9",
                    displayValue: "vItem 9",
                    isSelected: false
                },
                {
                    value: "vitem10",
                    displayValue: "vItem 10",
                    isSelected: false
                },
                {
                    value: "vitem11",
                    displayValue: "vItem 11",
                    isSelected: false
                },
                {
                    value: "vitem12",
                    displayValue: "vItem 12",
                    isSelected: false
                },
                {
                    value: "vitem13",
                    displayValue: "vItem 13",
                    isSelected: false
                },
                {
                    value: "vitem14",
                    displayValue: "vItem 14",
                    isSelected: false
                }
            ],
            selectedItems: [
                {
                    value: "xitem3",
                    displayValue: "xItem 3",
                    isSelected: false
                },
                {
                    value: "xitem4",
                    displayValue: "xItem 4",
                    isSelected: false
                },
                {
                    value: "vitem5",
                    displayValue: "vItem 5",
                    isSelected: false
                }
            ],
            unselectedItems2: [
                {
                    value: "witem1",
                    displayValue: "wItem 1",
                    isSelected: false
                },
                {
                    value: "witem2",
                    displayValue: "wItem 2",
                    isSelected: false
                },
                {
                    value: "witem3",
                    displayValue: "wItem 3",
                    isSelected: false
                }
            ],
            selectedItems2: [
                {
                    value: "yitem1",
                    displayValue: "yItem 1",
                    isSelected: false
                },
            ],

        }
    },
    methods: {
        saveItems: function () {
            var s = "";
            console.log(this.$data.vm)
            for (var i = 0; i < this.$data.vm.selectedItems.length; i++) {
                var element = this.$data.vm.selectedItems[i];
                s += element.displayValue + "\r\n";
            }
            alert('ready to save ' + this.$data.vm.selectedItems.length + ' items from Top Mover.\r\n' + s);
        },
        itemMoved: function (itemInfo) {
            var item = itemInfo.Item;
            var targetList = itemInfo.targetList;
            console.log("Item moved to the " + itemInfo.listType, itemInfo);
        }
    }
});