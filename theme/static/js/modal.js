Vue.component('modal', {
    template: '#modal-template'
});

ModalApp = new Vue({
    el: '#title-builder-app',
    data : {
        showModal: false,
        selected: 'none',
    },
    methods: {
        updateInput() {
            $("#txt-title").val(this.$data.selected)
        }
    }
});

function titleClick() {
    ModalApp.$data.showModal = true
}
