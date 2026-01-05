const IDENTIFIERS = {
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
};

Vue.component('edit-author-modal', {
    delimiters: ['${', '}'],
    template: '#edit-author-modal-template',
    props: {
        _author: {type: Object, required: true},
        is_person: {type: Boolean, required: true},
        can_remove: {type: Boolean, required: true},
        is_updating_author: {type: Boolean, required: false},
        is_deleting_author: {type: Boolean, required: false},
        edit_author_error: {type: String, required: false},
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
            identifierDict: IDENTIFIERS,
            showConfirmDelete: false
        }
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
        _author: function () {
            let identifiers = [];
            let localAuthor = $.extend(true, {}, this._author);

            $.each(this._author.identifiers, function (identifierName, identifierLink) {
                identifiers.push({identifierName: identifierName, identifierLink: identifierLink})
            });
            localAuthor.identifiers = identifiers;

            this.author = localAuthor;
            this.showConfirmDelete = false;
        }
    },
});

Vue.component('add-author-modal', {
    delimiters: ['${', '}'],
    template: '#add-author-modal-template',
    data: function () {
        return {
            userType: 0,
            resShortId: SHORT_ID,
            isAddingAuthor: false,
            addAuthorError: null,
            authorType: 0,
            authorTypes: {
                EXISTING_HS_USER: 0,
                OTHER_PERSON: 1,
                ORGANIZATION: 2,
            },
            identifierDict: IDENTIFIERS,
            author: {
                "name": null,
                "first_name": null,
                "last_name": null,
                "email": null,
                "organization": null,
                "identifiers": [],
                "address": null,
                "phone": null,
                "homepage": null,
            },
        }
    },
    mounted(){
        let that = this;
        $("#add-author-modal #user-wrapper").on("click", ".remove", function() {
            that.addAuthorError = "";
        })
    },
    methods: {
        addAuthorExistingUser: function () {
            let vue = this;
            vue.addAuthorError = null;

            let userId = $("#id_author").find(':selected').val();

            if (!userId) {
                vue.addAuthorError = "Select a user to add as an author";
                return;
            } else {
                const alreadyExists = leftHeaderApp.$data.authors.some(function (author) {
                    return author.profileUrl === "/user/" + userId + "/"; 
                });

                if (alreadyExists) {
                    vue.addAuthorError = "This author has already been added to this resource";
                    return;
                }
            }

            let url = '/hsapi/_internal/get-user-or-group-data/' + userId + "/false";

            vue.isAddingAuthor = true;
            $.ajax({
                type: "POST",
                url: url,
                dataType: 'html',
                success: function (result) {
                    let author = JSON.parse(result);

                    let formData = new FormData();
                    formData.append("resource-mode", RESOURCE_MODE.toLowerCase());
                    formData.append("organization", author.organization !== null ? author.organization : "");
                    formData.append("email", author.email !== null ? author.email : "");
                    formData.append("hydroshare_user_id", userId);
                    formData.append("address", author.address !== null ? author.address : "");
                    formData.append("phone", author.phone !== null ? author.phone : "");
                    formData.append("homepage", author.website !== null ? author.website : "");
                    formData.append("name", author.name);

                    $.each(author.identifiers, function (identifierName, identifierLink) {
                        formData.append("identifier_name", identifierName);
                        formData.append("identifier_link", identifierLink);
                    });

                    $.ajax({
                        type: "POST",
                        data: formData,
                        processData: false,
                        contentType: false,
                        url: '/hsapi/_internal/' + vue.resShortId + '/creator/add-metadata/',
                        success: function (response) {
                            if (response.status === "success") {
                                let newAuthor = {
                                    "id": response.element_id.toString(),
                                    "name": author.name,
                                    "email": author.email !== null ? author.email : "",
                                    "organization": author.organization,
                                    "identifiers": author.identifiers,
                                    "address": author.address !== null ? author.address : "",
                                    "phone": author.phone !== null ? author.phone : "",
                                    "homepage": author.website !== null ? author.website : "",
                                    "profileUrl": "/user/" + userId + "/",
                                };

                                leftHeaderApp.$data.authors.push(newAuthor);

                                // Update the Order values
                                leftHeaderApp.$data.authors = leftHeaderApp.$data.authors.map(function (item, index) {
                                    item.order = index + 1;
                                    return item;
                                });

                                $("#add-author-modal").modal("hide");
                                showCompletedMessage(response);
                            }
                            else {
                                vue.addAuthorError = response.message;
                            }
                            vue.isAddingAuthor = false;
                        },
                        error: function (response) {
                            vue.isAddingAuthor = false;
                            console.log(response);
                        }
                    });
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    vue.isAddingAuthor = false;
                    vue.addAuthorError = errorThrown;
                }
            });
        },
        addAuthorOtherPerson: function () {
            let vue = this;
            // Transform the identifier field back into an object
            let author = $.extend(true, {}, this.author);

            vue.addAuthorError = null;
            if (vue.authorType === vue.authorTypes.OTHER_PERSON) {
                author.name = vue.buildPersonName(author.first_name, author.last_name);
                if (!author.name) {
                    vue.addAuthorError = "First and last name are required. Please input the author name to add.";
                    return;
                }
            }

            let identifiers = {};

            this.author.identifiers.map(function (el) {
                if (el.identifierName && el.identifierLink) {
                    identifiers[el.identifierName] = el.identifierLink;
                }
            });

            author.identifiers = identifiers;

            let formData = new FormData();
            formData.append("resource-mode", RESOURCE_MODE.toLowerCase());

            formData.append("organization", author.organization !== null ? author.organization : "");
            formData.append("email", author.email !== null ? author.email : "");
            formData.append("address", author.address !== null ? author.address : "");
            formData.append("phone", author.phone !== null ? author.phone : "");
            formData.append("homepage", author.homepage !== null ? author.homepage : "");


            // Person specific fields
            if (vue.authorType === vue.authorTypes.OTHER_PERSON) {
                formData.append("name", author.name);
                $.each(author.identifiers, function (identifierName, identifierLink) {
                    formData.append("identifier_name", identifierName);
                    formData.append("identifier_link", identifierLink);
                });
            }

            vue.isAddingAuthor = true;

            $.ajax({
                type: "POST",
                data: formData,
                processData: false,
                contentType: false,
                url: '/hsapi/_internal/' + vue.resShortId + '/creator/add-metadata/',
                success: function (response) {
                    if (response.status === "success") {
                        let newAuthor = {
                            "id": response.element_id.toString(),
                            "email": author.email !== null ? author.email : "",
                            "organization": author.organization,
                            "address": author.address !== null ? author.address : "",
                            "phone": author.phone !== null ? author.phone : "",
                            "homepage": author.homepage !== null ? author.homepage : "",
                            "name": "",
                            "profileUrl": "",
                        };

                        // Person specific fields
                        if (vue.authorType === vue.authorTypes.OTHER_PERSON) {
                            newAuthor.name = author.name;
                            newAuthor.identifiers = author.identifiers;
                            newAuthor.profileUrl = null;
                        }

                        leftHeaderApp.$data.authors.push(newAuthor);

                        // Update the Order values
                        leftHeaderApp.$data.authors = leftHeaderApp.$data.authors.map(function (item, index) {
                            item.order = index + 1;
                            return item;
                        });

                        $("#add-author-modal").modal("hide");

                        // Reset form fields
                        vue.author = {
                            "name": null,
                            "first_name": null,
                            "last_name": null,
                            "email": null,
                            "organization": null,
                            "identifiers": [],
                            "address": null,
                            "phone": null,
                            "homepage": null,
                        };
                        showCompletedMessage(response);
                    }
                    else {
                        vue.addAuthorError = response.message;
                    }
                    vue.isAddingAuthor = false;
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    console.log(response);
                    vue.addAuthorError = errorThrown;
                    vue.isAddingAuthor = false;
                }
            });
        },
        onDeleteIdentifier: function (index) {
            this.author.identifiers.splice(index, 1);
        },
        // TODO: create a nested component with this identifier stuff
        onAddIdentifier: function () {
            this.author.identifiers.push({
                identifierName: null,
                identifierLink: null
            });
        },
        hasIdentifier: function(identifier) {
            let search = this.author.identifiers.filter(function (el) {
                return el.identifierName === identifier;
            });

            return search.length > 0;
        },
        buildPersonName: function(firstName, lastName) {
            const first = firstName ? firstName.trim() : "";
            const last = lastName ? lastName.trim() : "";

            if (!first || !last) {
                return "";
            }

            return `${first} ${last}`;
        }
    },
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
        loadOwnerCard: function(data) {
            const el = $(data.event.target);
            const cardWidth = 350;

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
                    // Remove the author from the list
                    vue.authors.splice(vue.selectedAuthor.index, 1);

                    // Update the Order values
                    vue.authors = vue.authors.map(function (item, index) {
                        item.order = index + 1;
                        return item;
                    });

                    $("#edit-author-modal").modal('hide');          // Dismiss the modal
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

            let authorId = $author[0].getAttribute("data-id");

            let oldIndex = vue.authors.findIndex(function (author) {
                return author.id === authorId;
            });

            vue.selectAuthor(vue.authors[oldIndex], oldIndex);

            let newIndex = 0;   // default

            // Iterate through the authors and find the target position index
            $author.first().parent().find("span[data-id]").filter(function (index, el) {
               if (el.getAttribute("data-id") == authorId) {
                   newIndex = index;
               }
            });

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
    },
    filters: {
        nameWithoutCommas: function (name, profileUrl) {
            if (!name) return null;
            name = name.toString().trim();

            if (name.indexOf(',') >= 0) {
                const fullName = name.split(',');
                if (fullName.length === 2) {
                    const firstNames = fullName[1].trim();
                    const lastNames = fullName[0].trim();
                    if (firstNames && lastNames) {
                        return firstNames + " " + lastNames;
                    }
                    if (firstNames) {
                        return firstNames;
                    }
                    if (lastNames) {
                        return lastNames;
                    }
                    return null;
                }
            }
            return name;    // default
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
    $.each(author.identifiers, function (identifierName, identifierLink) {
        formData.append("identifier_name", identifierName);
        formData.append("identifier_link", identifierLink);
    });

    // Person-exclusive fields
    if (isPerson) {
        formData.append("creator-" + (author.order - 1) + "-name", author.name);
        formData.append("creator-" + (author.order - 1) + "-hydroshare_user_id", author.profileUrl !== null ? author.profileUrl.replace(/\D/g,'') : "");
    }
    else {
        // Empty values still needed for valid request
        formData.append("creator-" + (author.order - 1) + "-name", "");
        formData.append("creator-" + (author.order - 1) + "-hydroshare_user_id", "");
    }

    return formData;
}
