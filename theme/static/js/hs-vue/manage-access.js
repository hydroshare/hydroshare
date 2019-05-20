/**
 * Created by Mauriel on 5/19/2019.
 */

let manageAccessCmp = new Vue({
    el: '#manage-access',
    delimiters: ['${', '}'],
    data: {
        users: USERS_JSON,
        currentUser: CURRENT_USER_PK,
        selfAccessLevel: SELF_ACCESS_LEVEL,
        quotaHolder: QUOTA_HOLDER_PK,
        resShortId: SHORT_ID,
        canChangeResourceFlags: CAN_CHANGE_RESOURCE_FLAGS,
        groupImageDefaultUrl: GROUP_IMAGE_DEFAULT_URL,
        isInviteUsers: true,
        selectedAccess: 'view',
        accessStr: {
            view: 'Can view',
            edit: 'Can edit',
            owner: 'Is owner'
        }
    },
    methods: {
        changeAccess: function (user, index, accessToGrant) {
            let vue = this;

            $.post('/hsapi/_internal/' + this.resShortId + '/share-resource-with-' + user.user_type + '/'
                + accessToGrant + '/' + user.id + '/', function (result) {
                let resp;
                try {
                    resp = JSON.parse(result)
                }
                catch (error) {
                    console.log(error);
                    return;
                }

                if (resp.status == "success") {
                    user.access = vue.accessStr[resp.privilege_granted];
                    vue.users.splice(index, 1, user);
                }
            });
        },
        undoAccess: function (user, index) {
            let vue = this;
            $.post('/hsapi/_internal/' + this.resShortId + '/undo-share-resource-with-'
                + user.user_type + '/' + user.id + '/', function (resp) {
                if (resp.status === "success") {
                    user.access = vue.accessStr[resp['undo_' + user.user_type + '_privilege']];
                    vue.users.splice(index, 1, user);
                }
            });
        },
        grantAccess: function () {
            let targetUserId;

            if (this.isInviteUsers) {
                if ($("#user-deck > .hilight").length > 0) {
                    targetUserId = $("#user-deck > .hilight")[0].getAttribute("data-value");
                }
                else {
                    return false;   // No user selected
                }
            }
            else {
                if ($("#id_group-deck > .hilight").length > 0) {
                    targetUserId = $("#id_group-deck > .hilight")[0].getAttribute("data-value");
                }
                else {
                    return false;   // No group selected
                }
            }

            let vue = this;

            $.post('/hsapi/_internal/' + this.resShortId + '/share-resource-with-' +
                (this.isInviteUsers ? 'user' : 'group') + '/' + this.selectedAccess + "/" +
                targetUserId + "/", function (result) {
                let resp;
                try {
                    resp = JSON.parse(result)
                }
                catch (error) {
                    console.log(error);
                    return;
                }

                let index = -1;

                // Check if this user already has any access and get its index in the array
                for (let i = 0; i < vue.users.length; i++) {
                    if (vue.users[i].id === targetUserId) {
                        index = i;
                        break;
                    }
                }

                if (index >= 0) {
                    // An entry was found, update the data
                    let user = vue.users[index];
                    user.access = vue.accessStr[resp.privilege_granted];
                    vue.users.splice(index, 1, user);
                }
                else {
                    // No entry found. Push new data
                    const newUserAccess = {
                        user_type: vue.isInviteUsers ? 'user' : 'group',
                        access: vue.accessStr[resp.privilege_granted],
                        id: targetUserId,
                        pictureUrl: resp.profile_pic === "No picture provided" ? null : resp.profile_pic,
                        best_name: resp.name,
                        user_name: resp.username,
                        can_undo: true,
                    };

                    vue.users.push(newUserAccess);
                }
            });
        }
    },
    computed: {
        hasOnlyOneOwner: function() {
            return this.users.filter(function(user) {
                return user.access === "Owner";
            }).length === 1;
        },
    }
});