import Vue from 'vue';
import Router from 'vue-router';
import Search from './components/Search.vue'
import Resources from './components/Resources.vue'

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
        {
            path: '/resources',
            name: 'Resources',
            component: Resources,
        }
    ],
});
