Vue.component('profile-link', {
    delimiters: ['${', '}'],
    template: '#profile-link-template',
    props: {
        user: {
            type: Object, required: true
        }
    }
});

Vue.component('profile-card', {
    delimiters: ['${', '}'],
    props: {
        user: {
            type: Object, required: true
        },
        position: {
            type: Object,
            default: {top: 0, left: 0}
        }
    },
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
});