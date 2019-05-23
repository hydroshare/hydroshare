// Define a new component called button-counter
Vue.component('profile-link', {
    delimiters: ['${', '}'],
    data: function () {
        return {
            user: {
                user_type: "initial",
                access: "initial",
                id: "initial",
                pictureUrl: "initial",
                best_name: "initial",
                user_name: "initial",
                can_undo: "initial",
                email: "initial",
                organization: "initial",
                title: "initial",
                contributions: "initial",
                subject_areas: ["one", "two", "three"],
                identifiers: [],
                state: "initial",
                joined: "initial",
            }
        }
    },
    template: '<a @click="showProfileCard(user)" data-toggle="dropdown" href="#">${user.best_name}</a>',
    methods: {
        showProfileCard: function (user) {
            console.log(user);
        }
    }
});

Vue.component('profile-card', {
    delimiters: ['${', '}'],
    data: function () {
        return {
            user: {
                user_type: "initial",
                access: "initial",
                id: "initial",
                pictureUrl: "initial",
                best_name: "initial",
                user_name: "initial",
                can_undo: "initial",
                email: "initial",
                organization: "initial",
                title: "initial",
                contributions: "initial",
                subject_areas: ["one", "two", "three"],
                identifiers: [],
                state: "initial",
                joined: "initial",
            }
        }
    },
    template: '#profile-card-template',
    methods: {
        showProfileCard: function (user) {
            console.log(user);
        }
    }
});

   // data-name="{{ user|best_name }}"
   // data-email="{{ user.email }}"
   // data-organization="{{ user.userprofile.organization|default:"" }}"
   // data-title="{{ user.userprofile.title|default:"" }}"
   // data-contributions="{{ user.uaccess.owned_resources.count|default:"" }}"
   // data-subjectareas="{{ user.userprofile.subject_areas|default:"" }}"
   //      {% for name, link in user.userprofile.identifiers.items %}
   // data-{{ name }}="{{ link }}"
   //      {% endfor %}
   // data-state="{{ user.userprofile.state|default:"" }}" data-country="{{ user.userprofile.country|default:"" }}"
   // data-joined="{{ user.date_joined|date:"M d, Y" }}"
   //      {% if user.userprofile.picture %}
   // data-profile-picture="{{ user.userprofile.picture.url }}"
   //      {% endif %}
   // data-profile-url="/user/{{ user.id }}">
   //  {{ user|best_name }}