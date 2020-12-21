// import 'bootstrap/dist/css/bootstrap.css'; moved to resource.vue
// import 'bootstrap-vue/dist/bootstrap-vue.css'; moved to resource.vue
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import Resource from './components/Resource.vue';

Vue.config.devtools = true;
Vue.use(BootstrapVue);

new Vue({
  render: h => h(Resource),
}).$mount('#app');
