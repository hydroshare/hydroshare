from __future__ import absolute_import

import logging

from autocomplete_light import shortcuts as autocomplete_light
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from mezzanine.conf import settings

from hs_access_control.models import PrivilegeCodes, GroupMembershipRequest, GroupResourcePrivilege
from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.views.utils import share_resource
from .utils import authorize, ACTION_TO_AUTHORIZE, send_action_to_take_email

logger = logging.getLogger(__name__)


def share_resource_with_group(request, shortkey, privilege, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""
    return share_resource(request, shortkey, privilege, group_id, user_or_group='group')

def _send_email_on_group_membership_acceptance(membership_request):
    """
    Sends email notification of group membership acceptance

    :param membership_request: an instance of GroupMembershipRequest class
    :return:
    """

    if membership_request.invitation_to is not None:
        # user accepted invitation from the group owner
        # here we are sending email to group owner who invited
        email_msg = """Dear {}
        <p>Your invitation to user '{}' to join the group '{}' has been accepted.</p>
        <p>Thank you</p>
        <p>The HydroShare Team</p>
        """.format(membership_request.request_from.first_name,
                   membership_request.invitation_to.first_name, membership_request.group_to_join.name)
    else:
        # group owner accepted user request
        # here wre are sending email to the user whose request to join got accepted
        email_msg = """Dear {}
        <p>Your request to join the group '{}' has been accepted.</p>
        <p>Thank you</p>
        <p>The HydroShare Team</p>
        """.format(membership_request.request_from.first_name, membership_request.group_to_join.name)

    send_mail(subject="HydroShare group membership",
              message=email_msg,
              html_message=email_msg,
              from_email=settings.DEFAULT_FROM_EMAIL,
              recipient_list=[membership_request.request_from.email])

class GroupForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)
    purpose = forms.CharField(required=False)
    picture = forms.ImageField(required=False)
    privacy_level = forms.CharField(required=True)
    auto_approve = forms.BooleanField(required=False)

    def clean_privacy_level(self):
        data = self.cleaned_data['privacy_level']
        if data not in ('public', 'private', 'discoverable'):
            raise forms.ValidationError("Invalid group privacy level.")
        return data

    def _set_privacy_level(self, group, privacy_level):
        if privacy_level == 'public':
            group.gaccess.public = True
            group.gaccess.discoverable = True
        elif privacy_level == 'private':
            group.gaccess.public = False
            group.gaccess.discoverable = False
        elif privacy_level == 'discoverable':
            group.gaccess.discoverable = True
            group.gaccess.public = False

        group.gaccess.save()

class GroupCreateForm(GroupForm):
    def save(self, request):
        frm_data = self.cleaned_data

        new_group = request.user.uaccess.create_group(title=frm_data['name'],
                                                      description=frm_data['description'],
                                                      purpose=frm_data['purpose'],
                                                      auto_approve=frm_data['auto_approve'])
        if 'picture' in request.FILES:
            new_group.gaccess.picture = request.FILES['picture']

        privacy_level = frm_data['privacy_level']
        self._set_privacy_level(new_group, privacy_level)
        return new_group


class GroupUpdateForm(GroupForm):
    def update(self, group_to_update, request):
        frm_data = self.cleaned_data
        group_to_update.name = frm_data['name']
        group_to_update.save()
        group_to_update.gaccess.description = frm_data['description']
        group_to_update.gaccess.purpose = frm_data['purpose']
        group_to_update.gaccess.auto_approve = frm_data['auto_approve']
        if 'picture' in request.FILES:
            group_to_update.gaccess.picture = request.FILES['picture']

        privacy_level = frm_data['privacy_level']
        self._set_privacy_level(group_to_update, privacy_level)


@login_required
def update_user_group(request, group_id, *args, **kwargs):
    user = request.user
    group_to_update = utils.group_from_id(group_id)

    if user.uaccess.can_change_group_flags(group_to_update):
        group_form = GroupUpdateForm(request.POST, request.FILES)
        if group_form.is_valid():
            try:
                group_form.update(group_to_update, request)
                messages.success(request, "Group update was successful.")
            except IntegrityError as ex:
                if group_form.cleaned_data['name'] in ex.message:
                    message = "Group name '{}' already exists".format(group_form.cleaned_data['name'])
                    messages.error(request, "Group update errors: {}.".format(message))
                else:
                    messages.error(request, "Group update errors:{}.".format(ex.message))
        else:
            messages.error(request, "Group update errors:{}.".format(group_form.errors.as_json))
    else:
        messages.error(request, "Group update errors: You don't have permission to update this group")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def create_user_group(request, *args, **kwargs):
    group_form = GroupCreateForm(request.POST, request.FILES)
    if group_form.is_valid():
        try:
            new_group = group_form.save(request)
            messages.success(request, "Group creation was successful.")
            return HttpResponseRedirect(reverse('group', args=[new_group.id]))
        except IntegrityError as ex:
            if group_form.cleaned_data['name'] in ex.message:
                message = "Group name '{}' already exists".format(group_form.cleaned_data['name'])
                messages.error(request, "Group creation errors: {}.".format(message))
            else:
                messages.error(request, "Group creation errors:{}.".format(ex.message))
    else:
        messages.error(request, "Group creation errors:{}.".format(group_form.errors.as_json))

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


class AddUserForm(forms.Form):
    user = forms.ModelChoiceField(User.objects.all(), widget=autocomplete_light.ChoiceWidget("UserAutocomplete"))

@login_required
def share_group_with_user(request, group_id, user_id, privilege, *args, **kwargs):
    requesting_user = request.user
    group_to_share = utils.group_from_id(group_id)
    user_to_share_with = utils.user_from_id(user_id)
    if privilege == 'view':
        access_privilege = PrivilegeCodes.VIEW
    elif privilege == 'edit':
        access_privilege = PrivilegeCodes.CHANGE
    elif privilege == 'owner':
        access_privilege = PrivilegeCodes.OWNER
    else:
        access_privilege = PrivilegeCodes.NONE

    if access_privilege != PrivilegeCodes.NONE:
        if requesting_user.uaccess.can_share_group(group_to_share, access_privilege):
            try:
                requesting_user.uaccess.share_group_with_user(group_to_share, user_to_share_with, access_privilege)
                messages.success(request, "User successfully added to the group")
            except PermissionDenied as ex:
                messages.error(request, ex.message)
        else:
            messages.error(request, "You don't have permission to add users to group")
    else:
        messages.error(request, "Invalid privilege for sharing group with user")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def unshare_group_with_user(request, group_id, user_id, *args, **kwargs):
    """
    Remove a user from a group

    :param request: group owner who is removing the user from the group
    :param group_id: id of the user being removed from the group
    :param user_id: id of the group from which the user to be removed
    :return:
    """
    requesting_user = request.user
    group_to_unshare = utils.group_from_id(group_id)
    user_to_unshare_with = utils.user_from_id(user_id)

    try:
        requesting_user.uaccess.unshare_group_with_user(group_to_unshare, user_to_unshare_with)
        if requesting_user == user_to_unshare_with:
            success_msg = "You successfully left the group."
        else:
            success_msg = "User successfully removed from the group."
        messages.success(request, success_msg)
    except PermissionDenied as ex:
        messages.error(request, ex.message)

    if requesting_user == user_to_unshare_with:
        return HttpResponseRedirect(reverse("my_groups"))
    else:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

@login_required
def make_group_membership_request(request, group_id, user_id=None, *args, **kwargs):
    """
    Allows either an owner of the group to invite a user to join a group or a user to make a request
    to join a group
    :param request: the user who is making the request
    :param group_id: ID of the group for which the join request/invitation to me made
    :param user_id: needed only when an owner is inviting a user to join a group. This is the id of the user the owner
                    is inviting
    :return:
    """
    requesting_user = request.user
    group_to_join = utils.group_from_id(group_id)
    user_to_join = None
    if user_id is not None:
        user_to_join = utils.user_from_id(user_id)
    try:
        membership_request = requesting_user.uaccess.create_group_membership_request(
            group_to_join, user_to_join)
        if user_to_join is not None:
            message = 'Group membership invitation was successful'
            # send mail to the user who was invited to join group
            send_action_to_take_email(request, user=user_to_join, action_type='group_membership',
                                      group=group_to_join, membership_request=membership_request)
        else:
            message = 'You are now a member of this group'
            # membership_request is None in case where group allows auto approval of membership
            # request. no need send email notification to group owners for membership approval
            if membership_request is not None:
                message = 'Group membership request was successful'
                # send mail to all owners of the group for approval of the request
                for grp_owner in group_to_join.gaccess.owners:
                    send_action_to_take_email(request, user=requesting_user,
                                              action_type='group_membership',
                                              group=group_to_join, group_owner=grp_owner,
                                              membership_request=membership_request)
            else:
                # send mail to all owners of the group to let them know that someone has
                # joined this group
                for grp_owner in group_to_join.gaccess.owners:
                    send_action_to_take_email(request, user=requesting_user,
                                              action_type='group_auto_membership',
                                              group=group_to_join,
                                              group_owner=grp_owner)
        messages.success(request, message)
    except PermissionDenied as ex:
        messages.error(request, ex.message)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])

def group_membership(request, uidb36, token, membership_request_id, **kwargs):
    """
    View for the link in the verification email that was sent to a user
    when they request/invite to join a group.
    User is logged in and the request to join a group is accepted. Then the user is redirected to the group
    profile page of the group for which the membership got accepted.

    :param uidb36: ID of the user to whom the email was sent (part of the link in the email)
    :param token: token that was part of the link in the email
    :param membership_request_id: ID of the GroupMembershipRequest object (part of the link in the email)
    """
    membership_request = GroupMembershipRequest.objects.filter(id=membership_request_id).first()
    if membership_request is not None:
        if membership_request.group_to_join.gaccess.active:
            user = authenticate(uidb36=uidb36, token=token, is_active=True)
            if user is not None:
                user.uaccess.act_on_group_membership_request(membership_request, accept_request=True)
                auth_login(request, user)
                # send email to notify membership acceptance
                _send_email_on_group_membership_acceptance(membership_request)
                if membership_request.invitation_to is not None:
                    message = "You just joined the group '{}'".format(membership_request.group_to_join.name)
                else:
                    message = "User '{}' just joined the group '{}'".format(membership_request.request_from.first_name,
                                                                            membership_request.group_to_join.name)

                messages.info(request, message)
                # redirect to group profile page
                return HttpResponseRedirect('/group/{}/'.format(membership_request.group_to_join.id))
            else:
                messages.error(request, "The link you clicked is no longer valid. Please ask to "
                                        "join the group again.")
                return redirect("/")
        else:
            messages.error(request, "The group is no longer active.")
            return redirect("/")
    else:
        messages.error(request, "The link you clicked is no longer valid.")
        return redirect("/")


@login_required
def act_on_group_membership_request(request, membership_request_id, action, *args, **kwargs):
    """
    Take action (accept or decline) on group membership request

    :param request: requesting user is either owner of the group taking action on a request from a user
                    or a user taking action on a invitation to join a group from a group owner
    :param membership_request_id: id of the membership request object (an instance of GroupMembershipRequest)
                                  to act on
    :param action: need to have a value of either 'accept' or 'decline'
    :return:
    """

    accept_request = action == 'accept'
    user_acting = request.user

    try:
        membership_request = GroupMembershipRequest.objects.get(pk=membership_request_id)
    except ObjectDoesNotExist:
        messages.error(request, 'No matching group membership request was found')
    else:
        if membership_request.group_to_join.gaccess.active:
            try:
                user_acting.uaccess.act_on_group_membership_request(membership_request, accept_request)
                if accept_request:
                    message = 'Membership request accepted'
                    messages.success(request, message)
                    # send email to notify membership acceptance
                    _send_email_on_group_membership_acceptance(membership_request)
                else:
                    message = 'Membership request declined'
                    messages.success(request, message)

            except PermissionDenied as ex:
                messages.error(request, ex.message)
        else:
            messages.error(request, "Group is not active")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def unshare_resource_with_group(request, shortkey, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    group_to_unshare_with = utils.group_from_id(group_id)
    ajax_response_data = {'status': 'success'}
    try:
        user.uaccess.unshare_resource_with_group(res, group_to_unshare_with)
        if user not in res.raccess.view_users:
            # user has no explicit access to the resource - redirect to resource listing page
            ajax_response_data['redirect_to'] = '/my-resources/'
    except PermissionDenied as exp:
        ajax_response_data['status'] = 'error'
        ajax_response_data['message'] = exp.message

    return JsonResponse(ajax_response_data)


@login_required
def delete_user_group(request, group_id, *args, **kwargs):
    """This one is not really deleting the group object, rather setting the active status
    to False (delete) which can be later restored (undelete) )"""
    try:
        hydroshare.set_group_active_status(request.user, group_id, False)
        messages.success(request, "Group delete was successful.")
    except PermissionDenied:
        messages.error(request, "Group delete errors: You don't have permission to delete"
                                " this group.")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def restore_user_group(request, group_id, *args, **kwargs):
    """This one is for setting the active status of the group back to True"""
    try:
        hydroshare.set_group_active_status(request.user, group_id, True)
        messages.success(request, "Group restore was successful.")
    except PermissionDenied:
        messages.error(request, "Group restore errors: You don't have permission to restore"
                                " this group.")

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


class GroupView(TemplateView):
    template_name = 'pages/group.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GroupView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        group_id = kwargs['group_id']
        g = Group.objects.get(pk=group_id)
        u = User.objects.get(pk=self.request.user.id)
        u.is_group_owner = u.uaccess.owns_group(g)
        u.is_group_editor = g in u.uaccess.edit_groups
        u.is_group_viewer = g in u.uaccess.view_groups

        g.join_request_waiting_owner_action = g.gaccess.group_membership_requests.filter(request_from=u).exists()
        g.join_request_waiting_user_action = g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
        g.join_request = g.gaccess.group_membership_requests.filter(invitation_to=u).first()

        group_resources = []
        # for each of the resources this group has access to, set resource dynamic
        # attributes (grantor - group member who granted access to the resource) and (date_granted)
        for res in g.gaccess.view_resources:
            grp = GroupResourcePrivilege.objects.get(resource=res, group=g)
            res.grantor = grp.grantor
            res.date_granted = grp.start
            group_resources.append(res)
        group_resources = sorted(group_resources, key=lambda  x:x.date_granted, reverse=True)

        # TODO: need to sort this resource list using the date_granted field

        return {
            'profile_user': u,
            'group': g,
            'view_users': g.gaccess.get_users_with_explicit_access(PrivilegeCodes.VIEW),
            'group_resources': group_resources,
            'add_view_user_form': AddUserForm(),
        }

class MyGroupsView(TemplateView):
    template_name = 'pages/my-groups.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MyGroupsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        u = User.objects.get(pk=self.request.user.id)

        groups = u.uaccess.view_groups
        group_membership_requests = GroupMembershipRequest.objects.filter(invitation_to=u).exclude(
            group_to_join__gaccess__active=False).all()
        # for each group object, set a dynamic attribute to know if the user owns the group
        for g in groups:
            g.is_group_owner = u.uaccess.owns_group(g)

        active_groups = [g for g in groups if g.gaccess.active]
        inactive_groups = [g for g in groups if not g.gaccess.active]
        my_pending_requests = GroupMembershipRequest.objects.filter(request_from=u).exclude(
            group_to_join__gaccess__active=False)
        return {
            'profile_user': u,
            'groups': active_groups,
            'inactive_groups': inactive_groups,
            'my_pending_requests': my_pending_requests,
            'group_membership_requests': group_membership_requests
        }
