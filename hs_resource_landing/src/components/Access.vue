<template>
  <div>
      <span id="show-manage-access-modal" data-toggle="tooltip" data-placement="bottom" data-html="true" title=""
            class="fa fa-user-plus icon-button
      icon-blue" @click="showModal=true" data-original-title="Manage who has access<br><br><small>Use this button to share your resource with
      specific HydroShare users or set its sharing status (Public, Discoverable, Private, Shareable). You can give
      other users the ability to view or edit this resource. You can also add additional owners who will have full
      permissions.</small>"></span>
    <!-- use the modal component, pass in the prop -->
    <modal v-if="showModal" @close="showModal = false">

      <h3 slot="header" class="modal-title">Manage access</h3>


      <div class="modal-body" slot="body">
        <div class="alert alert-info" role="alert">
          <p><span class="glyphicon glyphicon-info-sign" aria-hidden="true" data-toggle="collapse"
                   data-target="#usage-info">&nbsp;</span>
            Use this window to share your resource with specific HydroShare users or set its sharing status (Public,
            Discoverable, Private, Shareable).
            You can give other users the ability to view or edit this resource. You can also add additional owners who
            will have full permissions.</p>
          <br>

          <div id="usage-info" class="collapse">
            <ul>
              <li>
                <p><strong>Owners</strong> can perform all operations on a resource and set whether
                  a resource is Public,
                  Discoverable, or Private and Shareable. Resources that are Public have all their
                  content
                  visible to all users. Resources that are Discoverable have only their metadata
                  public.
                  Resources that are private are only accessible to specific users or groups that
                  they have been shared with.</p>
              </li>
              <li>
                <p><strong>Editors</strong> can edit resource metadata and add and delete resource
                  content files. If the resource
                  is Shareable editors can use manage access to extend editing or viewing access
                  to other users.</p>
              </li>
              <li><p><strong>Viewers</strong> can view resource metadata and download resource content
                files. If the resource is
                Shareable viewers can use manage access to extend viewing access to other users.</p>
              </li>
            </ul>
          </div>
          <div data-toggle="collapse" data-target="#usage-info"
               class="btn-show-more btn btn-default btn-xs">Show More
          </div>
          <br>
        </div>
      </div>

      <div class="panel panel-default">
        <div class="panel-heading">
          <h3 class="panel-title">Who has access</h3>
        </div>
        <div class="panel-body panel-access ">
          <table class="table access-table"><!-- TODO style pointer events -->
            <tbody>
            <tr v-for="(user, index) in users" v-bind:key="user.id"
                :class="{ 'hide-actions': selfAccessLevel !== 'owner' && (user.access === 'owner' && hasOnlyOneOwner ||
    user.user_type === 'user' && user.id === quotaHolder.id)}">
              <td>
                <table class="user-scope">
                  <tr v-if="user.user_type === 'user'">
                    <td>
                      <div v-if="user.pictureUrl"
                           :style="{backgroundImage: 'url(' + user.pictureUrl + ')'}"
                           class="profile-pic-thumbnail round-image">
                      </div>

                      <div v-else class="profile-pic-thumbnail round-image user-icon"></div>
                    </td>
                    <td>
                      <div class="user-name">
                        <a :href="'/user/' + user.id">${user.best_name}</a>
                      </div>
                      <div class="user-username-content">${user.user_name}</div>
                      <div>
                        <span v-if="user.id === currentUserId" class="badge you-flag">You</span>
                        <span v-if="user.id === quotaHolder.id" class="badge you-flag">
                            <i class="fa fa-pie-chart" aria-hidden="true"></i> Quota Holder
                        </span>
                      </div>
                    </td>
                  </tr>

                  <tr v-else>
                    <td>
                      <div class="group-image-wrapper extra-small">
                        <div class="group-image-extra-small group-preview-image-default"
                             :style="{backgroundImage: 'url(' + (user.pictureUrl || groupImageDefaultUrl) + ')'}">
                        </div>
                      </div>
                    </td>
                    <td>
                      <div>
                        <a :href="'/group/' + user.id">${user.best_name}</a>
                      </div>
                      <div class="user-username-content">(Group)</div>
                    </td>
                  </tr>
                </table>
              </td>

              <td class="user-roles">
        <span class="dropdown role-dropdown">
            <span class="dropdown-toggle"
                  id="roles-menu"
                  data-toggle="dropdown"
                  aria-haspopup="true" aria-expanded="true">
                    ${accessStr[user.access]}
                <span class="caret"></span>
            </span>

            <ul class="dropdown-menu" aria-labelledby="roles-menu">
                <li :class="getUserDropdownItemClass(user, 'view')">
                    <a @click="onChangeAccess(user, index, 'view')">Can view</a>
                </li>
                <li :class="getUserDropdownItemClass(user, 'edit')">
                    <a @click="onChangeAccess(user, index, 'edit')">Can edit</a>
                </li>
                <li v-if="user.user_type === 'user'"
                    :class="getUserDropdownItemClass(user, 'owner')">
                    <a @click="onChangeAccess(user, index, 'owner')">Is owner</a>
                </li>
            </ul>
        </span>
              </td>

              <td class="user-actions">
                <i @click="undoAccess(user, index)"
                   v-if="user.can_undo && quotaHolder.id !== user.id"
                   class="fa fa-undo" aria-hidden="true" data-toggle="tooltip"
                   title="Undo Share"></i>
              </td>

              <td class="user-actions">
        <span @click="user.id === currentUserId ? showDeleteSelfDialog(user, index) : removeAccess(user, index)"
              v-if="!(user.access === 'owner' && hasOnlyOneOwner) && user.id !== quotaHolder.id && (selfAccessLevel === 'owner' || user.id === currentUserId)"
              :id="'form-remove-' + user.user_type + '-' + user.id"
              class="glyphicon glyphicon-remove btn-remove-row"
              data-toggle="tooltip" title="Remove">
        </span>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel panel-default">
        <div class="panel-heading">
          <h3 class="panel-title">Give access</h3>
        </div>

        <div id="div-invite-people" class="panel-body">
          <div id="invite-flag" class="btn-group space-bottom" role="group"
               aria-label="Share with users or groups">
            <button type="button"
                    :class="{btn: true, 'btn-primary': isInviteUsers, 'btn-default': !isInviteUsers}"
                    @click="isInviteUsers = true"
                    data-value="users">Users
            </button>
            <button>TODO PLACEHOLDER</button>
            <!-- TODO MAKE FIX VUE -->
            <!--            <button type="button"-->
            <!--                    :class="{btn: true, 'btn-primary': !isInviteUsers, 'btn-default': isInviteUsers}"-->
            <!--                    @click="isInviteUsers = false; if (selectedAccess === 'owner') {selectedAccess = 'view'}"-->
            <!--                    data-value="groups">Groups-->
            <!--            </button>-->
          </div>

          <div class="row">
            <div v-show="isInviteUsers" class="add-view-user-form col-xs-12">
              <!-- TODO             {{ add_view_invite_user_form.user }}-->
            </div>

            <div v-show="!isInviteUsers" class="add-view-group-form col-xs-12">
              <!-- TODO             {{ add_view_group_form.group }}-->
            </div>

            <div class="col-xs-12">
              <div class="row">
                <div class="col-xs-6">
                  <div class="dropdown custom-dropdown">
                    <button class="btn btn-default dropdown-toggle" type="button"
                            id="roles_list" data-toggle="dropdown"
                            aria-haspopup="true">
                      <span id="selected_role" data-role="view">${accessStr[selectedAccess]}</span>
                      <span class="caret"></span>
                    </button>

                    <ul id="list-roles" class="dropdown-menu" aria-labelledby="roles_list">
                      <li :class="{ disabled: selfAccessLevel === 'None' }"
                          @click="selectedAccess = 'view'">
                        <a data-role="view">Can view</a>
                      </li>

                      <li :class="{ disabled: selfAccessLevel !== 'owner' && selfAccessLevel !== 'edit' }"
                          @click="selectedAccess = 'edit'">
                        <a data-role="edit">Can edit</a>
                      </li>

                      <li v-if="isInviteUsers"
                          :class="{ disabled: selfAccessLevel !== 'owner' }"
                          @click="selectedAccess = 'owner'">
                        <a data-role="owner">Is owner</a>
                      </li>
                    </ul>
                  </div>
                </div>

                <div class="col-xs-6">
                  <a id="btn-confirm-add-access"
                     @click="grantAccess"
                     class="btn btn-add-access btn-success glyphicon glyphicon-plus"><span
                      class="button-label">&nbsp;Add</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div v-if="error" class='alert alert-danger space-top small'>
            <strong>Error: </strong>${ error }
          </div>
        </div>
      </div>

      <div id="sharing-status">
        <div class="panel panel-default">
          <div class="panel-heading">
            <h3 class="panel-title">Sharing status</h3>
          </div>
          <div class="panel-body">
            <div v-if="selfAccessLevel === 'owner'"
                 class="alert alert-info" role="alert"><i class="fa fa-lock" aria-hidden="true"></i>
              You are the owner of this resource.
            </div>
            <div v-if="selfAccessLevel === 'edit'"
                 class="alert alert-info" role="alert">You have been given specific permission to
              {% if cm.raccess.published %} view{% else %} edit{% endif %} this resource.
            </div>
            <div v-if="selfAccessLevel === 'view'"
                 class="alert alert-info" role="alert">You have been given specific permission to
              view this resource.
            </div>

            <template v-if="canChangeResourceFlags">
              <div class="btn-group" role="group">
                <!--                PUBLIC-->
                <button
                    :disabled="!canBePublicDiscoverable || resAccess.isPublic || isProcessingAccess"
                    @click="setResourceAccess('make_public')"
                    :class="{active: resAccess.isPublic}"
                    class="btn btn-default"
                    id="btn-public" data-toggle="tooltip" data-placement="auto"
                    title='Can be viewed and downloaded by anyone.' type="button">
                  Public
                </button>
                <!--DISCOVERABLE-->
                <button :disabled="!canBePublicDiscoverable || isProcessingAccess"
                        @click="setResourceAccess('make_discoverable')"
                        :class="{active: resAccess.isDiscoverable && !resAccess.isPublic}"
                        class="btn btn-default"
                        id="btn-discoverable" data-toggle="tooltip" data-placement="auto"
                        type="button" title='Metadata is public but data are protected.'>
                  Discoverable
                </button>
                <!--PRIVATE-->
                <button
                    :disabled="!resAccess.isPublic && !resAccess.isDiscoverable || isProcessingAccess"
                    @click="setResourceAccess('make_private')"
                    :class="{active: !resAccess.isPublic && !resAccess.isDiscoverable}"
                    class="btn btn-default"
                    id="btn-private" data-toggle="tooltip" data-placement="auto"
                    title='Can be viewed and downloaded only by designated users or research groups.'
                    type="button">
                  Private
                </button>
              </div>

              <div
                  v-if="selfAccessLevel === 'owner' && resType === 'NetcdfResource' && !resAccess.isPublic"
                  class="alert alert-warning small space-top">
                Note that making the resource public may take a little extra time to update
                Hyrax server in order to provide OPeNDAP service for this resource.
              </div>

              <div v-if="selfAccessLevel === 'owner'">
                <div class="checkbox">
                  <label>
                    <input type="checkbox" v-model="resAccess.isShareable" :disabled="isProcessingShareable"
                           @change="setShareable(resAccess.isShareable ? 'make_shareable' : 'make_not_shareable')">
                    Shareable
                  </label>
                </div>

                <div v-if="resAccess.isShareable" class="text-muted small">
                  <ul>
                    <li>
                      <p>
                        Check the box to let others who have access to this resource be able to share
                        it with others at the same permission level (Edit or View) and enable adding to Collections.
                      </p>
                    </li>
                    <li>
                      <p>
                        Uncheck the box to prevent others from sharing the resource without the
                        owner’s permission, or from adding the resource to Collections before the resource is made
                        Discoverable or Public.
                      </p>
                    </li>
                  </ul>
                </div>

                <p v-else class="text-muted small">
                  Check this box to allow others to share the resource without the
                  owner's permission.
                </p>
              </div>
            </template>

            <div v-if="sharingError" class='alert alert-danger space-top small'>
              <strong>Error: </strong>${ sharingError }
            </div>
          </div>
        </div>

<!--         Change quota holder -->
        <div v-if="selfAccessLevel === 'owner'" class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">Storage</h3>
    </div>
    <div class="panel-body">
        <span>The quota holder of this resource is: </span>
        <span>
            <profile-link v-on:load-card="onLoadQuotaHolderCard($event)" :user="quotaHolder"></profile-link>
            <profile-card :user="quotaHolder" :position="cardPosition"></profile-card>
        </span>

        <button v-show="!hasOnlyOneOwner"
                id="btn-change-quota-holder" type="button" class="btn btn-default btn-xs"
                style="margin-left: 5px;"
                data-toggle="collapse" data-target="#form-quota-holder">
            Change
        </button>

        <div v-show="!hasOnlyOneOwner" id="form-quota-holder" class="collapse">
            <hr>
            <div class="form-group">
                <fieldset>
                    <div class="control-group">
                        <label for="new_holder_username" class="control-label requiredField">
                            Change quota holder to another owner</label>

                        <div class="controls">
                            <select ref="newHolder" class="form-control input-sm select"
                                    id="new_holder_username"
                                    name="new_holder_username">
                                <option v-for="user in users"
                                        v-if="user.user_type === 'user' && user.access === 'owner' && user.id !== quotaHolder"
                                        :value="user.user_name">${user.best_name}
                                </option>
                            </select>

                            <div v-if="quotaError" class='alert alert-danger space-top small'>
                                <strong>Error: </strong>${ quotaError }
                            </div>
                        </div>
                    </div>
                </fieldset>
            </div>

            <button
                :class="{disabled: isChangingQuotaHolder}"
                class="btn btn-default space-right" data-toggle="collapse"
                type="button"
                data-target="#form-quota-holder">Cancel
            </button>

            <button @click="setQuotaHolder($refs.newHolder.value)"
                    :class="{disabled: isChangingQuotaHolder}"
                    class="btn btn-primary"
                    type="button">${isChangingQuotaHolder ? "Saving Changes..." : "Save Changes"}
            </button>
        </div>
        <hr>
        <p>The size of this resource is <strong>{{ cm.size|filesizeformat }}</strong>.</p>
    </div>
</div>
      </div>

      <div class="modal-footer">
        <a type="button" data-dismiss="modal" class="btn btn-default">Close</a>
      </div>

    </modal>
  </div>
</template>

<script>
import axios from 'axios';
import Modal from './Modal.vue';

export default {
  name: 'Access',
  props: ['currentUserId', 'shortId'],
  data() {
    return {
      QUOTA_HOLDER_PK: {},
      GROUP_IMAGE_DEFAULT_URL: 'img/home-page/step4.png',
      CAN_CHANGE_RESOURCE_FLAGS: true,
      CAN_BE_PUBLIC_OR_DISCOVERABLE: true,
      RESOURCE_ACCESS: {
        isPublic: true,
        isDiscoverable: true,
        isShareable: true,
      },
      CITATION_ID: 123,
      RES_KEYWORDS: 'asf sadf',
      SELF_ACCESS_LEVEL: 'asdf',
      CAN_CHANGE: true,
      RES_TYPE: 'composite',
      FILE_COUNT: 4,
      SUPPORTED_FILE_TYPES: 'asdf',
      ALLLOW_MULTIPLE_FILE_UPLOAD: true,
      AUTHORS: 'kjuh',
      USERS_JSON: {},
      users: [],
      // selfAccessLevel: SELF_ACCESS_LEVEL,
      // quotaHolder: USERS_JSON.find(user => user.id === QUOTA_HOLDER_PK),
      // resType: RES_TYPE,
      // canChangeResourceFlags: CAN_CHANGE_RESOURCE_FLAGS,
      // groupImageDefaultUrl: GROUP_IMAGE_DEFAULT_URL,
      // canBePublicDiscoverable: CAN_BE_PUBLIC_OR_DISCOVERABLE,
      isInviteUsers: true,
      selectedAccess: 'view',
      accessStr: {
        view: 'Can view',
        edit: 'Can edit',
        owner: 'Is owner',
      },
      error: '',
      quotaError: '',
      sharingError: '',
      isProcessing: false,
      isProcessingAccess: false,
      isProcessingShareable: false,
      isChangingQuotaHolder: false,
      cardPosition: {
        top: 0,
        left: 0,
      },
    };
  },
  components: {
    Modal,
  },
  watch: {
    resAccess(newAccess, oldAccess) {
      console.log(oldAccess);
      // TODO: move to Highlight's component once it's ready
      // $('#publish')
      //     .toggleClass('disabled', !newAccess.isPublic);
      // $('#publish > span')
      //     .attr('data-original-title', !newAccess.isPublic ?
      //         'Publish this resource<small class=\'space-top\'>You must make your resource public in the Manage Access Panel before it can be published.' : 'Publish this resource');
      // $('#publish')
      //     .attr('data-toggle', !newAccess.isPublic ? '' : 'modal');   // Disable the agreement modal

      let accessStr = 'Private';
      if (newAccess.isPublic && newAccess.isDiscoverable) {
        accessStr = 'Public';
      } else if (!newAccess.isPublic && newAccess.isDiscoverable) {
        accessStr = 'Discoverable';
      }
      console.log(accessStr);
      // $('#hl-sharing-status')
      //   .text(accessStr); // Update highlight sharing status
    },
    users() {
      leftHeaderApp.$data.owners = this.users.filter(user => user.access === 'owner');
    },
  },
  computed: {
    hasOnlyOneOwner() {
      return this.users.filter(user => user.access === 'owner').length === 1;
    }
    ,
  },
  methods: {
    onChangeAccess(user, index, accessToGrant) {
      if (this.currentUserId === user.id && user.access === 'owner') {
        this.showPermissionDialog(user, index, accessToGrant);
      } else {
        this.changeAccess(user, index, accessToGrant);
      }
    },
    changeAccess(user, index, accessToGrant) {
      this.error = '';
      // user.loading = true;
      this.isProcessing = true;
      this.users.splice(index, 1, user);

      $.post(`/hsapi/_internal/${this.shortId}/share-resource-with-${user.user_type}/${
        accessToGrant}/${user.id}/`, (result) => {
        let resp;
        try {
          resp = JSON.parse(result);
        } catch (error) {
          console.log(error);
          // vue.isProcessing = false;
          return;
        }

        if (resp.status == 'success') {
          user = resp.user;
          if (vue.currentUserId === user.id) {
            vue.selfAccessLevel = user.access;
          }
        } else {
          console.log(resp);
          this.error = resp.error_msg;
        }

        // user.loading = false;
        vue.users.splice(index, 1, user);
        // vue.isProcessing = false;
      });
    },
    getUserDropdownItemClass(user, accessToGrant) {
      let ddClass = {
        active: false,
        disabled: true,
      };

      if (accessToGrant === 'view') {
        ddClass = {
          active: user.access === 'view',
          disabled: user.access === 'none',
        };
      } else if (accessToGrant === 'edit') {
        ddClass = {
          active: user.access === 'edit',
          disabled: this.selfAccessLevel !== 'owner' && this.selfAccessLevel !== 'edit',
        };
      } else if (accessToGrant === 'owner') {
        ddClass = {
          active: user.access === 'owner',
          disabled: !this.canChangeResourceFlags || this.selfAccessLevel !== 'owner',
        };
      }

      // eslint-disable-next-line no-mixed-operators
      ddClass.disabled = !ddClass.active && (ddClass.disabled || user.access === 'owner'
          && this.hasOnlyOneOwner || user.user_type === 'user' && user.id === this.quotaHolder.id);

      return ddClass;
    },
    showPermissionDialog(user, index, accessToGrant) {
      console.log(user, index, accessToGrant);
      // close the manage access panel (modal)
      // $('#manage-access')
      //   .modal('hide');

      // display change share permission confirmation dialog
      // $('#dialog-confirm-change-share-permission')
      //   .dialog({
      //     resizable: false,
      //     draggable: false,
      //     height: 'auto',
      //     width: 500,
      //     modal: true,
      //     dialogClass: 'noclose',
      //     buttons: {
      //       Cancel() {
      //         $(this)
      //           .dialog('close');
      //         // show manage access control panel again
      //         $('#manage-access')
      //           .modal('show');
      //       },
      //       Confirm() {
      //         $(this)
      //           .dialog('close');
      //         $('#manage-access')
      //           .modal('show');
      //         vue.changeAccess(user, index, accessToGrant);
      //       },
      //     },
      //     open() {
      //        $(this)
      //          .closest('.ui-dialog')
      //          .find('.ui-dialog-buttonset button:first') // the first button
      //          .addClass('btn btn-default');
      //
      //        $(this)
      //            .closest('.ui-dialog')
      //            .find('.ui-dialog-buttonset button:nth-child(2)') // the first button
      //            .addClass('btn btn-danger');
      //      },
      //    });
    },
    showDeleteSelfDialog(user, index) {
      console.log(user, index);
      // close the manage access panel (modal)
      // $('#manage-access ')
      //     .modal('hide');
      // const vue = this;

      // display remove access confirmation dialog
      // $('#dialog-confirm-delete-self-access')
      //     .dialog({
      //       resizable: false,
      //       draggable: false,
      //       height: 'auto',
      //       width: 500,
      //       modal: true,
      //       dialogClass: 'noclose',
      //       buttons: {
      //         Cancel() {
      //           $(this)
      //               .dialog('close');
      //           // show manage access control panel again
      //           $('#manage-access')
      //               .modal('show');
      //         },
      //         Remove() {
      //           $(this)
      //               .dialog('close');
      //           vue.removeAccess(user, index);
      //         },
      //       },
      //       open() {
      //         $(this)
      //             .closest('.ui-dialog')
      //             .find('.ui-dialog-buttonset button:first') // the first button
      //             .addClass('btn btn-default');
      //
      //         $(this)
      //             .closest('.ui-dialog')
      //             .find('.ui-dialog-buttonset button:nth-child(2)') // the second button
      //             .addClass('btn btn-danger');
      //       },
      //     });
    },
    undoAccess(user, index) {
      this.error = '';
      // user.loading = true;
      vue.users.splice(index, 1, user); // TODO SHOULD THIS BE REPEATED BELOW?

      axios.post(`/hsapi/_internal/${this.shortId}/undo-share-resource-with-${user.user_type}/${user.id}/`,
        {
          params: {
            asdf: 'asdf',
          },
        })
        .then((resp) => {
          if (resp.status === 'success') {
            try {
              user.access = resp[`undo_${user.user_type}_privilege`];
              user.can_undo = false;
              if (user.access === 'none') {
                vue.users.splice(index, 1); // The entry was removed
                return;
              }
              vue.users.splice(index, 1, user);
            } catch (e) {
              // do nothing
            }
          } else {
            this.error = resp.error_msg;
            console.log(resp);
          }
        })
        .catch((error) => {
            console.log(`error undo share resource: ${error}`); // eslint-disable-line
        })
        .then(() => {
          // user.loading = false;
          vue.users.splice(index, 1, user); // TODO IS THIS REPEATED FROM A BAD COPY PASTE? TEST
          this.isProcessing = false;
        });
    },
  },
  grantAccess() {
    let targetUserId;

    if (this.isInviteUsers) {
      if ($('#user-deck > .hilight').length > 0) {
        targetUserId = parseInt($('#user-deck > .hilight')[0].getAttribute('data-value'), 10);
      } else {
        return false; // No user selected
      }
    } else if ($('#id_group-deck > .hilight').length > 0) {
      targetUserId = parseInt($('#id_group-deck > .hilight')[0].getAttribute('data-value'), 10);
    } else {
      return false; // No group selected
    }

    $('.hilight > span')
      .click(); // Clear the autocomplete
    this.error = '';
    const vue = this;

    let index = -1;
    const user = this.users.filter((u, i) => {
      const answer = u.id === targetUserId;
      if (answer) {
        index = i;
      }
      return u.id === targetUserId;
    })[0];

    if (index >= 0) {
      if (user.access === this.selectedAccess) {
        return; // The user already has this access
      }

      // user.loading = true;
      this.users.splice(index, 1, user);
    }
    this.isProcessing = true;

    $.post(`/hsapi/_internal/${this.shortId}/share-resource-with-${
      this.isInviteUsers ? 'user' : 'group'}/${this.selectedAccess}/${
      targetUserId}/`, (result) => {
      let resp;
      try {
        resp = JSON.parse(result);
      } catch (error) {
        console.log(error);
        vue.error = 'Failed to change permission';
        vue.isProcessing = false;
        return;
      }

      if (resp.status === 'success') {
        if (index >= 0) {
          // An entry was found, update the data
          user.access = resp.user.access;
          // user.loading = false;
          vue.users.splice(index, 1, user);
          if (vue.currentUserId === user.id) {
            vue.selfAccessLevel = user.access;
          }
        } else {
          // No entry found. Push new data
          const newUserAccess = resp.user;
          newUserAccess.loading = false;
          vue.users.push(newUserAccess);
        }
      } else {
        vue.error = resp.error_msg;
        if (index >= 0) {
          // user.loading = false;
          vue.users.splice(index, 1, user);
        }
      }
      vue.isProcessing = false;
    });
  },
  removeAccess(user, index) {
    // user.loading = true;
    this.users.splice(index, 1, user);
    const vue = this;
    vue.error = '';
    this.isProcessing = true;

    $.post(`/hsapi/_internal/${this.shortId}/unshare-resource-with-${
      user.user_type}/${user.id}/`, (resp) => {
      if (resp.status === 'success') {
        vue.users.splice(index, 1);
        vue.isProcessing = false;
        if (resp.hasOwnProperty('redirect_to')) {
          window.location.href = resp.redirect_to;
        }
      } else {
        // user.loading = false;
        vue.users.splice(index, 1, user);
        vue.error = resp.message;
        vue.isProcessing = false;
        console.log(resp);
      }
    });
  },
  setResourceAccess(action) {
    this.isProcessingAccess = true;
    $.post(`/hsapi/_internal/${this.shortId}/set-resource-flag/`,
      {
        flag: action,
        'resource-mode': this.resourceMode,
      }, (resp) => {
        if (resp.status === 'success') {
          if (action === 'make_public') {
            this.resAccess = {
              isPublic: true,
              isDiscoverable: true,
              isShareable: this.resAccess.isShareable,
            };
          } else if (action === 'make_discoverable') {
            this.resAccess = {
              isPublic: false,
              isDiscoverable: true,
              isShareable: this.resAccess.isShareable,
            };
          } else if (action === 'make_private') {
            this.resAccess = {
              isPublic: false,
              isDiscoverable: false,
              isShareable: this.resAccess.isShareable,
            };
          }
        }
        this.isProcessingAccess = false;
      });
  },
  setShareable(action) {
    this.isProcessingShareable = true;
    this.sharingError = '';
    $.post(`/hsapi/_internal/${this.shortId}/set-resource-flag/`,
      {
        flag: action,
        'resource-mode': this.resourceMode,
      }, (resp) => {
        if (resp.status === 'error') {
          this.sharingError = resp.message;
        }
        this.isProcessingShareable = false;
      });
  },
  setQuotaHolder(username) {
    this.quotaError = '';
    this.isChangingQuotaHolder = true;

    $.post(`/hsapi/_internal/${this.shortId}/change-quota-holder/`,
      { new_holder_username: username }, (resp) => {
        if (resp.status === 'success') {
          let newHolder;
          let index;

          for (let i = 0; i < vue.users.length; i++) {
            if (vue.users[i].user_name === username) {
              newHolder = vue.users[i];
              index = i;
              break;
            }
          }

          newHolder.can_undo = false;
          vue.users.splice(index, 1, newHolder);

          // Changing quota holder can't be undone
          this.quotaHolder = newHolder;
        } else {
          this.quotaError = resp.message;
        }
        this.isChangingQuotaHolder = false;
      });
  },
  onMetadataInsufficient() {
    // Set the resource access to private
    this.resAccess = {
      isPublic: false,
      isDiscoverable: false,
      isShareable: this.resAccess.isShareable,
    };
    // The metadata is insufficient
    this.canBePublicDiscoverable = false;
  },
  onLoadQuotaHolderCard(data) {
    const el = $(data.event.target);
    const cardWidth = 350;
    this.cardPosition.left = el.position().left - (cardWidth / 2) + (el.width() / 2);
    this.cardPosition.top = el.position().top + 30;
  },
};
</script>

<style scoped>

</style>
