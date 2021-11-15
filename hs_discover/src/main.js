import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import Search from './components/Search.vue';

Vue.use(BootstrapVue);

function delayPopOutSurvey() {
  const cookie = $.cookie('discover-survey');
  if (!cookie) {
    const delaySeconds = 20;
    const buttonExists = $('.typeform-sidetab-button').length;
    if (buttonExists) {
      setTimeout(
        () => {
          $('.typeform-sidetab-button').click();
        }, delaySeconds * 1000,
      );
    }
  }
}

Vue.prototype.$delayPopOutSurvey = delayPopOutSurvey;

new Vue({
  render: h => h(Search),
}).$mount('#app');
