let TopicsApp = new Vue({
  el: '#app',
  data: {
    numbers: [
        {
            val: 'one',
            edit: false
        },
        {	val: 'two',
         	edit: false
        },
        {
            val: 'three',
            edit: false
        }
    ]
  },
  methods: {
  	toggleEdit: function(ev, num){
  	    Vue.set(num, 'edit', !num.edit);
        this.$data.numbers.forEach(function(item){
            if (item !== num){
                Vue.set(item, 'edit', false)
            }
        })
    },
    saveEdit: function(ev, num){
      	Vue.set(num, 'edit', false);
    }
  }
});