import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import Search from './components/Search.vue';

Vue.use(BootstrapVue);

new Vue({
  render: h => h(Search),
}).$mount('#app');
