// import 'bootstrap/dist/css/bootstrap.css';
// import 'bootstrap-vue/dist/bootstrap-vue.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import Resource from './components/Resource.vue';

Vue.config.devtools = true;
Vue.use(BootstrapVue);

new Vue({
  render: h => h(Resource),
}).$mount('#app');
