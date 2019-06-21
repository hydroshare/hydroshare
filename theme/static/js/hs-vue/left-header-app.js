Vue.component('edit-author-modal', {
    delimiters: ['${', '}'],
    template: '#edit-author-modal-template',
    props: {
        author: {type: Object, required: true},
        is_person: {type: Boolean, required: true},
        can_remove: {type: Boolean, required: true},
    },
});

let leftHeaderApp = new Vue({
    el: '#left-header',
    delimiters: ['${', '}'],
    data: {
        owners: USERS_JSON.map(function(user) {
            user.loading = false;
            return user;
        }).filter(function(user){
            return user.access === 'owner';
        }),
        res_mode: RESOURCE_MODE,
        resShortId: SHORT_ID,
        can_change: CAN_CHANGE,
        authors: AUTHORS,
        selectedAuthor: {
            author: {
                "id": null,
                "name": null,
                "email": null,
                "organization": null,
                "identifiers": {},
                "address": null,
                "phone": null,
                "homepage": null,
                "profileUrl": null,
                "order": null
            },
            index: null
        },
        editAuthorError: null,
        userCardSelected: {
            user_type: null,
            access: null,
            id: null,
            pictureUrl: null,
            best_name: null,
            user_name: null,
            can_undo: null,
            email: null,
            organization: null,
            title: null,
            contributions: null,
            subject_areas: null,
            identifiers: [],
            state: null,
            country: null,
            joined: null,
        },
        lastChanagedBy: LAST_CHANGED_BY,
        cardPosition: {
            top: 0,
            left: 0,
        }
    },
    computed: {
         // Returns true if the Author object passed originally to selectedAuthor is a Person
        isPerson: function () {
            if (this.selectedAuthor.author.name) {
                return this.selectedAuthor.author.name.trim().length > 0;
            }
            return true;    // default
        },
    },
    methods: {
        onLoadOwnerCard: function(data) {
            let el = $(data.event.target);
            let cardWidth = 350;

            this.userCardSelected = data.user;
            this.cardPosition.left = el.position().left - (cardWidth / 2) + (el.width() / 2);
            this.cardPosition.top = el.position().top + 30;
        },
        deleteAuthor: function () {
            // TODO: change endpoint to return json data
            $.post('/hsapi/_internal/' + this.resShortId + '/creator/' + this.selectedAuthor.author.id +
                '/delete-metadata/', function (result) {
                console.log(result);
            });
        },
        updateAuthor: function(author) {
            let formData = new FormData();
            let vue = this;

            vue.editAuthorError = null;

            formData.append("csrfmiddlewaretoken", csrf_token);
            formData.append("resource-mode", this.res_mode.toLowerCase());
            formData.append("creator-" + author.order + "-name", author.name);
            formData.append("creator-" + author.order + "-order", author.order !== null ? author.order : "");
            // TODO: figure out why sending HydroShare identifier in the request fails
            formData.append("creator-" + author.order + "-description", author.profileUrl !== null ? author.profileUrl : "");
            formData.append("creator-" + author.order + "-organization", author.organization !== null ? author.organization : "");
            formData.append("creator-" + author.order + "-email", author.email !== null ? author.email : "");
            formData.append("creator-" + author.order + "-address", author.address !== null ? author.address : "");
            formData.append("creator-" + author.order + "-phone", author.phone !== null ? author.phone : "");
            formData.append("creator-" + author.order + "-homepage", author.homepage !== null ? author.homepage : "");

            $.ajax({
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                url: '/hsapi/_internal/' + this.resShortId + '/creator/' + author.id + '/update-metadata/',
                success: function (response) {
                    if (response.status === "success") {
                        vue.authors.splice(vue.selectedAuthor.index, 1, author);    // Save changes to the data
                        showCompletedMessage(response);
                        $("#edit-author-modal").modal('hide');
                    }
                    else {
                        vue.editAuthorError = response.message;
                    }
                    console.log(response);
                },
                error: function (response) {
                    vue.editAuthorError = response.message;
                    console.log(response);
                }
            });
        },
        selectAuthor: function(author, index) {
            this.selectedAuthor.author = $.extend(true, {}, author);  // Deep copy
            this.selectedAuthor.index = index;
        }
    }
});