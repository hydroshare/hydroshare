import 'bootstrap/dist/css/bootstrap.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
// import App from './App.vue';
// import router from './router';
import Ping from './components/Ping.vue'

Vue.use(BootstrapVue)

new Vue({
    render: h =>h(Ping),
}).$mount('#app');

