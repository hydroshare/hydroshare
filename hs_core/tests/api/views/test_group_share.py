import json
import os
import shutil

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.urls import reverse

from rest_framework import status

from hs_core.testing import ViewTestCase
from hs_core import hydroshare
from hs_core.views import share_group_with_user, unshare_group_with_user, \
    make_group_membership_request, act_on_group_membership_request
from hs_access_control.models import PrivilegeCodes


class TestShareGroup(ViewTestCase):

    def setUp(self):
        super(TestShareGroup, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.john = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.mike = hydroshare.create_account(
            'mk@gmail.com',
            username='mikeJ',
            first_name='Mike',
            last_name='Johnson',
            superuser=False,
            password='mkmypassword',
            groups=[]
        )

        self.lisa = hydroshare.create_account(
            'lm@gmail.com',
            username='lisaM',
            first_name='Lisa',
            last_name='Martha',
            superuser=False,
            password='lmmypassword',
            groups=[]
        )

        # crate a group for testing member access to group
        self.test_group = self.john.uaccess.create_group(
            title='Test Group',
            description="This is to test group access to user",
            purpose="Testing user access to group")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestShareGroup, self).tearDown()

    def test_share_group(self):
        # here we are testing share_group_with_user view function

        # test making mike as a member of test_group with view permission

        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)
        # give mike view permission on the group
        self._check_share_with_user(privilege='view')
        # test mike is now a member of test_group
        self.assertIn(self.mike, self.test_group.gaccess.members)

        # give mike edit permission on the group
        self._check_share_with_user(privilege='edit')
        # test mike is now has edit permission on test_group
        self.assertIn(self.mike, self.test_group.gaccess.edit_users)

        # give mike owner permission on the group
        self._check_share_with_user(privilege='owner')
        # test mike is now has owner permission on test_group
        self.assertIn(self.mike, self.test_group.gaccess.owners)

    def test_share_group_failure(self):
        # here we are testing share_group_with_user view function

        # test making mike as a member of test_group with view permission

        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)
        # let mike give himself view permission on the group - should fail
        privilege = 'view'
        url_params = {'group_id': self.test_group.id, 'privilege': privilege,
                      'user_id': self.mike.id}
        url = reverse('share_group_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.mike
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = share_group_with_user(request, group_id=self.test_group.id,
                                         privilege=privilege, user_id=self.mike.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'error']
        self.assertNotEqual(len(success_messages), 0)
        self.test_group.gaccess.refresh_from_db()
        # test mike is still not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)

    def test_unshare_group(self):
        # here we are testing unshare_group_with_user view function

        # test removing mike as a member of test_group

        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)

        # make mike a member of the test_group
        self.john.uaccess.share_group_with_user(self.test_group, self.mike, PrivilegeCodes.VIEW)
        # test mike is now a member of test_group
        self.assertIn(self.mike, self.test_group.gaccess.members)
        url_params = {'group_id': self.test_group.id, 'user_id': self.mike.id}
        url = reverse('unshare_group_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = unshare_group_with_user(request, group_id=self.test_group.id,
                                           user_id=self.mike.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        self.test_group.gaccess.refresh_from_db()
        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)

    def test_unshare_group_failure(self):
        # here we are testing unshare_group_with_user view function

        # test mike (unauthorized) removing john from test_group - should fail

        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)

        # test john is a member of test_group
        self.assertIn(self.john, self.test_group.gaccess.members)

        url_params = {'group_id': self.test_group.id, 'user_id': self.john.id}
        url = reverse('unshare_group_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        # let mike try to remove john
        request.user = self.mike
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = unshare_group_with_user(request, group_id=self.test_group.id,
                                           user_id=self.john.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        err_messages = [m for m in flag_messages if m.tags == 'error']
        self.assertNotEqual(len(err_messages), 0)
        self.test_group.gaccess.refresh_from_db()
        # test john is still a member of test_group
        self.assertIn(self.john, self.test_group.gaccess.members)

    def test_invite_user_to_join(self):
        # here we are testing make_group_membership_request view function
        # where the owner of a group invites another user to join the group

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let john invite mike to join test_group
        self._check_membership_request()
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)

    def test_invite_user_to_join_failure(self):
        # here we are testing make_group_membership_request view function
        # where a non-owner of a group invites another user to join the group -should fail

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        url_params = {'group_id': self.test_group.id, 'user_id': self.mike.id}
        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url, data={})
        # lisa is not the owner of the group - invitation should fail
        request.user = self.lisa
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = make_group_membership_request(request, group_id=self.test_group.id,
                                                 user_id=self.mike.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_content = json.loads(response.content)
        self.assertEqual(response_content['status'], "error")
        self.test_group.gaccess.refresh_from_db()
        # there should not be any pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)

    def test_request_to_join(self):
        # here we are testing make_group_membership_request view function
        # where a user requesting to join a group

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let mike make request to join test group
        self._check_membership_request(invitation=False)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)

    def test_request_to_join_failure(self):
        # here we are testing make_group_membership_request view function
        # where a user requesting to join a group

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let mike make request to join test group
        self._check_membership_request(invitation=False)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)

        # now if mike again makes a request to join the same group - should fail
        url_params = {'group_id': self.test_group.id}
        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.mike
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = make_group_membership_request(request, group_id=self.test_group.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_content = json.loads(response.content)
        self.assertEqual(response_content["status"], "error")
        self.test_group.gaccess.refresh_from_db()
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)

    def test_act_on_membership_invitation(self):
        # here we are testing act_on_group_membership_request view function
        # user accepting/rejecting invitation to join a group

        # test accepting invitation

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let john invite mike to join test group
        self.john.uaccess.create_group_membership_request(self.test_group, self.mike)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        membership_request = self.test_group.gaccess.group_membership_requests.first()
        self._check_act_on_membership_request(self.mike, membership_request, 'accept')
        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # test mike is a member of test_group
        self.assertIn(self.mike, self.test_group.gaccess.members)

        # test rejecting invitation

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let john invite lisa to join test group
        self.john.uaccess.create_group_membership_request(self.test_group, self.lisa)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        membership_request = self.test_group.gaccess.group_membership_requests.first()
        self._check_act_on_membership_request(self.lisa, membership_request, 'reject')
        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # test lisa is not a member of test_group
        self.assertNotIn(self.lisa, self.test_group.gaccess.members)

    def test_act_on_membership_invitation_failure(self):
        # here we are testing act_on_group_membership_request view function
        # user accepting/rejecting invitation to join a group

        # test action on invitation request failure

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let john invite mike to join test group
        self.john.uaccess.create_group_membership_request(self.test_group, self.mike)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        membership_request = self.test_group.gaccess.group_membership_requests.first()
        # let lisa (not a group member try to act on this invitation) - should fail
        self._check_act_on_membership_request(self.lisa, membership_request, 'accept',
                                              success=False)
        # there should be 1 pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)

    def test_act_on_membership_request(self):
        # here we are testing act_on_group_membership_request view function
        # group owner accepting/rejecting user request to join a group

        # test accepting user request to join

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let mike request to join test group
        self.mike.uaccess.create_group_membership_request(self.test_group)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        membership_request = self.test_group.gaccess.group_membership_requests.first()
        # let john (group owner) accept mike's request
        self._check_act_on_membership_request(self.john, membership_request, 'accept')
        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # test mike is a member of test_group
        self.assertIn(self.mike, self.test_group.gaccess.members)

        # test rejecting request to join group

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let lisa request to join test group
        self.lisa.uaccess.create_group_membership_request(self.test_group)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        membership_request = self.test_group.gaccess.group_membership_requests.first()
        # let john reject lisa's request
        self._check_act_on_membership_request(self.john, membership_request, 'reject')
        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # test lisa is not a member of test_group
        self.assertNotIn(self.lisa, self.test_group.gaccess.members)

    def test_act_on_membership_request_failure(self):
        # here we are testing act_on_group_membership_request view function
        # group owner accepting/rejecting user request to join a group

        # test accepting user request to join failure

        # there should not be any pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 0)
        # let mike request to join test group
        self.mike.uaccess.create_group_membership_request(self.test_group)
        # there should 1 pending request at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        membership_request = self.test_group.gaccess.group_membership_requests.first()
        # let lisa (not a group owner) try to accept mike's request - should fail
        self._check_act_on_membership_request(self.lisa, membership_request, 'accept',
                                              success=False)
        # there should be 1 pending requests at this point
        self.assertEqual(len(self.test_group.gaccess.group_membership_requests), 1)
        # test mike is not a member of test_group
        self.assertNotIn(self.mike, self.test_group.gaccess.members)

    def _check_share_with_user(self, privilege):

        url_params = {'group_id': self.test_group.id, 'privilege': privilege,
                      'user_id': self.mike.id}
        url = reverse('share_group_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = share_group_with_user(request, group_id=self.test_group.id,
                                         privilege=privilege, user_id=self.mike.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        self.test_group.gaccess.refresh_from_db()

    def _check_membership_request(self, invitation=True):

        user_id = None
        if invitation:
            user_id = self.mike.id
            user = self.john
        else:
            user = self.mike

        if user_id is not None:
            url_params = {'group_id': self.test_group.id, 'user_id': user_id}
        else:
            url_params = {'group_id': self.test_group.id}

        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = user
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        if user_id is not None:
            response = make_group_membership_request(request, group_id=self.test_group.id,
                                                     user_id=user_id)
        else:
            response = make_group_membership_request(request, group_id=self.test_group.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_group.gaccess.refresh_from_db()

    def _check_act_on_membership_request(self, acting_user, membership_request, action,
                                         success=True):

        url_params = {'membership_request_id': membership_request.id, 'action': action}
        url = reverse('act_on_group_membership_request', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = acting_user
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = act_on_group_membership_request(request,
                                                   membership_request_id=membership_request.id,
                                                   action=action)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        tag = 'success' if success else 'error'
        session_messages = [m for m in flag_messages if m.tags == tag]
        self.assertNotEqual(len(session_messages), 0)
        self.test_group.gaccess.refresh_from_db()
