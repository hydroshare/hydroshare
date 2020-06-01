import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
// import App from './App.vue';
// import router from './router';
import Search from './components/Search.vue';

Vue.use(BootstrapVue)

new Vue({
    render: h =>h (Search),
}).$mount('#app');
