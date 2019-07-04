Vue.component('edit-author-modal', {
    delimiters: ['${', '}'],
    template: '#edit-author-modal-template',
    props: {
        _author: {type: Object, required: true},
        is_person: {type: Boolean, required: true},
        can_remove: {type: Boolean, required: true},
        is_updating_author: {type: Boolean, required: false},
        is_deleting_author: {type: Boolean, required: false},
    },
    methods: {
        onDeleteIdentifier: function (index) {
            this.author.identifiers.splice(index, 1);
        },
        onAddIdentifier: function() {
            this.author.identifiers.push({
                identifierName: null,
                identifierLink: null
            });
        },
        onDeleteAuthor: function () {
            this.$emit('delete-author');
        },
        onSaveAuthor: function() {
            // Transform the identifier field back into an object
            let author = $.extend(true, {}, this.author);
            let identifiers = {};

            this.author.identifiers.map(function(el) {
                if (el.identifierName && el.identifierLink) {
                    identifiers[el.identifierName] = el.identifierLink;
                }
            });

            author.identifiers = identifiers;
            this.$emit('update-author', author);
        },
        hasIdentifier: function(identifier) {
            let search = this.author.identifiers.filter(function (el) {
                return el.identifierName === identifier;
            });

            return search.length > 0;
        }
    },
    watch: {
        _author: function() {
            let identifiers = [];

            $.each(this._author.identifiers, function (identifierName, identifierLink) {
                identifiers.push({identifierName: identifierName, identifierLink: identifierLink})
            });

            let localAuthor = $.extend(true, {}, this._author);
            localAuthor.identifiers = identifiers;

            this.author = localAuthor;
        }
    },
    data: function () {
        let identifiers = [];

        $.each(this._author.identifiers, function (identifierName, identifierLink) {
            identifiers.push({identifierName: identifierName, identifierLink: identifierLink})
        });

        let localAuthor = $.extend(true, {}, this._author);
        localAuthor.identifiers = identifiers;

        return {
            author: localAuthor,
            identifierDict: {
                ORCID: {
                    title: "ORCID",
                    value: "ORCID"
                },
                ResearchGateID: {
                    title: "ResearchGate",
                    value: "ResearchGateID"
                },
                ResearcherID: {
                    title: "ResearcherID",
                    value: "ResearcherID"
                },
                GoogleScholarID: {
                    title: "Google Scholar",
                    value: "GoogleScholarID"
                }
            },
        }
    }
});

Vue.component('add-author-modal', {
    delimiters: ['${', '}'],
    template: '#add-author-modal-template',
    props: {

    },
    methods: {

    },
    watch: {

    },
    data: function () {
        return {
            userType: 0,
        }
    }
});

Vue.component('author-preview-modal', {
    delimiters: ['${', '}'],
    template: '#author-preview-modal-template',
    props: {
        author: {type: Object, required: true},
        is_person: {type: Boolean, required: true},
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
        isUpdatingAuthor: false,
        editAuthorError: null,
        isDeletingAuthor: false,
        deleteAuthorError: null,
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
            if (this.selectedAuthor.author.name !== null) {
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
            let vue = this;
            vue.isDeletingAuthor = true;
            vue.deleteAuthorError = null;
            $.post('/hsapi/_internal/' + this.resShortId + '/delete-author/' + this.selectedAuthor.author.id +
                '/', function (response) {
                if (response.status === "success") {
                    vue.authors.splice(vue.selectedAuthor.index, 1);    // Remove the author from the list
                    // Update the Order values
                    vue.authors = vue.authors.map(function (item, index) {
                        item.order = index + 1;
                        return item;
                    });

                    // Dismiss the modal
                    $("#edit-author-modal").modal('hide');
                }
                else {
                    vue.deleteAuthorError = response.message;
                }
                vue.isDeletingAuthor = false;
            });
        },
        updateAuthor: function(author) {
            let vue = this;

            vue.editAuthorError = null;
            vue.isUpdatingAuthor = true;

            let formData = getAuthorFormData(author, this.isPerson);

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
                    vue.isUpdatingAuthor = false;
                },
                error: function (response) {
                    vue.editAuthorError = response.message;
                    vue.isUpdatingAuthor = false;
                    console.log(response);
                }
            });
        },
        updateAuthorOrder: function($author) {
            let vue = this;

            vue.editAuthorError = null;
            vue.isUpdatingAuthor = true;

            let authorId = $author.attr("data-id");

            let oldIndex = vue.authors.findIndex(function (author) {
                return author.id === authorId;
            });

            vue.selectAuthor(vue.authors[oldIndex], oldIndex);
            let newIndex = getElementIndex($author[0]);
            vue.selectedAuthor.author.order = newIndex + 1;

            $author.closest(".sortable").sortable("cancel"); // Cancel the sort. Positioning is now handled by Vue.

            if (newIndex === oldIndex) {
                vue.isUpdatingAuthor = false;
                return;
            }

            let formData = getAuthorFormData(vue.selectedAuthor.author, this.isPerson);

            $.ajax({
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                url: '/hsapi/_internal/' + vue.resShortId + '/creator/' + vue.selectedAuthor.author.id + '/update-metadata/',
                success: function (response) {
                    if (response.status === "success") {
                        // Update the author's positions in the array
                        vue.authors.splice(newIndex, 0, vue.authors.splice(oldIndex, 1)[0]);

                        // Update the Order values
                        vue.authors = vue.authors.map(function (item, index) {
                            item.order = index + 1;
                            return item;
                        });
                    }
                    else {
                        vue.editAuthorError = response.message;
                    }
                    vue.isUpdatingAuthor = false;
                },
                error: function (response) {
                    vue.editAuthorError = response.message;
                    vue.isUpdatingAuthor = false;
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

function getAuthorFormData(author, isPerson) {
    let formData = new FormData();
    formData.append("resource-mode", RESOURCE_MODE.toLowerCase());
    formData.append("creator-" + (author.order - 1) + "-order", author.order !== null ? parseInt(author.order): "");

    formData.append("creator-" + (author.order - 1) + "-organization", author.organization !== null ? author.organization : "");
    formData.append("creator-" + (author.order - 1) + "-email", author.email !== null ? author.email : "");
    formData.append("creator-" + (author.order - 1) + "-address", author.address !== null ? author.address : "");
    formData.append("creator-" + (author.order - 1) + "-phone", author.phone !== null ? author.phone : "");
    formData.append("creator-" + (author.order - 1) + "-homepage", author.homepage !== null ? author.homepage : "");

    // Person-exclusive fields
    if (isPerson) {
        formData.append("creator-" + (author.order - 1) + "-name", author.name);

        $.each(author.identifiers, function (identifierName, identifierLink) {
            formData.append("identifier_name", identifierName);
            formData.append("identifier_link", identifierLink);
        });
    }

    return formData;
}