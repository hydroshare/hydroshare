import Vue from 'vue';
import Router from 'vue-router';
import Search from './components/Search.vue'

Vue.use(Router)

export default new Router({
    mode: 'history',
    base: process.env.BASE_URL,
    routes: [
        {
            path: '/',
            name: 'Search',
            component: Search,
        },
    ],
});
