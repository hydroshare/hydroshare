Vue.component('profile-link', {
    delimiters: ['${', '}'],
    template: '#profile-link-template',
    props: {user: Object},
    methods: {
        onClick: function () {
            this.$emit('load-card', this.user);
        }
    }
});

Vue.component('profile-card', {
    delimiters: ['${', '}'],
    props: {user: Object},
    computed: {
        hasIdentifiers: function () {
            return !$.isEmptyObject(this.user.identifiers);
        }
    },
    data: function () {
        return {
            identifierAttributes: {
                ORCID: {
                    classes: "ai ai-orcid hover-shadow",
                    title: "ORCID"
                },
                ResearchGateID: {
                    classes: "ai ai-researchgate-square hover-shadow",
                    title: "ResearchGate"
                },
                ResearcherID: {
                    classes: "",
                    title: "ResearcherID"
                },
                GoogleScholarID: {
                    classes: "ai ai-google-scholar-square hover-shadow",
                    title: "Google Scholar"
                }
            },
        }
    },
    template: '#profile-card-template',
    methods: {

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