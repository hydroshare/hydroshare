Vue.component('modal', {
  template: '#modal-template'
});

ModalApp = new Vue({
  el: '#modal-app',
  data: {
    showModal: false
  }
});

function titleClick() {
    ModalApp.$data.showModal = true
}