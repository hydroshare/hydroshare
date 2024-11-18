Vue.component('profile-link', {
    delimiters: ['${', '}'],
    template: '#profile-link-template',
    props: {
        user: { type: Object, required: true },
        showDetails: { type: Boolean, required: false, default: false }
    }
});

Vue.component('profile-card', {
    delimiters: ['${', '}'],
    template: '#profile-card-template',
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
                    title: "ORCID",
                    src: STATIC_URL + "img/orcid.logo.icon.svg",
                },
                ResearchGateID: {
                    classes: "ai ai-researchgate-square hover-shadow",
                    title: "ResearchGate",
                    src: STATIC_URL + "img/researchgate.png"
                },
                ResearcherID: {
                    classes: "ai ai-researcherid-square hover-shadow",
                    title: "ResearcherID",
                    src: STATIC_URL + "img/researcherID.png"
                },
                GoogleScholarID: {
                    classes: "ai ai-google-scholar-square hover-shadow",
                    title: "Google Scholar",
                    src: STATIC_URL + "img/google-scholar.svg"
                }
            },
        }
    }
});