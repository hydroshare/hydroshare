from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import share_group_with_user, unshare_group_with_user
from hs_access_control.models import PrivilegeCodes


class TestShareGroup(TestCase):

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

        # crate a group for testing member access to group
        self.test_group = self.john.uaccess.create_group(
            title='Test Group',
            description="This is to test group access to user",
            purpose="Testing user access to group")

        self.factory = RequestFactory()

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
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

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
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

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
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

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

    def _check_share_with_user(self, privilege):

        url_params = {'group_id': self.test_group.id, 'privilege': privilege,
                      'user_id': self.mike.id}
        url = reverse('share_group_with_user', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(self.test_group.id)
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

        response = share_group_with_user(request, group_id=self.test_group.id,
                                         privilege=privilege, user_id=self.mike.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        self.test_group.gaccess.refresh_from_db()

    def _set_request_message_attributes(self, request):
        # the following 3 lines are for preventing error in unit test due to the view being
        # tested uses messaging middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

    def _add_session_to_request(self, request):
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
