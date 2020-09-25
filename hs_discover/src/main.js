import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import Search from './components/Search.vue';

Vue.config.devtools = true;
Vue.use(BootstrapVue);
Vue.prototype.mapTest = window.mapTest;

new Vue({
  render: h => h(Search),
}).$mount('#app');
