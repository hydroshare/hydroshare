let TopicsApp = new Vue({
        el: '#topics-app',
        data: {
            numbers: []
        },
        mounted() {
            // depends on topics.html making topics available by importing from Django namespace via JSON exchange
            // console.log(this.$data.numbers);
            // console.log(topics)
            topics.forEach(function(topic){
                this.$data.numbers.push({'val': topic, 'edit': false})
            }.bind(this))
        },
        methods:
            {
                toggleEdit: function (ev, num) {
                    Vue.set(num, 'edit', !num.edit);
                    this.$data.numbers.forEach(function (item) {
                        if (item !== num) {
                            Vue.set(item, 'edit', false)
                        }
                    })
                },
                saveEdit: function (ev, num) {
                    Vue.set(num, 'edit', false);
                }
            }
    });
