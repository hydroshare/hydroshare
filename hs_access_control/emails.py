import logging

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpRequest
from mezzanine.conf import settings

from .models.community import RequestCommunity
from .models.invite import GroupCommunityRequest
from .enums import CommunityRequestEvents, CommunityGroupEvents


class CommunityGroupEmailNotification:
    """A class for sending email notifications related to group association with a community"""

    def __init__(self, request: HttpRequest, group_community_request: GroupCommunityRequest,
                 on_event: CommunityGroupEvents):
        self.request = request
        self.group_community_request = group_community_request
        self.on_event = on_event

    def send(self):
        """Sends email"""
        site_domain = f"{self.request.scheme}://{self.request.get_host()}"
        group_url = f"{site_domain}/group/{self.group_community_request.group.id}"
        community_url = f"{site_domain}/community/{self.group_community_request.community.id}"

        if self.on_event == CommunityGroupEvents.INVITED:
            # send emails to all group owners
            recipient_emails = [grp_owner.email for grp_owner in self.group_community_request.group.gaccess.owners]
            subject = "Invitation for your group to join Community"
            message = f"""Dear Group Owners,
            <p>Your HydroShare Group <a href="{group_url}">
            {self.group_community_request.group.name}</a> has been invited to join the HydroShare
            Community <a href="{community_url}">
            {self.group_community_request.community.name}</a> To act on this request, please visit the landing
            page for your Group in HydroShare, click on the Communities tab, and then select whether you want to
            accept or reject this request.</p>
            <p>Thank you,</p>
            <p>The HydroShare Team</p>
            """
        elif self.on_event == CommunityGroupEvents.JOIN_REQUESTED:
            # send emails to all community owners
            recipient_emails = [com_owner.email for com_owner in self.group_community_request.community.owners]
            subject = "Group wants join your Community"
            message = f"""Dear Community Owners,
           <p>The HydroShare Group <a href="{group_url}">{self.group_community_request.group.name}</a>
            has requested to join your HydroShare Community <a href="{community_url}">
           {self.group_community_request.community.name}</a>. To act on this request, please visit the landing
           page for your Community in HydroShare, Click on the Groups tab, and then select whether you want to
           accept or reject this request.</p>
           <p>Thank you,</p>
           <p>The HydroShare Team</p>
           """
        elif self.on_event == CommunityGroupEvents.DECLINED:
            if self.group_community_request.community_owner is None:
                # declined request was originally created by a group owner and was declined by one of the community
                # owners. Notify the group owner who made the request
                recipient_emails = [self.group_community_request.group_owner.email]
                subject = "Group request to join a Community was declined"
                message = f"""Dear {self.group_community_request.group_owner.first_name},
                <p>Your request for HydroShare Group <a href="{group_url}">
                {self.group_community_request.group.name}</a> to join HydroShare Community
                <a href="{community_url}">{self.group_community_request.community.name}</a> was declined.</p>
                <p>Thank you,</p>
                <p>The HydroShare Team</p>
                """
            else:
                # an invitation for a group to join a community was declined by one of the group owners
                # notify the community owner who invited
                recipient_emails = [self.group_community_request.community_owner.email]
                subject = "Group invitation join a Community was declined"
                message = f"""Dear {self.group_community_request.community_owner.first_name},
                <p>Your invitation to HydroShare Group <a href="{group_url}">
                {self.group_community_request.group.name}</a> to join the HydroShare Community
                <a href="{community_url}">
                {self.group_community_request.community.name}</a> was declined.</p>
                <p>Thank you,</p>
                <p>The HydroShare Team</p>
                """
        else:
            assert self.on_event == CommunityGroupEvents.APPROVED
            # group request join community approved event
            if self.group_community_request.community_owner is None:
                # request approved by the community owner - so notify group owner
                recipient_emails = [self.group_community_request.group_owner.email]
                subject = "Group request to join a Community was approved"
                message = f"""Dear {self.group_community_request.group_owner.first_name},
                <p>Your request for your HydroShare Group <a href="{group_url}">
                {self.group_community_request.group.name}</a> to join the HydroShare
                Community <a href="{community_url}">
                {self.group_community_request.community.name}</a> was approved.</p>
                <p>Thank you,</p>
                <p>The HydroShare Team</p>
                """
            else:
                # request accepted by the group owner - so notify community owner
                subject = "Group invitation to join a Community was accepted"
                recipient_emails = [self.group_community_request.community_owner.email]
                message = f"""Dear {self.group_community_request.community_owner.first_name},
                <p>Your invitation for HydroShare Group <a href="{group_url}">
                {self.group_community_request.group.name}</a> to join the HydroShare Community
                <a href="{community_url}">{self.group_community_request.community.name}</a> was accepted.</p>
                <p>Thank you,</p>
                <p>The HydroShare Team</p>
                """
        from hs_core.views.utils import get_default_admin_user
        admin_user = get_default_admin_user()
        send_mail(subject=subject, message=message, html_message=message, from_email=admin_user.email,
                  recipient_list=recipient_emails, fail_silently=True)


class CommunityRequestEmailNotification:
    """A class for sending emails related to creating a new community"""
    def __init__(self, request: HttpRequest, community_request: RequestCommunity, on_event: CommunityRequestEvents):
        self.request = request
        self.community_request = community_request
        self.on_event = on_event

    def send(self):
        """Sends email"""
        site_domain = f"{self.request.scheme}://{self.request.get_host()}"
        community_request_url = f"{site_domain}/communities/manage-requests/{self.community_request.id}"
        if self.on_event == CommunityRequestEvents.CREATED:
            mail_to = _get_default_mail_to_user()
            if not mail_to:
                err_msg = "No support email was found to send email for approving request to create a community"
                logging.error(err_msg)
                return

            recipient_emails = [mail_to]

            subject = "New HydroShare Community Create Request"
            message = f"""Dear HydroShare Admin,
            <p>User {self.community_request.requested_by.first_name} is requesting creation of the following
            HydroShare Community. Please click on the link below to review this request.
            <p><a href="{community_request_url}">
            {self.community_request.community_to_approve.name}</a></p>
            <p>Thank you,</p>
            <p>The HydroShare Team</p>
            """

        elif self.on_event == CommunityRequestEvents.RESUBMITTED:
            mail_to = _get_default_mail_to_user()
            if not mail_to:
                err_msg = "No support email was found to send email for approving a resubmission request " \
                          "to create a community"
                logging.error(err_msg)
                return

            recipient_emails = [mail_to]

            subject = "New HydroShare Community Request Resubmission"
            requested_by = self.community_request.requested_by.first_name
            message = f"""Dear HydroShare Admin,
            <p>User {requested_by} has resubmitted a request to create the following HydroShare Community.
            Please click on the link below to review this request.
            <p><a href="{community_request_url}">
            {self.community_request.community_to_approve.name}</a></p>
            <p>Thank you,</p>
            <p>The HydroShare Team</p>
            """

        elif self.on_event == CommunityRequestEvents.DECLINED:
            recipient_emails = [self.community_request.requested_by.email]
            subject = "HydroShare Community Create Request Declined"
            message = f"""Dear {self.community_request.requested_by.first_name},
            <p>Your request to create the HydroShare Community
            <a href="{community_request_url}">
            {self.community_request.community_to_approve.name}</a> was not approved due to
            the reason stated below:</p>
            <p>{self.community_request.decline_reason}</p>
            <p>Thank you,</p>
            <p>The HydroShare Team</p>
            """
        else:
            # community request approved event
            community_url = f"{site_domain}/community/{self.community_request.community_to_approve.id}"
            assert self.on_event == CommunityRequestEvents.APPROVED
            recipient_emails = [self.community_request.requested_by.email]
            subject = "HydroShare Community Create Request Approved"
            message = f"""Dear {self.community_request.requested_by.first_name},
            <p>Your request to create the HydroShare Community
            <a href="{community_url}">
            {self.community_request.community_to_approve.name}</a> has been approved.</p>
            <p>Thank you,</p>
            <p>The HydroShare Team</p>
            """

        from hs_core.views.utils import get_default_admin_user
        admin_user = get_default_admin_user()
        try:
            send_mail(subject=subject, message=message, html_message=message, from_email=admin_user.email,
                      recipient_list=recipient_emails)
        except Exception as err:
            err_msg = f"Failed to email message '{message}'. Error: {str(err)}"
            logging.error(err_msg)


def _get_default_mail_to_user():
    mail_to = ""
    if hasattr(settings, 'DEFAULT_SUPPORT_EMAIL'):
        mail_to = settings.DEFAULT_SUPPORT_EMAIL
    if not mail_to:
        try:
            mail_to = User.objects.get(username__iexact='CUAHSI').email
        except User.DoesNotExist:
            pass
    return mail_to
